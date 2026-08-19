from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now
from core.models import BaseModel
from organization.models import LocalChurch, Region
import calendar


class ChurchServices(BaseModel):
    name = models.CharField(max_length=100, null=True, blank=True)
    short_name = models.CharField(max_length=8, null=True, blank=True)
    description = models.CharField(max_length=200, null=True, blank=True)
    local_church = models.ForeignKey(LocalChurch, on_delete=models.DO_NOTHING, null=True,
                                     related_name="church_services_local_church")

    class Meta:
        db_table = 'church_services'
        verbose_name_plural = 'Church Services'

    def __str__(self):
        return f"{self.name}"


class Attendance(BaseModel):
    id = models.AutoField(primary_key=True)
    church_service = models.ForeignKey(ChurchServices, on_delete=models.DO_NOTHING, null=True,
                                       related_name="church_service")
    adult_male = models.IntegerField(default=0)
    adult_female = models.IntegerField(default=0)
    youth_male = models.IntegerField(default=0)
    youth_female = models.IntegerField(default=0)
    children_male = models.IntegerField(default=0)
    children_female = models.IntegerField(default=0)
    campus_male = models.IntegerField(default=0)
    campus_female = models.IntegerField(default=0)
    cau = models.IntegerField(default=0)
    visitor = models.IntegerField(default=0)
    conv = models.IntegerField(default=0)
    ypf_male = models.IntegerField(default=0)
    ypf_female = models.IntegerField(default=0)
    zoom = models.IntegerField(default=0)
    youtube = models.IntegerField(default=0)
    date = models.DateField(blank=False, null=False, default=now)
    comment = models.TextField(blank=True, null=True, max_length=512)
    local_church = models.ForeignKey(LocalChurch, on_delete=models.DO_NOTHING, null=True,
                                     related_name="local_church_attendance")

    def __str__(self):
        return f"Attendance for {self.church_service}"

    class Meta:
        db_table = 'attendance'


class Day(BaseModel):
    DAY_CHOICES = [
        ("DAY 1", "DAY 1"),
        ("DAY 2", "DAY 2"),
        ("DAY 3", "DAY 3"),
        ("DAY 4", "DAY 4"),
        ("DAY 5", "DAY 5"),
        ("DAY 6", "DAY 6"),
        ("DAY 7", "DAY 7"),
    ]

    SESSION_CHOICES = [
        ("", "No Session"),
        ("Morning", "Morning"),
        ("Evening", "Evening"),
    ]

    name = models.CharField(max_length=20, choices=DAY_CHOICES)
    date = models.DateField()
    session = models.CharField(
        max_length=10, choices=SESSION_CHOICES, default="", blank=True
    )
    local_church = models.ForeignKey(LocalChurch, on_delete=models.CASCADE,
                                     related_name="local_church_gck_attendance")
    is_workers = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Append the session to the name dynamically
        if self.session:
            self.name = f"{self.name} ({self.session})"
        else:
            # Ensure no session suffix if no session is set
            self.name = self.name.split(" (")[0]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def month(self):
        """Returns the name of the month for the date."""
        if self.date:
            return calendar.month_name[self.date.month]
        return None


class GCKEvent(models.Model):
    name = models.CharField(max_length=255)
    year_month = models.DateField(unique=True)  # Ensures One Event Per Month

    def __str__(self):
        return f"{self.name} ({self.year_month.strftime('%B %Y')})"


class GCKAttendance(BaseModel):
    gck_event = models.ForeignKey(GCKEvent, null=True, blank=True, related_name="attendances", on_delete=models.CASCADE)
    adult = models.PositiveIntegerField(default=0)
    young_prf = models.PositiveIntegerField(default=0)  # Young Professionals
    campus = models.PositiveIntegerField(default=0)
    youths = models.PositiveIntegerField(default=0)
    children = models.PositiveIntegerField(default=0)
    zoom = models.PositiveIntegerField(default=0)
    youtube = models.PositiveIntegerField(default=0)
    fb_reached = models.PositiveIntegerField(default=0)
    fb_likes = models.PositiveIntegerField(default=0)
    fb_comments = models.PositiveIntegerField(default=0)
    ig_reached = models.PositiveIntegerField(default=0)
    ig_engagement = models.PositiveIntegerField(default=0)
    remarks = models.TextField(default="No Remarks")
    day = models.ForeignKey(Day, related_name="attendances", on_delete=models.CASCADE)
    converts = models.PositiveIntegerField(default=0)
    is_workers = models.BooleanField(default=False)

    def __str__(self):
        return f"GCK Attendance for {self.day.name}"

    @property
    def date(self):
        """Returns the date of the related Day instance."""
        return self.day.date if self.day else None

    def delete(self, *args, **kwargs):
        # Get the related Day instance
        day = self.day
        super().delete(*args, **kwargs)  # Delete the GCKAttendance instance

        # If no other attendances are linked to the Day, delete the Day
        if not day.attendances.exists() and self.day:
            day.delete()


class GCKConvertsFollowUpReport(BaseModel):
    local_church = models.ForeignKey(LocalChurch, on_delete=models.CASCADE,
                                     related_name="local_church_gck_converts_follow_up")
    month = models.CharField(max_length=20, blank=True, null=True, default="")
    name = models.CharField(max_length=255, blank=True, null=True, default="")
    date = models.DateField(blank=True, null=True)
    sex = models.CharField(max_length=10, blank=True, null=True, default="")
    phone_number = models.CharField(max_length=20, blank=True, null=True, default="")
    email_address = models.EmailField(blank=True, null=True, default="")
    location = models.CharField(max_length=255, blank=True, null=True, default="")
    global_crusade = models.TextField(blank=True, null=True, default="")
    comments = models.TextField(blank=True, null=True, default="")
    follow_up_worker = models.CharField(max_length=255, blank=True, null=True, default="")
    follow_up_letter_from_gs = models.TextField(blank=True, null=True, default="")

    # Conversion and After
    conversion_and_after = models.TextField(blank=True, null=True, default="")
    chapter_1_secrets_of_spiritual_growth = models.TextField(blank=True, null=True, default="")
    additional_follow_up_report_chapter_1 = models.TextField(blank=True, null=True, default="")
    chapter_2_blueprints_for_spiritual_growth = models.TextField(blank=True, null=True, default="")
    additional_follow_up_report_chapter_2 = models.TextField(blank=True, null=True, default="")

    # Study Sections
    study_1_assurance_of_salvation = models.TextField(blank=True, null=True, default="")
    additional_follow_up_report_study_1 = models.TextField(blank=True, null=True, default="")
    water_baptism = models.TextField(blank=True, null=True, default="")
    study_2_character_of_the_christian = models.TextField(blank=True, null=True, default="")
    additional_follow_up_report_study_2 = models.TextField(blank=True, null=True, default="")
    study_3_searching_the_scriptures = models.TextField(blank=True, null=True, default="")
    additional_follow_up_report_study_3 = models.TextField(blank=True, null=True, default="")
    study_4_privileges_in_prayer = models.TextField(blank=True, null=True, default="")
    additional_follow_up_report_study_4 = models.TextField(blank=True, null=True, default="")
    study_5_restitution = models.TextField(blank=True, null=True, default="")
    additional_follow_up_report_study_5 = models.TextField(blank=True, null=True, default="")
    study_6_tell_thy_friends = models.TextField(blank=True, null=True, default="")
    additional_follow_up_report_study_6 = models.TextField(blank=True, null=True, default="")

    def __str__(self):
        return self.name or "Unnamed Report"


class GCKProjections(BaseModel):
    date = models.DateField(blank=True, null=True)
    month = models.CharField(max_length=20, blank=True, null=True, default="")
    att_by_weeks = models.PositiveIntegerField(default=0)
    att_target_for_month = models.PositiveIntegerField(default=0)
    att_sunday_crusade = models.PositiveIntegerField(default=0)

    region = models.ForeignKey(Region, on_delete=models.CASCADE,
                               related_name="region_gck_projections")

    def __str__(self):
        return self.region.name
