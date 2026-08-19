from django.contrib import admin
from .models import Source, Income, DonationInKind


class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "entry_by", "description")
    search_fields = ("name", "type", "description", "entry_by__full_name")
    list_filter = ("type", "entry_by")  # Filter by type or entry_by
    ordering = ("name",)  # Sort by name alphabetically
    list_per_page = 10


class IncomeAdmin(admin.ModelAdmin):
    list_display = (
        "local_church", "account", "amount", "date", "description", "source"
    )
    search_fields = (
        "local_church__local_church_name",  # Search by LocalChurch name
        "account__name",  # Search by BankAccount name
        "description",
        "source__name",  # Search by Source name
    )
    list_filter = ("local_church", "account", "source")  # Filter by local_church, account, and source
    ordering = ("-date",)  # Sort by date descending
    list_per_page = 10


class DonationInKindAdmin(admin.ModelAdmin):
    list_display = ("local_church", "donor", "donor_name", "description", "donation_item", "estimated_value",
                    "donation_date", "image")
    search_fields = ("local_church", "donor", "donor_name",)
    list_filter = ("local_church", "donor", "donor_name",)  # Filter by type or entry_by
    list_per_page = 10


admin.site.register(Source, SourceAdmin)
admin.site.register(Income, IncomeAdmin)
admin.site.register(DonationInKind, DonationInKindAdmin)
