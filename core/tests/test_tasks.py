from django.test import TestCase
from mock import patch

from core.tasks import run_harvester


class TasksTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(TasksTests, cls).setUpTestData()

    @patch('core.controllers.HarvestingController.run_harvest',
           return_value=(['add_data', 'add_data2'], ['update_Data'], ['remove_data']))
    @patch('core.controllers.HarvestingController.add_resources')
    @patch('core.controllers.HarvestingController.update_resources')
    @patch('core.controllers.HarvestingController.delete_resources')
    def test_run_harvester(self,
                           mock_run_harvest,
                           mock_add_resources,
                           mock_update_resources,
                           mock_delete_resources):
        run_harvester("geonode")
