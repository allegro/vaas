#!/bin/bash

VAAS_SRC_HOME='/home/vagrant/vaas/vaas-app/src'
VAAS_PUPPET_FILES='/home/vagrant/vaas/vagrant/puppet/files'

# Kill the server if it is already running:
server_pids=$(ps -ef|awk '/manage.py[ ]runserver/ {print $2}'|xargs)
if [ "$server_pids" != '' ] ; then
  kill $server_pids
fi

if [ ! -f $VAAS_SRC_HOME/vaas/settings/__init__.py ] ; then
  cp $VAAS_PUPPET_FILES/init_local_settings.py $VAAS_SRC_HOME/vaas/settings/__init__.py
fi

if [ ! -f $VAAS_SRC_HOME/vaas/resources/db_config.yml ] ; then
  cp $VAAS_PUPPET_FILES/db_config.yml $VAAS_SRC_HOME/vaas/resources/db_config.yml
fi

if [ ! -f $VAAS_SRC_HOME/vaas/resources/data.yaml ] ; then
  cp $VAAS_PUPPET_FILES/data.yaml $VAAS_SRC_HOME/vaas/resources/data.yaml
fi

if [ ! -f /tmp/db.sqlite3 ] ; then
  $VAAS_SRC_HOME/manage.py syncdb --noinput
  $VAAS_SRC_HOME/manage.py loaddata $VAAS_SRC_HOME/vaas/resources/data.yaml
fi

$VAAS_SRC_HOME/manage.py runserver 0.0.0.0:3030 &
