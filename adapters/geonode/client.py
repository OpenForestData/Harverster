import json
import logging
import os
from typing import List

import requests
from django.conf import settings

from adapters.geonode.models import HarvestingDatestamp
from core.clients import HarvestingClient
from core.exceptions import HttpException
from core.models import Resource

logger = logging.getLogger(__name__)


def http_exception_handler(e: HttpException):
    logger.exception(e)
    HarvestingDatestamp(status='ERROR').save()


class GeonodeClient(HarvestingClient):
    offset = settings.GEONODE_OFFSET

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_url += 'api/'

    def harvest(self) -> List[Resource]:
        """
        Harvests every resource from Geonode and returns is as a list of Resources
        :return: list of harvested data from Geonode
        """

        return (
                self.get_resources('layers/', self.__map_layer_to_resource) +
                self.get_resources('maps/', self.__map_map_to_resource) +
                self.get_resources('documents/', self.__map_document_to_resource)
        )

    def get_resources(self, resource_path, resource_map_function, full_sync=False) -> List[Resource]:
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

        return [resource_map_function(resource) for resource in resources]

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
        response = requests.get(self.service_url + path, params=params, headers=headers)
        if response.status_code != requests.codes.ok:
            msg = f'GET {self.service_url + path} with params {params} returned: {response.status_code} {response.text}'
            raise HttpException(msg)

        return json.loads(response.text)

    def __map_layer_to_resource(self, layer) -> Resource:
        """
        Maps layer to Resource object
        :param layer: dict to map to Resource
        :return: Resource representing layer
        """
        res = Resource(os.environ.get('LAYERS_PARENT_DATAVERSE'))

        mapping = self.__base_mapping(layer)
        mapping.update(self.__bounding_box_mapping(layer))

        for key, val in mapping.items():
            setattr(res.dataset, key, val)

        # TODO: Add datafile

        return res

    def __map_map_to_resource(self, geomap) -> Resource:
        """
        Maps geonode map to Resource object
        :param geomap: dict to map to Resource
        :return: Resource representing geonode map
        """
        res = Resource(os.environ.get('MAPS_PARENT_DATAVERSE'))

        mapping = self.__base_mapping(geomap)
        mapping.update(self.__bounding_box_mapping(geomap))

        for key, val in mapping.items():
            setattr(res.dataset, key, val)

        # TODO: Add datafile

        return res

    def __map_document_to_resource(self, document) -> Resource:
        """
        Maps document to Resource object
        :param document: dict to map to Resource
        :return: Resource representing document
        """
        res = Resource(os.environ.get('DOCUMENTS_PARENT_DATAVERSE'))

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
