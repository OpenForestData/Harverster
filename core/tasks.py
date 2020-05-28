from celery import shared_task
from celery.schedules import crontab
from pyDataverse.api import Api

from harvester import settings
from harvester.celery import app


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

    # Calls test('world') every 30 seconds
    sender.add_periodic_task(30.0, test.s('world'), expires=10)

    # Executes every Monday morning at 7:30 a.m.
    sender.add_periodic_task(
        crontab(**settings.HARVESTED_PERIOD),
        harvest.s(settings.HARVESTED_SYSTEM),
    )


def get_client(name):
    """
    Return client based on given app name
    :param name: name of application client should serve
    :return: Client object
    """
    client_dict = {}
    return client_dict[name] if name in client_dict else None


@shared_task
def harvest(name):
    """
    Using designated client harvests data form specified system
    """

    dataverse_client = Api

    client = get_client(name)
    client.harvest()
    for resource in client.resources:
        Api. resource.dataset
        resource.datafiles
