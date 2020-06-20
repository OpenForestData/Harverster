from django.db import models


class HarvestingDatestamp(models.Model):
    resource_name = models.fields.CharField(max_length=10)
    date = models.fields.DateTimeField(auto_now_add=True)
    status = models.fields.CharField(max_length=10)
