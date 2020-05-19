from abc import ABC, abstractmethod
from pyDataverse.models import Dataset
from pyDataverse.api import Api

class BaseClient(ABC):

    dataverse_api = Api

    def harvest(self):
        """
        Function loads data from designated system and uploads it to Dataverse
        """
        resources = self.get_resources()


    @abstractmethod
    def get_resources(self):
        pass