#!/bin/bash -
USERNAME=$1
EMAIL=$2
PASSWORD=$3
API_KEY=$4
DSM=vaas.settings.docker
touch /tmp/uwsgi.log

if [ ! -e /home/vagrant/static ] ; then
    su -c "\
    source /home/vagrant/prod-env/bin/activate &&
    echo yes | DJANGO_SETTINGS_MODULE=$DSM django-admin.py collectstatic"\
    vagrant
fi

if [ ! -f /tmp/db.sqlite3 ] ; then
    su -c "\
    source /home/vagrant/prod-env/bin/activate &&
    DJANGO_SETTINGS_MODULE=$DSM django-admin.py migrate --run-syncdb --noinput"\
    vagrant
fi

if [ -e /data/data.yaml ] ; then
    su -c "\
    source /home/vagrant/prod-env/bin/activate &&
    DJANGO_SETTINGS_MODULE=$DSM django-admin.py loaddata /data/data.yaml"\
    vagrant
else
    su -c "\
    source /home/vagrant/prod-env/bin/activate &&
    DJANGO_SETTINGS_MODULE=$DSM django-admin.py create_user_and_api_key $USERNAME $EMAIL $PASSWORD $API_KEY"\
    vagrant
fi

/var/tmp/backend_statuses.sh &
nginx &
redis-server &
su - vagrant -c '/home/vagrant/prod-env/bin/python /home/vagrant/prod-env/bin/celery -A vaas.settings worker -l info --concurrency=1' &
/home/vagrant/prod-env/bin/uwsgi --env DJANGO_SETTINGS_MODULE=$DSM --uid vagrant --master --processes 8 --die-on-term --socket /tmp/vaas.sock -H /home/vagrant/prod-env --module vaas.external.wsgi --chmod-socket=666 --logto /tmp/uwsgi.log &
tail -f /tmp/uwsgi.log
