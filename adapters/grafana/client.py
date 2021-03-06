import json
import logging
import os
from typing import List

import requests
from django.conf import settings
from django.utils import timezone
from pyDataverse.models import Datafile

from core.clients import HarvestingClient
from core.exceptions import HttpException
from core.models import Resource, ResourceMapping

logger = logging.getLogger(__name__)


def http_exception_handler(exception: HttpException):
    logger.exception(exception)


class GrafanaClient(HarvestingClient):
    """
    Harvesting Client for harvesting Resources from Grafana
    """

    def harvest(self, force_update: bool = False) -> (List[Resource], list, list):
        """
        Harvests every resource from Grafana and returns is as a list of Resources

        :param force_update: force updating every resource with resource mapping
        :type force_update: bool
        :return: list of harvested data from Grafana
        """

        return self.get_resources('api/search/', self.__map_dashboard_to_resource, ResourceMapping.DASHBOARD,
                                  force_update)

    def get_resources(self, resource_path: str, resource_map_function, resource_mapping_category,
                      force_update: bool = False) -> (List[Resource], list, list):
        """
        Fetch data from Grafana API endpoint, maps it to Resource and returns it as a list of add/update/remove
        Resources

        :param resource_path: url relative path to API endpoint
        :type resource_path: str
        :param resource_map_function: function mapping data type retrieved from endpoint to Resource object
        :param resource_mapping_category: category of mapping showed in ResourceMapping category field
        :param force_update: force updating every resource with resource mapping
        :type force_update: bool
        :return: list of fetched data as Resources list
        """
        params: dict = {
            'limit': 10,
        }

        try:
            results: list = self.__get_request(resource_path, params)
        except HttpException as exception:
            http_exception_handler(exception)
            return []

        resources: list = results
        page_number: int = 1
        while len(results) > 0:
            page_number += 1
            results: list = self.__get_next_page(resource_path, page_number, params['limit'])
            resources += results

        # Get detailed resource data
        resources: list = self.__get_detailed_data(resources)
        add_resources: List[Resource] = self.__filter_new_resources(resources, resource_map_function,
                                                                    resource_mapping_category)
        update_resources = []
        if force_update:
            update_resources = self.__filter_update_resources(resources, resource_map_function)
        delete_resources: list = self.__filter_remove_resources(resources)

        return add_resources, update_resources, delete_resources

    @staticmethod
    def __filter_new_resources(resources: list, resource_map_function, category) -> List[Resource]:
        """
        Filter only new Resources in list of raw data from source

        :param resources: fetched data from source with resources raw data
        :type resources: list
        :param resource_map_function: mapping function for resource
        :param category: category of resource for mapping
        :return: list of mapped resources
        """
        add_resources: list = []

        for resource in resources:
            uid: str = resource['search']['uid']
            resource_mapping: ResourceMapping = ResourceMapping.objects.filter(uid=uid).first()

            if resource_mapping is None or resource_mapping.pid is None:
                if resource_mapping is None:
                    ResourceMapping(uid=uid, pid=None, last_update=timezone.now(), category=category).save()

                add_resources.append(resource)

        return [resource_map_function(resource) for resource in add_resources]

    @staticmethod
    def __filter_update_resources(resources: list, resource_map_function) -> List[Resource]:
        """
        Filter only Resources to update in raw data from source

        :param resources: fetched data from source with resources raw data
        :type resources: list
        :param resource_map_function: mapping function for resource
        :return: list of mapped resources
        """
        update_resources: list = []

        for resource in resources:
            uid: str = resource['search']['uid']
            resource_mapping: ResourceMapping = ResourceMapping.objects.filter(uid=uid).first()

            resource['pid'] = resource_mapping.pid if resource_mapping.pid else None

            if resource_mapping is not None and resource_mapping.pid is not None:
                update_resources.append(resource)

        return [resource_map_function(resource, create_file=False) for resource in update_resources]

    @staticmethod
    def __filter_remove_resources(resources: list) -> list:
        """
        Filter Resources deleted in source

        :param resources: fetched data from source with resources raw data
        :type resources: list
        :return: list of resources to delete
        """
        resources_uid: List[str] = [resource['search']['uid'] for resource in resources]
        delete_resources = ResourceMapping.objects.filter(
            category=ResourceMapping.DASHBOARD
        ).exclude(
            uid__in=resources_uid
        )

        return list(delete_resources)

    def __get_detailed_data(self, resources: list) -> list:
        """
        Fetch detailed data from Grafana API dashboard route

        :param resources: list of harvested data from Grafana search route
        :type resources: list
        :return: list of harvested data from Grafana with detailed data
        """
        headers: dict = {
            'Authorization': f'Bearer {self.api_key}'
        }

        detailed_resources: list = []

        for resource in resources:
            uid: str = resource['uid']
            response = requests.get(self.service_url + 'api/dashboards/uid/' + uid, headers=headers, timeout=10)
            response_json = json.loads(response.text)

            res: dict = {
                'meta': response_json['meta'],
                'dashboard': response_json['dashboard'],
                'search': resource
            }

            detailed_resources.append(res)

        return detailed_resources

    def __get_next_page(self, path: str, page: int, limit: int) -> list:
        """
        Sends get_request for next page

        :param path: relative url path
        :type path: str
        :param page: request list page
        :type page: int
        :param limit: request list limit
        :type limit: int
        :return: __get_request function with params for next page
        """
        params: dict = {
            'limit': limit,
            'page': page
        }

        return self.__get_request(path, params)

    def __get_request(self, path: str, params: dict) -> list:
        """
        Constructs GET request form given arguments, and loads json response as dict

        :param path: relative url path
        :type path: list
        :param params: GET request parameters
        :type params: dict
        :return: response json as dict
        """
        headers: dict = {
            'Authorization': f'Bearer {self.api_key}'
        }

        response = requests.get(self.service_url + path, params=params, headers=headers, timeout=10)

        if response.status_code == requests.codes.ok:
            return json.loads(response.text)

        msg = f'GET {self.service_url + path} with params {params} returned: {response.status_code} {response.text}'
        raise HttpException(msg)

    def __map_dashboard_to_resource(self, dashboard: dict, create_file: bool = True) -> Resource:
        """
        Maps dashboard to Resource object

        :param dashboard: dict to map to Resource
        :type dashboard: dict
        :param create_file: define create file or not
        :type create_file: bool
        :return: Resource representing layer
        """
        uid: str = dashboard['search']['uid']

        # Todo: Move to separated function in core
        if create_file:
            datafile: Datafile = Datafile()

            # Create file data
            file_data: dict = {
                'uid': uid,
                'site_url': self.service_url,
                'details_url': f'/api/dashboards/uid/{uid}'
            }

            # Create file
            file_name: str = f'{uid}.mpkg'
            file_full_path: str = (settings.EXTERNAL_FILES_ROOT + file_name)
            file_object = open(file_full_path, 'w')
            json.dump(file_data, file_object)

            # Create datafile.data
            data: dict = {
                'description': 'External tool file',
                'filename': file_full_path
            }

            # Close file
            file_object.close()

            # Set datafile data
            datafile.set(data=data)

            res: Resource = Resource(os.environ.get('DASHBOARDS_PARENT_DATAVERSE'), datafile=datafile, uid=uid)
        else:
            pid: str = dashboard['pid']

            res: Resource = Resource(os.environ.get('DASHBOARDS_PARENT_DATAVERSE'), pid=pid, uid=uid)

        mapping: dict = self.__base_mapping(dashboard)

        for key, val in mapping.items():
            setattr(res.dataset, key, val)

        res.last_update = timezone.now()

        return res

    def __create_alternative_url(self, obj: str) -> str:
        """
        Create alternative url for Resource and return in full form

        :param obj: detail url data of resource
        :type obj: str
        :return: alternative url of resource
        """
        service_url: str = self.service_url if self.service_url[-1] == '/' else self.service_url[:-1]
        detail_url: str = obj[1:] if obj[0] == '/' else obj

        return service_url + 'd/' + detail_url

    def __base_mapping(self, obj: dict) -> dict:
        """
        Map raw data to compatible format for dataverse Resource

        :param obj: resource raw data to map
        :type obj: dict
        :return: mapped resource
        """
        return {
            'title': obj['search']['title'],
            'publicationDate': obj['meta']['created'],
            'author': [{'authorName': obj['meta']['createdBy'],
                        'authorAffiliation': ' '}],
            'alternativeURL': self.__create_alternative_url(obj['search']['uid']),
            'datasetContact': [{'datasetContactEmail': 'ofd@ibs.bialowieza.pl',
                                'datasetContactName': obj['meta']['createdBy']}],
            'dataSources': ['Grafana'],
            'subject': ['Earth and Environmental Sciences'],
            'dsDescription': [{'dsDescriptionValue': obj['search'].get('title', 'Unknown')}],
            'depositor': obj['meta']['createdBy'],
            'dateOfDeposit': obj['meta']['created'],
        }
