from django.test import TestCase
from django.utils.timezone import now

from contributor.models import Contribution, TaxReceipt, MiscellaneousUser, MiscellaneousContribution, \
    AnonymousContribution, EmailQueue
from decimal import Decimal

from utils.test_db import Testdb


class ContributionModelTests(TestCase):
    """ Test for the models in the contributors app"""

    def setUp(self):
        self.testdb = Testdb()
        self.user = self.testdb.create_user()
        self.local_church = self.testdb.create_local_church()
        self.date = now().replace(year=2023, month=3, day=1).date()

    def test_create_contribution(self):
        contribution = Contribution.objects.create(
            contributor=self.user,
            amount=Decimal('100.00'),
            deposited_date=self.date,
            payment_type='offerings_can',
            special_contribution=True,
            month='January',
            local_church=self.local_church
        )

    def test_default_payment_type(self):
        contribution = Contribution.objects.create(
            contributor=self.user,
            amount=Decimal('50.00'),
            deposited_date=self.date
        )
        self.assertEqual(contribution.payment_type, 'offerings_can')

    def test_create_tax_receipt(self):
        tax_receipt = TaxReceipt.objects.create(receipt_receiver=self.user, pdf_file=None)
        self.assertEqual(tax_receipt.receipt_receiver, self.user)

    def test_create_miscellaneous_user(self):
        user = MiscellaneousUser.objects.create(
            full_name="John Doe",
            first_name="John",
            middle_name="Middle",
            last_name="Doe",
            email="johndoe@example.com",
            address="123 Main St"
        )
        self.assertEqual(str(user), "John Doe")
        self.assertEqual(user.email, "johndoe@example.com")

    def test_create_miscellaneous_contribution(self):
        misc_user = self.testdb.create_miscellaneous_user()
        contribution = MiscellaneousContribution.objects.create(
            contributor=misc_user,
            deposited_date=self.date,
            amount=Decimal('150.00'),
            payment_type='interec_e_transfer',
            special_contribution=False,
            month='March',
            local_church=self.local_church
        )
        self.assertEqual(str(contribution), f'150.00 deposit on{self.date}')

    def test_create_anonymous_contribution(self):
        contribution = AnonymousContribution.objects.create(
            deposited_date=self.date,
            amount=Decimal('200.00'),
            payment_type='direct_transfer',
            special_contribution=True,
            month='April',
            local_church=self.local_church
        )
        self.assertEqual(str(contribution), f'200.00 deposited on{self.date}')

    def test_create_email_queue(self):
        email_queue = EmailQueue.objects.create(
            contributor_id=1,
            report_year=2023,
            email="test@example.com",
            report_type="offerings"
        )
        self.assertEqual(email_queue.email, "test@example.com")
        self.assertEqual(email_queue.report_year, 2023)
