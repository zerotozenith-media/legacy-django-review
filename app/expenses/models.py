from django.db import models
from core.models import BaseModel
from organization.models import LocalChurch, Region
from django.utils.timezone import now


class Category(BaseModel):
    RECURRENT = 1
    CAPITAL = 2

    CATEGORY_CHOICES = (
        (RECURRENT, "recurrent"),
        (CAPITAL, "capital"),
    )
    name = models.CharField(max_length=255)
    category_type = models.PositiveSmallIntegerField(
        choices=CATEGORY_CHOICES, default=1
    )

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class SubCategory(BaseModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(Category, on_delete=models.DO_NOTHING, null=True, related_name='subcategories')

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Sub Categories"

    def __str__(self):
        return self.name


class Expense(BaseModel):
    TAX_CATEGORY_CHOICES = (
        ('HST', 'HST'),
        ('GST', 'GST'),
        ('PST', 'PST'),
        ('PVQ', 'PVQ'),
        ('TPS', 'TPS'),
        ('Carbon', 'Carbon'),
        ('Tax_7', 'Tax 7*'),
        ('Tax_8', 'Tax 8*'),
        ('Non-Applicable', 'Non-Applicable'),
    )
    DEFAULT_TAX_CATEGORY = 'HST'

    local_church = models.ForeignKey(LocalChurch, on_delete=models.DO_NOTHING, null=True, related_name='expenses')
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING, null=True, blank=True,
                               related_name='region_expenses')
    amount = models.DecimalField(max_digits=12, decimal_places=6)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    date = models.DateField(default=now)
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, null=True, related_name='expenses_categories')
    sub_category = models.ForeignKey(SubCategory, on_delete=models.DO_NOTHING, null=True,
                                     related_name='expenses_sub_categories')
    tax_category = models.CharField(max_length=20, choices=TAX_CATEGORY_CHOICES, default=DEFAULT_TAX_CATEGORY)

    def __str__(self):
        return f"Expense: {self.amount} on {self.created_date}"

    class Meta:
        ordering = ["-created_date"]
