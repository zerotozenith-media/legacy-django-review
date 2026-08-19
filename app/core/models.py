from django.db import models


class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True
        ordering = ['-created_date']
