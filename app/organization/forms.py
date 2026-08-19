from django import forms
from .models import DetailReport, AllocationReconciliation
from .utils import get_user_local_church


class DetailReportForm(forms.ModelForm):
    class Meta:
        model = DetailReport
        fields = ['local_church', 'comment', 'problem', 'testimony', 'follow_up']


class UploadFileForm(forms.Form):
    file = forms.FileField()


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Upload CSV File",
        help_text="Upload a CSV file formatted like the provided sample."
    )
