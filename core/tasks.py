import logging

from celery import shared_task
from pyDataverse.api import Api

from core.controllers import HarvestingController
from core.utils import get_client
from harvester import settings

logger = logging.getLogger(__name__)


@shared_task()
def run_harvester(name: str) -> None:
    """
    Using designated client harvests data form specified system

    :param name: client name
    """
    logger.debug(f"Starting run harvest function for {name}")
    dataverse_client = Api(settings.DATAVERSE_URL, settings.DATAVERSE_API_KEY)
    app_client = get_client(name)

    harvester = HarvestingController(app_client, dataverse_client)

    add_data, modify_data, remove_data = harvester.run_harvest()
    logger.debug(f"Harvested data from source of {name}")

    if add_data:
        logger.debug(f"Starting adding new resources from {name}")
        harvester.add_resources(add_data)
    if modify_data:
        logger.debug(f"Starting updating resources from {name}")
        harvester.update_resources(modify_data)
    if remove_data:
        logger.debug(f"Starting removing resources from {name}")
        harvester.delete_resources(remove_data)
