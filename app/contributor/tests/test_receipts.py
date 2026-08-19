from django.urls import reverse
from django.test import TestCase, Client
from django.utils.timezone import now
from django.core import mail
from income.models import DonationInKind
from utils.test_db import Testdb

DONATIONS_RECEIPT_URL = reverse("donations-receipt-list")


class GenerateReceiptsTests(TestCase):
    """Tests for generating receipts for users' contributions."""

    def setUp(self):
        """Set up test data and authenticate the user."""
        self.testdb = Testdb()
        self.client = Client()
        self.user = self.testdb.create_user()
        self.other_user = self.testdb.create_user(username="otheruser", email="other@example.com")
        self.client.force_login(self.user)

        self.local_church = self.testdb.create_local_church()
        self.region = self.testdb.create_region(region_overseer=self.user)

        self.donations_user = self.create_donations(self.user)
        self.donations_other_user = self.create_donations(self.other_user)

    def create_donations(self, user):
        """Helper function to create multiple donations for a user."""
        donations = []
        for i in range(5):
            donation = DonationInKind.objects.create(
                local_church=self.local_church,
                donor=user,
                donor_name=f"{user.first_name} Doe",
                donation_item=f"Item {i + 1}",
                description=f"Description for item {i + 1}",
                donation_date=now().date(),
                serial_no=f"SN{i + 1}ABC",
                estimated_value=500.00 + i * 50,
                tax_receipt_issued=True,
                tax_receipt_number=f"TRX12345{i + 1}",
                tax_receipt_date=now().date(),
            )
            donations.append(donation)
        return donations

    def test_login_required(self):
        """Test that the view requires authentication."""
        self.client.logout()
        res = self.client.get(DONATIONS_RECEIPT_URL)
        self.assertEqual(res.status_code, 302)

        login_url = f"{reverse('login')}?next={DONATIONS_RECEIPT_URL}"
        self.assertRedirects(res, login_url)

    def test_list_users_with_downloadable_donation_receipts(self):
        """Test that users with donation receipts can access the list."""
        res = self.client.get(DONATIONS_RECEIPT_URL)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, self.user.first_name)
        self.assertContains(res, self.other_user.first_name)

    # def test_download_receipt_pdf_for_selected_user(self):
    #     """Test downloading a donation receipt for the selected user as a PDF."""
    #     selected_donation = self.donations_user[2]  # Pick one of the donations for the user
    #     receipt_url = reverse("donations-receipt-download", args=[selected_donation.id])
    #     res = self.client.get(receipt_url)
    #
    #     self.assertEqual(res.status_code, 200)
    #     self.assertEqual(res["Content-Type"], "application/pdf")
    #     self.assertIn("attachment", res["Content-Disposition"])
    #     self.assertIn(selected_donation.donor_name, res.content.decode())
    #     self.assertIn(selected_donation.donation_item, res.content.decode())
    #
    # def test_send_receipt_email(self):
    #     """Test that a donation receipt is sent to the user via email."""
    #     selected_donation = self.donations_user[1]
    #     email_url = reverse("donations-receipt-email", args=[selected_donation.id])
    #     res = self.client.post(email_url)
    #
    #     self.assertEqual(res.status_code, 200)
    #     self.assertEqual(len(mail.outbox), 1)
    #     self.assertEqual(mail.outbox[0].subject, "Your Donation Receipt")
    #     self.assertIn(selected_donation.donor_name, mail.outbox[0].body)
    #     self.assertIn(selected_donation.donation_item, mail.outbox[0].body)
