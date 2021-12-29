#!/usr/bin/env bash

while true ; do
  python /home/app/vaas/manage.py backend_statuses
  sleep 120
done
