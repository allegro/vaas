#!/usr/bin/env bash

echo "Collect static files"
python /home/app/vaas/manage.py collectstatic --no-input

echo "Migrating"
python /home/app/vaas/manage.py migrate --run-syncdb

echo "Loading test_data"
python /home/app/vaas/manage.py loaddata ./vaas/resources/data.yaml

echo "Install the test requirements to allow [manage.py test] to be called within the container"
pip install -r /home/app/vaas/requirements/test.txt

echo "Start dev server"
# python /home/app/vaas/manage.py runserver 0.0.0.0:3030
exec uwsgi --ini /home/app/vaas/uwsgi.cfg --http-socket :3030 --http-timeout 120 --http-keepalive --http-connect-timeout 60 --stats :3031 --stats-http