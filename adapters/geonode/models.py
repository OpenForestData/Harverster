from django.db import models


class HarvestingDatestamp(models.Model):
    date = models.fields.DateTimeField(auto_now_add=True)
    status = models.fields.CharField(max_length=10)


class GeonodeResource(models.Model):
    pass
