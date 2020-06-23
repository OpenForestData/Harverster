import json
import logging
import os
from typing import List

import requests
from pyDataverse.models import Datafile

from core.clients import HarvestingClient
from core.exceptions import HttpException
from core.models import Resource

logger = logging.getLogger(__name__)


def http_exception_handler(e: HttpException):
    logger.exception(e)


class OrthancClient(HarvestingClient):

    def harvest(self) -> List[Resource]:
        """
        Harvests every resource from Orthanc and returns is as a list of Resources
        :return: list of harvested data from Orthanc
        """

        return self.get_resources('studies/', self.__map_study_to_resource)

    def get_resources(self, resource_path, resource_map_function) -> (list, list, list):
        """
        Fetch data from Orthanc API endpoint, maps it to Resource and returns it as a list of Resources
        :param resource_path: url relative path to API endpoint
        :param resource_map_function: function mapping data type retrieved from endpoint to Resource object
        :return: list of fetched data as Resources list
        """
        try:
            results = self.__get_request(resource_path, {})
        except HttpException as e:
            http_exception_handler(e)
            return []

        resources = results
        resources = self.__get_detailed_data(resources)

        return resources, [], []

    def __get_detailed_data(self, resources) -> list:
        """
        Fetch detailed data from Orthanc API dashboard route
        :param resources: list of harvested data from Orthanc search route
        :return: list of harvested data from Orthanc with detailed data
        """
        detailed_resources = []

        for resource in resources:
            response = requests.get(self.service_url + 'studies/' + resource)
            response_json = json.loads(response.text)

            detailed_resources.append(response_json)

        return detailed_resources

    def __get_only_new(self, resources, category, resource_map_function) -> list:
        raise NotImplementedError

    def __get_only_for_update(self, resources, resource_map_function) -> list:
        raise NotImplementedError

    def __get_only_to_remove(self, resources):
        raise NotImplementedError

    def __get_request(self, path: str, params: dict) -> dict:
        """
        Constructs GET request form given arguments, and loads json response as dict
        :param path: relative url path
        :param params: GET request parameters
        :return: response json as dict
        """
        response = requests.get(self.service_url + path, params=params)

        if response.status_code == requests.codes.ok:
            return json.loads(response.text)

        msg = f'GET {self.service_url + path} with params {params} returned: {response.status_code} {response.text}'
        raise HttpException(msg)

    def __map_study_to_resource(self, study, create_file: bool = True) -> Resource:
        """

        """
        uid = study['ID']

        # Todo: Move to separated function in core
        if create_file:
            datafile = Datafile()

            # Create file data
            file_data = {
                'uid': uid,
                'site_url': self.service_url,
                'details_url': f'studies/{uid}'
            }

            # Create file
            file_name = f'{uid}.study_orthanc'
            # TODO: Fix file open localization
            file_object = open(file_name, 'w')
            json.dump(file_data, file_object)

            # Create datafile.data
            data = {
                'description': 'External tool file',
                'filename': file_name
            }

            # Close file
            file_object.close()

            # Set datafile data
            datafile.set(data=data)

            res = Resource(os.environ.get('STUDIES_PARENT_DATAVERSE'), datafile=datafile, uid=uid)
        else:
            res = Resource(os.environ.get('STUDIES_PARENT_DATAVERSE'), uid=uid)

        mapping = self.__base_mapping(study)

        for key, val in mapping.items():
            setattr(res.dataset, key, val)

        return res

    @staticmethod
    def __base_mapping(obj):
        raise NotImplementedError
