from abc import ABC, abstractmethod
from typing import List

from .models import Resource


class HarvestingClient(ABC):

    def __init__(self, api_key=None):
        self.api_key = api_key

    @abstractmethod
    def harvest(self) -> List[Resource]:
        """
        Function loads data from designated system and uploads it to Dataverse
        """