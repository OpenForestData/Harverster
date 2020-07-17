from django.test import TestCase

from adapters.geonode.client import GeonodeClient


class GeonodeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(GeonodeTests, cls).setUpTestData()

        cls.geonode_client = GeonodeClient('https://test.url')

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
