from celery import shared_task
from celery.schedules import crontab
from pyDataverse.api import Api

from core.controllers import HarvestingController
from core.utils import get_client
from harvester import settings
from harvester.celery import app


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(**settings.HARVESTED_PERIOD),
        run_harvester.s(settings.HARVESTED_SYSTEM),
    )


@shared_task
def run_harvester(name):
    """
    Using designated client harvests data form specified system
    """

    dataverse_client = Api(settings.DATAVERSE_URL, settings.DATAVERSE_API_KEY)
    app_client = get_client(name)

    harvester = HarvestingController(app_client, dataverse_client)
    resources = harvester.run_harvest()
    harvester.upload_resources(resources)

