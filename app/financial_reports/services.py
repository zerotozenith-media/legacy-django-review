from collections import defaultdict
from decimal import Decimal

from django.db.models import Sum, Value
from django.db.models.functions import Coalesce

from income.models import Income, Source
from expenses.models import Expense, Category
from organization.models import Region
from transfer.models import Transfer  # adjust import path to match your app name
from contributor.models import (
    Contribution,
    MiscellaneousContribution,
    AnonymousContribution,
    TransactionType,
)

# Preferred display order for transfer rows when their `type` values match
# (case-insensitive). Anything not in this list still shows up, sorted
# alphabetically after the known ones.
TRANSFER_TYPE_DISPLAY_ORDER = [
    "Inter transfers between accounts (DCLM)",
    "Gc Transfers from Regions",
    "DCLM Churches E Transfers",
    "Gc Deposits from Regions",
]


def _regions():
    return list(Region.objects.order_by("name"))


# ---------------------------------------------------------------------------
# Tithe / Offering / Special Contribution -> Contribution + Misc + Anonymous
# None of these three models has a direct `region` FK, only `local_church`,
# so we group through local_church__region__name and merge all three sources
# into one {region_name: total} dict per row.
# ---------------------------------------------------------------------------
def _contribution_totals(payment_type, special, year, month=None):
    totals = defaultdict(lambda: Decimal("0"))
    filters = dict(
        deposited_date__year=year,
        payment_type=payment_type,
        special_contribution=special,
    )
    if month:
        filters["deposited_date__month"] = month

    for model in (Contribution, MiscellaneousContribution, AnonymousContribution):
        qs = (
            model.objects.filter(**filters)
            .values("local_church__region__name")
            .annotate(total=Sum("amount"))
        )
        for row in qs:
            region = row["local_church__region__name"]
            if region:
                totals[region] += row["total"] or Decimal("0")

    return dict(totals)


# ---------------------------------------------------------------------------
# Everything else (Publication, Interest, Sales, Other Donations, FX, etc.)
# -> Income model, grouped by its own direct `region` FK, keyed by Source.
# ---------------------------------------------------------------------------
def _income_totals_by_source_and_region(year, month=None):
    qs = Income.objects.filter(date__year=year)
    if month:
        qs = qs.filter(date__month=month)
    qs = qs.values("source_id", "region__name").annotate(total=Sum("amount"))
    grouped = defaultdict(dict)
    for row in qs:
        grouped[row["source_id"]][row["region__name"]] = row["total"]
    return grouped


def _expense_totals_by_subcategory_and_region(year, month=None):
    """Get expense totals grouped by subcategory and region."""
    qs = Expense.objects.filter(date__year=year)
    if month:
        qs = qs.filter(date__month=month)

    # Annotate with effective region name (fallback to local_church__region)
    qs = qs.annotate(
        effective_region=Coalesce("region__name", "local_church__region__name"),
        effective_subcategory=Coalesce("sub_category__name", Value("Uncategorized")),
    )

    qs = qs.values("effective_subcategory", "effective_region").annotate(
        total=Sum("amount")
    )

    grouped = defaultdict(dict)
    for row in qs:
        subcat_name = row["effective_subcategory"]
        region_name = row["effective_region"]
        if region_name:  # Only include if region exists
            grouped[subcat_name][region_name] = row["total"]
    return grouped


# ---------------------------------------------------------------------------
# TRANSFERS WITHIN CHURCHES accounts -> Transfer model, grouped by its own
# `type` field (free text), which has a direct `region` FK.
# ---------------------------------------------------------------------------
def _transfer_totals_by_type_and_region(year, month=None):
    qs = Transfer.objects.filter(date__year=year)
    if month:
        qs = qs.filter(date__month=month)
    qs = qs.values("type", "region__name").annotate(total=Sum("amount"))
    grouped = defaultdict(dict)
    for row in qs:
        type_label = row["type"] or "Uncategorized Transfer"
        grouped[type_label][row["region__name"]] = row["total"]
    return grouped


def _sorted_transfer_types(type_labels):
    """Known transfer types first (in sheet order), everything else after, alphabetically."""
    order_lookup = {
        name.lower(): i for i, name in enumerate(TRANSFER_TYPE_DISPLAY_ORDER)
    }

    def sort_key(label):
        return (
            order_lookup.get(label.lower(), len(TRANSFER_TYPE_DISPLAY_ORDER)),
            label.lower(),
        )

    return sorted(type_labels, key=sort_key)


def _per_region_totals(rows, region_names):
    """Column-wise sum across a list of {label, values, total} rows."""
    return [
        sum((row["values"][i] for row in rows), Decimal("0"))
        for i in range(len(region_names))
    ]


def _row(label, by_region, region_names):
    values = [by_region.get(name) or Decimal("0") for name in region_names]
    return {"label": label, "values": values, "total": sum(values, Decimal("0"))}


# Sources holding tithe, offering or special contribution money are summed
# from the Contribution models above, so their Income rows must not be added
# again here.
#
# This used to be a hardcoded set of lowercased names:
#
#     "tithe & offering cad", "tithe & offering usd", "special contribution cad"
#
# which could never match the source the seed command actually creates
# ("Tithe and Offerings"), and could never match a name a user invented on the
# Add Income form. It is now the Source.counted_via_contributions flag, so
# renaming a source cannot silently reintroduce double counting.


def build_expense_groups(category_type, expense_by_subcat, region_names):
    """Build expense groups by category with subcategories."""
    groups = []

    # Get all categories of the specified type
    categories = Category.objects.filter(category_type=category_type).prefetch_related(
        "subcategories"
    )

    for category in categories:
        subrows = []
        # Get subcategories for this category
        for sub in category.subcategories.all():
            by_region = expense_by_subcat.get(sub.name, {})
            values = [by_region.get(name, Decimal("0")) for name in region_names]
            total = sum(values, Decimal("0"))
            if total > 0:  # Only include subcategories with data
                subrows.append({"label": sub.name, "values": values, "total": total})

        if subrows:  # Only include categories that have subcategories with data
            group_values = []
            for i in range(len(region_names)):
                group_values.append(
                    sum((r["values"][i] for r in subrows), Decimal("0"))
                )

            groups.append(
                {
                    "category": category.name,
                    "values": group_values,
                    "total": sum(group_values, Decimal("0")),
                    "rows": subrows,
                }
            )

    return groups


def build_income_expenditure_summary(year, month=None):
    regions = _regions()
    region_names = [r.name for r in regions]

    # ---- Tithe / Offering / Special Contribution rows ----
    income_rows = [
        _row(
            "Tithe & Offering CAD $",
            _contribution_totals(
                TransactionType.OFFERINGS_CAN.value, False, year, month
            ),
            region_names,
        ),
        _row(
            "Special Contribution CAD $",
            _contribution_totals(
                TransactionType.OFFERINGS_CAN.value, True, year, month
            ),
            region_names,
        ),
        _row(
            "Tithe & Offering USD",
            _contribution_totals(
                TransactionType.OFFERINGS_USD.value, False, year, month
            ),
            region_names,
        ),
    ]

    # ---- Remaining income rows ----
    # Sources flagged counted_via_contributions are excluded at the database
    # level, so money already counted from the Contribution models above is
    # not added a second time.
    income_by_source = _income_totals_by_source_and_region(year, month)
    other_sources = (
        Source.objects.filter(type="Income")
        .exclude(counted_via_contributions=True)
        .order_by("name")
    )
    for source in other_sources:
        income_rows.append(
            _row(source.name, income_by_source.get(source.id, {}), region_names)
        )

    total_income = sum(r["total"] for r in income_rows)

    # ---- Transfers ----
    transfer_by_type = _transfer_totals_by_type_and_region(year, month)
    transfer_rows = [
        _row(type_label, transfer_by_type[type_label], region_names)
        for type_label in _sorted_transfer_types(transfer_by_type.keys())
    ]

    # ---- TOTAL / TOTAL 2 ----
    all_income_and_transfer_rows = income_rows + transfer_rows
    total_by_region = _per_region_totals(all_income_and_transfer_rows, region_names)
    transfers_by_region = _per_region_totals(transfer_rows, region_names)
    total2_by_region = [
        total_by_region[i] - transfers_by_region[i] for i in range(len(region_names))
    ]

    total_grand = sum(total_by_region, Decimal("0"))
    total2_grand = sum(total2_by_region, Decimal("0"))

    # ---- Expenses: grouped by Category -> SubCategory ----
    expense_by_subcat = _expense_totals_by_subcategory_and_region(year, month)

    recurrent_groups = build_expense_groups(
        Category.RECURRENT, expense_by_subcat, region_names
    )
    capital_groups = build_expense_groups(
        Category.CAPITAL, expense_by_subcat, region_names
    )

    total_expense = sum(g["total"] for g in recurrent_groups)
    total_capital = sum(g["total"] for g in capital_groups)

    return {
        "regions": region_names,
        "income_rows": income_rows,
        "transfer_rows": transfer_rows,
        "total_income": total_income,
        "total_by_region": total_by_region,
        "total_grand": total_grand,
        "total2_by_region": total2_by_region,
        "total2_grand": total2_grand,
        "recurrent_groups": recurrent_groups,
        "total_expense": total_expense,
        "surplus_deficit": total2_grand - total_expense,
        "capital_groups": capital_groups,
        "total_capital": total_capital,
    }


# ---------------------------------------------------------------------------
# Regions Bank Stmt Balances -> mirrors reconciliation_and_allocation's
# app_income / app_expense (Income + Contribution models / Expense) vs
# bank_income / bank_expense (Reconciliation, recon_type='income'/'expense').
# ---------------------------------------------------------------------------
from organization.models import Reconciliation  # noqa: E402  (kept near point of use)


def _report_income_by_region(year, month=None):
    """Income model + all three Contribution models, summed by region — same
    definition as `app_income` in reconciliation_and_allocation()."""
    totals = defaultdict(lambda: Decimal("0"))

    income_qs = Income.objects.filter(date__year=year).annotate(
        effective_region=Coalesce("region__name", "local_church__region__name")
    )
    if month:
        income_qs = income_qs.filter(date__month=month)
    for row in income_qs.values("effective_region").annotate(total=Sum("amount")):
        if row["effective_region"]:
            totals[row["effective_region"]] += row["total"] or Decimal("0")

    for model in (Contribution, MiscellaneousContribution, AnonymousContribution):
        contrib_filters = {"deposited_date__year": year}
        if month:
            contrib_filters["deposited_date__month"] = month
        qs = (
            model.objects.filter(**contrib_filters)
            .values("local_church__region__name")
            .annotate(total=Sum("amount"))
        )
        for row in qs:
            if row["local_church__region__name"]:
                totals[row["local_church__region__name"]] += row["total"] or Decimal(
                    "0"
                )

    return dict(totals)


def _report_expense_by_region(year, month=None):
    """Expense model summed by region — same definition as `app_expense`."""
    qs = Expense.objects.filter(date__year=year).annotate(
        effective_region=Coalesce("region__name", "local_church__region__name")
    )
    if month:
        qs = qs.filter(date__month=month)
    qs = qs.values("effective_region").annotate(total=Sum("amount"))
    return {
        row["effective_region"]: row["total"] for row in qs if row["effective_region"]
    }


def _bank_statement_totals_by_region(recon_type, year, month=None):
    """Reconciliation model summed by region for a given recon_type."""
    qs = Reconciliation.objects.filter(recon_type=recon_type, date__year=year)
    if month:
        qs = qs.filter(date__month=month)
    qs = qs.values("region__name").annotate(total=Sum("amount"))
    return {row["region__name"]: row["total"] for row in qs if row["region__name"]}


def build_regions_bank_stmt_balances(year, month=None):
    regions = _regions()
    region_names = [r.name for r in regions]

    report_income = _report_income_by_region(year, month)
    report_expense = _report_expense_by_region(year, month)
    bank_income = _bank_statement_totals_by_region("income", year, month)
    bank_expense = _bank_statement_totals_by_region("expense", year, month)

    rows = []
    for name in region_names:
        r_income = report_income.get(name) or Decimal("0")
        b_income = bank_income.get(name) or Decimal("0")
        r_expense = report_expense.get(name) or Decimal("0")
        b_expense = bank_expense.get(name) or Decimal("0")
        rows.append(
            {
                "region": name,
                "bank_income": b_income,
                "report_income": r_income,
                "income_difference": b_income - r_income,
                "bank_expense": b_expense,
                "report_expense": r_expense,
                "expense_difference": b_expense - r_expense,
            }
        )

    totals = {
        "bank_income": sum((r["bank_income"] for r in rows), Decimal("0")),
        "report_income": sum((r["report_income"] for r in rows), Decimal("0")),
        "income_difference": sum((r["income_difference"] for r in rows), Decimal("0")),
        "bank_expense": sum((r["bank_expense"] for r in rows), Decimal("0")),
        "report_expense": sum((r["report_expense"] for r in rows), Decimal("0")),
        "expense_difference": sum(
            (r["expense_difference"] for r in rows), Decimal("0")
        ),
    }

    return {"rows": rows, "totals": totals}
