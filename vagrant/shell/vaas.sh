#!/bin/bash

VAAS_SRC_HOME='/home/ubuntu/vaas/vaas-app/src'

# prepare repositories
sudo apt-get update -y
sudo apt-get install -y redis-server python-dev

sudo ~/venv/bin/docker-compose -f ~/vaas/docker-compose.yml up -d --force-recreate

# update venv
cd ~/
source venv/bin/activate
pip install -r vaas/vaas-app/requirements/dev.txt

# Kill the server if it is already running:
server_pids=$(ps -ef|awk '/manage.py[ ]runserver/ {print $2}'|xargs)
if [ "$server_pids" != '' ] ; then
  kill $server_pids
fi

if [ ! -f $VAAS_SRC_HOME/vaas/settings/__init__.py ] ; then
cat <<EOF >  $VAAS_SRC_HOME/vaas/settings/__init__.py
from vaas.settings.base import *
from vaas.settings.production import *
EOF
fi

if [ ! -f $VAAS_SRC_HOME/vaas/resources/db_config.yml ] ; then
cat <<EOF > $VAAS_SRC_HOME/vaas/resources/db_config.yml
default:
  ENGINE: 'django.db.backends.sqlite3'
  NAME: /tmp/db.sqlite3
EOF
fi

if [ ! -f /lib/systemd/system/celery.service ] ; then
sudo tee /lib/systemd/system/celery.service > /dev/null <<EOF
## managed by puppet ##
[Unit]
Description=Celery Service
After=syslog.target

[Service]
Type=forking
User=ubuntu
Group=ubuntu
PermissionsStartOnly=true
Environment=DJANGO_SETTINGS_MODULE=vaas.settings.local
ExecStartPre=/bin/mkdir -p /var/run/celery
ExecStartPre=/bin/chown -R ubuntu:ubuntu /var/run/celery
ExecStart=/bin/sh -c '/home/ubuntu/venv/bin/celery multi start worker --workdir=/home/ubuntu/vaas/vaas-app/src -A vaas.settings worker --logfile=/tmp/celery.log --pidfile=/var/run/celery/celery.pid --concurrency=1'
ExecStop=/bin/sh -c '/home/ubuntu/venv/bin/celery multi stopwait worker --pidfile=/var/run/celery/calery.pid'
ExecReload=/bin/sh -c '/home/ubuntu/venv/bin/celery multi restart worker --workdir=/home/ubuntu/vaas/vaas-app/src -A vaas.settings worker --logfile=/tmp/celery.log --pidfile=/var/run/celery/celery.pid --concurrency=1'

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl start celery.service
fi

job_status=$(sudo systemctl is-active celery.service)
if [[ ${job_status} = *active* ]]; then
    sudo systemctl restart celery.service
else
    sudo systemctl start celery.service
fi

if [ ! -f /tmp/db.sqlite3 ] ; then
  $VAAS_SRC_HOME/manage.py migrate --run-syncdb --noinput
  $VAAS_SRC_HOME/manage.py loaddata $VAAS_SRC_HOME/vaas/resources/data.yaml
fi

$VAAS_SRC_HOME/manage.py runserver 0.0.0.0:3030 &
