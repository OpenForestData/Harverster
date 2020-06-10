"""
Django settings for harvester project.

Generated by 'django-admin startproject' using Django 2.2.12.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""
import json
import os
from ast import literal_eval

if os.environ.get('READ_DOT_ENV'):
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='../')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = literal_eval(os.environ.get('DEBUG', 'True'))

ALLOWED_HOSTS = []

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'django_celery_beat',

    'adapters.geonode.apps.GeonodeConfig',
    'adapters.grafana.apps.GrafanaConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'harvester.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'harvester.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get("DB_NAME"),
        'USER': os.environ.get("DB_USER"),
        'PASSWORD': os.environ.get("DB_PASSWORD", 5432),
        'HOST': os.environ.get("DB_HOST"),
        'PORT': '5432',
    },
    'mongodb': {
        "ENGINE": 'djongo',
        "NAME": os.environ.get("MONGO_DATABASE"),
        'ENFORCE_SCHEMA': True,
        'CLIENT': {
            'host': os.environ.get("MONGO_HOST"),
            'port': os.environ.get("MONGO_PORT", 27017),
            'username': os.environ.get("MONGO_USER"),
            'password': os.environ.get("MONGO_PASSWORD"),
        },
    }
}

DATABASE_ROUTERS = ('core.database_router.DBRouter',)

NOSQL_MODELS = ['HarvestingDatestamp', 'GeonodeResourceIdMapping']
NOSQL_DATABASE = 'mongodb'

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'

# Celery
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')

# App specific settings
HARVESTED_SYSTEM = os.environ.get('HARVESTED_SYSTEM')
HARVESTED_PERIOD = json.loads(os.environ['HARVESTED_PERIOD'])

# Dataverse
DATAVERSE_URL = os.environ.get('DATAVERSE_URL')
DATAVERSE_API_KEY = os.environ.get('DATAVERSE_API_KEY')


# Geonode
GEONODE_OFFSET = os.environ.get('GEONODE_OFFSET', 1000)

CLIENTS_DICT = {
    'geonode': {
        'module': 'adapters.geonode.client',
        'class': 'GeonodeClient',
        'url': 'http://gis.openforestdata.pl/'
    }
}
