#!/bin/bash

VAAS_SRC_HOME='/home/vagrant/vaas/vaas-app/src'

# prepare repositories
sudo apt-get update -y
sudo apt-get install -y redis-server

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

if [ ! -f /etc/init/celery.conf ] ; then
sudo tee /etc/init/celery.conf > /dev/null <<EOF
start on runlevel [2345]
stop on runlevel [06]

env DJANGO_SETTINGS_MODULE=vaas.settings.local

setgid vagrant
setuid vagrant

script
    exec /home/vagrant/venv/bin/python /home/vagrant/venv/bin/celery --workdir=/home/vagrant/vaas/vaas-app/src -A vaas.settings worker -l info
end script

respawn
EOF
fi

job_status=$(status celery)
if [[ ${job_status} = *running* ]]; then
    sudo restart celery
else
    sudo start celery
fi

if [ ! -f /tmp/db.sqlite3 ] ; then
  $VAAS_SRC_HOME/manage.py syncdb --noinput
  $VAAS_SRC_HOME/manage.py loaddata $VAAS_SRC_HOME/vaas/resources/data.yaml
fi

$VAAS_SRC_HOME/manage.py runserver 0.0.0.0:3030 &
