from django.db import models
from pyDataverse.models import Dataset, Datafile


class Resource(object):
    """
    Represents resource imported form harvested systems
    """

    def __init__(self, parent_dataverse: str, dataset: Dataset = None, datafile: Datafile = None, uid: str = None):
        self.parent_dataverse = parent_dataverse
        if not dataset:
            dataset = Dataset()
        self.dataset = dataset
        self.datafile = datafile
        self.uid = uid


class ResourceMapping(models.Model):
    GRAFANA = 1
    GEONODE = 2
    category_choices = (
        (GRAFANA, 'grafana'),
        (GEONODE, 'geonode'),
    )

    uid = models.fields.CharField(unique=True, max_length=40)
    pid = models.fields.CharField(max_length=24, blank=True, null=True)
    created_at = models.fields.DateTimeField(auto_now_add=True)
    last_update = models.fields.DateTimeField()
    category = models.fields.SmallIntegerField(choices=category_choices)

    class Meta:
        ordering = ["-last_update"]
