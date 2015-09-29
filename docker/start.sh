#!/bin/bash -

DSM=vaas.settings.docker
touch /tmp/uwsgi.log

if [ ! -e /home/ubuntu/static ] ; then
    su -c "\
    source /home/ubuntu/prod-env/bin/activate &&
    echo yes | DJANGO_SETTINGS_MODULE=$DSM django-admin.py collectstatic"\
    ubuntu
fi

if [ ! -f /tmp/db.sqlite3 ] ; then
    su -c "\
    source /home/ubuntu/prod-env/bin/activate &&
    DJANGO_SETTINGS_MODULE=$DSM django-admin.py syncdb --noinput"\
    ubuntu
fi

if [ -e /data/data.yaml ] ; then
    su -c "\
    source /home/ubuntu/prod-env/bin/activate &&
    DJANGO_SETTINGS_MODULE=$DSM django-admin.py loaddata /data/data.yaml"\
    ubuntu
else
    su -c "\
    source /home/ubuntu/prod-env/bin/activate &&
    echo \"from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@domain.invalid', 'admin')\" |\
    DJANGO_SETTINGS_MODULE=$DSM django-admin.py shell"\
    ubuntu
fi

nginx &
/home/ubuntu/prod-env/bin/uwsgi --env DJANGO_SETTINGS_MODULE=$DSM --uid ubuntu --master --processes 8 --die-on-term --socket /tmp/vaas.sock -H /home/ubuntu/prod-env --module vaas.external.wsgi --chmod-socket=666 --logto /tmp/uwsgi.log &
tail -f /tmp/uwsgi.log
