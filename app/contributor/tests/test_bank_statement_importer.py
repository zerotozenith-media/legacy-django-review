from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from contributor.models import MiscellaneousUser, MiscellaneousContribution
from organization.models import LocalChurchName, LocalChurch
from utils.test_db import Testdb
import os

BANK_STATEMENT_IMPORTER_URL = reverse('bank_statement_importer')

base_dir = os.path.dirname(os.path.abspath(__file__))  # Current script directory
file_path = os.path.join(base_dir, 'files', 'fake_bank_statement.pdf')


class BankStatementImporterViewTest(TestCase):
    def setUp(self):
        # Create test user and log in
        self.testdb = Testdb()

        self.client = Client()
        self.user = self.testdb.create_user()
        self.client.force_login(self.user)
        self.local_church = self.testdb.create_local_church()
        self.region = self.testdb.create_region(region_overseer=self.user)

    def test_get_local_churches_by_region(self):
        """Test retrieving local churches by region_id."""
        # Create test local church names
        name_1 = LocalChurchName.objects.create(title="First Church")
        name_2 = LocalChurchName.objects.create(title="Second Church")
        local_church_1 = self.testdb.create_local_church(local_church_name=name_1, region=self.region)
        local_church_2 = self.testdb.create_local_church(local_church_name=name_2, region=self.region)

        region_id = self.region.id

        # Retrieve local churches for the given region_id
        local_churches = LocalChurch.objects.filter(region_id=region_id)

        # Assertions
        self.assertEqual(local_churches.count(), 2)
        self.assertIn(local_church_1, local_churches)
        self.assertIn(local_church_2, local_churches)
        self.assertEqual(local_churches[0].region.id, region_id)

    def test_post_valid_pdf_file(self):
        """Test that a valid PDF file processes successfully."""
        with open(file_path, "rb") as pdf_file:
            res = self.client.post(BANK_STATEMENT_IMPORTER_URL, {
                'region': self.region.id,
                "account_type": "current_account",
                'file': SimpleUploadedFile(file_path, pdf_file.read(), content_type="application/pdf")
            })
        self.assertEqual(res.status_code, 200)
        self.assertIn("Bank statement uploaded and processed successfully!", res.content.decode())

        # Check if the miscellaneous_user is created
        miscellaneous_user = MiscellaneousUser.objects.filter(full_name__exact="Rachel E. Thomas",
                                                              registered_miscellaneous=self.user).first()
        self.assertIsNotNone(miscellaneous_user)

        # Check if the miscellaneous_contribution is created
        miscellaneous_contribution = MiscellaneousContribution.objects.filter(contributor=miscellaneous_user).first()
        self.assertIsNotNone(miscellaneous_contribution)
        self.assertEqual(miscellaneous_contribution.amount, 923.00)
        self.assertEqual(miscellaneous_contribution.deposited_date.strftime('%Y-%m-%d'), "2024-08-28")

    def test_login_required(self):
        """Test that the bank statement importer view requires authentication."""
        self.client.logout()
        res = self.client.get(BANK_STATEMENT_IMPORTER_URL)
        self.assertEqual(res.status_code, 302)

        # Assert the user is redirected to the login page
        login_url = f"{reverse('login')}?next={BANK_STATEMENT_IMPORTER_URL}"
        self.assertRedirects(res, login_url)
