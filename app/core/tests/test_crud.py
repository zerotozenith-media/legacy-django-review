from django.urls import reverse
from django.test import TestCase, Client
from decimal import Decimal
from datetime import datetime

from contributor.models import AnonymousContribution, Contribution, TransactionType, MiscellaneousContribution
from utils.test_db import Testdb


class CrudTests(TestCase):
    """Tests for Update and Delete."""

    def setUp(self):
        """Set up test data and authenticate the user."""
        self.testdb = Testdb()

        self.client = Client()
        self.user = self.testdb.create_user()
        self.client.force_login(self.user)
        self.local_church = self.testdb.create_local_church()
        self.region = self.testdb.create_region(region_overseer=self.user)

        # Create initial records for each type
        self.contribution = Contribution.objects.create(
            contributor=self.user,
            amount=Decimal('50.00'),
            deposited_date=datetime.now().date(),
            payment_type=TransactionType.OFFERINGS_USD.value,
            special_contribution=False,
            month='January',
            local_church=self.local_church
        )
        self.anonymous_contribution = AnonymousContribution.objects.create(
            local_church=self.local_church,
            payment_type=TransactionType.OFFERINGS_USD.value,
            deposited_date=datetime.now().date(),
            amount=Decimal('100.00'),
            special_contribution=False,
            month='January'
        )
        miscellaneous_user = self.testdb.create_miscellaneous_user()
        self.miscellaneous_contribution = MiscellaneousContribution.objects.create(
            contributor=miscellaneous_user,
            amount=Decimal('200.00'),
            deposited_date=datetime.now().date(),
            payment_type=TransactionType.OFFERINGS_USD.value,
            special_contribution=False,
            month='January',
            local_church=self.local_church
        )

    def test_update_contribution(self):
        """Test updating an existing contribution."""

        # New data to update the existing contribution
        updated_data = {
            "local_church": self.local_church.id,
            "toggleSwitch": 'off',  # Will simulate normal offering (not anonymous)
            "donor": self.user.id,
            "miscellaneous": "Updated Donation",
            "donation_date": datetime.now().strftime('%Y-%m-%d'),
            "amount": "150.00",  # New amount for update
            "specialToggleSwitch": 'on',  # Marking as special contribution
            "anonymous_donor": '',  # Not anonymous
        }

        # Send POST request to update the contribution
        url = reverse('offerings', args=[self.contribution.id, self.contribution.type, "USD"])
        response = self.client.post(url, updated_data)
        self.assertRedirects(response, reverse('offerings_usd_list'))

        # Verify the contribution has been updated in the database
        updated_contribution = Contribution.objects.get(id=self.contribution.id)

        # Assert the updated values
        self.assertEqual(updated_contribution.amount, Decimal(updated_data['amount']))
        self.assertEqual(updated_contribution.contributor.full_name, self.user.full_name)
        self.assertEqual(updated_contribution.special_contribution, True)
        self.assertEqual(updated_contribution.payment_type, TransactionType.OFFERINGS_USD.value)
        self.assertEqual(updated_contribution.local_church.id, self.local_church.id)
        self.assertEqual(updated_contribution.month, 'January')  # Month should remain the same unless changed

    def test_update_contribution_cad(self):
        """Test updating an existing contribution cad."""

        # New data to update the existing contribution
        updated_data = {
            "local_church": self.local_church.id,
            "toggleSwitch": 'off',  # Will simulate normal offering (not anonymous)
            "donor": self.user.id,
            "miscellaneous": "Updated Donation",
            "donation_date": datetime.now().strftime('%Y-%m-%d'),
            "amount": "150.00",  # New amount for update
            "specialToggleSwitch": 'on',  # Marking as special contribution
            "anonymous_donor": '',  # Not anonymous
        }

        # Send POST request to update the contribution
        url = reverse('offerings', args=[self.contribution.id, self.contribution.type, "CAD"])
        response = self.client.post(url, updated_data)
        self.assertRedirects(response, reverse('offerings_usd_list'))

        # Verify the contribution has been updated in the database
        updated_contribution = Contribution.objects.get(id=self.contribution.id)

        # Assert the updated values
        self.assertEqual(updated_contribution.amount, Decimal(updated_data['amount']))
        self.assertEqual(updated_contribution.contributor.full_name, self.user.full_name)
        self.assertEqual(updated_contribution.special_contribution, True)
        self.assertEqual(updated_contribution.payment_type, TransactionType.OFFERINGS_CAN.value)
        self.assertEqual(updated_contribution.local_church.id, self.local_church.id)
        self.assertEqual(updated_contribution.month, 'January')  # Month should remain the same unless changed

    def test_update_contribution_to_miscellaneous(self):
        """Test updating an existing contribution to miscellaneous."""
        # New data to update the existing contribution
        updated_data = {
            "local_church": self.local_church.id,
            "toggleSwitch": 'on',  # Will simulate normal offering (not anonymous)
            "miscellaneous": "Updated Donation",
            "donation_date": datetime.now().strftime('%Y-%m-%d'),
            "amount": "150.00",  # New amount for update
            "specialToggleSwitch": 'on',  # Marking as special contribution
            "anonymous_donor": '',  # Not anonymous
        }

        # Send POST request to update the contribution
        url = reverse('offerings', args=[self.contribution.id, self.contribution.type, "USD"])
        response = self.client.post(url, updated_data)
        self.assertRedirects(response, reverse('offerings_usd_list'))

        # Verify the contribution has been deleted in the database
        contribution = Contribution.objects.filter(id=self.contribution.id)
        self.assertFalse(contribution.exists())

        # Verify the miscellaneous contribution has been created in the database
        self.assertEqual(MiscellaneousContribution.objects.all().count(), 2)

    def test_update_contribution_to_anonymous(self):
        """Test updating an existing contribution to Anonymous."""
        # New data to update the existing contribution
        updated_data = {
            "local_church": self.local_church.id,
            "toggleSwitch": 'off',  # Will simulate normal offering (not anonymous)
            "miscellaneous": "Updated Donation",
            "donation_date": datetime.now().strftime('%Y-%m-%d'),
            "amount": "150.00",  # New amount for update
            "specialToggleSwitch": 'on',  # Marking as special contribution
            "anonymous_donor": 'on',  # Not anonymous
        }

        # Send POST request to update the contribution
        url = reverse('offerings', args=[self.contribution.id, self.contribution.type, "USD"])
        response = self.client.post(url, updated_data)
        self.assertRedirects(response, reverse('offerings_usd_list'))

        # Verify the contribution has been deleted in the database
        contribution = Contribution.objects.filter(id=self.contribution.id)
        self.assertFalse(contribution.exists())

        # Verify the miscellaneous contribution has been created in the database
        self.assertEqual(AnonymousContribution.objects.all().count(), 2)

    def test_update_anonymous_contribution(self):
        """Test updating an AnonymousContribution."""
        updated_data = {
            "local_church": self.local_church.id,
            "toggleSwitch": 'off',  # Will simulate normal offering (not anonymous)
            "donation_date": datetime.now().strftime('%Y-%m-%d'),
            "amount": "250.00",
            "specialToggleSwitch": 'off',  # Remove special contribution
            "anonymous_donor": 'on',  # Not anonymous
        }

        # Update the anonymous contribution
        url = reverse('offerings', args=[self.anonymous_contribution.id, self.anonymous_contribution.type, "USD"])
        response = self.client.post(url, updated_data)
        self.assertRedirects(response, reverse('offerings_usd_list'))

        # Verify the update in the database
        updated_contribution = AnonymousContribution.objects.get(id=self.anonymous_contribution.id)
        self.assertEqual(updated_contribution.amount, Decimal(updated_data['amount']))
        self.assertFalse(updated_contribution.special_contribution)

    def test_update_anonymous_contribution_to_miscellaneous(self):
        """Test updating an existing anonymous contribution to miscellaneous."""
        # New data to update the existing contribution
        updated_data = {
            "local_church": self.local_church.id,
            "toggleSwitch": 'on',  # Will simulate normal offering (not anonymous)
            "miscellaneous": "Updated Donation",
            "donation_date": datetime.now().strftime('%Y-%m-%d'),
            "amount": "150.00",  # New amount for update
            "specialToggleSwitch": 'on',  # Marking as special contribution
            "anonymous_donor": '',  # Not anonymous
        }

        # Send POST request to update the contribution
        url = reverse('offerings', args=[self.anonymous_contribution.id, self.anonymous_contribution.type, "USD"])
        response = self.client.post(url, updated_data)
        self.assertRedirects(response, reverse('offerings_usd_list'))

        # Verify the contribution has been deleted in the database
        contribution = AnonymousContribution.objects.filter(id=self.anonymous_contribution.id)
        self.assertFalse(contribution.exists())

        # Verify the miscellaneous contribution has been created in the database
        self.assertEqual(MiscellaneousContribution.objects.all().count(), 2)

    def test_update_anonymous_contribution_to_contribution(self):
        """Test updating an existing contribution to contribution."""
        # New data to update the existing contribution
        updated_data = {
            "local_church": self.local_church.id,
            "toggleSwitch": 'off',  # Will simulate normal offering (not anonymous)
            "donor": self.user.id,
            "miscellaneous": "Updated Donation",
            "donation_date": datetime.now().strftime('%Y-%m-%d'),
            "amount": "150.00",  # New amount for update
            "specialToggleSwitch": 'on',  # Marking as special contribution
            "anonymous_donor": '',  # Not anonymous
        }

        # Send POST request to update the contribution
        url = reverse('offerings', args=[self.anonymous_contribution.id, self.anonymous_contribution.type, "USD"])
        response = self.client.post(url, updated_data)
        self.assertRedirects(response, reverse('offerings_usd_list'))

        # Verify the contribution has been deleted in the database
        contribution = AnonymousContribution.objects.filter(id=self.anonymous_contribution.id)
        self.assertFalse(contribution.exists())

        # Verify the contribution has been created in the database
        self.assertEqual(Contribution.objects.all().count(), 2, Contribution.objects.all())

    def test_update_miscellaneous_contribution(self):
        """Test updating a MiscellaneousContribution."""
        updated_data = {
            "local_church": self.local_church.id,
            "toggleSwitch": 'on',  # Will simulate normal offering (not anonymous)
            "miscellaneous": "Updated Donation",
            "donation_date": datetime.now().strftime('%Y-%m-%d'),
            "amount": "150.00",  # New amount for update
            "specialToggleSwitch": 'on',  # Marking as special contribution
            "anonymous_donor": '',  # Not anonymous
        }

        # Update the miscellaneous contribution
        url = reverse('offerings', args=[self.miscellaneous_contribution.id,
                                         self.miscellaneous_contribution.type, "USD"])
        response = self.client.post(url, updated_data)
        self.assertRedirects(response, reverse('offerings_usd_list'))

        # Verify the update in the database
        updated_contribution = MiscellaneousContribution.objects.get(id=self.miscellaneous_contribution.id)
        self.assertEqual(updated_contribution.amount, Decimal(updated_data['amount']))
        self.assertTrue(updated_contribution.special_contribution)

    def test_update_miscellaneous_contribution_to_anonymous(self):
        """Test updating an existing anonymous contribution to anonymous."""
        # New data to update the existing contribution
        updated_data = {
            "local_church": self.local_church.id,
            "toggleSwitch": 'off',  # Will simulate normal offering (not anonymous)
            "miscellaneous": "Updated Donation",
            "donation_date": datetime.now().strftime('%Y-%m-%d'),
            "amount": "1500.00",  # New amount for update
            "specialToggleSwitch": 'on',  # Marking as special contribution
            "anonymous_donor": 'on',  # Not anonymous
        }

        # Send POST request to update the contribution
        url = reverse('offerings', args=[self.miscellaneous_contribution.id,
                                         self.miscellaneous_contribution.type, "USD"])
        response = self.client.post(url, updated_data)
        self.assertRedirects(response, reverse('offerings_usd_list'))

        # Verify the contribution has been deleted in the database
        contribution = MiscellaneousContribution.objects.filter(id=self.anonymous_contribution.id)
        self.assertFalse(contribution.exists())

        # Verify the miscellaneous contribution has been created in the database
        self.assertEqual(AnonymousContribution.objects.all().count(), 2)

    def test_update_miscellaneous_contribution_to_contribution(self):
        """Test updating an existing miscellaneous to contribution."""
        # New data to update the existing contribution
        updated_data = {
            "local_church": self.local_church.id,
            "toggleSwitch": 'off',  # Will simulate normal offering (not anonymous)
            "donor": self.user.id,
            "miscellaneous": "Updated Donation",
            "donation_date": datetime.now().strftime('%Y-%m-%d'),
            "amount": "150.00",  # New amount for update
            "specialToggleSwitch": 'on',  # Marking as special contribution
            "anonymous_donor": '',  # Not anonymous
        }

        # Send POST request to update the contribution
        url = reverse('offerings', args=[self.miscellaneous_contribution.id,
                                         self.miscellaneous_contribution.type, "USD"])
        response = self.client.post(url, updated_data)
        self.assertRedirects(response, reverse('offerings_usd_list'))

        # Verify the contribution has been deleted in the database
        contribution = MiscellaneousContribution.objects.filter(id=self.miscellaneous_contribution.id)
        self.assertFalse(contribution.exists())

        # Verify the contribution has been created in the database
        self.assertEqual(Contribution.objects.all().count(), 2)

    def test_delete_anonymous_contribution(self):
        """Test deleting an AnonymousContribution."""
        url = reverse('offerings', args=[self.anonymous_contribution.id, "Anonymous", "USD"])
        response = self.client.delete(url)
        self.assertRedirects(response, reverse('offerings_usd_list'))

        # Verify the anonymous contribution is deleted
        with self.assertRaises(AnonymousContribution.DoesNotExist):
            AnonymousContribution.objects.get(id=self.anonymous_contribution.id)

    def test_delete_miscellaneous_contribution(self):
        """Test deleting a MiscellaneousContribution."""
        url = reverse('offerings',
                      args=[self.miscellaneous_contribution.id, self.miscellaneous_contribution.type, "USD"])
        response = self.client.delete(url)
        self.assertRedirects(response, reverse('offerings_usd_list'))

        # Verify the miscellaneous contribution is deleted
        with self.assertRaises(MiscellaneousContribution.DoesNotExist):
            MiscellaneousContribution.objects.get(id=self.miscellaneous_contribution.id)

    def test_delete_contribution(self):
        """Test deleting a MiscellaneousContribution."""
        url = reverse('offerings', args=[self.contribution.id, self.contribution.type, "USD"])
        response = self.client.delete(url)
        self.assertRedirects(response, reverse('offerings_usd_list'))

        # Verify the miscellaneous contribution is deleted
        with self.assertRaises(Contribution.DoesNotExist):
            Contribution.objects.get(id=self.contribution.id)
