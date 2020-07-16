import pytest
from django.test import TestCase

from adapters.geonode.client import GeonodeClient
from core.utils import get_client


class CoreUtilsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(CoreUtilsTests, cls).setUpTestData()

    def test_core_get_client(self):
        assert isinstance(get_client('geonode'), GeonodeClient)

        with pytest.raises(KeyError, match=r"There is no client under name: .* in settings.CLIENTS_DICT\."):
            get_client('test')
