from django.db import models
from pyDataverse.models import Dataset, Datafile


class Resource:
    """
    Represents resource imported form harvested systems
    """
    dataset: Dataset = Dataset()

    def __init__(
            self,
            parent_dataverse: str,
            datafile: Datafile = None,
            uid: str = None,
            pid: str = None
    ):
        self.parent_dataverse = parent_dataverse
        self.datafile = datafile
        self.uid = uid
        self.pid = pid

    def is_pid(self):
        """
        Check if value exists and return True or False value

        :return: True if pid is not None
        """
        return self.pid is not None

    def is_valid(self):
        """
        Check if dataset and datafile is valid

        :return: True if value is correct
        """
        is_valid = True

        if self.datafile is not None and not self.datafile.is_valid():
            is_valid = False

        if self.dataset is not None and not self.dataset.is_valid():
            is_valid = False

        return is_valid


class ResourceMapping(models.Model):
    """
    Model used for mapping resources and store last_update date
    """
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
