Configuration
=============

Configuration page


Docker-compose enviroments
--------------------------

- ``SECRET_KEY`` - secret key for django framework. (Default: SECRET_KEY_REPLACE)
- ``DB_HOST`` - host address for database. (Default: harvester_db)
- ``DB_USER`` - username for database. (Default: harvester_user)
- ``DB_PASSWORD`` - password for database user. (Default: harvester_password)
- ``CELERY_BROKER_URL`` - celery broker url. (Default: redis://harvester_redis:6379/0)
- ``DATAVERSE_URL`` - dataverse url. (Default: https://url-to-dataverse.com)
- ``DATAVERSE_API_KEY`` - dataverse api key. (Default: DATAVERSE_API_KEY_REPLACE)
- ``LAYERS_PARENT_DATAVERSE`` - dataverse url slug for layers. (Default: layers)
- ``MAPS_PARENT_DATAVERSE`` - dataverse url slug for maps. (Default: maps)
- ``DOCUMENTS_PARENT_DATAVERSE`` - dataverse url slug for documents. (Default: documents)
- ``DASHBOARDS_PARENT_DATAVERSE`` - dataverse url slug for dashboards. (Default: dashboards)
- ``STUDIES_PARENT_DATAVERSE`` - dataverse url slug for studies. (Default: studies)

Setting
-------
Clients dict for harvesting task:::

    CLIENTS_DICT = {
        'geonode': {
            'module': 'adapters.geonode.client',
            'class': 'GeonodeClient',
            'url': 'https://url-to-geonode.com',
            'api_key': None
        },
        'grafana': {
            'module': 'adapters.grafana.client',
            'class': 'GrafanaClient',
            'url': 'https://url-to-grafana.com',
            'api_key': 'grafana-api-key'
        },
        'orthanc': {
            'module': 'adapters.orthanc.client',
            'class': 'OrthancClient',
            'url': 'https://url-to-orthanc.com',
            'api_key': None
        }
    }
