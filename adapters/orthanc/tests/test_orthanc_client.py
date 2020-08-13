import json
from typing import List

import pytest
from django.test import TestCase
from django.utils import timezone
from mock import patch, Mock

from adapters.orthanc.client import OrthancClient
from core.exceptions import HttpException
from core.models import ResourceMapping


class ResponseMock:
    def __init__(self, text=None, status_code=200):
        self.status_code = status_code
        self.text = text


class OrthancTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(OrthancTests, cls).setUpTestData()

        cls.orthanc_client: OrthancClient = OrthancClient('https://test.url')

        cls.get_request_data: List[str] = [
            'd279e981-c99c42ff-1b4f98f6-9b8f3864-3ff04cc5',
            'cb634f41-ec7085aa-fc8f88c7-76b90616-4907a9f9',
            'e5b873b0-16c3d1e2-132ad5b1-139c67e5-ee7f0c97',
        ]

        cls.get_detailed_data: List[dict] = [
            {'ID': 'd279e981-c99c42ff-1b4f98f6-9b8f3864-3ff04cc5', 'IsStable': True, 'LastUpdate': '20200515T084424',
             'MainDicomTags': {'AccessionNumber': '', 'InstitutionName': 'PB', 'ReferringPhysicianName': '',
                               'StudyDate': '', 'StudyID': '',
                               'StudyInstanceUID': '1.2.276.0.7230010.3.1.2.567598148.27567.1585172748.124',
                               'StudyTime': ''}, 'ParentPatient': 'da39a3ee-5e6b4b0d-3255bfef-95601890-afd80709',
             'PatientMainDicomTags': {'PatientBirthDate': '', 'PatientID': '', 'PatientName': '', 'PatientSex': ''},
             'Series': ['bc7a8387-180413b5-1e63642d-307a9e0c-21781589'], 'Type': 'Study'
             },
            {'ID': 'cb634f41-ec7085aa-fc8f88c7-76b90616-4907a9f9', 'IsStable': True, 'LastUpdate': '20200715T091757',
             'MainDicomTags': {'AccessionNumber': '0', 'InstitutionName': 'Unknown',
                               'ReferringPhysicianName': 'Unknown', 'StudyDate': '20200122',
                               'StudyDescription': 'Unknown', 'StudyID': '1.2.276.0.1.3.1.',
                               'StudyInstanceUID': '1.2.276.0.1.3.1.127.0.0.1.7812.1594035217.3',
                               'StudyTime': '08:59:22'},
             'ParentPatient': 'bc7819b3-4ff87570-745fbe46-1e36a16f-80e562ce',
             'PatientMainDicomTags': {'PatientBirthDate': 'Unknown', 'PatientID': 'Unknown', 'PatientName': 'Unknown',
                                      'PatientSex': 'Unknown'},
             'Series': ['f979acae-b7bb1d5e-502810a6-2669d8fd-44d00292'], 'Type': 'Study'
             },
            {'ID': 'e5b873b0-16c3d1e2-132ad5b1-139c67e5-ee7f0c97', 'IsStable': True, 'LastUpdate': '20200717T065528',
             'MainDicomTags': {'AccessionNumber': '0', 'InstitutionName': 'Unknown',
                               'ReferringPhysicianName': 'Unknown', 'StudyDate': '20200113',
                               'StudyDescription': 'Unknown', 'StudyID': '1.2.276.0.1.3.1.',
                               'StudyInstanceUID': '1.2.276.0.1.3.1.127.0.0.1.10444.1594890249.9',
                               'StudyTime': '11:22:28'},
             'ParentPatient': 'bc7819b3-4ff87570-745fbe46-1e36a16f-80e562ce',
             'PatientMainDicomTags': {'PatientBirthDate': 'Unknown', 'PatientID': 'Unknown', 'PatientName': 'Unknown',
                                      'PatientSex': 'Unknown'},
             'Series': ['12380109-f4248846-e72d3cef-30ece866-37bb3f77'], 'Type': 'Study'
             },
        ]

        cls.resource_mapping_remove_uid = '8a272bb7-7e534946-5b7f8836-906abb07-ac644bcb'
        cls.resource_mapping_add = ResourceMapping(uid=cls.get_request_data[2],
                                                   last_update=timezone.now() - timezone.timedelta(weeks=30),
                                                   category=ResourceMapping.STUDY).save()
        cls.resource_mapping_update = ResourceMapping(uid=cls.get_request_data[1], pid='PID_UPDATE',
                                                      last_update=timezone.now() - timezone.timedelta(weeks=30),
                                                      category=ResourceMapping.STUDY).save()
        cls.resource_mapping_remove = ResourceMapping(uid=cls.resource_mapping_remove_uid,
                                                      pid='PID_DELETE', last_update=timezone.now(),
                                                      category=ResourceMapping.STUDY).save()

        cls.resource = cls.orthanc_client._OrthancClient__map_study_to_resource(cls.get_detailed_data[0])

    def test_orthanc_client_attrs(self):
        assert hasattr(self.orthanc_client, "harvest")
        assert hasattr(self.orthanc_client, "get_resources")
        assert hasattr(self.orthanc_client, "_OrthancClient__get_detailed_data")
        assert hasattr(self.orthanc_client, "_OrthancClient__filter_new_resources")
        assert hasattr(self.orthanc_client, "_OrthancClient__filter_update_resources")
        assert hasattr(self.orthanc_client, "_OrthancClient__filter_remove_resources")
        assert hasattr(self.orthanc_client, "_OrthancClient__get_request")
        assert hasattr(self.orthanc_client, "_OrthancClient__map_study_to_resource")
        assert hasattr(self.orthanc_client, "_OrthancClient__date_mapping")
        assert hasattr(self.orthanc_client, "_OrthancClient__unknown_value_mapping")
        assert hasattr(self.orthanc_client, "_OrthancClient__create_alternative_url")
        assert hasattr(self.orthanc_client, "_OrthancClient__base_mapping")

    @patch('adapters.orthanc.client.OrthancClient._OrthancClient__get_detailed_data')
    @patch('adapters.orthanc.client.OrthancClient._OrthancClient__get_request')
    def test_orthanc_client_harvest(self, mock_get_request, mock_get_detailed_data):
        mock_get_request.return_value = self.get_request_data
        mock_get_detailed_data.return_value = self.get_detailed_data
        add_data, update_data, remove_data = self.orthanc_client.harvest()

        assert add_data[0].uid == self.get_request_data[0]
        assert update_data[0].uid == self.get_request_data[1]
        assert remove_data[0].uid == self.resource_mapping_remove_uid

    @patch('adapters.orthanc.client.OrthancClient._OrthancClient__get_request')
    def test_orthanc_client_get_resources_exception(self, mock_get_request):
        mock_get_request.side_effect = Mock(side_effect=HttpException())

        self.orthanc_client.get_resources('studies/', self.orthanc_client._OrthancClient__map_study_to_resource,
                                          ResourceMapping.STUDY)

    @patch('requests.get')
    def test_orthanc_client_get_detailed_data(self, mock_requests_get):
        resp = ResponseMock(
            json.dumps(self.get_detailed_data[0])
        )

        mock_requests_get.return_value = resp

        assert self.orthanc_client._OrthancClient__get_detailed_data(
            self.get_request_data[:1]) == self.get_detailed_data[:1]

    @patch('requests.get')
    def test_orthanc_client_get_request(self, mock_requests_get):
        resp = ResponseMock(
            text=json.dumps(self.get_request_data)
        )
        mock_requests_get.return_value = resp

        assert self.orthanc_client._OrthancClient__get_request('/studies', {}) == self.get_request_data

        resp = ResponseMock(text=json.dumps(self.get_request_data), status_code=400)
        mock_requests_get.return_value = resp

        with pytest.raises(HttpException):
            self.orthanc_client._OrthancClient__get_request('/studies', {})
