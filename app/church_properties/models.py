# models.py
from django.db import models

from core.models import BaseModel


class ChurchProperties(BaseModel):
    local_church = models.ForeignKey('organization.LocalChurch', on_delete=models.DO_NOTHING, blank=True, null=True,
                                     related_name='church_branch')
    name = models.CharField(max_length=255)
    purchase_date = models.DateField()
    description = models.TextField(null=True, blank=True)
    serial_no = models.CharField(max_length=100, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2)
    disposal_date = models.DateField(null=True, blank=True)
    mode_of_disposal = models.CharField(max_length=200, blank=True, null=True)
    amount_sold = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Church Properties'

    # def get_absolute_url(self):
    #     return reverse('property_detail', args=[str(self.id)])
