from django.test import TestCase
from pyDataverse.api import Api

from adapters.grafana.client import GrafanaClient
from core.controllers import HarvestingController


class HarvestingControllerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(HarvestingControllerTests, cls).setUpTestData()

        cls.harvesting_client = GrafanaClient(service_url='https://test.url')
        cls.dataverse_client = Api('https://dataverse.url.com', api_token='9c9d2213-482d-405d-9490-96b984b96898')

        cls.harvesting_controller = HarvestingController(cls.harvesting_client, cls.dataverse_client)

    def test_harvesting_controller_attrs(self):
        assert hasattr(self.harvesting_controller, "run_harvest")
        assert hasattr(self.harvesting_controller, "add_resources")
        assert hasattr(self.harvesting_controller, "delete_resources")
        assert hasattr(self.harvesting_controller, "update_resources")
        assert hasattr(self.harvesting_controller, "publish_resource")
