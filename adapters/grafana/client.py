import json
import logging
import os
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


class GrafanaClient(HarvestingClient):

    def harvest(self) -> List[Resource]:
        """
        Harvests every resource from Grafana and returns is as a list of Resources

        :return: list of harvested data from Grafana
        """

        return self.get_resources('api/search/', self.__map_dashboard_to_resource)

    def get_resources(self, resource_path: str, resource_map_function) -> (List[Resource],
                                                                           list,
                                                                           list):
        """
        Fetch data from Grafana API endpoint, maps it to Resource and returns it as a list of add/update/remove
        Resources

        :param resource_path: url relative path to API endpoint
        :param resource_map_function: function mapping data type retrieved from endpoint to Resource object
        :return: list of fetched data as Resources list
        """
        params: dict = {
            'limit': 10,
        }

        try:
            results: list = self.__get_request(resource_path, params)
        except HttpException as e:
            http_exception_handler(e)
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
                                                                    ResourceMapping.DASHBOARD)
        delete_resources: list = self.__filter_remove_resources(resources)

        return add_resources, [], delete_resources

    @staticmethod
    def __filter_new_resources(resources: list, resource_map_function, category) -> List[Resource]:
        """
        Filter only new Resources in list of raw data from source

        :param resources: fetched data from source with resources raw data
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
    def __filter_remove_resources(resources: list) -> list:
        """
        Filter Resources deleted in source

        :param resources: fetched data from source with resources raw data
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
        :return: list of harvested data from Grafana with detailed data
        """
        headers: dict = {
            'Authorization': f'Bearer {self.api_key}'
        }

        detailed_resources: list = []

        for resource in resources:
            uid: str = resource['uid']
            response = requests.get(self.service_url + 'api/dashboards/uid/' + uid, headers=headers)
            response_json = json.loads(response.text)

            res: dict = {
                'meta': response_json['meta'],
                'dashboard': response_json['dashboard'],
                'search': resource
            }

            detailed_resources.append(res)

        return detailed_resources

    def __get_next_page(self, path: str, page: int, limit: int) -> list:
        params: dict = {
            'limit': limit,
            'page': page
        }

        return self.__get_request(path, params)

    def __get_request(self, path: str, params: dict) -> list:
        """
        Constructs GET request form given arguments, and loads json response as dict
        :param path: relative url path
        :param params: GET request parameters
        :return: response json as dict
        """
        headers: dict = {
            'Authorization': f'Bearer {self.api_key}'
        }

        response = requests.get(self.service_url + path, params=params, headers=headers)

        if response.status_code == requests.codes.ok:
            return json.loads(response.text)

        msg = f'GET {self.service_url + path} with params {params} returned: {response.status_code} {response.text}'
        raise HttpException(msg)

    def __map_dashboard_to_resource(self, dashboard: dict, create_file: bool = True) -> Resource:
        """
        Maps dashboard to Resource object
        :param dashboard: dict to map to Resource
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
            file_name: str = f'{uid}.dashboard_grafana'
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

            res: Resource = Resource(os.environ.get('DASHBOARDS_PARENT_DATAVERSE'), datafile=datafile, uid=uid)
        else:
            res: Resource = Resource(os.environ.get('DASHBOARDS_PARENT_DATAVERSE'), uid=uid)

        mapping: dict = self.__base_mapping(dashboard)

        for key, val in mapping.items():
            setattr(res.dataset, key, val)

        return res

    def __create_alternative_url(self, obj: str) -> str:
        """
        Create alternative url for Resource and return in full form

        :param obj: detail url data of resource
        :return: alternative url of resource
        """
        service_url: str = self.service_url if self.service_url[-1] == '/' else self.service_url[:-1]
        detail_url: str = obj[1:] if obj[0] == '/' else obj

        return service_url + detail_url

    def __base_mapping(self, obj) -> dict:
        """
        Map raw data to compatible format for dataverse Resource

        :param obj: resource raw data to map
        :return: mapped resource
        """
        # TODO: Fix keyword mapping
        return {
            'title': obj['search']['title'],
            'publicationDate': obj['meta']['created'],
            'author': [{'authorName': obj['meta']['createdBy'],
                        'authorAffiliation': 'Grafana'}],
            'alternativeURL': self.__create_alternative_url(obj['search']['uid']),
            'datasetContact': [{'datasetContactEmail': obj['meta']['createdBy'] + '@test.com',
                                'datasetContactName': obj['meta']['createdBy']}],
            'subject': ['Earth and Environmental Sciences'],
            # 'keyword': obj['search']['tags'],
            'dsDescription': [{'dsDescriptionValue': ''}],
            'depositor': obj['meta']['createdBy'],
            'dateOfDeposit': obj['meta']['created'],
        }
