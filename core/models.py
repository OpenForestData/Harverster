from django.db import models
from pyDataverse.models import Dataset, Datafile


class Resource(object):
    """
    Represents resource imported form harvested systems
    """
    def __init__(self, parent_dataverse: str, dataset: Dataset = None, datafile: Datafile = None):
        self.parent_dataverse = parent_dataverse
        if not dataset:
            dataset = Dataset()
        self.dataset = dataset
        self.datafile = datafile
