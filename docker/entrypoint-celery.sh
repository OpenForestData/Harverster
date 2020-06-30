#!/bin/bash

/app/docker/wait_for.sh harvester_db:5432 -t 15 -- echo "Database (harvester_db) is up!"
/app/docker/wait_for.sh harvester_redis:6379 -t 15 -- echo "Redis (harvester_redis) is up!"

cd /app/
celery -A harvester worker -l=INFO