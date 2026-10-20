"""
Tests for the counted_via_contributions flag on income Source.

The defect these cover
----------------------
Tithe, offering and special contribution money is recorded on the
Contributions screens and summed by the financial report from the three
Contribution models. The report also sums Income rows grouped by Source. If
the same money is entered on both screens, it is counted twice.

The report used to guard against this by comparing a source's lowercased name
against a hardcoded set:

    "tithe & offering cad", "tithe & offering usd", "special contribution cad"

The seed command creates a source named "Tithe and Offerings". That string is
not in the set, so the guard never fired. Users can also create sources with
any name they type, from the Add Income form, so no fixed list of names could
have held.

The guard is now a database flag, which cannot be defeated by a rename.
"""

from decimal import Decimal

from django.test import TestCase
from django.utils.timezone import now

from contributor.models import Contribution, TransactionType
from financial_reports.services import build_income_expenditure_summary
from income.models import Income, Source
from income.selectors import looks_like_contribution_source, selectable_sources
from organization.models import LocalChurch, LocalChurchName, Region


class ContributionSourceDetectionTests(TestCase):
    """The name test used when a source is created or migrated."""

    def test_detects_tithe_and_offering_spellings(self):
        for name in [
            "Tithe and Offerings",
            "Tithe & Offering CAD",
            "tithe & offering usd",
            "Tithes",
            "OFFERING",
            "Special Contribution CAD",
            "  offerings  ",
        ]:
            with self.subTest(name=name):
                self.assertTrue(
                    looks_like_contribution_source(name),
                    f"{name!r} should be detected as contribution money",
                )

    def test_leaves_ordinary_sources_alone(self):
        for name in [
            "Charity Donations",
            "Material Sales",
            "Other Donations",
            "Sales",
            "Interest on savings accounts",
            "Publication",
            None,
            "",
        ]:
            with self.subTest(name=name):
                self.assertFalse(
                    looks_like_contribution_source(name),
                    f"{name!r} should not be flagged",
                )


class SelectableSourcesTests(TestCase):
    """What the Add and Edit Income forms may offer."""

    @classmethod
    def setUpTestData(cls):
        cls.ordinary = Source.objects.create(
            name="Charity Donations", type="Income"
        )
        cls.flagged = Source.objects.create(
            name="Tithe and Offerings",
            type="Income",
            counted_via_contributions=True,
        )

    def test_add_form_excludes_flagged_sources(self):
        names = list(selectable_sources().values_list("name", flat=True))
        self.assertIn("Charity Donations", names)
        self.assertNotIn("Tithe and Offerings", names)

    def test_edit_form_keeps_the_already_saved_flagged_source(self):
        """An existing record pointing at a flagged source must keep it.

        Without this, opening such a record and pressing save would silently
        clear or change its source, because the saved value would not be among
        the valid choices.
        """
        names = list(
            selectable_sources(
                current_source_id=self.flagged.pk
            ).values_list("name", flat=True)
        )
        self.assertIn("Tithe and Offerings", names)
        self.assertIn("Charity Donations", names)

    def test_edit_form_still_excludes_other_flagged_sources(self):
        other_flagged = Source.objects.create(
            name="Special Contribution CAD",
            type="Income",
            counted_via_contributions=True,
        )
        names = list(
            selectable_sources(
                current_source_id=self.flagged.pk
            ).values_list("name", flat=True)
        )
        self.assertIn("Tithe and Offerings", names)
        self.assertNotIn(other_flagged.name, names)


class DoubleCountingRegressionTests(TestCase):
    """The behaviour the old name-matching guard failed to deliver.

    This is the test that would have caught the original defect: a source
    named "Tithe and Offerings", which the hardcoded list could never match.
    """

    @classmethod
    def setUpTestData(cls):
        cls.year = now().year
        cls.region = Region.objects.create(name="Toronto")
        cls.local_church = LocalChurch.objects.create(
            local_church_name=LocalChurchName.objects.create(title="Toronto Central"),
            region=cls.region,
        )

        # $500 of tithe, recorded properly on the Contributions side.
        Contribution.objects.create(
            amount=Decimal("500.00"),
            deposited_date=now().date(),
            payment_type=TransactionType.OFFERINGS_CAN.value,
            special_contribution=False,
            local_church=cls.local_church,
        )

        # The same $500 entered again as Income against a tithe source, which
        # is exactly the mistake the flag exists to neutralise.
        cls.tithe_source = Source.objects.create(
            name="Tithe and Offerings",
            type="Income",
            counted_via_contributions=True,
        )
        Income.objects.create(
            amount=Decimal("500.00"),
            description="Duplicate entry of the same tithe",
            date=now().date(),
            source=cls.tithe_source,
            region=cls.region,
            local_church=cls.local_church,
        )

    def _income_row_labels(self, report):
        return [row["label"] for row in report["income_rows"]]

    def test_flagged_source_is_not_listed_as_its_own_income_row(self):
        report = build_income_expenditure_summary(self.year)
        self.assertNotIn("Tithe and Offerings", self._income_row_labels(report))

    def test_tithe_is_counted_once_not_twice(self):
        report = build_income_expenditure_summary(self.year)

        tithe_rows = [
            row for row in report["income_rows"]
            if row["label"] == "Tithe & Offering CAD $"
        ]
        self.assertEqual(len(tithe_rows), 1)
        self.assertEqual(tithe_rows[0]["total"], Decimal("500.00"))

        # The duplicate Income row must not appear anywhere in the income side.
        self.assertEqual(
            sum(row["total"] for row in report["income_rows"]),
            Decimal("500.00"),
            "The same $500 was counted more than once",
        )

    def test_unflagging_the_source_restores_the_double_count(self):
        """Confirms the flag is what prevents it, not something else.

        If this test ever fails, the exclusion has stopped depending on the
        flag and the protection has moved somewhere unverified.
        """
        Source.objects.filter(pk=self.tithe_source.pk).update(
            counted_via_contributions=False
        )
        report = build_income_expenditure_summary(self.year)
        self.assertEqual(
            sum(row["total"] for row in report["income_rows"]),
            Decimal("1000.00"),
        )
