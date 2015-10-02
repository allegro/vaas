#!/bin/bash
while true ; do
  su -c "\
  DJANGO_SETTINGS_MODULE=vaas.settings.docker /home/ubuntu/prod-env/bin/django-admin.py backend_statuses"\
  ubuntu
  sleep 120
done
