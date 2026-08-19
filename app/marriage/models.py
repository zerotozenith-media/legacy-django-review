from cities_light.models import Region, Country
from django.db import models

from authentication.models import User
from core.models import BaseModel


class MarriageRecord(BaseModel):
    YES_NO_CHOICES = [
        ('YES', 'Yes'),
        ('NO', 'No'),
    ]

    # Brother's details
    brother_name = models.CharField(max_length=255)
    brother_local_church = models.ForeignKey('organization.LocalChurch', on_delete=models.SET_NULL,
                                             null=True, blank=True, related_name="brother_local_church")
    brother_country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name="brother_country")
    brother_province_state = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True,
                                               related_name="brother_province_state")
    brother_medical_tests_submitted = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='NO')
    brother_medical_tests_reviewed = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='NO')

    # Sister's details
    sister_name = models.CharField(max_length=255)
    sister_local_church = models.ForeignKey('organization.LocalChurch', on_delete=models.SET_NULL,
                                            null=True, blank=True, related_name="sister_local_church")
    sister_country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name="sister_country")
    sister_province_state = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True,
                                              related_name="sister_province_state")
    sister_medical_tests_submitted = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='NO')
    sister_medical_tests_reviewed = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='NO')

    remarks = models.TextField(blank=True, null=True)
    registered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name="registered_by")

    def __str__(self):
        return f"{self.brother_name} & {self.sister_name}"
