import json
import logging
import os
from typing import List

import requests
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from pyDataverse.models import Datafile

from adapters.geonode.models import HarvestingDatestamp
from core.clients import HarvestingClient
from core.exceptions import HttpException
from core.models import Resource, ResourceMapping

logger = logging.getLogger(__name__)


def http_exception_handler(e: HttpException):
    logger.exception(e)
    HarvestingDatestamp(status='ERROR').save()


class GeonodeClient(HarvestingClient):
    offset = settings.GEONODE_OFFSET

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_url += 'api/'

    def harvest(self):
        """
        Harvests every resource from Geonode and returns is as a list of Resources
        :return: list of harvested data from Geonode
        """
        layers = self.get_resources('layers/', self.__map_layer_to_resource, ResourceMapping.LAYER)
        maps = self.get_resources('maps/', self.__map_map_to_resource, ResourceMapping.MAP)
        documents = self.get_resources('documents/', self.__map_document_to_resource, ResourceMapping.DOCUMENT)

        add_data = layers[0] + maps[0] + documents[0]
        update_data = layers[1] + maps[1] + documents[1]
        remove_data = layers[2] + maps[2] + documents[2]

        return add_data, update_data, remove_data

    def get_resources(self,
                      resource_path,
                      resource_map_function,
                      resource_mapping_category,
                      full_sync=False) -> (List[Resource],
                                           List[Resource],
                                           List[Resource]):
        """
        Fetch data from Geonode API endpoint, maps it to Resource and returns it as a list of Resources
        :param resource_path: url relative path to API endpoint
        :param resource_map_function: function mapping data type retrieved from endpoint to Resource object
        :param full_sync: True if resources all resources should be harvested
        :return: list of fetched data as Resources list
        """
        params = {
            'offset': 0,
            'order_by': 'date'
        }

        if not full_sync:
            params['date__gte'] = self.__get_last_sync_date()

        try:
            results = self.__get_request(resource_path, params)
        except HttpException as e:
            http_exception_handler(e)
            return []

        resources = results['objects']

        while results['meta']['next'] is not None:
            results = self.__get_next_page(resource_path, results['meta']['limit'], results['meta']['offset'])
            resources += results['objects']

        # TODO: Check if timezone is needed
        # HarvestingDatestamp(status='OK').save()

        add_resources = self.__get_only_new(resources, resource_mapping_category, resource_map_function)
        update_resources = self.__get_only_for_update(resources, resource_map_function)
        delete_resources = self.__get_only_to_remove(resources, resource_mapping_category)

        return add_resources, update_resources, delete_resources

    def __get_only_new(self, resources, category, resource_map_function) -> list:
        add_resources = []
        for resource in resources:
            uid = resource['uuid']
            resource_mapping = ResourceMapping.objects.filter(uid=uid).first()

            if resource_mapping is None or resource_mapping.pid is None:
                if resource_mapping is None:
                    ResourceMapping(uid=uid, pid=None, last_update=timezone.now(), category=category).save()

                add_resources.append(resource)

        return [resource_map_function(resource) for resource in add_resources]

    def __get_only_for_update(self, resources, resource_map_function) -> list:
        update_resources = []
        for resource in resources:
            uid = resource['uuid']
            resource_mapping = ResourceMapping.objects.filter(uid=uid).first()

            resource['pid'] = resource_mapping.pid if resource_mapping.pid else None
            date = parse_datetime(resource['date'])

            if resource_mapping is not None and (
                    resource_mapping.last_update.replace(tzinfo=None) < date):
                update_resources.append(resource)

        return [resource_map_function(resource, create_file=False) for resource in update_resources]

    def __get_only_to_remove(self, resources, resource_mapping_category):
        resources_uid = [resource['uuid'] for resource in resources]
        delete_resources = ResourceMapping.objects.filter(
            category=resource_mapping_category
        ).exclude(
            uid__in=resources_uid
        )

        return list(delete_resources)

    def __get_next_page(self, path, limit, offset):
        params = {
            'limit': limit,
            'offset': offset + limit
        }
        return self.__get_request(path, params)

    def __get_last_sync_date(self):
        # TODO: get this from database
        return '1990-01-01T12:34:00'

    def __get_request(self, path: str, params: dict, headers: dict = None) -> dict:
        """
        Constructs GET request form given arguments, and loads json response as dict
        :param path: relative url path
        :param params: GET request parameters
        :param headers: request headers
        :return: response json as dict
        """
        # TODO: Remove verify argument
        response = requests.get(self.service_url + path, params=params, headers=headers, verify=False)
        if response.status_code != requests.codes.ok:
            msg = f'GET {self.service_url + path} with params {params} returned: {response.status_code} {response.text}'
            raise HttpException(msg)

        return json.loads(response.text)

    def __map_layer_to_resource(self, layer, create_file: bool = True) -> Resource:
        """
        Maps layer to Resource object
        :param layer: dict to map to Resource
        :return: Resource representing layer
        """
        uuid = layer['uuid']

        if create_file:
            res = Resource(os.environ.get('LAYERS_PARENT_DATAVERSE'), uid=uuid)
        else:
            pid = layer['pid']

            res = Resource(os.environ.get('LAYERS_PARENT_DATAVERSE'), uid=uuid, pid=pid)

        mapping = self.__base_mapping(layer)
        mapping.update(self.__bounding_box_mapping(layer))

        for key, val in mapping.items():
            setattr(res.dataset, key, val)

        # TODO: Add datafile

        return res

    def __map_map_to_resource(self, geomap, create_file: bool = True) -> Resource:
        """
        Maps geonode map to Resource object
        :param geomap: dict to map to Resource
        :return: Resource representing geonode map
        """
        uuid = geomap['uuid']

        # Todo: Move to separated function in core
        if create_file:
            datafile = Datafile()

            # Create file data

            file_data = {
                'uuid': uuid,
                'site_url': geomap['site_url'],
                'detail_url': geomap['detail_url']
            }

            # Create file
            file_name = f'{uuid}.map_geonode'
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

            res = Resource(os.environ.get('MAPS_PARENT_DATAVERSE'), datafile=datafile, uid=uuid)
        else:
            pid = geomap['pid']

            res = Resource(os.environ.get('MAPS_PARENT_DATAVERSE'), uid=uuid, pid=pid)

        mapping = self.__base_mapping(geomap)
        mapping.update(self.__bounding_box_mapping(geomap))

        for key, val in mapping.items():
            setattr(res.dataset, key, val)

        return res

    def __map_document_to_resource(self, document, create_file: bool = True) -> Resource:
        """
        Maps document to Resource object
        :param document: dict to map to Resource
        :return: Resource representing document
        """
        uuid = document['uuid']

        if create_file:
            res = Resource(os.environ.get('DOCUMENTS_PARENT_DATAVERSE'), uid=uuid)
        else:
            pid = document['pid'] if document['pid'] else None

            res = Resource(os.environ.get('DOCUMENTS_PARENT_DATAVERSE'), uid=uuid, pid=pid)

        mapping = self.__base_mapping(document)

        for key, val in mapping.items():
            setattr(res.dataset, key, val)

        # TODO: Add datafile ?

        return res

    @staticmethod
    def __base_mapping(obj):
        return {
            'title': obj['title'],
            'author': [{'authorName': obj['owner_name'],
                        'authorAffiliation': 'Geonode'}],
            'dsDescription': [{'dsDescriptionValue': obj['abstract']}],
            'datasetContact': [{'datasetContactEmail': obj['owner_name'] + '@test.com',
                                'datasetContactName': obj['owner_name']}],
            'subject': ['Earth and Environmental Sciences'],
        }

    @staticmethod
    def __bounding_box_mapping(obj):
        return {
            'geographicBoundingBox': [{'westLongitude': obj['bbox_x0'], 'eastLongitude': obj['bbox_x1'],
                                       'northLongitude': obj['bbox_y0'], 'southLongitude': obj['bbox_y1']}]
        }
