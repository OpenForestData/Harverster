#!/bin/sh

cd /app/

celery -A harvester worker -l info -B --scheduler django_celery_beat.schedulers:DatabaseScheduler