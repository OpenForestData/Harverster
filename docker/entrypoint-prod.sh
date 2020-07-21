#!/bin/sh

python /app/manage.py migrate

/usr/local/bin/gunicorn harvester.wsgi
