from django.test import TestCase
from mock import Mock

from core.controllers import HarvestingController


class HarvestingControllerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(HarvestingControllerTests, cls).setUpTestData()

        cls.harvesting_client = Mock()
        cls.harvesting_client.harvest = Mock(return_value='Mocked')
        cls.dataverse_client = Mock()

        cls.harvesting_controller = HarvestingController(cls.harvesting_client, cls.dataverse_client)

    def test_harvesting_controller_attrs(self):
        assert hasattr(self.harvesting_controller, "run_harvest")
        assert hasattr(self.harvesting_controller, "add_resources")
        assert hasattr(self.harvesting_controller, "delete_resources")
        assert hasattr(self.harvesting_controller, "update_resources")
        assert hasattr(self.harvesting_controller, "publish_resource")

    def test_harvesting_controller_run_harvest(self):
        assert self.harvesting_controller.run_harvest() == 'Mocked'
