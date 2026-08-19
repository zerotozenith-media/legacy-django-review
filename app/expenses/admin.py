from django.contrib import admin
from .models import Category, SubCategory, Expense


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type')
    list_filter = ('category_type',)
    search_fields = ('name',)
    ordering = ('name',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # You can add custom filtering logic here if needed
        return queryset


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    list_filter = ('parent',)
    search_fields = ('name',)
    ordering = ('name',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # You can add custom filtering logic here if needed
        return queryset


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        'local_church', 'amount', 'tax_amount', 'description', 'date', 'category', 'sub_category', 'tax_category')
    list_filter = ('local_church', 'category', 'sub_category', 'tax_category', 'date')
    search_fields = ('description', 'local_church__name')
    ordering = ('-date',)
    list_per_page = 10

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # You can add custom filtering logic here if needed
        return queryset
