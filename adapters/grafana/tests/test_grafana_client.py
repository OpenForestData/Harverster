from django.test import TestCase

from adapters.grafana.client import GrafanaClient


class GrafanaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(GrafanaTests, cls).setUpTestData()

        cls.grafana_client = GrafanaClient('https://test.url')

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
