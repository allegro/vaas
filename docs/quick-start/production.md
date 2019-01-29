Configuring VaaS in production environment
==========================================
VaaS is a Django application. It can be run in multiple ways, as documented in [Django deployment documentation](https://docs.djangoproject.com/en/1.8/howto/deployment/). The example below is just one way of deploying VaaS. It uses Uwsgi, Nginx and Mysql on an Ubuntu server, as ubuntu user.

Build VaaS package
------------------
Use the commands below to build VaaS from source:

    git clone https://github.com/allegro/vaas.git
    /usr/local/bin/virtualenv dist-env
    . dist-env/bin/activate
    cd vaas/vaas-app
    python setup.py egg_info
    pip install -r src/vaas.egg-info/requires.txt
    python setup.py sdist --format=zip

Install VaaS package
--------------------
Use the commands below to install VaaS package built in the previous step on a web server:

    virtualenv prod-env
    . prod-env/bin/activate
    pip install python-ldap==2.4.15
    pip install django-auth-ldap==1.2.0
    pip install MySQL-python==1.2.3
    pip install lck.django
    pip install uwsgi
    pip install vaas-{version-number}.zip


Configure Mysql
---------------
Install Mysql server and create a new database and user for VaaS.


VaaS configuration location
---------------------------

All django related settings should be stored in location

    ~/.vaas

VaaS application handles three files in yaml format, but only one is required:
     * db_config.yml - database configuration *required*
     * production.yml - place to override some django settings *optional*
     * ldap.yml - ldap integration config *optional* - more at [ldap configuration](../documentation/ldap.md)

Configure VaaS application
--------------------------
VaaS requires the following configuration file:

db_config.yml:

    ---
    default:
      ENGINE: 'django.db.backends.mysql'
      NAME: 'vaas'
      USER: 'vaas'
      PASSWORD: 'vaas'
      HOST: 'mysql.hostname'


Configure Uwsgi
---------------
One way to run Uwsgi is to configure it with upstart. Create a file called /etc/init/uwsgi.conf with the following contents:

    description "Vaas - Varnish Configuration"
    start on runlevel [2345]
    stop on runlevel [06]
    
    exec /home/vagrant/prod-env/bin/uwsgi --env DJANGO_SETTINGS_MODULE=vaas.settings --uid vagrant --master --processes 8 --die-on-term --socket /tmp/vaas.sock -H /home/vagrant/prod-env --module vaas.external.wsgi --chmod-socket=666 --logto /tmp/uwsgi.log

Then start uwsgi with:

    service uwsgi start

Configure Nginx
---------------
Create a file in /etc/nginx/sites-available/vaas.conf and link it to /etc/nginx/sites-enabled. Add the following contents to the file replacing SERVER_NAME with your server name:

    upstream django {
        server unix:///tmp/vaas.sock;
    }
    
    server {
        listen      80;
        server_name <SERVER_NAME>;
        charset     utf-8;
    
        client_max_body_size 75M;
    
        location /static {
            alias /home/vagrant/prod-env/local/lib/python2.7/site-packages/vaas/static;
        }
    
        location / {
            uwsgi_pass  django;
            include     /etc/nginx/uwsgi_params;
            uwsgi_read_timeout 300;
        }
    }

Then start Nginx with:

    service nginx start


Override django settings
------------------------
It's possible to override some django settings by special config file named production.yml as follow:

production.yml:

    SECURE_PROXY_SSL_HEADER: !!python/tuple ['HTTP_X_FORWARDED_PROTO', 'https']
    ALLOWED_HOSTS: [''.example.com']
