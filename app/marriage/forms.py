from django import forms

from marriage.models import MarriageRecord


class MarriageRecordForm(forms.ModelForm):
    class Meta:
        model = MarriageRecord
        fields = [
            'brother_name', 'brother_local_church', 'brother_country', 'brother_province_state',
            'brother_medical_tests_submitted', 'brother_medical_tests_reviewed',
            'sister_name', 'sister_local_church', 'sister_country', 'sister_province_state',
            'sister_medical_tests_submitted', 'sister_medical_tests_reviewed', 'remarks'
        ]
        widgets = {
            'brother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter brother’s name'}),
            'brother_local_church': forms.Select(attrs={'class': 'form-control'}),
            'brother_country': forms.Select(attrs={'class': 'form-control', 'id': 'brother-country'}),
            'brother_province_state': forms.Select(attrs={'class': 'form-control', 'id': 'brother-province-state'}),
            'brother_medical_tests_submitted': forms.Select(attrs={'class': 'form-control'}),
            'brother_medical_tests_reviewed': forms.Select(attrs={'class': 'form-control'}),

            'sister_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter sister’s name'}),
            'sister_local_church': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Enter sister’s name'}),
            'sister_country': forms.Select(attrs={'class': 'form-control', 'id': 'sister-country',
                                                  'placeholder': 'Enter sister’s name'}),
            'sister_province_state': forms.Select(attrs={'class': 'form-control', 'id': 'sister-province-state'}),
            'sister_medical_tests_submitted': forms.Select(attrs={'class': 'form-control'}),
            'sister_medical_tests_reviewed': forms.Select(attrs={'class': 'form-control'}),

            'remarks': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter any remarks', 'rows': 3}),
        }


class EditMarriageRecordForm(MarriageRecordForm):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        instance_id = kwargs.pop('instance_id', None)
        super().__init__(*args, **kwargs)
        self.instance = None

        if instance_id:
            try:
                instance = MarriageRecord.objects.get(id=instance_id)
                self.instance = instance

                # Populate fields
                for field in self.Meta.fields:
                    if hasattr(instance, field):
                        self.fields[field].initial = getattr(instance, field)
            except MarriageRecord.DoesNotExist:
                pass
