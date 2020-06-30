import logging

from celery import shared_task
from pyDataverse.api import Api

from core.controllers import HarvestingController
from core.utils import get_client
from harvester import settings

logger = logging.getLogger(__name__)


@shared_task()
def run_harvester(name):
    """
    Using designated client harvests data form specified system
    """
    logger.debug("Started run harvest function")
    dataverse_client = Api(settings.DATAVERSE_URL, settings.DATAVERSE_API_KEY)
    app_client = get_client(name)

    harvester = HarvestingController(app_client, dataverse_client)

    add_data, modify_data, remove_data = harvester.run_harvest()

    if add_data:
        harvester.add_resources(add_data)
    if modify_data:
        harvester.update_resources(modify_data)
    if remove_data:
        harvester.delete_resources(remove_data)
