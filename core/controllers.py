import json
import logging
from typing import List

import requests
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
        logger.debug(f'Starting harvest from {self.harvesting_client.service_url}.')
        # Get all results
        result = self.harvesting_client.harvest()
        logger.debug(f'Harvest from {self.harvesting_client.service_url} completed.')
        return result

    def add_resources(self, resources: List[Resource]) -> None:
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

            # Update mapping with created PID identify
            resource_mapping = ResourceMapping.objects.get(uid=resource.uid)
            resource_mapping.pid = pid
            resource_mapping.save()

        logger.debug(f'Upload to {self.dataverse_client.base_url} completed.')

    def delete_resources(self, resources: List[Resource]) -> None:
        logger.debug(f'Starting removing datasets from {self.dataverse_client.base_url}.')
        for resource in resources:
            resp = self.dataverse_client.delete_dataset(resource.pid)
            if resp.status_code != requests.codes.ok:
                raise HttpException(resp.text)

            resource_mapping = ResourceMapping.objects.get(uid=resource.uid)
            resource_mapping.delete()

        logger.debug(f'Upload to {self.dataverse_client.base_url} completed.')
