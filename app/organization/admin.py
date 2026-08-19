from django.contrib import admin
from .models import (
    City, Region, LocalChurch, LocalChurchName, BankAccount, Currency, GcCode, DetailReport,
    PaymentAllocation, Reconciliation, AllocationReconciliation
)

PER_PAGE = 20


# Admin for Region
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'region_overseer', 'gck_canada_payment')
    search_fields = ('name', 'region_overseer__full_name')
    list_filter = ('region_overseer',)
    list_per_page = PER_PAGE
    
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'region')
    search_fields = ('name', 'region__name')
    list_filter = ('region',)
    list_per_page = PER_PAGE


# Admin for LocalChurch
class LocalChurchAdmin(admin.ModelAdmin):
    list_display = ('local_church_name', 'local_church_pastor', 'region')
    search_fields = ('local_church_name__title', 'local_church_pastor__full_name', 'region__name')
    list_filter = ('region',)
    list_per_page = PER_PAGE


# Admin for BankAccount
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'account_number', 'balance', 'region')
    search_fields = ('account_name', 'account_number', 'region__name')
    list_filter = ('region',)
    list_per_page = PER_PAGE


# Admin for Currency
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')
    list_per_page = PER_PAGE


# Admin for GcCode
class GcCodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'local_church')
    search_fields = ('name', 'code', 'local_church__local_church_name__title')
    list_filter = ('local_church',)
    list_per_page = PER_PAGE


# Admin for DetailReport
class DetailReportAdmin(admin.ModelAdmin):
    list_display = ('local_church', 'date', 'comment', 'problem', 'testimony', 'follow_up')
    search_fields = ('local_church__local_church_name__title', 'comment', 'problem', 'testimony', 'follow_up')
    list_filter = ('local_church', 'date')
    list_per_page = PER_PAGE


# Admin for PaymentAllocation
class PaymentAllocationAdmin(admin.ModelAdmin):
    list_display = ('region', 'date', 'income', 'total_amount', 'paid_amount', 'name', 'payment_date')
    search_fields = ('region__name', 'name', 'note')
    list_filter = ('region', 'name')
    fields = ('region', 'date', 'income', 'total_amount', 'paid_amount', 'name', 'payment_date', 'note')
    list_per_page = PER_PAGE


# Admin for Reconciliation
class ReconciliationAdmin(admin.ModelAdmin):
    list_display = ('region', 'date', 'description', 'recon_type', 'amount')
    search_fields = ('region__name', 'description', 'recon_type')
    list_filter = ('region', 'recon_type')
    list_per_page = PER_PAGE


# Admin for AllocationReconciliation
class AllocationReconciliationAdmin(admin.ModelAdmin):
    list_display = ('region',  'account_type', 'payment_date', 'amount', 'uploaded_at')
    search_fields = ('region__name',)
    list_filter = ('account_type',)
    list_per_page = PER_PAGE


# Register models with their corresponding admin classes
admin.site.register(Region, RegionAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(LocalChurch, LocalChurchAdmin)
admin.site.register(LocalChurchName)
admin.site.register(BankAccount, BankAccountAdmin)
admin.site.register(Currency, CurrencyAdmin)
admin.site.register(GcCode, GcCodeAdmin)
admin.site.register(DetailReport, DetailReportAdmin)
admin.site.register(PaymentAllocation, PaymentAllocationAdmin)
admin.site.register(Reconciliation, ReconciliationAdmin)
admin.site.register(AllocationReconciliation, AllocationReconciliationAdmin)
