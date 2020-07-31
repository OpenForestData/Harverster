import json

import pytest
from django.test import TestCase
from django.utils import timezone
from mock import patch, Mock

from adapters.geonode.client import GeonodeClient
from core.exceptions import HttpException
from core.models import ResourceMapping


class ResponseMock:
    def __init__(self, text=None, status_code=200):
        self.status_code = status_code
        self.text = text


class GeonodeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(GeonodeTests, cls).setUpTestData()

        cls.geonode_client = GeonodeClient('https://test.url')

        cls.resource_mapping_add_uid = '760b8a3c-b20f-11ea-8429-0242ac12000c'
        cls.resource_mapping_added_uid = '850b8a3c-b20f-11ea-8429-0242ac12000c'
        cls.resource_mapping_update_uid = '430b8a3c-b20f-11ea-8429-0242ac12000c'
        cls.resource_mapping_remove_uid = '180b8a3c-b20f-11ea-8429-0242ac12000c'

        cls.get_request_data_item = (
            {
                'abstract': 'No abstract provided', 'bbox_x0': '-180.000000000000000',
                'bbox_x1': '180.000000000000000', 'bbox_y0': '-90.000000000000000',
                'bbox_y1': '90.000000000000000', 'constraints_other': None,
                'csw_type': 'document',
                'csw_wkt_geometry': ('POLYGON((-180.000000 -90.000000,-180.000000 90.000000,180.000000'
                                     ' 90.000000,180.000000 -90.000000,-180.000000 -90.000000))'),
                'data_quality_statement': None, 'date': '2020-06-19T09:30:06.188641',
                'date_type': 'publication', 'detail_url': '/documents/10',
                'dirty_state': False, 'edition': None, 'id': 10, 'is_approved': True,
                'is_published': True, 'keywords': [], 'language': 'eng', 'license': 1,
                'maintenance_frequency': None, 'online': True, 'owner__username': 'olga',
                'owner_name': 'olga', 'popular_count': 3, 'purpose': None, 'rating': 0,
                'regions': ['Global'], 'restriction_code_type': None, 'share_count': 0,
                'site_url': 'https://geonode_test.com/',
                'spatial_representation_type': None, 'srid': 'EPSG:4326',
                'store_type': 'dataset',
                'supplemental_information': 'Nie umieszczono informacji',
                'temporal_extent_end': None, 'temporal_extent_start': None,
                'thumbnail_url': 'http://localhost:8000/uploaded/thumbs/docu'
                                 'ment-760b8a3c-b20f-11ea-8429-0242ac12000c-thumb.png',
                'title': '1796_MapaGubernijMieleczyckiey.jpg',
                'uuid': cls.resource_mapping_add_uid
            }
        )
        cls.get_request_data = {
            'geonode_version': '3.0.0',
            'meta': {'limit': 200, 'next': None, 'offset': 0, 'previous': None, 'total_count': 2},
            'objects': [
                cls.get_request_data_item,
                {
                    **cls.get_request_data_item,
                    'uuid': cls.resource_mapping_added_uid
                },
                {
                    **cls.get_request_data_item,
                    'uuid': cls.resource_mapping_update_uid
                },
            ]
        }

        cls.resource_mapping_add = ResourceMapping(uid=cls.resource_mapping_added_uid,
                                                   last_update=timezone.now() - timezone.timedelta(weeks=30),
                                                   category=ResourceMapping.DASHBOARD).save()
        cls.resource_mapping_update = ResourceMapping(uid=cls.resource_mapping_update_uid, pid='PID_UPDATE',
                                                      last_update=timezone.now() - timezone.timedelta(weeks=30),
                                                      category=ResourceMapping.DASHBOARD).save()
        cls.resource_mapping_remove = ResourceMapping(uid=cls.resource_mapping_remove_uid,
                                                      pid='PID_DELETE', last_update=timezone.now(),
                                                      category=ResourceMapping.DASHBOARD).save()

    def test_geonode_client_attrs(self):
        assert hasattr(self.geonode_client, "harvest")
        assert hasattr(self.geonode_client, "get_resources")
        assert hasattr(self.geonode_client, "_GeonodeClient__filter_new_resources")
        assert hasattr(self.geonode_client, "_GeonodeClient__filter_update_resources")
        assert hasattr(self.geonode_client, "_GeonodeClient__filter_remove_resources")
        assert hasattr(self.geonode_client, "_GeonodeClient__get_next_page")
        assert hasattr(self.geonode_client, "_GeonodeClient__get_request")
        assert hasattr(self.geonode_client, "_GeonodeClient__map_layer_to_resource")
        assert hasattr(self.geonode_client, "_GeonodeClient__map_map_to_resource")
        assert hasattr(self.geonode_client, "_GeonodeClient__map_document_to_resource")
        assert hasattr(self.geonode_client, "_GeonodeClient__create_alternative_url")
        assert hasattr(self.geonode_client, "_GeonodeClient__base_mapping")
        assert hasattr(self.geonode_client, "_GeonodeClient__bounding_box_mapping")

    @patch('adapters.geonode.client.GeonodeClient.get_resources')
    def test_geonode_client_harvest(self, mock_get_resources):
        mock_get_resources.return_value = (['add_data'], ['update_data'], ['remove_data'])

        add_data, update_data, remove_data = self.geonode_client.harvest()

        assert add_data[0] == 'add_data'
        assert update_data[0] == 'update_data'
        assert remove_data[0] == 'remove_data'

    @patch('adapters.geonode.client.GeonodeClient._GeonodeClient__get_next_page')
    @patch('adapters.geonode.client.GeonodeClient._GeonodeClient__get_request')
    def test_geonode_client_get_resources_layer(self, mock_get_request, mock_get_next_page):
        mock_get_request.return_value = self.get_request_data
        mock_get_next_page.return_value = {}
        self.geonode_client.offset = 0
        self.geonode_client.get_resources('api/layers/', self.geonode_client._GeonodeClient__map_layer_to_resource,
                                          ResourceMapping.LAYER)

        self.geonode_client.get_resources('api/maps/', self.geonode_client._GeonodeClient__map_map_to_resource,
                                          ResourceMapping.MAP)

        self.geonode_client.get_resources('api/documents/',
                                          self.geonode_client._GeonodeClient__map_document_to_resource,
                                          ResourceMapping.DOCUMENT)

    @patch('adapters.geonode.client.GeonodeClient._GeonodeClient__get_request')
    def test_geonode_client_get_resources_exception(self, mock_get_request):
        mock_get_request.side_effect = Mock(side_effect=HttpException())

        self.geonode_client.get_resources('api/documents/',
                                          self.geonode_client._GeonodeClient__map_document_to_resource,
                                          ResourceMapping.DOCUMENT)

    @patch('adapters.geonode.client.GeonodeClient._GeonodeClient__get_request')
    def test_geonode_client_get_next_page(self, mock_get_request):
        mock_get_request.return_value = 'Mocked'

        assert self.geonode_client._GeonodeClient__get_next_page('/docs1', 10, 10) == 'Mocked'

    @patch('requests.get')
    def test_geonode_client_get_request(self, mock_requests_get):
        resp = ResponseMock(
            text=json.dumps(self.get_request_data)
        )
        mock_requests_get.return_value = resp

        assert self.geonode_client._GeonodeClient__get_request('/docs', {}) == self.get_request_data

        resp = ResponseMock(text=json.dumps(self.get_request_data), status_code=400)
        mock_requests_get.return_value = resp

        with pytest.raises(HttpException):
            self.geonode_client._GeonodeClient__get_request('/docs', {})
