from django import forms
from datetime import date

from contributor.helper import add_contribution
from contributor.models import Contribution, MiscellaneousContribution
from organization.models import LocalChurch
from organization.utils import get_user_local_church


class UploadFileForm(forms.Form):
    file = forms.FileField(label='Choose a file', widget=forms.ClearableFileInput(attrs={'accept': '.xlsx'}))


class ImportBankStatementForm(forms.Form):
    file = forms.FileField(label='Choose a bank statement', widget=forms.ClearableFileInput(attrs={'accept': '.pdf'}))


class InteracContributionForm(forms.Form):
    """Form for creating an Interac contribution."""

    local_church = forms.ModelChoiceField(
        queryset=LocalChurch.objects.none(),
        label="Local Church",
        empty_label="Select a local church",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Select a local church',
            'id': 'local_church',
        })
    )
    name = forms.CharField(
        max_length=255,
        label="Received From",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter the donor name',
            'autocomplete': 'off',
            'id': 'donor_name',
        })
    )
    date = forms.DateField(
        label="Deposit Date",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'Select the deposit date'
        })
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Amount",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.0',
            'min': '0',
            'step': '0.01'
        })
    )
    special_contribution = forms.BooleanField(
        required=False,
        label="Special Contribution",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input p-2',
            'id': 'special_contribution',
            'role': 'switch',
            'name': 'special_contribution'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Dynamically set the queryset for local_church if the user is passed
        if self.user:
            self.fields['local_church'].queryset = get_user_local_church(self.user)

    def clean_amount(self):
        """Ensure the amount is greater than zero."""
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("The amount must be greater than zero.")
        return amount

    def clean_date(self):
        """Ensure the deposit date is not in the future."""
        deposit_date = self.cleaned_data.get('date')
        if deposit_date > date.today():
            raise forms.ValidationError("The deposit date cannot be in the future.")
        return deposit_date

    def save(self):
        """Save the contribution using the add_contribution function."""
        data = self.cleaned_data
        print(data)
        contribution = add_contribution(
            local_church_id=data['local_church'].id,
            contributor_name=data['name'],
            type="interec_e_transfer",  # Fixed type for Interac contributions
            deposit_date=data['date'],
            amount=data['amount'],
            special_contribution=data['special_contribution'],
            registered_by=self.user,
        )
        return contribution


class ContributionForm(forms.Form):
    """Form for creating contribution."""

    local_church = forms.ModelChoiceField(
        queryset=LocalChurch.objects.none(),
        label="Local Church",
        empty_label="Select a local church",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Select a local church',
            'id': 'local_church',
        })
    )
    name = forms.CharField(
        max_length=255,
        label="Received From",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter the donor name',
            'autocomplete': 'off',
            'id': 'donor_name',
        })
    )
    date = forms.DateField(
        label="Deposit Date",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'Select the deposit date'
        })
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Amount",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.0',
            'min': '0',
            'step': '0.01'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Dynamically set the queryset for local_church if the user is passed
        if self.user:
            self.fields['local_church'].queryset = get_user_local_church(self.user)

    def clean_amount(self):
        """Ensure the amount is greater than zero."""
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("The amount must be greater than zero.")
        return amount

    def clean_date(self):
        """Ensure the deposit date is not in the future."""
        deposit_date = self.cleaned_data.get('date')
        if deposit_date > date.today():
            raise forms.ValidationError("The deposit date cannot be in the future.")
        return deposit_date

    def save(self):
        """Save the contribution using the add_contribution function."""
        data = self.cleaned_data
        contribution = add_contribution(
            local_church_id=data['local_church'].id,
            contributor_name=data['name'],
            type="interec_e_transfer",  # Fixed type for Interac contributions
            deposit_date=data['date'],
            amount=data['amount'],
            special_contribution=False,
            registered_by=self.user
        )
        return contribution


class EditInteracContributionForm(forms.Form):
    """Form for editing a contribution."""

    local_church = forms.ModelChoiceField(
        queryset=LocalChurch.objects.none(),
        label="Local Church",
        empty_label="Select a local church",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Select a local church',
            'id': 'local_church',
        })
    )
    name = forms.CharField(
        max_length=255,
        label="Received From",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter the donor name',
            'autocomplete': 'off',
            'id': 'donor_name',
            "readonly": True
        })
    )
    date = forms.DateField(
        label="Deposit Date",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'Select the deposit date'
        })
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Amount",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.0',
            'min': '0',
            'step': '0.01'
        })
    )

    special_contribution = forms.BooleanField(
        required=False,
        label="Special Contribution",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input p-2',
            'id': 'special_contribution',
            'role': 'switch',
            'name': 'special_contribution'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.type = kwargs.pop('type', None)
        self.contribution_id = kwargs.pop('id', None)
        self.instance = None

        super().__init__(*args, **kwargs)

        # Dynamically set the queryset for local_church if the user is passed
        if self.user:
            self.fields['local_church'].queryset = get_user_local_church(self.user)

        # Pre-populate the form based on type and id
        if self.type and self.contribution_id:
            if self.type == "Contribution":
                self.instance = Contribution.objects.filter(id=self.contribution_id).first()
            else:
                self.instance = MiscellaneousContribution.objects.filter(id=self.contribution_id).first()

            if self.instance:
                self.fields['local_church'].initial = self.instance.local_church
                self.fields['name'].initial = self.instance.contributor.full_name
                self.fields['date'].initial = self.instance.deposited_date
                self.fields['special_contribution'].initial = self.instance.special_contribution
                self.fields['amount'].initial = f"{self.instance.amount:.2f}"

    def clean_amount(self):
        """Ensure the amount is greater than zero."""
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("The amount must be greater than zero.")
        return amount

    def clean_date(self):
        """Ensure the deposit date is not in the future."""
        deposit_date = self.cleaned_data.get('date')
        if deposit_date > date.today():
            raise forms.ValidationError("The deposit date cannot be in the future.")
        return deposit_date

    def save(self):
        """Update the contribution instance."""
        print(self.cleaned_data, "============================")
        if not self.instance:
            raise ValueError("No instance found to update.")

        # Update the instance fields
        self.instance.local_church = self.cleaned_data['local_church']
        self.instance.deposited_date = self.cleaned_data['date']
        self.instance.special_contribution = self.cleaned_data['special_contribution']
        self.instance.amount = self.cleaned_data['amount']

        # Save the updated instance
        self.instance.save()
        return self.instance

