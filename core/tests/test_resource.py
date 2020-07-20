import os

import factory
from django.test import TestCase
from pyDataverse.models import Datafile

from core.models import ResourceMapping, Resource


class CoreTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(CoreTests, cls).setUpTestData()

        cls.resource_mapping1 = ResourceMapping()
        cls.resource_mapping2 = ResourceMapping()

        cls.resource1 = Resource(
            os.environ.get('DASHBOARDS_PARENT_DATAVERSE'),
            uid='uuid'
        )
        cls.resource2 = Resource(
            os.environ.get('DASHBOARDS_PARENT_DATAVERSE'),
            uid='uuid2',
            pid='Nonono'
        )

    def test_resource_attrs(self):
        assert hasattr(self.resource2, "parent_dataverse")
        assert hasattr(self.resource2, "pid")
        assert hasattr(self.resource2, "uid")
        assert hasattr(self.resource2, "dataset")
        assert hasattr(self.resource2, "datafile")

    def test_resource_pid(self):
        assert self.resource1.is_pid() is False
        assert self.resource2.is_pid() is True

    def test_resource_is_valid(self):
        assert self.resource1.is_valid() is False

        self.resource1.datafile = Datafile()
        assert self.resource1.is_valid() is False

        self.resource1.dataset.set({
            'title': 'title',
            'author': [{'authorName': 'Name'}],
            'datasetContact': [{'datasetContactEmail': 'test@test.com',
                                'datasetContactName': 'test'}],
            'subject': ['Earth and Environmental Sciences'],
            'dsDescription': [{'dsDescriptionValue': ''}],
        })
        self.resource1.datafile.set({
            'filename': 'pwd/to/file',
            'pid': 'pid_id'
        })
        assert self.resource1.is_valid() is True
