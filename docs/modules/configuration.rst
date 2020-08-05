Configuration
=============

Enviroments
-----------

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
- ``GEONODE_URL`` - geonode url for resources
- ``GEONODE_API_KEY`` - geonode api key for authenticated resources
- ``GRAFANA_URL`` - grafana url for resources
- ``GRAFANA_API_KEY`` - grafana api key for authenticated resources
- ``ORTHANC_URL`` - orthanc url for resources
- ``ORTHANC_API_KEY`` - orthanc api key for authenticated resources


Periodic tasks
--------------

For periodic tasks arguments you must specify three arguments:

- client - ("geonode", "grafana", "orthanc")
- create publish - (true, false)
- update publish - (null, "major", "minor")

e.g. ["geonode", true, "major"]
