from abc import ABC, abstractmethod
from typing import List

from .models import Resource


class HarvestingClient(ABC):

    def __init__(self, service_url, api_key=None):
        if service_url[-1] != '/':
            service_url += '/'
        self.service_url = service_url
        self.api_key = api_key

    @abstractmethod
    def harvest(self) -> List[Resource]:
        """
        Function loads data from designated system and uploads it to Dataverse
        """