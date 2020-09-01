# OpenForest Harvester
Application copies resources to dataverse from possible sources creating datasets and datafiles

## Installation

### Requirements
All requirements all stored in requirements.txt file.

To run in container environment you need to install docker and docker-compose

### Application external dependencies
- PostgreSQL database ➤ https://www.postgresql.org/
- Orthanc DICOM server ➤ https://www.orthanc-server.com/
- Grafana ➤ https://grafana.com/
- Geonode ➤ http://geonode.org/

### Application environment variables
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

### Application installation (local)

- Run project (GNU/Linux, macOS)::
```
URL="localhost" docker-compose pull
URL="localhost" docker-compose build
URL="localhost" docker-compose up -d
```

- Run project (Windows)
```
$env:URL="localhost"; docker-compose pull
$env:URL="localhost"; docker-compose build
$env:URL="localhost"; docker-compose up -d
```

## Application tests
You need to install special dependencies with:
```
pip install factory-boy pytest pytest-cov pytest-pythonpath pytest-django mock
```
To run tests write:
```
pytest -v
```
## Deployment

## Contribution
The project was performed by Whiteaster sp.z o.o., with register office in Chorzów, Poland - www.whiteaster.com and provided under the GNU GPL v.3 license to the Contracting Entity - Mammal Research Institute Polish Academy of Science in Białowieża, Poland. We are proud to release this project under an Open Source license. If you want to share your comments, impressions or simply contact us, please write to the following e-mail address: info@whiteaster.com
