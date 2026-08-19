from django.contrib import admin
from .models import Transfer


class TransferAdmin(admin.ModelAdmin):
    list_display = ('region', 'account', 'amount', 'type', 'description', 'date')
    search_fields = ('region__name', 'account__account_name', 'type', 'description')
    list_filter = ('region', 'account', 'type', 'date')
    ordering = ['-date']
    list_per_page = 10


# Register the Transfer model with the admin
admin.site.register(Transfer, TransferAdmin)
