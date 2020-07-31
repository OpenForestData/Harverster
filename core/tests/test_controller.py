import os

import pytest
from django.test import TestCase
from django.utils import timezone
from mock import Mock, patch
from pyDataverse.models import Datafile

from core.controllers import HarvestingController
from core.exceptions import HttpException
from core.models import Resource, ResourceMapping


class ResponseMock:
    def __init__(self, text=None, status_code=200):
        self.status_code = status_code
        self.text = text


class HarvestingControllerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(HarvestingControllerTests, cls).setUpTestData()

        cls.harvesting_client = Mock()
        cls.harvesting_client.harvest = Mock(return_value='Mocked')
        cls.dataverse_client = Mock()
        cls.dataverse_client.create_dataset = Mock(return_value=ResponseMock(
            '{"data": {"persistentId": "PID"}}',
            status_code=201
        ))
        cls.dataverse_client.upload_file = Mock()

        cls.resource1_uid = 'uuid'
        cls.resource1 = Resource(
            os.environ.get('DASHBOARDS_PARENT_DATAVERSE'),
            uid=cls.resource1_uid,
            datafile=Datafile()
        )
        cls.resource1.dataset.set({
            'title': 'title',
            'author': [{'authorName': 'Name'}],
            'datasetContact': [{'datasetContactEmail': 'test@test.com',
                                'datasetContactName': 'test'}],
            'subject': ['Earth and Environmental Sciences'],
            'dsDescription': [{'dsDescriptionValue': ''}],
        })
        cls.resource1.datafile.set({
            'filename': 'pwd/to/file',
        })
        cls.resource2 = Resource(
            os.environ.get('DASHBOARDS_PARENT_DATAVERSE'),
            uid='uuid2',
            pid='Nonono'
        )

        cls.resource_mapping_1 = ResourceMapping(uid=cls.resource1_uid,
                                                 last_update=timezone.now() - timezone.timedelta(weeks=30),
                                                 category=ResourceMapping.DASHBOARD).save()
        cls.resource_mapping_2 = ResourceMapping(uid='uuid_resource_mapping_2',
                                                 pid='PID2',
                                                 last_update=timezone.now() - timezone.timedelta(weeks=30),
                                                 category=ResourceMapping.DASHBOARD).save()

        cls.harvesting_controller = HarvestingController(cls.harvesting_client, cls.dataverse_client)

    def test_harvesting_controller_attrs(self):
        assert hasattr(self.harvesting_controller, "run_harvest")
        assert hasattr(self.harvesting_controller, "add_resources")
        assert hasattr(self.harvesting_controller, "delete_resources")
        assert hasattr(self.harvesting_controller, "update_resources")
        assert hasattr(self.harvesting_controller, "publish_resource")

    def test_harvesting_controller_run_harvest(self):
        assert self.harvesting_controller.run_harvest() == 'Mocked'

    @patch('core.controllers.HarvestingController.publish_resource')
    def test_harvesting_controller_add_resources(self, mock_publish_resource):
        self.harvesting_controller.add_resources([self.resource1], True)

        self.resource1.datafile = None
        self.harvesting_controller.add_resources([self.resource1], False)

        self.dataverse_client.create_dataset = Mock(return_value=ResponseMock(
            '{"data": {"persistentId": "PID"}}',
            status_code=200
        ))

        with pytest.raises(HttpException):
            self.harvesting_controller.add_resources([self.resource1], False)

    @patch('core.controllers.HarvestingController.publish_resource')
    def test_harvesting_controller_update_resources(self, mock_publish_resource):
        self.resource1.pid = 'PID'
        self.dataverse_client.edit_dataset_metadata = Mock(return_value=ResponseMock(
            'Text',
            status_code=200
        ))
        self.harvesting_controller.update_resources([self.resource1], None)
        self.harvesting_controller.update_resources([self.resource1], 'minor')
        self.harvesting_controller.update_resources([self.resource1], 'major')

        with pytest.raises(ValueError):
            self.harvesting_controller.update_resources([self.resource1], True)

        self.dataverse_client.edit_dataset_metadata = Mock(return_value=ResponseMock(
            'Text',
            status_code=201
        ))
        with pytest.raises(HttpException):
            self.harvesting_controller.update_resources([self.resource1], None)

    def test_harvesting_controller_delete_resources(self):
        self.dataverse_client.delete_dataset = Mock(return_value=ResponseMock(
            'Text',
            status_code=200
        ))
        resource_mapping_uid = 'uuid_delete_resource'
        ResourceMapping(uid=resource_mapping_uid,
                        pid='PID',
                        last_update=timezone.now() - timezone.timedelta(weeks=30),
                        category=ResourceMapping.DASHBOARD).save()
        resource = ResourceMapping.objects.get(uid=resource_mapping_uid)
        self.harvesting_controller.delete_resources([resource])

        self.dataverse_client.delete_dataset = Mock(return_value=ResponseMock(
            'Text',
            status_code=201
        ))

        with pytest.raises(HttpException):
            self.harvesting_controller.delete_resources([resource])

    def test_harvesting_controller_publish_resource(self):
        self.dataverse_client.publish_dataset = Mock(return_value=ResponseMock(
            'Text',
            status_code=200
        ))
        resource_mapping_uid = 'uuid_publish_resource'

        self.harvesting_controller.publish_resource(resource_mapping_uid)
        self.harvesting_controller.publish_resource(resource_mapping_uid, 'major')

        self.dataverse_client.publish_dataset = Mock(return_value=ResponseMock(
            'Text',
            status_code=201
        ))

        with pytest.raises(HttpException):
            self.harvesting_controller.publish_resource(resource_mapping_uid)
