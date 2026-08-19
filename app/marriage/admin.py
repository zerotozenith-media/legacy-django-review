from django.contrib import admin

from marriage.models import MarriageRecord


@admin.register(MarriageRecord)
class MarriageRecordAdmin(admin.ModelAdmin):
    list_display = (
        'brother_name', 'brother_local_church', 'brother_country', 'brother_province_state',
        'brother_medical_tests_submitted', 'brother_medical_tests_reviewed',
        'sister_name', 'sister_local_church', 'sister_country', 'sister_province_state',
        'sister_medical_tests_submitted', 'sister_medical_tests_reviewed', 'remarks'
    )

    search_fields = ('brother_name', 'sister_name')
    list_filter = ('brother_country', 'sister_country', 'brother_province_state', 'sister_province_state')
