from django.db import models
from core.models import BaseModel
from authentication.models import User


class Region(BaseModel):
    name = models.CharField(max_length=50, blank=False, null=False)
    region_overseer = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="managed_region", null=True,
                                        blank=True)
    gck_canada_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='cities')
    
    class Meta:
        unique_together = ['name', 'region']
    
    def __str__(self):
        return self.name


class LocalChurch(BaseModel):
    local_church_name = models.ForeignKey('LocalChurchName', on_delete=models.CASCADE)
    local_church_pastor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='pastor_churches')
    region = models.ForeignKey(Region, on_delete=models.PROTECT, blank=True, null=True, related_name="local_churches")

    def __str__(self) -> str:
        return self.local_church_name.title

    class Meta:
        verbose_name = "Local Church"
        verbose_name_plural = "Local Churches"


class LocalChurchName(BaseModel):
    title = models.CharField(max_length=100)

    def __str__(self) -> str:
        return f"{self.title}"


class BankAccount(BaseModel):
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING, null=True, related_name='region_bank')
    # it should be region because every every region can have one or more bank accounts
    account_name = models.CharField(max_length=256, blank=True, null=True)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    account_description = models.TextField()
    balance = models.DecimalField(max_digits=20, decimal_places=6)

    def __str__(self) -> str:
        return f"{self.account_name}"


class Currency(BaseModel):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"

    def __str__(self):
        return self.code


class GcCode(BaseModel):
    name = models.CharField(max_length=256, null=True, blank=True)
    code = models.CharField(max_length=50, unique=True, null=False, blank=False)
    local_church = models.ForeignKey('organization.LocalChurch', on_delete=models.DO_NOTHING,
                                     related_name="gc_local_churches", null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='gc_codes')

    class Meta:
        verbose_name = "GC Code"
        verbose_name_plural = "GC Codes"

    def __str__(self):
        return self.code


class DetailReport(models.Model):
    local_church = models.ForeignKey('LocalChurch', on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    problem = models.TextField(null=True, blank=True)
    testimony = models.TextField(null=True, blank=True)
    follow_up = models.TextField(null=True, blank=True)


class PaymentAllocation(models.Model):
    ALLOCATION_CHOICES = [
        ('dclm', "DCLM"),
        ('gck', "GCK"),
        ('gck_canada', "GCK Canada"),
    ]
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING, null=True, related_name='region_allocation_payment')
    date = models.DateField(null=True, blank=True)
    income = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=20, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=20, decimal_places=2)
    note = models.TextField(null=True, blank=True)
    name = models.CharField(choices=ALLOCATION_CHOICES, null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)


class Reconciliation(models.Model):
    RECON_TYPE_CHOICES = [
        ('income', "Income"),
        ('expense', "Expense"),
        ('other', "Other"),
    ]
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING, null=True,
                               related_name='region_bank_reconciliation')
    date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    recon_type = models.CharField(choices=RECON_TYPE_CHOICES, default='other', null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)


class AllocationReconciliation(models.Model):
    ACCOUNT_CHOICES = [
        ('dclm_gck', "DCLM/GCK"),
        ('gck_canada', "GCK CANADA"),
    ]
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING, null=True,
                               related_name='region_allocation_reconciliation')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_CHOICES)
    payment_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account_type} statement for {self.region} - {self.payment_date}"
