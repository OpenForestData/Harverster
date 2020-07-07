from django.db import models
from pyDataverse.models import Dataset, Datafile


class Resource(object):
    """
    Represents resource imported form harvested systems
    """

    def __init__(
            self,
            parent_dataverse: str,
            dataset: Dataset = None,
            datafile: Datafile = None,
            uid: str = None,
            pid: str = None
    ):
        self.parent_dataverse = parent_dataverse
        if not dataset:
            dataset = Dataset()
        self.dataset = dataset
        self.datafile = datafile
        self.uid = uid
        self.pid = pid


class ResourceMapping(models.Model):
    DASHBOARD = 1
    LAYER = 2
    MAP = 3
    DOCUMENT = 4
    STUDY = 5

    category_choices = (
        (DASHBOARD, 'dashboard'),
        (LAYER, 'layer'),
        (MAP, 'map'),
        (DOCUMENT, 'document'),
        (STUDY, 'study'),
    )

    uid = models.fields.CharField(unique=True, max_length=50)
    pid = models.fields.CharField(max_length=24, blank=True, null=True)
    created_at = models.fields.DateTimeField(auto_now_add=True)
    last_update = models.fields.DateTimeField()
    category = models.fields.SmallIntegerField(choices=category_choices)

    class Meta:
        ordering = ["-last_update"]
