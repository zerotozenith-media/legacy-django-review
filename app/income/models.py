from django.db import models
from authentication.models import User
from organization.models import BankAccount, LocalChurch, Region
from core.models import BaseModel
from django.utils.timezone import now


class Source(BaseModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=255, default="Income", null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    entry_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, related_name="source_entry")

    def __str__(self):
        return self.name


class Income(BaseModel):
    local_church = models.ForeignKey(LocalChurch, on_delete=models.DO_NOTHING, null=True, related_name="local_church_income")
    account = models.ForeignKey(BankAccount, on_delete=models.DO_NOTHING, null=True , related_name="account_income")
    amount = models.DecimalField(max_digits=12, decimal_places=6)
    description = models.TextField()
    date = models.DateField(default=now)
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True,blank=True, related_name="source_income")
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING, null=True, blank=True,
                               related_name='region_income')

    def __str__(self):
        return f"Income: {self.amount} on {self.date}"

    class Meta:
        ordering = ["-date"]


class DonationInKind(BaseModel):
    local_church = models.ForeignKey(LocalChurch, on_delete=models.DO_NOTHING, null=True,
                                     related_name="local_church_donation_in_kind")
    donor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text="The user who made the donation (if applicable).")
    donor_name = models.CharField(max_length=255, null=True, blank=True, help_text="Name of the donor if not a registered user.")
    donation_item = models.CharField(max_length=255, help_text="Description of the donated item (e.g., Car, Speaker).")
    description = models.TextField(blank=True, null=True, help_text="Additional details about the donation.")
    donation_date = models.DateField(default=now)
    serial_no = models.CharField(max_length=255, null=True, blank=True)
    estimated_value = models.DecimalField(max_digits=10, decimal_places=2,  help_text="Estimated market value of the donation.")
    tax_receipt_issued = models.BooleanField(default=False, help_text="Indicates whether a tax receipt has been issued.")
    tax_receipt_number = models.CharField(max_length=50, blank=True, null=True, help_text="The tax receipt number if issued.")
    tax_receipt_date = models.DateField(blank=True, null=True, help_text="The date when the tax receipt was issued.")
    image = models.ImageField(
        upload_to='donations/images/',
        blank=True,
        null=True,
        help_text="Optional image of the donated item."
    )

    def __str__(self):
        donor_display = self.donor.first_name if self.donor else self.donor_name or "Anonymous"
        return f"Donation in Kind: {self.donation_item} from {donor_display}"
