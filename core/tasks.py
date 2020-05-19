from celery import shared_task


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

    client = get_client(name)
    client.harvest()
