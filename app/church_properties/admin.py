from django.contrib import admin
from .models import ChurchProperties


@admin.register(ChurchProperties)
class ChurchPropertiesAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'local_church', 'purchase_date', 'amount_paid', 'mode_of_disposal', 'disposal_date', 'amount_sold')
    list_filter = ('local_church', 'purchase_date', 'disposal_date', 'mode_of_disposal')
    search_fields = ('name', 'serial_no', 'local_church__name')
    ordering = ('purchase_date',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # You can add custom filtering logic here if needed
        return queryset
