from django.test import TestCase

from adapters.orthanc.client import OrthancClient


class OrthancTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(OrthancTests, cls).setUpTestData()

        cls.orthanc_client = OrthancClient('https://test.url')

    def test_orthanc_client_attrs(self):
        assert hasattr(self.orthanc_client, "harvest")
        assert hasattr(self.orthanc_client, "get_resources")
        assert hasattr(self.orthanc_client, "_OrthancClient__get_detailed_data")
        assert hasattr(self.orthanc_client, "_OrthancClient__filter_new_resources")
        assert hasattr(self.orthanc_client, "_OrthancClient__filter_update_resources")
        assert hasattr(self.orthanc_client, "_OrthancClient__filter_remove_resources")
        assert hasattr(self.orthanc_client, "_OrthancClient__get_request")
        assert hasattr(self.orthanc_client, "_OrthancClient__map_study_to_resource")
        assert hasattr(self.orthanc_client, "_OrthancClient__email_mapping")
        assert hasattr(self.orthanc_client, "_OrthancClient__date_mapping")
        assert hasattr(self.orthanc_client, "_OrthancClient__unknown_value_mapping")
        assert hasattr(self.orthanc_client, "_OrthancClient__create_alternative_url")
        assert hasattr(self.orthanc_client, "_OrthancClient__base_mapping")
