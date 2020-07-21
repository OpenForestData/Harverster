#!/bin/sh

python /app/manage.py migrate

/usr/local/bin/gunicorn harvester.wsgi -b 0.0.0.0:8000
