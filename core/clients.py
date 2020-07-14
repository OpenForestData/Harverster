from abc import ABC, abstractmethod
from typing import List

from .models import Resource


class HarvestingClient(ABC):
    """
    Abstract HavrestingClient inheritance class describing standard client public methods
    """

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

    @abstractmethod
    def get_resources(self, resource_path: str, resource_map_function, resource_mapping_category) -> (
            List[Resource], List[Resource], list):
        """
        Fetch data from Source API endpoint and map it to Resource and return it as a list of add/update/remove
        Resources

        :param resource_path: url relative path to API endpoint
        :type resource_path: str
        :param resource_map_function: function mapping data type retrieved from endpoint to Resource object
        :param resource_mapping_category: category of mapping showed in ResourceMapping category field
        :return: list of fetched data as Resources list
        """
