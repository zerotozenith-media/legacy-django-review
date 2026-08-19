from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from contributor.models import MiscellaneousUser, TaxReceipt, MiscellaneousContribution, AnonymousContribution, \
    EmailQueue
from organization.models import LocalChurch, LocalChurchName, Region


class Testdb:
    def __init__(self):
        self.password = "testpass123"
        self.email = "test@example.com"
        self.local_church_pastor = self.create_user("pastor@example.com")
        self.region_overseer = self.create_user("region_overseer@example.com")
        self.local_church_name = LocalChurchName.objects.create(title="New Church")
        self.date = now().replace(year=2024, month=11, day=30).date()

    def create_user(self, email="", role=3, first_name="First", middle_name="Middle", last_name="Last", **args):
        """Create and return a new user."""
        return get_user_model().objects.create_user(
            email=email if email else self.email,
            password=self.password,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            role=role,
            **args
        )

    def create_local_church(self, local_church_name=None, local_church_pastor=None, region=None):
        """Create amd return a local church."""
        return LocalChurch.objects.create(
            local_church_name=local_church_name if local_church_name else self.local_church_name,
            local_church_pastor=local_church_pastor if local_church_name else self.local_church_pastor,
            region=region

        )

    def create_region(self, name="Toronto", region_overseer=None, gck_canada_payment=Decimal("200.00")):
        """Create amd return a region."""
        return Region.objects.create(
            name=name,
            region_overseer=region_overseer if region_overseer else self.region_overseer,
            gck_canada_payment=gck_canada_payment
        )

    @staticmethod
    def create_miscellaneous_user(email="", first_name="First", middle_name="Middle",
                                  last_name="Last", **args):
        return MiscellaneousUser.objects.create(
            full_name=f"{first_name} {last_name}",
            email=email if email else "MiscellaneousUser@example,com",
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            **args
        )

    @staticmethod
    def create_anonymous_contribution(
            local_church, deposited_date,
            payment_type="direct_transfer", amount=Decimal("500.00"),
            special_contribution=True, month="June"
    ):
        return AnonymousContribution.objects.create(
            deposited_date=deposited_date,
            payment_type=payment_type,
            amount=amount,
            special_contribution=special_contribution,
            month=month,
            local_church=local_church
        )

    @staticmethod
    def create_miscellaneous_contribution(
            contributor, local_church, deposited_date,
            payment_type="interec_e_transfer", amount=Decimal("500.00"),
            special_contribution=False, month="March"
    ):
        """Create and returns a miscellaneous contributor"""

        return MiscellaneousContribution.objects.create(
            contributor=contributor,
            deposited_date=deposited_date,
            amount=amount,
            payment_type=payment_type,
            special_contribution=special_contribution,
            month=month,
            local_church=local_church
        )

    @staticmethod
    def create_tax_receipt(receipt_receiver, pdf_file=None):
        return TaxReceipt.objects.create(receipt_receiver=receipt_receiver, pdf_file=pdf_file)

    @staticmethod
    def test_create_email_queue(
            contributor_id,
            report_year,
            email,
            report_type
    ):
        return EmailQueue.objects.create(
            contributor_id=contributor_id,
            report_year=report_year,
            email=email,
            report_type=report_type
        )
