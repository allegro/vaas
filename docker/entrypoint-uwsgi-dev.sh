#!/usr/bin/env bash

echo "Collect static files"
python /home/app/vaas/manage.py collectstatic --no-input

echo "Migrating"
python /home/app/vaas/manage.py migrate --run-syncdb

echo "Loadind test_data"
python /home/app/vaas/manage.py loaddata ./vaas/resources/data.yaml

echo "Start dev server"
python /home/app/vaas/manage.py runserver 0.0.0.0:3030