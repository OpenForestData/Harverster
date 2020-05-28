from django.conf import settings


class DBRouter(object):

    def db_for_read(self, model, **hints):
        if model.__name__ in settings.NOSQL_MODELS:
            return settings.NOSQL_DATABASE
        return None

    def db_for_write(self, model, **hints):
        if model.__name__ in settings.NOSQL_MODELS:
            return settings.NOSQL_DATABASE
        return None
