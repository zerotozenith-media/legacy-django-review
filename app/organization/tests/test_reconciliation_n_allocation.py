from datetime import datetime
from io import BytesIO

from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
from organization.models import PaymentAllocation, AllocationReconciliation
from utils.test_db import Testdb
import os

# Test file path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_FILE_PATH = os.path.join(BASE_DIR, "files", "fake_bank_statement_styled_letterhead2.pdf")

PAYMENT_ALLOCATION_RECONCILIATION_URL = reverse('reconciliation_n_allocation')


class PaymentAllocationReconciliationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.testdb = Testdb()
        self.user = self.testdb.create_user(role=3)  # National Overseer
        self.client.force_login(self.user)

        # Create Region and Payment Allocation
        self.region = self.testdb.create_region(name="Ottawa")
        self.payment_allocation = PaymentAllocation.objects.create(
            region=self.region,
            date="2024-09-01",
            income=Decimal(10000.00),
            total_amount=Decimal(1000.00),
            paid_amount=Decimal(0.00),
            name="dclm",
            note="Will paid",
            payment_date="2024-09-01"
        )
        self.payment_allocation = PaymentAllocation.objects.create(
            region=self.region,
            date="2024-09-01",
            income=Decimal(10000.00),
            total_amount=Decimal(1000.00),
            paid_amount=Decimal(0.00),
            name="gck",
            note="Will paid",
            payment_date="2024-09-01"
        )
        self.region2 = self.testdb.create_region(name="Windsor")
        self.payment_allocation = PaymentAllocation.objects.create(
            region=self.region2,
            date="2024-09-01",
            income=Decimal(10000.00),
            total_amount=Decimal(1000.00),
            paid_amount=Decimal(0.00),
            name="dclm",
            note="Will paid",
            payment_date="2024-09-01"
        )
        self.payment_allocation = PaymentAllocation.objects.create(
            region=self.region2,
            date="2024-09-01",
            income=Decimal(10000.00),
            total_amount=Decimal(1000.00),
            paid_amount=Decimal(0.00),
            name="gck",
            note="Will paid",
            payment_date="2024-09-01"
        )
        self.region3 = self.testdb.create_region(name="Edmonton")
        self.payment_allocation = PaymentAllocation.objects.create(
            region=self.region3,
            date="2024-09-01",
            income=Decimal(10000.00),
            total_amount=Decimal(1000.00),
            paid_amount=Decimal(0.00),
            name="dclm",
            note="Will paid",
            payment_date="2024-09-01"
        )
        self.region4 = self.testdb.create_region(name="Camrose")
        self.payment_allocation = PaymentAllocation.objects.create(
            region=self.region4,
            date="2024-09-01",
            income=Decimal(10000.00),
            total_amount=Decimal(1000.00),
            paid_amount=Decimal(0.00),
            name="dclm",
            note="Will paid",
            payment_date="2024-09-01"
        )
        self.region5 = self.testdb.create_region(name="Oshawa")
        self.payment_allocation = PaymentAllocation.objects.create(
            region=self.region5,
            date="2024-09-01",
            income=Decimal(10000.00),
            total_amount=Decimal(1000.00),
            paid_amount=Decimal(0.00),
            name="dclm",
            note="Will paid",
            payment_date="2024-09-01"
        )

        self.region6 = self.testdb.create_region(name="Regina")
        self.payment_allocation = PaymentAllocation.objects.create(
            region=self.region6,
            date="2024-09-01",
            income=Decimal(10000.00),
            total_amount=Decimal(1000.00),
            paid_amount=Decimal(0.00),
            name="dclm",
            note="Will paid",
            payment_date="2024-09-01"
        )

    def create_data(self):
        # PaymentAllocation for the region
        PaymentAllocation.objects.create(
            region=self.region,
            date=datetime(2024, 12, 1),
            income=Decimal("10000.00"),
            total_amount=Decimal("1000.00"),
            paid_amount=Decimal("1000.00"),
            payment_date=datetime(2024, 12, 1),
            name="dclm"
        )
        PaymentAllocation.objects.create(
            region=self.region,
            date=datetime(2024, 12, 1),
            income=Decimal("20000.00"),
            total_amount=Decimal("3000.00"),
            paid_amount=Decimal("3000.00"),
            payment_date=datetime(2024, 12, 1),
            name="gck"
        )

        # AllocationReconciliation for the same region
        AllocationReconciliation.objects.create(
            region=self.region,
            account_type="dclm_gck",
            payment_date=datetime(2024, 12, 1),
            amount=Decimal("4000.00"),
        )

    def test_reconciliation_matched(self):
        """Test that reconciliation works when allocations match."""
        self.create_data()
        response = self.client.get(PAYMENT_ALLOCATION_RECONCILIATION_URL, {
            'region_id': self.region.id,
            'month': 12,
            'year': 2024
        })

        self.assertEqual(response.status_code, 200)
        context = response.context

        # Verify the context contains the expected values
        self.assertEqual(context['region_name'], self.region.name)
        self.assertEqual(context['total_allocation_paid_dclm_gck'], Decimal("4000.00"))
        self.assertEqual(context['bank_statement_dclm_gck'], Decimal("4000.00"))
        self.assertTrue(context['reconciliation_matched'])

    def test_reconciliation_mismatch(self):
        """Test that reconciliation fails when allocations do not match."""
        self.create_data()

        # Modify one AllocationReconciliation amount to create a mismatch
        AllocationReconciliation.objects.filter(account_type="dclm_gck").update(amount=Decimal("2500.00"))

        response = self.client.get(PAYMENT_ALLOCATION_RECONCILIATION_URL, {
            'region_id': self.region.id,
            'month': 12,
            'year': 2024
        })

        self.assertEqual(response.status_code, 200)
        context = response.context

        # Verify the context reflects the mismatch
        self.assertEqual(context['region_name'], self.region.name)
        self.assertEqual(context['total_allocation_paid_dclm_gck'], Decimal("4000.00"))
        self.assertEqual(context['bank_statement_dclm_gck'], Decimal("2500.00"))
        self.assertFalse(context['reconciliation_matched'])

    def test_upload_allocation_reconciliation_bank_statement(self):
        """Test successful upload and processing of a PDF bank statement."""
        with open(PDF_FILE_PATH, "rb") as pdf:
            response = self.client.post(
                PAYMENT_ALLOCATION_RECONCILIATION_URL,
                {
                    "upload_allocation_reconciliation_bank_statement": True,
                    "file": SimpleUploadedFile("fake_bank_statement_styled_letterhead2.pdf",
                                               pdf.read(),
                                               content_type="application/pdf"),
                },
            )

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "transactions have been saved successfully.")
        self.assertEqual(AllocationReconciliation.objects.count(), 38)

        # Verify AllocationReconciliation data
        allocation = AllocationReconciliation.objects.first()
        self.assertEqual(allocation.region.name, "WINDSOR".title())
        self.assertEqual(allocation.account_type, "dclm_gck")
        self.assertEqual(allocation.amount, Decimal("281.00"))
        self.assertEqual(allocation.payment_date, datetime(2024, 8, 26).date())

    def test_missing_region_handling(self):
        """Test handling of transactions with missing regions."""
        with open(PDF_FILE_PATH, "rb") as pdf:
            response = self.client.post(
                PAYMENT_ALLOCATION_RECONCILIATION_URL,
                {
                    "upload_allocation_reconciliation_bank_statement": "true",
                    "file": SimpleUploadedFile("fake_bank_statement.pdf", pdf.read(), content_type="application/pdf"),
                },
            )

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No region found for transaction")

    def test_invalid_pdf_handling(self):
        """Test error handling for invalid PDF files."""
        invalid_file = BytesIO(b"Not a real PDF content")
        response = self.client.post(
            PAYMENT_ALLOCATION_RECONCILIATION_URL,
            {
                "upload_allocation_reconciliation_bank_statement": True,
                "file": SimpleUploadedFile("invalid_file.pdf", invalid_file.read(), content_type="application/pdf"),
            },
        )

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Error processing file")
