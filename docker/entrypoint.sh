#!/bin/sh

python /app/manage.py migrate
python /app/manage.py collectstatic --noinput

/usr/local/bin/gunicorn harvester.wsgi -b 0.0.0.0:8000
