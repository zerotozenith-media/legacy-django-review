import calendar
from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from organization.models import LocalChurch
from organization.utils import get_user_local_church
from .models import Day, GCKAttendance, GCKEvent


class GCKAttendanceForm(forms.ModelForm):
    gck_event = forms.ModelChoiceField(
        queryset=GCKEvent.objects.all(),
        empty_label="Select an Event",
        label="Event",
        widget=forms.Select(attrs={'class': 'form-control', "required": True})
    )

    # Adding fields from the Day model to the form
    day_name = forms.CharField(
        max_length=20,
        label="Day",
        widget=forms.Select(choices=Day.DAY_CHOICES, attrs={'class': 'form-control', 'placeholder': 'Select a Day'})
    )

    session = forms.ChoiceField(
        choices=Day.SESSION_CHOICES,
        label="Session",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False  # Ensures the field is optional
    )

    day_local_church = forms.ModelChoiceField(
        queryset=LocalChurch.objects.none(),
        empty_label="Select a local church",
        label="Local Church",
        widget=forms.Select(attrs={'class': 'form-control', "required": True})
    )
    day_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', "required": True}),
        label="Date"
    )

    # Exclude 'day' field as it will be created based on the related Day model
    class Meta:
        model = GCKAttendance
        fields = [
            'adult', 'young_prf', 'campus', 'youths', 'children', 'zoom', 'youtube',
            'fb_reached', 'fb_likes', 'fb_comments', 'ig_reached', 'ig_engagement', 'converts', 'remarks'
        ]
        widgets = {
            'adult': forms.NumberInput(attrs={'class': 'form-control'}),
            'young_prf': forms.NumberInput(attrs={'class': 'form-control'}),
            'campus': forms.NumberInput(attrs={'class': 'form-control'}),
            'youths': forms.NumberInput(attrs={'class': 'form-control'}),
            'children': forms.NumberInput(attrs={'class': 'form-control'}),
            'zoom': forms.NumberInput(attrs={'class': 'form-control'}),
            'youtube': forms.NumberInput(attrs={'class': 'form-control'}),
            'fb_reached': forms.NumberInput(attrs={'class': 'form-control'}),
            'fb_likes': forms.NumberInput(attrs={'class': 'form-control'}),
            'fb_comments': forms.NumberInput(attrs={'class': 'form-control'}),
            'ig_reached': forms.NumberInput(attrs={'class': 'form-control'}),
            'ig_engagement': forms.NumberInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'converts': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'adult': 'Adult Attendance',
            'young_prf': 'Young Professionals',
            'campus': 'Campus',
            'youths': 'Youths',
            'children': 'Children',
            'zoom': 'Zoom Attendance',
            'youtube': 'YouTube Attendance',
            'fb_reached': 'Facebook Reached',
            'fb_likes': 'Facebook Likes',
            'fb_comments': 'Facebook Comments',
            'ig_reached': 'Instagram Reached',
            'ig_engagement': 'Instagram Engagement',
            'remarks': 'Remarks',
            'converts': 'Converts'

        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Dynamically set the queryset for local_church if the user is passed
        if self.user:
            self.fields['day_local_church'].queryset = get_user_local_church(self.user)

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('day_name')
        day_date = cleaned_data.get('day_date')
        session = cleaned_data.get('session')
        local_church = cleaned_data.get('day_local_church')

        if day_date > date.today():
            raise forms.ValidationError("The date cannot be in the future.")

        if Day.objects.filter(name=name, local_church=local_church, date__month=day_date.month,
                              date__year=day_date.year, session=session, is_workers=False).exists():
            raise ValidationError("A Day entry for this Year, month, and local church already exists.")

        if Day.objects.filter(name=f'{name} ({session})', local_church=local_church, date__month=day_date.month,
                              date__year=day_date.year, session=session, is_workers=False).exists():
            raise ValidationError("A Day entry for this Year, month, session and local church already exists.")
        return cleaned_data

    def save(self, commit=True):
        # Get or create the Day instance based on day_name, day_local_church, and day_date
        day_name = self.cleaned_data['day_name']
        day_local_church = self.cleaned_data['day_local_church']
        day_date = self.cleaned_data['day_date']
        session = self.cleaned_data.get('session')

        day, created = Day.objects.get_or_create(
            name=day_name,
            local_church=day_local_church,
            date=day_date,
            session=session,
            is_workers=False
        )

        # Save the GCKAttendance instance with the associated Day instance
        gck_attendance = super().save(commit=False)
        gck_attendance.day = day
        gck_attendance.gck_event = self.cleaned_data['gck_event']

        if commit:
            gck_attendance.is_workers = False
            gck_attendance.save()

        return gck_attendance


class EditGCKAttendanceForm(forms.ModelForm):
    gck_event = forms.ModelChoiceField(
        queryset=GCKEvent.objects.all(),
        empty_label="Select an Event",
        label="Event",
        widget=forms.Select(attrs={'class': 'form-control', "required": True})
    )

    # Adding fields from the Day model to the form
    day_name = forms.CharField(
        max_length=20,
        label="Day",
        widget=forms.Select(choices=Day.DAY_CHOICES, attrs={'class': 'form-control', 'placeholder': 'Select a Day'})
    )
    day_local_church = forms.ModelChoiceField(
        queryset=LocalChurch.objects.none(),
        empty_label="Select a local church",
        label="Local Church",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    day_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date"
    )
    session = forms.ChoiceField(
        choices=Day.SESSION_CHOICES,  # Adding a blank choice
        label="Session",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False  # Ensures the field is optional
    )

    class Meta:
        model = GCKAttendance
        fields = [
            'adult', 'young_prf', 'campus', 'youths', 'children', 'zoom', 'youtube',
            'fb_reached', 'fb_likes', 'fb_comments', 'ig_reached', 'ig_engagement', 'remarks', 'converts'
        ]
        widgets = {
            'adult': forms.NumberInput(attrs={'class': 'form-control'}),
            'young_prf': forms.NumberInput(attrs={'class': 'form-control'}),
            'campus': forms.NumberInput(attrs={'class': 'form-control'}),
            'youths': forms.NumberInput(attrs={'class': 'form-control'}),
            'children': forms.NumberInput(attrs={'class': 'form-control'}),
            'zoom': forms.NumberInput(attrs={'class': 'form-control'}),
            'youtube': forms.NumberInput(attrs={'class': 'form-control'}),
            'fb_reached': forms.NumberInput(attrs={'class': 'form-control'}),
            'fb_likes': forms.NumberInput(attrs={'class': 'form-control'}),
            'fb_comments': forms.NumberInput(attrs={'class': 'form-control'}),
            'ig_reached': forms.NumberInput(attrs={'class': 'form-control'}),
            'ig_engagement': forms.NumberInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'converts': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'adult': 'Adult Attendance',
            'young_prf': 'Young Professionals',
            'campus': 'Campus',
            'youths': 'Youths',
            'children': 'Children',
            'zoom': 'Zoom Attendance',
            'youtube': 'YouTube Attendance',
            'fb_reached': 'Facebook Reached',
            'fb_likes': 'Facebook Likes',
            'fb_comments': 'Facebook Comments',
            'ig_reached': 'Instagram Reached',
            'ig_engagement': 'Instagram Engagement',
            'remarks': 'Remarks',
            'converts': 'Converts',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        attendance_id = kwargs.pop('attendance_id', None)  # Capture attendance ID from the arguments
        super().__init__(*args, **kwargs)
        self.instance = None

        # Dynamically set the queryset for local_church if the user is passed
        if self.user:
            self.fields['day_local_church'].queryset = get_user_local_church(self.user)

        if attendance_id:
            try:
                attendance_instance = GCKAttendance.objects.get(id=attendance_id)
                self.instance = attendance_instance
                day_instance = attendance_instance.day

                self.fields['gck_event'].initial = attendance_instance.gck_event

                # Populate Day-related fields
                base_day_name = day_instance.name.split('(')[0].strip()
                self.fields['day_name'].initial = base_day_name
                self.fields['day_local_church'].initial = day_instance.local_church
                self.fields['day_date'].initial = day_instance.date
                self.fields['session'].initial = day_instance.session

                # Populate attendance-specific fields
                for field in self.Meta.fields:
                    if hasattr(attendance_instance, field):
                        self.fields[field].initial = getattr(attendance_instance, field)

                print(self.fields['day_name'].initial, day_instance.name)

            except GCKAttendance.DoesNotExist:
                pass  # Handle case where attendance_id is invalid

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('day_name')
        day_date = cleaned_data.get('day_date')
        local_church = cleaned_data.get('day_local_church')
        session = cleaned_data.get('session')

        if day_date > date.today():
            raise forms.ValidationError("The date cannot be in the future.")

        if name == self.instance.day.name:
            return cleaned_data

        if Day.objects.filter(name=name, local_church=local_church, date__month=day_date.month,
                              date__year=day_date.year, session=session, is_workers=False).exists():
            raise ValidationError("A Day entry for this Year, month, and local church already exists.")

        if self.instance and self.instance.day.name == f"{name} ({session})":
            return cleaned_data

        if Day.objects.filter(name=f'{name} ({session})', local_church=local_church, date__month=day_date.month,
                              date__year=day_date.year, session=session, is_workers=False).exists():
            raise ValidationError("A Day entry for this Year, month, session and local church already exists.")

        return cleaned_data

    def save(self, commit=True):
        # Get the day-related fields from cleaned_data
        day_name = self.cleaned_data['day_name']
        day_local_church = self.cleaned_data['day_local_church']
        day_date = self.cleaned_data['day_date']
        session = self.cleaned_data.get('session')

        # Get the existing attendance instance
        gck_attendance = self.instance  # This will be the instance passed to the form
        if not gck_attendance.pk:
            raise forms.ValidationError("GCK Attendance Report instance does not exist.")

        # Retrieve the related Day instance from the attendance record
        day = gck_attendance.day

        gck_attendance.gck_event = self.cleaned_data['gck_event']

        # Update the fields in the Day instance
        day.name = day_name
        day.local_church = day_local_church
        day.date = day_date
        day.session = session
        day.is_workers = False

        # Save the updated Day instance
        if commit:
            day.save()

        # Update other attendance fields (adult, campus, etc.)
        for field in self.Meta.fields:
            setattr(gck_attendance, field, self.cleaned_data[field])

        # Save the updated attendance instance
        if commit:
            gck_attendance.is_workers = False
            gck_attendance.save()

        return gck_attendance


class GCKWorkersAttendanceForm(forms.ModelForm):
    # Adding fields from the Day model to the form
    day_name = forms.CharField(
        max_length=20,
        label="Day",
        widget=forms.Select(choices=Day.DAY_CHOICES, attrs={'class': 'form-control', 'placeholder': 'Select a Day'})
    )

    session = forms.ChoiceField(
        choices=Day.SESSION_CHOICES,
        label="Session",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False  # Ensures the field is optional
    )

    day_local_church = forms.ModelChoiceField(
        queryset=LocalChurch.objects.none(),
        empty_label="Select a local church",
        label="Local Church",
        widget=forms.Select(attrs={'class': 'form-control', "required": True})
    )
    day_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', "required": True}),
        label="Date"
    )

    # Exclude 'day' field as it will be created based on the related Day model
    class Meta:
        model = GCKAttendance
        fields = ['young_prf', 'campus', 'youths']
        widgets = {
            'young_prf': forms.NumberInput(attrs={'class': 'form-control'}),
            'campus': forms.NumberInput(attrs={'class': 'form-control'}),
            'youths': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Dynamically set the queryset for local_church if the user is passed
        if self.user:
            self.fields['day_local_church'].queryset = get_user_local_church(self.user)

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('day_name')
        day_date = cleaned_data.get('day_date')
        session = cleaned_data.get('session')
        local_church = cleaned_data.get('day_local_church')

        if day_date > date.today():
            raise forms.ValidationError("The date cannot be in the future.")

        if Day.objects.filter(name=name, local_church=local_church, date__month=day_date.month,
                              date__year=day_date.year, session=session, is_workers=True).exists():
            raise ValidationError("A Day entry for this Year, month, and local church already exists.")

        if Day.objects.filter(name=f'{name} ({session})', local_church=local_church, date__month=day_date.month,
                              date__year=day_date.year, session=session, is_workers=True).exists():
            raise ValidationError("A Day entry for this Year, month, session and local church already exists.")
        return cleaned_data

    def save(self, commit=True):
        # Get or create the Day instance based on day_name, day_local_church, and day_date
        day_name = self.cleaned_data['day_name']
        day_local_church = self.cleaned_data['day_local_church']
        day_date = self.cleaned_data['day_date']
        session = self.cleaned_data.get('session')

        day, created = Day.objects.get_or_create(
            name=day_name,
            local_church=day_local_church,
            date=day_date,
            session=session,
            is_workers=True
        )

        # Save the GCKAttendance instance with the associated Day instance
        gck_attendance = super().save(commit=False)
        gck_attendance.day = day

        if commit:
            gck_attendance.is_workers = True
            gck_attendance.save()

        return gck_attendance


class EditGCKWorkersAttendanceForm(forms.ModelForm):
    # Adding fields from the Day model to the form
    day_name = forms.CharField(
        max_length=20,
        label="Day",
        widget=forms.Select(choices=Day.DAY_CHOICES, attrs={'class': 'form-control', 'placeholder': 'Select a Day'})
    )
    day_local_church = forms.ModelChoiceField(
        queryset=LocalChurch.objects.none(),
        empty_label="Select a local church",
        label="Local Church",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    day_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date"
    )
    session = forms.ChoiceField(
        choices=Day.SESSION_CHOICES,  # Adding a blank choice
        label="Session",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False  # Ensures the field is optional
    )

    class Meta:
        model = GCKAttendance
        fields = ['young_prf', 'campus', 'youths']
        widgets = {
            'young_prf': forms.NumberInput(attrs={'class': 'form-control'}),
            'campus': forms.NumberInput(attrs={'class': 'form-control'}),
            'youths': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        attendance_id = kwargs.pop('attendance_id', None)  # Capture attendance ID from the arguments
        super().__init__(*args, **kwargs)
        self.instance = None

        # Dynamically set the queryset for local_church if the user is passed
        if self.user:
            self.fields['day_local_church'].queryset = get_user_local_church(self.user)

        if attendance_id:
            try:
                attendance_instance = GCKAttendance.objects.get(id=attendance_id)
                self.instance = attendance_instance
                day_instance = attendance_instance.day

                # Populate Day-related fields
                base_day_name = day_instance.name.split('(')[0].strip()
                self.fields['day_name'].initial = base_day_name
                self.fields['day_local_church'].initial = day_instance.local_church
                self.fields['day_date'].initial = day_instance.date
                self.fields['session'].initial = day_instance.session

                # Populate attendance-specific fields
                for field in self.Meta.fields:
                    if hasattr(attendance_instance, field):
                        self.fields[field].initial = getattr(attendance_instance, field)
            except GCKAttendance.DoesNotExist:
                pass  # Handle case where attendance_id is invalid

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('day_name')
        day_date = cleaned_data.get('day_date')
        local_church = cleaned_data.get('day_local_church')
        session = cleaned_data.get('session')

        if day_date > date.today():
            raise forms.ValidationError("The date cannot be in the future.")

        if name == self.instance.day.name:
            return cleaned_data

        if self.instance and self.instance.day.name == f"{name} ({session})":
            return cleaned_data

        if Day.objects.filter(name=name, local_church=local_church, date__month=day_date.month,
                              date__year=day_date.year, session=session, is_workers=True).exists():
            raise ValidationError("A Day entry for this Year, month, and local church already exists.")

        if Day.objects.filter(name=f'{name} ({session})', local_church=local_church, date__month=day_date.month,
                              date__year=day_date.year, session=session, is_workers=True).exists():
            raise ValidationError("A Day entry for this Year, month, session and local church already exists.")

        return cleaned_data

    def save(self, commit=True):
        # Get the day-related fields from cleaned_data
        day_name = self.cleaned_data['day_name']
        day_local_church = self.cleaned_data['day_local_church']
        day_date = self.cleaned_data['day_date']
        session = self.cleaned_data.get('session')

        # Get the existing attendance instance
        gck_attendance = self.instance  # This will be the instance passed to the form
        if not gck_attendance.pk:
            raise forms.ValidationError("GCK Attendance Report instance does not exist.")

        # Retrieve the related Day instance from the attendance record
        day = gck_attendance.day

        # Update the fields in the Day instance
        day.name = day_name
        day.local_church = day_local_church
        day.date = day_date
        day.session = session
        day.is_workers = True

        # Save the updated Day instance
        if commit:
            day.save()

        # Update other attendance fields (adult, campus, etc.)
        for field in self.Meta.fields:
            setattr(gck_attendance, field, self.cleaned_data[field])

        # Save the updated attendance instance
        if commit:
            gck_attendance.is_workers = True
            gck_attendance.save()

        return gck_attendance


class GCKEventForm(forms.ModelForm):
    year_month = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "month",
                "class": "form-control",
                "placeholder": "2025-01"
            }
        ),
        input_formats=["%Y-%m"],  # Ensures correct format
        label="GCK Event Month (YYYY-MM)",
    )

    class Meta:
        model = GCKEvent
        fields = ["name", "year_month"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter event name"}),
        }
        labels = {
            "name": "GCK Name",
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        initial = kwargs.get('initial', {})

        # If creating new (no instance), prefill with current year and empty month
        if not instance:
            today = date.today()
            initial.setdefault('year_month', today.strftime('%Y-%m'))

        # If updating existing, ensure we format it properly (YYYY-MM)
        else:
            if instance.year_month:
                initial['year_month'] = instance.year_month.strftime('%Y-%m')

        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

