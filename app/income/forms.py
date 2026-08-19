from django import forms
from .models import DonationInKind


class DonationInKindForm(forms.ModelForm):
    class Meta:
        model = DonationInKind
        fields = [
            "local_church",
            "donor",
            "donor_name",
            "donation_item",
            "serial_no",
            "description",
            "donation_date",
            "estimated_value",
            "image",
        ]
        widgets = {
            "local_church": forms.Select(attrs={"class": "form-control"}),
            "donor": forms.Select(attrs={"class": "form-control"}),
            "donor_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Donor's name"}),
            "donation_item": forms.TextInput(attrs={"class": "form-control", "placeholder": "Item name"}),
            "serial_no": forms.TextInput(attrs={"class": "form-control", "placeholder": "Item serial number"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3,
                                                 "placeholder": "Additional details about the donation."}),
            "donation_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "estimated_value": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
