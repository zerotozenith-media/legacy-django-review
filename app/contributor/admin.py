from django.contrib import admin
from .models import Contribution, MiscellaneousContribution, AnonymousContribution, MiscellaneousUser, EmailQueue


# Contribution Admin
@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = [
        "contributor",
        "amount",
        "deposited_date",
        "payment_type",
        "special_contribution",
        "month",
        "local_church",
        "account_type",
    ]
    list_filter = ["payment_type", "special_contribution", "account_type", "local_church"]
    search_fields = ["contributor__full_name", "local_church__local_church_name__title"]
    list_per_page = 20


# Miscellaneous Contribution Admin
@admin.register(MiscellaneousContribution)
class MiscellaneousContributionAdmin(admin.ModelAdmin):
    list_display = [
        "contributor",
        "deposited_date",
        "amount",
        "payment_type",
        "special_contribution",
        "month",
        "local_church",
    ]
    list_filter = ["payment_type", "special_contribution"]
    search_fields = ["contributor__full_name", "local_church__local_church_name__title"]
    list_per_page = 20


# Anonymous Contribution Admin
@admin.register(AnonymousContribution)
class AnonymousContributionAdmin(admin.ModelAdmin):
    list_display = [
        "deposited_date",
        "amount",
        "payment_type",
        "special_contribution",
        "month",
        "local_church",
    ]
    list_filter = ["payment_type", "special_contribution"]
    search_fields = ["local_church__local_church_name__title"]
    list_per_page = 20


# Miscellaneous User Admin
@admin.register(MiscellaneousUser)
class MiscellaneousUserAdmin(admin.ModelAdmin):
    list_display = [
        "full_name",
        "first_name",
        "middle_name",
        "last_name",
        "email",
        "address",
        "registered_miscellaneous",
    ]
    search_fields = ["full_name", "email"]


# Email Queue Admin
@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    list_display = [field.name for field in EmailQueue._meta.fields if field.name != "id"]  # noqa
    search_fields = ["email", "report_type"]
    list_filter = ["report_year", "report_type"]
