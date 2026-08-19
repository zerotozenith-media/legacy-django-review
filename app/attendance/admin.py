from django.contrib import admin
from .models import ChurchServices, Attendance, Day, GCKAttendance, GCKConvertsFollowUpReport, GCKProjections


# ChurchServices Admin Configuration
@admin.register(ChurchServices)
class ChurchServicesAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'description', 'local_church')
    search_fields = ('name', 'short_name', 'description',
                     'local_church__local_church_name')  # Modify according to the field names you want to search
    list_filter = ('local_church',)  # Filter by local church
    ordering = ('name',)  # Order by name
    list_per_page = 20  # Limit the number of records shown per page

    # Fields to show when editing or adding a Church Service
    fieldsets = (
        (None, {'fields': ('name', 'short_name', 'description')}),
        ('Church Information', {'fields': ('local_church',)}),
    )


# Attendance Admin Configuration
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        # Returns all model field names for the list view.
        return [field.name for field in self.model._meta.fields]

    search_fields = ('church_service__name', 'local_church__local_church_name', 'date')
    list_filter = ('church_service', 'local_church', 'date')  # Filter by church service, local church, and date
    ordering = ('-date',)  # Order by date descending
    list_per_page = 20  # Limit the number of records shown per page

    # Fields to show when editing or adding an attendance record
    fieldsets = (
        (None, {'fields': ('church_service', 'date', 'comment', 'local_church')}),
        ('Attendance Counts', {'fields': (
            'adult_male', 'adult_female', 'youth_male', 'youth_female',
            'children_male', 'children_female', 'campus_male', 'campus_female',
            'cau', 'visitor', 'conv', 'ypf_male', 'ypf_female', 'zoom', 'youtube'
        )}),
    )


@admin.register(GCKAttendance)
class GCKAttendanceAdmin(admin.ModelAdmin):
    list_display = ('day', 'date', 'gck_event',  'adult', 'young_prf', 'campus', 'youths', 'children', 'zoom',
                    'youtube', 'fb_reached', 'fb_likes', 'fb_comments', 'ig_reached',
                    'ig_engagement', 'converts', 'remarks', 'is_workers')
    list_filter = ('day__name', 'day__date')
    search_fields = ('day__name', 'remarks')
    ordering = ('day__date',)


@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'session', 'local_church', 'is_workers')


@admin.register(GCKConvertsFollowUpReport)
class GCKConvertsFollowUpReportAdmin(admin.ModelAdmin):
    list_display = ('name', "date")


@admin.register(GCKProjections)
class GCKProjectionsAdmin(admin.ModelAdmin):
    list_display = ('region', 'month', "att_by_weeks", "att_target_for_month", "att_sunday_crusade")






