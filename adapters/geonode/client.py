import json
import logging
import os
from typing import List

import pytz
import requests
from django.conf import settings
from django.utils.dateparse import parse_datetime
from pyDataverse.models import Datafile

from core.clients import HarvestingClient
from core.exceptions import HttpException
from core.models import Resource, ResourceMapping

logger = logging.getLogger(__name__)


def http_exception_handler(exception: HttpException):
    logger.exception(exception)


class GeonodeClient(HarvestingClient):
    """
    Harvesting Client for harvesting Resources from Geonode
    """

    offset = settings.GEONODE_OFFSET

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def harvest(self) -> (List[Resource], List[Resource], list):
        """
        Harvests every resource from Geonode and returns as a list of add/update/remove Resources

        :return: list of add/update/remove lists with Resources of harvested data from Geonode
        """
        layers = self.get_resources('api/layers/', self.__map_layer_to_resource, ResourceMapping.LAYER)
        maps = self.get_resources('api/maps/', self.__map_map_to_resource, ResourceMapping.MAP)
        documents = self.get_resources('api/documents/', self.__map_document_to_resource, ResourceMapping.DOCUMENT)

        add_data = layers[0] + maps[0] + documents[0]
        update_data = layers[1] + maps[1] + documents[1]
        remove_data = layers[2] + maps[2] + documents[2]

        return add_data, update_data, remove_data

    def get_resources(self, resource_path: str, resource_map_function, resource_mapping_category) -> (List[Resource],
                                                                                                      List[Resource],
                                                                                                      list):
        """
        Fetch data from Geonode API endpoint, maps it to Resource and returns it as a list of Resources to add, update
        and remove

        :param resource_path: url relative path to API endpoint
        :type resource_path: str
        :param resource_map_function: function mapping data type retrieved from endpoint to Resource object
        :param resource_mapping_category: category of mapping showed in ResourceMapping category field
        :return: list of add/update/remove fetched data as Resources lists
        """
        params: dict = {
            'offset': 0,
            'order_by': 'date'
        }

        try:
            results: dict = self.__get_request(resource_path, params)
        except HttpException as exception:
            http_exception_handler(exception)
            return [], [], []

        resources: list = results['objects']

        while results['meta']['next'] is not None:
            results: dict = self.__get_next_page(resource_path, results['meta']['limit'], results['meta']['offset'])
            resources += results['objects']

        add_resources: list = self.__filter_new_resources(resources, resource_map_function, resource_mapping_category)
        update_resources: list = self.__filter_update_resources(resources, resource_map_function)
        delete_resources: list = self.__filter_remove_resources(resources, resource_mapping_category)

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
            uid: str = resource['uuid']
            resource_mapping: ResourceMapping = ResourceMapping.objects.filter(uid=uid).first()

            if resource_mapping is None or resource_mapping.pid is None:
                if resource_mapping is None:
                    last_update = parse_datetime(resource['date']).replace(tzinfo=pytz.UTC)
                    ResourceMapping(uid=uid, pid=None, last_update=last_update, category=category).save()

                add_resources.append(resource)

        return [resource_map_function(resource) for resource in add_resources]

    @staticmethod
    def __filter_update_resources(resources: list, resource_map_function) -> List[Resource]:
        """
        Filter only Resources to update in raw data from source

        :param resources: fetched data from source with resources raw data
        :param resource_map_function: mapping function for resource
        :return: list of mapped resources
        """
        update_resources: list = []

        for resource in resources:
            uid: str = resource['uuid']
            resource_mapping: ResourceMapping = ResourceMapping.objects.filter(uid=uid).first()

            resource['pid'] = resource_mapping.pid if resource_mapping.pid else None
            date = parse_datetime(resource['date'])

            if resource_mapping is not None and (
                    resource_mapping.last_update.replace(tzinfo=None) < date):
                update_resources.append(resource)

        return [resource_map_function(resource, create_file=False) for resource in update_resources]

    @staticmethod
    def __filter_remove_resources(resources: list, category) -> list:
        """
        Filter Resources deleted in source

        :param resources: fetched data from source with resources raw data
        :type resources: list
        :param category: category of resource for mapping
        :return: list of resources to delete
        """
        resources_uid: List[str] = [resource['uuid'] for resource in resources]

        delete_resources = ResourceMapping.objects.filter(
            category=category
        ).exclude(
            uid__in=resources_uid
        )

        return list(delete_resources)

    def __get_next_page(self, path: str, limit: int, offset: int):
        """
        Sends get_request for next page

        :param path: relative url path
        :type path: str
        :param limit:  request list limit
        :type limit: int
        :param offset: request list offset
        :type offset: int
        :return: __get_request function with params for next page
        """
        params: dict = {
            'limit': limit,
            'offset': offset + limit
        }

        return self.__get_request(path, params)

    def __get_request(self, path: str, params: dict, headers: dict = None) -> dict:
        """
        Constructs GET request form given arguments, and loads json response as dict

        :param path: relative url path
        :type path: str
        :param params: GET request parameters
        :type params: dict
        :param headers: request headers
        :type headers: dict
        :return: response json as dict
        """
        response = requests.get(self.service_url + path, params=params, headers=headers, timeout=10)

        if response.status_code != requests.codes.ok:
            msg = f'GET {self.service_url + path} with params {params} returned: {response.status_code} {response.text}'
            raise HttpException(msg)

        return json.loads(response.text)

    def __map_layer_to_resource(self, layer: dict, create_file: bool = True) -> Resource:
        """
        Maps layer to Resource object

        :param layer: dict to map to Resource
        :type layer: dict
        :param create_file: define create file or not
        :type create_file: bool
        :return: Resource representing layer
        """
        uuid: str = layer['uuid']

        if create_file:
            res: Resource = Resource(os.environ.get('LAYERS_PARENT_DATAVERSE'), uid=uuid)
        else:
            pid: str = layer['pid']

            res: Resource = Resource(os.environ.get('LAYERS_PARENT_DATAVERSE'), uid=uuid, pid=pid)

        mapping: dict = self.__base_mapping(layer)
        mapping.update(self.__bounding_box_mapping(layer))

        for key, val in mapping.items():
            setattr(res.dataset, key, val)

        return res

    def __map_map_to_resource(self, geomap: dict, create_file: bool = True) -> Resource:
        """
        Maps geonode map to Resource object

        :param geomap: dict to map to Resource
        :type geomap: dict
        :param create_file: define create file or not
        :type create_file: bool
        :return: Resource representing geonode map
        """
        uuid: str = geomap['uuid']

        # Todo: Move to separated function in core
        if create_file:
            datafile: Datafile = Datafile()

            # Create file data

            file_data: dict = {
                'uuid': uuid,
                'site_url': self.service_url,
                'detail_url': geomap['detail_url']
            }

            # Create file
            file_path = settings.EXTERNAL_FILES_ROOT
            if file_path[0] != '/':
                file_path = '/' + file_path
            file_name: str = f'{uuid}.abw'
            file_full_path: str = (file_path + file_name)
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

            res: Resource = Resource(os.environ.get('MAPS_PARENT_DATAVERSE'), datafile=datafile, uid=uuid)
        else:
            pid: str = geomap['pid']

            res: Resource = Resource(os.environ.get('MAPS_PARENT_DATAVERSE'), uid=uuid, pid=pid)

        mapping: dict = self.__base_mapping(geomap)
        mapping.update(self.__bounding_box_mapping(geomap))

        for key, val in mapping.items():
            setattr(res.dataset, key, val)

        return res

    def __map_document_to_resource(self, document: dict, create_file: bool = True) -> Resource:
        """
        Maps document to Resource object

        :param document: dict to map to Resource
        :type document: dict
        :param create_file: define create file or not
        :type create_file: bool
        :return: Resource representing document
        """
        uuid: str = document['uuid']

        if create_file:
            res: Resource = Resource(os.environ.get('DOCUMENTS_PARENT_DATAVERSE'), uid=uuid)
        else:
            pid: str = document['pid'] if document['pid'] else None

            res: Resource = Resource(os.environ.get('DOCUMENTS_PARENT_DATAVERSE'), uid=uuid, pid=pid)

        mapping: dict = self.__base_mapping(document)

        for key, val in mapping.items():
            setattr(res.dataset, key, val)

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

        return service_url + detail_url

    def __base_mapping(self, obj: dict) -> dict:
        """
        Map raw data to compatible format for dataverse Resource

        :param obj: resource raw data to map
        :type obj: dict
        :return: mapped resource
        """
        return {
            'title': obj['title'],
            'author': [{'authorName': obj['owner_name'],
                        'authorAffiliation': 'Geonode'}],
            'alternativeURL': self.__create_alternative_url(obj['detail_url']),
            'dsDescription': [{'dsDescriptionValue': obj['abstract']}],
            'datasetContact': [{'datasetContactEmail': obj['owner_name'] + '@test.com',
                                'datasetContactName': obj['owner_name']}],
            'subject': ['Earth and Environmental Sciences'],
        }

    @staticmethod
    def __bounding_box_mapping(obj: dict) -> dict:
        """
        Map geographic data to dataverse compatible format

        :param obj: box mapping raw data
        :type obj: dict
        :return: mapped geographicBoundingBox
        """
        return {
            'geographicBoundingBox': [{'westLongitude': obj['bbox_x0'], 'eastLongitude': obj['bbox_x1'],
                                       'northLongitude': obj['bbox_y0'], 'southLongitude': obj['bbox_y1']}]
        }
