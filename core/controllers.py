import json
import logging
from typing import List

import requests
from django.utils import timezone
from pyDataverse.api import Api

from core.clients import HarvestingClient
from core.exceptions import HttpException
from core.models import Resource, ResourceMapping

logger = logging.getLogger(__name__)


class HarvestingController:

    def __init__(self, harvesting_client: HarvestingClient, dataverse_client: Api):
        self.harvesting_client = harvesting_client
        self.dataverse_client = dataverse_client

    def run_harvest(self) -> (List[Resource], List[Resource], List[Resource]):
        """
        Run harvesting client and return list of resources to add/update/remove

        :return: list of add/update/remove resources
        """
        logger.debug(f'Starting harvest from {self.harvesting_client.service_url}.')

        # Get all results
        result = self.harvesting_client.harvest()
        logger.debug(f'Harvest from {self.harvesting_client.service_url} completed.')
        return result

    def add_resources(self, resources: List[Resource], publish_added: bool = False) -> None:
        """
        Add every resource from list to dataverse and publish if specified

        :param resources: list of resources
        :param publish_added: specifies publishing dataset after adding to dataverse or not
        :return: None
        """
        logger.debug(f'Starting upload to {self.dataverse_client.base_url}.')

        for resource in resources:
            resp = self.dataverse_client.create_dataset(resource.parent_dataverse, resource.dataset.json())
            if resp.status_code != requests.codes.created:
                raise HttpException(resp.text)

            resp_dict = json.loads(resp.text)
            pid = resp_dict['data']['persistentId']

            # Upload datafile if exists
            if resource.datafile:
                self.dataverse_client.upload_file(pid, resource.datafile.filename)

            if publish_added:
                self.publish_resource(pid, type_version='major')

            # Update mapping with created PID identify
            resource_mapping = ResourceMapping.objects.get(uid=resource.uid)
            resource_mapping.pid = pid
            resource_mapping.save()

        logger.debug(f'Upload to {self.dataverse_client.base_url} completed.')

    def delete_resources(self, resources: List[Resource]) -> None:
        """
        Delete every resource in list from dataverse

        :param resources: list of resources
        :return: None
        """
        logger.debug(f'Starting removing datasets from {self.dataverse_client.base_url}.')

        for resource in resources:
            resp = self.dataverse_client.delete_dataset(resource.pid)
            if resp.status_code != requests.codes.ok:
                raise HttpException(resp.text)

            resource_mapping = ResourceMapping.objects.get(uid=resource.uid)
            resource_mapping.delete()

        logger.debug(f'Removing datasets from {self.dataverse_client.base_url} completed.')

    def update_resources(self, resources: List[Resource], update_publish_type=None) -> None:
        """
        Update every resource from list to dataverse and publish if specified

        :param resources: list of resources
        :param update_publish_type: specifies publishing method (None, 'major', 'minor')
        :return: None
        """
        logger.debug(f'Starting updating datasets from {self.dataverse_client.base_url}.')

        if update_publish_type not in (None, 'major', 'minor'):
            raise ValueError(
                f"Update_publish_type can only take values from (None, 'major', 'minor'), given {update_publish_type}")

        for resource in resources:
            resp = self.dataverse_client.edit_dataset_metadata(
                resource.pid,
                resource.dataset.json('dv_ed'),
                is_replace=True
            )

            if resp.status_code != requests.codes.ok:
                raise HttpException(resp.text)

            if update_publish_type in (None, 'major', 'minor'):
                self.publish_resource(resource.pid, type_version=update_publish_type)

            resource_mapping = ResourceMapping.objects.get(uid=resource.uid)
            resource_mapping.last_update = timezone.now()
            resource_mapping.save()

        logger.debug(f'Updating datasets from {self.dataverse_client.base_url} completed.')

    def publish_resource(self, pid: str, type_version: str = 'minor') -> None:
        """
        Publish dataset with given type of version

        :param pid: persistentID of dataset
        :param type_version: type of publishing 'major' or 'minor'
        :return: None
        """
        logger.debug(f'Starting publishing resource with persistentId {pid} with type={type_version}')
        resp = self.dataverse_client.publish_dataset(pid, type=type_version)

        if resp.status_code != requests.codes.ok:
            raise HttpException(resp.text)

        logger.debug(f'Successfully published dataset with persistenceId {pid}.')
