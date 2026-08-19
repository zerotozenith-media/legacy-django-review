from datetime import date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import build_income_expenditure_summary, build_regions_bank_stmt_balances

EARLIEST_REPORT_YEAR = 2020  # adjust to whenever your records actually start


@login_required
def summary_income_expenditure(request):
    year = int(request.GET.get("year", date.today().year))
    month = request.GET.get("month")
    
    # Use the new dynamic function
    report = build_income_expenditure_summary(year, month)
    
    context = {
        "report": report,
        "year": year,
        "month": month,
        "years": range(date.today().year, EARLIEST_REPORT_YEAR - 1, -1),
        "active_tab": "summary",
    }
    return render(request, "financial_reports/summary_income_expenditure.html", context)


# --- Not built yet: render a lightweight placeholder so the sidebar link
# doesn't 404. Swap each of these out with a real view + services.py
# function as you build the corresponding sheet.

@login_required
def t3010_resources(request):
    return render(request, "financial_reports/coming_soon.html",
                  {"sheet_title": "T 3010 Resources", "active_tab": "t3010"})


@login_required
def usd_account(request):
    return render(request, "financial_reports/coming_soon.html",
                  {"sheet_title": "USD Account", "active_tab": "usd"})


@login_required
def inter_transfer_template(request):
    return render(request, "financial_reports/coming_soon.html",
                  {"sheet_title": "Inter Transfer Template", "active_tab": "transfer"})


@login_required
def asset_liability_statement(request):
    return render(request, "financial_reports/coming_soon.html",
                  {"sheet_title": "Statement of Asset & Liability", "active_tab": "asset_liab"})


@login_required
def assets_bought(request):
    return render(request, "financial_reports/coming_soon.html",
                  {"sheet_title": "Asset Bought in the Year", "active_tab": "assets_bought"})


@login_required
def regions_bank_stmt_balances(request):
    year = int(request.GET.get("year", date.today().year))
    month = request.GET.get("month")
    context = {
        "report": build_regions_bank_stmt_balances(year, month),
        "year": year,
        "month": month,
        "years": range(date.today().year, EARLIEST_REPORT_YEAR - 1, -1),
        "active_tab": "bank_stmt_balances",
    }
    return render(request, "financial_reports/regions_bank_stmt_balances.html", context)