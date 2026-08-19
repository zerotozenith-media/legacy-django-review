from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from .managers import UserManager


class User(AbstractUser):
    MEMBER = 1
    LOCAL_CHURCH_PASTOR = 2
    NATIONAL_OVERSEER = 3
    REGION_OVERSEER = 4
    MARRIAGE_RECORDS = 5
    DONOR = 6

    ROLE_CHOICES = (
        (MEMBER, "member"),
        (LOCAL_CHURCH_PASTOR, "local_church_pastor"),
        (NATIONAL_OVERSEER, "national_overseer"),
        (REGION_OVERSEER, "region_overseer"),
        (MARRIAGE_RECORDS, "marriage_records"),
        (DONOR, "donor")
    )

    username = None
    email = models.EmailField(_("email address"), unique=True)
    full_name = models.CharField(max_length=512, blank=True, null=True)
    first_name = models.CharField(max_length=256, blank=True, null=True)
    middle_name = models.CharField(max_length=256, blank=True, null=True)
    last_name = models.CharField(max_length=256, blank=True, null=True)
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, blank=True, null=True)
    address = models.CharField(max_length=512, blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    local_church = models.ForeignKey('organization.LocalChurch', on_delete=models.DO_NOTHING, blank=True, null=True, related_name='user_local_church')

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.full_name if self.full_name else self.email
