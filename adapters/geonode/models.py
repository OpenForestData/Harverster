from django.db import models


class HarvestingDatestamp(models.Model):
    resource_name = models.fields.CharField(max_length=10)
    date = models.fields.DateTimeField(auto_now_add=True)
    status = models.fields.CharField(max_length=10)


class ResourceIdMapping(models.Model):
    geonode_id = models.fields.IntegerField()
    dataverse_id = models.fields.IntegerField()
    dataverse_pid = models.fields.CharField(max_length=12)


class GeonodeResource(models.Model):
    pass
