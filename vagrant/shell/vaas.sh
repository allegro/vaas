#!/bin/bash

VAAS_SRC_HOME='/home/vagrant/vaas/vaas-app/src'

sudo ~/venv/bin/docker-compose -f ~/vaas/docker-compose.yml up -d --force-recreate

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

if [ ! -f /tmp/db.sqlite3 ] ; then
  $VAAS_SRC_HOME/manage.py syncdb --noinput
  $VAAS_SRC_HOME/manage.py loaddata $VAAS_SRC_HOME/vaas/resources/data.yaml
fi

$VAAS_SRC_HOME/manage.py runserver 0.0.0.0:3030 &
