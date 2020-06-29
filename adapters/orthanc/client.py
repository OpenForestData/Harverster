import json
import logging
import os
from datetime import datetime
from typing import List

import requests
from django.utils import timezone
from pyDataverse.models import Datafile

from core.clients import HarvestingClient
from core.exceptions import HttpException
from core.models import Resource, ResourceMapping

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
            results: dict = self.__get_request(resource_path, {})
        except HttpException as e:
            http_exception_handler(e)
            return []

        resources: dict = results
        resources: list = self.__get_detailed_data(resources)

        add_resources: List[Resource] = self.__filter_new_resources(resources, resource_map_function,
                                                                    ResourceMapping.STUDY)
        update_resources: List[Resource] = self.__filter_update_resources(resources, resource_map_function)
        delete_resources: list = self.__filter_remove_resources(resources)

        return add_resources, update_resources, delete_resources

    def __get_detailed_data(self, resources: dict) -> list:
        """
        Fetch detailed data from Orthanc API dashboard route

        :param resources: list of harvested data from Orthanc search route
        :return: list of harvested data from Orthanc with detailed data
        """
        detailed_resources: list = []

        for resource in resources:
            response = requests.get(self.service_url + 'studies/' + resource)
            response_json = json.loads(response.text)

            detailed_resources.append(response_json)

        return detailed_resources

    @staticmethod
    def __filter_new_resources(resources: list, category, resource_map_function) -> list:
        """
        Filter only new Resources in list of raw data from source

        :param resources: fetched data from source with resources raw data
        :param resource_map_function: mapping function for resource
        :param category: category of resource for mapping
        :return: list of mapped resources
        """
        add_resources: list = []

        for resource in resources:
            uid: str = resource['ID']
            resource_mapping = ResourceMapping.objects.filter(uid=uid).first()

            if resource_mapping is None or resource_mapping.pid is None:
                if resource_mapping is None:
                    ResourceMapping(uid=uid, pid=None, last_update=timezone.now(), category=category).save()
                add_resources.append(resource)

        return [resource_map_function(resource) for resource in add_resources]

    @staticmethod
    def __filter_update_resources(resources, resource_map_function) -> list:
        """
        Filter only Resources to update in raw data from source

        :param resources: fetched data from source with resources raw data
        :param resource_map_function: mapping function for resource
        :return: list of mapped resources
        """
        update_resources: list = []

        for resource in resources:
            uid: list = resource['ID']
            resource_mapping: ResourceMapping = ResourceMapping.objects.filter(uid=uid).first()

            resource['pid'] = resource_mapping.pid if resource_mapping.pid else None
            date = datetime.strptime(resource['LastUpdate'], '%Y%m%dT%H%M%S')

            if resource_mapping is not None and (
                    resource_mapping.last_update.replace(tzinfo=None) < date):
                update_resources.append(resource)

        return [resource_map_function(resource, create_file=False) for resource in update_resources]

    @staticmethod
    def __filter_remove_resources(resources: list) -> list:
        """
        Filter Resources deleted in source

        :param resources: fetched data from source with resources raw data
        :param category: category of resource for mapping
        :return: list of resources to delete
        """
        resources_uid: List[str] = [resource['ID'] for resource in resources]
        delete_resources = ResourceMapping.objects.filter(
            category=ResourceMapping.STUDY
        ).exclude(
            uid__in=resources_uid
        )

        return list(delete_resources)

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

    def __map_study_to_resource(self, study: dict, create_file: bool = True) -> Resource:
        """
        Maps study to Resource object

        :param study: dict to map to Resource
        :return: Resource representing study
        """
        uid: str = study['ID']

        # Todo: Move to separated function in core
        if create_file:
            datafile: Datafile = Datafile()

            # Create file data
            file_data: dict = {
                'uid': uid,
                'site_url': self.service_url,
                'details_url': f'studies/{uid}'
            }

            # Create file
            file_name: str = f'{uid}.study_orthanc'
            # TODO: Fix file open localization
            file_object = open(file_name, 'w')
            json.dump(file_data, file_object)

            # Create datafile.data
            data: dict = {
                'description': 'External tool file',
                'filename': file_name
            }

            # Close file
            file_object.close()

            # Set datafile data
            datafile.set(data=data)

            res: Resource = Resource(os.environ.get('STUDIES_PARENT_DATAVERSE'), datafile=datafile, uid=uid)
        else:
            pid: str = study['pid']

            res: Resource = Resource(os.environ.get('STUDIES_PARENT_DATAVERSE'), uid=uid, pid=pid)

        mapping: dict = self.__base_mapping(study)

        for key, val in mapping.items():
            setattr(res.dataset, key, val)

        return res

    @staticmethod
    def __email_mapping(obj: str) -> str:
        if physician_name := obj:
            return physician_name + '@test.pl'
        else:
            return 'unknown@test.pl'

    @staticmethod
    def __date_mapping(obj: str) -> str:
        if date_value := obj.strip():
            return datetime.strptime(date_value, '%Y%m%d').strftime('%Y-%m-%d')
        else:
            return datetime.now().strftime('%Y-%m-%d')

    @staticmethod
    def __unknown_value_mapping(obj: str, return_value: any = 'Unknown') -> str:
        if unknown_value := obj.strip():
            return unknown_value
        else:
            return return_value

    def __create_alternative_url(self, obj: str) -> str:
        """
        Create alternative url for Resource and return in full form

        :param obj: detail url data of resource
        :return: alternative url of resource
        """
        service_url: str = self.service_url if self.service_url[-1] == '/' else self.service_url[:-1]
        detail_url: str = f'osimis-viewer/app/index.html?study={obj}'

        return service_url + detail_url

    def __base_mapping(self, obj) -> dict:
        """
        Map raw data to compatible format for dataverse Resource

        :param obj: resource raw data to map
        :return: mapped resource
        """
        return {
            'title':
                self.__unknown_value_mapping(obj['PatientMainDicomTags']['PatientName']
                                             ) + ' ' + self.__unknown_value_mapping(obj['MainDicomTags']['StudyID']),
            'publicationDate': self.__date_mapping(obj['MainDicomTags']['StudyDate']),
            'author': [{
                'authorName': self.__unknown_value_mapping(obj['MainDicomTags']['ReferringPhysicianName']),
                'authorAffiliation': 'Orthanc'
            }],
            'alternativeURL': self.__create_alternative_url(obj['ID']),
            'datasetContact': [{
                'datasetContactEmail': self.__email_mapping(obj['MainDicomTags']['ReferringPhysicianName']),
                'datasetContactName': self.__unknown_value_mapping(obj['MainDicomTags']['ReferringPhysicianName'])
            }],
            'subject': ['Earth and Environmental Sciences'],
            'dsDescription': [{
                'dsDescriptionValue': obj['MainDicomTags'].get('StudyDescription', ' ')
            }],
            'depositor': self.__unknown_value_mapping(obj['MainDicomTags']['ReferringPhysicianName']),
            'dateOfDeposit': self.__date_mapping(obj['MainDicomTags']['StudyDate']),
        }
