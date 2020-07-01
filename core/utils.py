import importlib

from harvester import settings


def get_client(name):
    """
    Return client based on given app name

    :param name: name of application client should serve
    :return: Client object
    """
    client_dict = settings.CLIENTS_DICT
    if name not in client_dict:
        raise KeyError(f'There is no client under name: {name} in settings.CLIENTS_DICT.')

    client_data = client_dict[name]
    client_class = getattr(importlib.import_module(client_data['module']), client_data['class'])

    return client_class(client_data['url'], client_data['api_key'])
