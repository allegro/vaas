#!/usr/bin/env bash

echo "Collect static files"
python /home/app/vaas/manage.py collectstatic --no-input

echo "Migrating"
python /home/app/vaas/manage.py migrate --run-syncdb

echo "Loading base-data"
python /home/app/vaas/manage.py loaddata ./vaas/resources/base-data.yaml

echo "Install the test requirements to allow [manage.py test] to be called within the container"
pip install -r /home/app/vaas/requirements/base.txt

echo "Start uwsgi server"
exec uwsgi --ini /etc/uwsgi.cfg --http-socket :3030