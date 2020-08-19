import json

import pytest
from django.test import TestCase
from django.utils import timezone
from mock import patch, Mock

from adapters.grafana.client import GrafanaClient
from core.exceptions import HttpException
from core.models import ResourceMapping


class ResponseMock:
    def __init__(self, text=None, status_code=200):
        self.status_code = status_code
        self.text = text


class GrafanaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(GrafanaTests, cls).setUpTestData()

        cls.grafana_client = GrafanaClient('https://test.url')

        uri = 'db/new-dashboard-cp'
        url = '/d/rKJbnIgGk/new-dashboard-cp'
        title = 'New dashboard Cp'

        cls.get_request_data = [
            {
                'id': 1, 'uid': 'rKJbnIgGk', 'title': title, 'uri': uri,
                'url': url, 'slug': '', 'type': 'dash-db', 'tags': [], 'isStarred': False
            },
        ]

        cls.get_detailed_data_item = {
            'meta': {
                'type': 'db', 'canSave': False, 'canEdit': False, 'canAdmin': False, 'canStar': True,
                'slug': 'new-dashboard-cp', 'url': url,
                'expires': '0001-01-01T00:00:00Z', 'created': '2020-05-12T12:21:24Z',
                'updated': '2020-05-12T12:21:24Z', 'updatedBy': 'test', 'createdBy': 'test', 'version': 1,
                'hasAcl': False, 'isFolder': False, 'folderId': 0, 'folderTitle': 'General', 'folderUrl': '',
                'provisioned': False, 'provisionedExternalId': ''
            }, 'dashboard': {
                'annotations': {
                    'list': [
                        {
                            '$$hashKey': 'object:86', 'builtIn': 1, 'datasource': '-- Grafana --', 'enable': True,
                            'hide': True,
                            'iconColor': 'rgba(0, 211, 255, 1)', 'name': 'Annotations & Alerts', 'type': 'dashboard'}]},
                'editable': True, 'gnetId': None,
                'graphTooltip': 0,
                'hideControls': False, 'id': 1,
                'links': [], 'panels': [
                    {'aliasColors': {}, 'bars': False, 'dashLength': 10, 'dashes': False, 'datasource': 'InfluxDB',
                     'fill': 1, 'fillGradient': 0, 'gridPos': {'h': 9, 'w': 12, 'x': 0, 'y': 0}, 'hiddenSeries': False,
                     'id': 2, 'legend': {'avg': False, 'current': False, 'max': False, 'min': False, 'show': True,
                                         'total': False, 'values': False}, 'lines': True, 'linewidth': 1,
                     'nullPointMode': 'null', 'options': {'dataLinks': []}, 'percentage': False, 'pointradius': 2,
                     'points': False, 'renderer': 'flot', 'seriesOverrides': [], 'spaceLength': 10, 'stack': False,
                     'steppedLine': False, 'targets': [
                        {'groupBy': [{'params': ['$__interval'], 'type': 'time'}, {'params': ['null'], 'type': 'fill'}],
                         'orderByTime': 'ASC', 'policy': 'default', 'refId': 'A', 'resultFormat': 'time_series',
                         'select': [[{'params': ['value'], 'type': 'field'}, {'params': [], 'type': 'mean'}]],
                         'tags': []}], 'thresholds': [], 'timeFrom': None, 'timeRegions': [], 'timeShift': None,
                     'title': 'Panel Title', 'tooltip': {'shared': True, 'sort': 0, 'value_type': 'individual'},
                     'type': 'graph',
                     'xaxis': {'buckets': None, 'mode': 'time', 'name': None, 'show': True, 'values': []},
                     'yaxes': [{'format': 'short', 'label': None, 'logBase': 1, 'max': None, 'min': None, 'show': True},
                               {'format': 'short', 'label': None, 'logBase': 1, 'max': None, 'min': None,
                                'show': True}], 'yaxis': {'align': False, 'alignLevel': None}}], 'refresh': '',
                'schemaVersion': 22,
                'style': 'dark', 'tags': [],
                'templating': {'list': []},
                'time': {'from': 'now-6h',
                         'to': 'now'},
                'timepicker': {}, 'timezone': '',
                'title': title,
                'uid': 'rKJbnIgGk',
                'variables': {'list': []},
                'version': 1},
            'search': {'id': 1, 'uid': 'rKJbnIgGk', 'title': title, 'uri': uri,
                       'url': url, 'slug': '', 'type': 'dash-db', 'tags': [],
                       'isStarred': False}
        }
        cls.get_detailed_data_add_uid = 'adfdsffds'
        cls.resource_mapping_added_uid = 'adfdsfcz'
        cls.resource_mapping_updated_uid = 'askjfhcnA'
        cls.resource_mapping_remove_uid = 'abcbnIgGA'

        cls.get_request_data.append({**cls.get_request_data[0], 'uid': cls.get_detailed_data_add_uid})
        cls.get_request_data.append({**cls.get_request_data[0], 'uid': cls.resource_mapping_added_uid})
        cls.get_request_data.append({**cls.get_request_data[0], 'uid': cls.resource_mapping_updated_uid})
        cls.get_detailed_data = [
            cls.get_detailed_data_item,
            {
                **cls.get_detailed_data_item, 'search': {
                    **cls.get_detailed_data_item['search'],
                    'uid': cls.get_detailed_data_add_uid}
            },
            {
                **cls.get_detailed_data_item, 'search': {
                    **cls.get_detailed_data_item['search'],
                    'uid': cls.resource_mapping_added_uid}
            },
            {
                **cls.get_detailed_data_item, 'search': {
                    **cls.get_detailed_data_item['search'],
                    'uid': cls.resource_mapping_updated_uid},
                'pid': 'PID'
            },
        ]

        cls.resource_mapping_add = ResourceMapping(uid=cls.get_detailed_data_add_uid,
                                                   last_update=timezone.now() - timezone.timedelta(weeks=30),
                                                   category=ResourceMapping.DASHBOARD).save()
        cls.resource_mapping_added = ResourceMapping(uid=cls.resource_mapping_added_uid, pid='PID_ADDED',
                                                     last_update=timezone.now() - timezone.timedelta(weeks=30),
                                                     category=ResourceMapping.DASHBOARD).save()
        cls.resource_mapping_updated = ResourceMapping(uid=cls.resource_mapping_updated_uid, pid='PID_UPDATED',
                                                       last_update=timezone.now() - timezone.timedelta(weeks=35),
                                                       category=ResourceMapping.DASHBOARD).save()
        cls.resource_mapping_remove = ResourceMapping(uid=cls.resource_mapping_remove_uid,
                                                      pid='PID_DELETE', last_update=timezone.now(),
                                                      category=ResourceMapping.DASHBOARD).save()

    def test_grafana_client_attrs(self):
        assert hasattr(self.grafana_client, "harvest")
        assert hasattr(self.grafana_client, "get_resources")
        assert hasattr(self.grafana_client, "_GrafanaClient__filter_new_resources")
        assert hasattr(self.grafana_client, "_GrafanaClient__filter_remove_resources")
        assert hasattr(self.grafana_client, "_GrafanaClient__get_detailed_data")
        assert hasattr(self.grafana_client, "_GrafanaClient__get_next_page")
        assert hasattr(self.grafana_client, "_GrafanaClient__get_request")
        assert hasattr(self.grafana_client, "_GrafanaClient__map_dashboard_to_resource")
        assert hasattr(self.grafana_client, "_GrafanaClient__create_alternative_url")
        assert hasattr(self.grafana_client, "_GrafanaClient__base_mapping")

    @patch('adapters.grafana.client.GrafanaClient.get_resources')
    def test_grafana_client_harvest(self, mock_get_resources):
        mock_get_resources.return_value = (['add_data'], [], ['remove_data'])

        add_data, update_data, remove_data = self.grafana_client.harvest()

        assert len(add_data) == 1
        assert add_data[0] == 'add_data'
        assert len(update_data) == 0
        assert remove_data[0] == 'remove_data'

    @patch('adapters.grafana.client.GrafanaClient._GrafanaClient__get_detailed_data')
    @patch('adapters.grafana.client.GrafanaClient._GrafanaClient__get_next_page')
    @patch('adapters.grafana.client.GrafanaClient._GrafanaClient__get_request')
    def test_grafana_client_get_resources(self, mock_get_request, mock_get_next_page_data, mock_get_detailed_data):
        mock_get_request.return_value = self.get_request_data
        mock_get_next_page_data.return_value = []
        mock_get_detailed_data.return_value = self.get_detailed_data

        add_data, update_data, remove_data = self.grafana_client.harvest()

        assert add_data[0].uid == self.get_request_data[0]['uid']
        assert len(add_data) == 2
        assert len(update_data) == 0
        assert remove_data[0].uid == self.resource_mapping_remove_uid

    @patch('adapters.grafana.client.GrafanaClient._GrafanaClient__get_request')
    def test_grafana_client_get_resources_exception(self, mock_get_request):
        mock_get_request.side_effect = Mock(side_effect=HttpException())

        self.grafana_client.get_resources('dashboards/', self.grafana_client._GrafanaClient__map_dashboard_to_resource,
                                          ResourceMapping.DASHBOARD)

    @patch('requests.get')
    def test_grafana_client_get_detailed_data(self, mock_requests_get):
        resp = ResponseMock(json.dumps(
            self.get_detailed_data[0]
        ))

        mock_requests_get.return_value = resp

        assert self.grafana_client._GrafanaClient__get_detailed_data(
            self.get_request_data[:1]) == self.get_detailed_data[:1]

    @patch('adapters.grafana.client.GrafanaClient._GrafanaClient__get_request')
    def test_grafana_client_get_next_page(self, mock_get_request):
        mock_get_request.return_value = 'Mocked'

        assert self.grafana_client._GrafanaClient__get_next_page('/path', 2, 10) == 'Mocked'

    @patch('requests.get')
    def test_grafana_client_get_request(self, mock_requests_get):
        resp = ResponseMock(
            text=json.dumps(self.get_request_data[:1])
        )
        mock_requests_get.return_value = resp

        assert self.grafana_client._GrafanaClient__get_request('/dashboards', {}) == self.get_request_data[:1]

        resp = ResponseMock(text=json.dumps(self.get_request_data[:1]), status_code=400)
        mock_requests_get.return_value = resp

        with pytest.raises(HttpException):
            self.grafana_client._GrafanaClient__get_request('/dashboards', {})

    def test_grafana_client_map_dashboard_to_resource(self):
        assert (self.grafana_client._GrafanaClient__map_dashboard_to_resource(self.get_detailed_data[3], False).uid ==
                self.get_detailed_data[3]['search']['uid'])
