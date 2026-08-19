from django.db import models
from organization.models import BankAccount, Region
from core.models import BaseModel
from django.utils.timezone import now


class Transfer(BaseModel):
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING, null=True, related_name="region_transfer")
    account = models.ForeignKey(BankAccount, on_delete=models.DO_NOTHING, null=True, related_name="account_transfer")
    amount = models.DecimalField(max_digits=12, decimal_places=6)
    type = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField()
    date = models.DateField(default=now)

    def __str__(self):
        return f"Transfer: {self.amount} on {self.date}"

    class Meta:
        ordering = ["-date"]
