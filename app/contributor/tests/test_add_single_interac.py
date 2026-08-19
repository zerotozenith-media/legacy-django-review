from django.urls import reverse
from django.test import TestCase, Client

from contributor.forms import InteracContributionForm
from contributor.models import TransactionType
from organization.models import LocalChurchName
from utils.test_db import Testdb

SINGLE_INTERAC_URL = reverse('add-single-interac')


class SingleInteracContributionTests(TestCase):
    """Tests for the SingleInteracContributionCreateView and its form."""

    def setUp(self):
        """Set up test data and authenticate the user."""
        self.testdb = Testdb()

        self.client = Client()
        self.user = self.testdb.create_user()
        self.client.force_login(self.user)
        self.local_church = self.testdb.create_local_church()
        self.region = self.testdb.create_region(region_overseer=self.user)

        self.form_data = {
            'local_church': self.local_church.id,
            'name': 'John Doe',
            'date': '2024-11-28',
            'amount': '100.00',
        }

    def test_login_required(self):
        """Test view requires authentication."""
        self.client.logout()
        res = self.client.get(SINGLE_INTERAC_URL)
        self.assertEqual(res.status_code, 302)

        # Assert the user is redirected to the login page
        login_url = f"{reverse('login')}?next={SINGLE_INTERAC_URL}"
        self.assertRedirects(res, login_url)

    def test_form_valid_data(self):
        """Test that the form is valid with correct data."""
        form = InteracContributionForm(user=self.user, data=self.form_data)
        self.assertTrue(form.is_valid())

    def test_form_local_church_queryset_for_staff_and_members(self):
        """Test all local churches are return for staffs and role = 3 users."""
        name = LocalChurchName.objects.create(title="Other church")
        self.testdb.create_local_church(local_church_name=name)

        # Instantiate the form with the test user
        form = InteracContributionForm(user=self.user)
        queryset = form.fields['local_church'].queryset

        # Ensure only the user's churches are in the queryset
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.local_church, queryset)

    def test_only_pastor_local_church_queryset(self):
        """Test for pastors only their chuches are returned."""
        self.user.role = 2  # Pastor
        self.user.pastor_churches.add(self.local_church)
        self.user.save()
        self.user.refresh_from_db()

        name = LocalChurchName.objects.create(title="Other church")
        self.testdb.create_local_church(local_church_name=name)

        # Instantiate the form with the test user
        form = InteracContributionForm(user=self.user)
        queryset = form.fields['local_church'].queryset

        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.local_church, queryset)

    def test_only_regional_pastor_local_church_queryset(self):
        """Test for pastors only their chuches are returned."""
        self.user.role = 4  # Regional Pastor
        self.user.save()
        self.user.refresh_from_db()

        self.local_church.region = self.region
        self.local_church.save()
        self.local_church.refresh_from_db()

        name = LocalChurchName.objects.create(title="Other church")
        self.testdb.create_local_church(local_church_name=name)

        # Instantiate the form with the test user
        form = InteracContributionForm(user=self.user)
        queryset = form.fields['local_church'].queryset

        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.local_church, queryset)

    def test_form_invalid_amount(self):
        """Test that the form is invalid when the amount is negative."""
        self.form_data['amount'] = '-100'

        form = InteracContributionForm(data=self.form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors, self.form_data)
        self.assertEqual(form.errors['amount'][0], "The amount must be greater than zero.")

    def test_form_missing_local_church(self):
        """Test that the form is invalid if local church is missing."""
        form_data = {
            'name': 'John Doe',
            'date': '2024-11-28',
            'amount': '100.00',
        }
        form = InteracContributionForm(user=self.user, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('local_church', form.errors)

    def test_form_save_method(self):
        """Test that the save method creates a Contribution with correct fields."""
        form = InteracContributionForm(user=self.user, data=self.form_data)
        self.assertTrue(form.is_valid())
        contribution = form.save()

        self.assertEqual(contribution.local_church, self.local_church)
        self.assertEqual(contribution.deposited_date.isoformat(), '2024-11-28')
        self.assertEqual(contribution.amount, 100.00)
        self.assertFalse(contribution.special_contribution)
        self.assertEqual(contribution.payment_type, TransactionType.INTEREC_E_TRANSFER.value)

    def test_get_request(self):
        """Test that a GET request renders the form."""
        response = self.client.get(SINGLE_INTERAC_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contributors/add_single_interac.html')
        self.assertIn('form', response.context)

    def test_post_valid_data(self):
        """Test that a POST request with valid data creates a Contribution."""
        response = self.client.post(SINGLE_INTERAC_URL, self.form_data)
        self.assertEqual(response.status_code, 302)  # Should redirect on success
        self.assertRedirects(response, reverse('interac_transfer_list'))

        messages = list(response.wsgi_request._messages)
        self.assertTrue(any(message.message == "Interac contribution successfully added!" for message in messages),
                        "Expected success message not found in response messages.")

    def test_post_invalid_data(self):
        """Test that a POST request with invalid data re-renders the form with errors."""
        data = {
            'local_church': self.local_church.id,
            'name': '',
            'date': '2024-11-28',
            'amount': '-100.00',
        }
        response = self.client.post(SINGLE_INTERAC_URL, data)
        self.assertEqual(response.status_code, 200)  # Form re-rendered
        self.assertTemplateUsed(response, 'contributors/add_single_interac.html')

    def test_invalid_local_church(self):
        """Test that the form raises an error if the local church does not exist."""
        data = {
            'local_church': 999,  # Non-existent local church
            'name': 'John Doe',
            'date': '2024-11-28',
            'amount': '100.00',
        }
        response = self.client.post(SINGLE_INTERAC_URL, data)
        self.assertEqual(response.status_code, 200)  # Form re-rendered

    def test_zero_amount(self):
        """Test that an amount of zero results in a validation error."""
        data = {
            'local_church': self.local_church,
            'name': 'John Doe',
            'date': '2024-11-28',
            'amount': '0.00',  # Zero amount
        }
        response = self.client.post(SINGLE_INTERAC_URL, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'amount', 'The amount must be greater than zero.')
