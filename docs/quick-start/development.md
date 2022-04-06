


Local Development
===============
This project provides a basic Docker Compose setup for Vaas. It is useful for experimentation, testing and development purposes.


Install Tools
----------------
To get up and running, after cloning the repository:

1. Install Docker. Read about [installing Docker](https://docs.docker.com/get-docker/).
1. Install Docker Compose. Read about [installing Docker Compose](https://docs.docker.com/compose/install/).


Run Vaas in Docker Comose
----------------
To start Vaas you just have to run:
```bash
docker-compose up -d
```

Check That Everything Is Working
----------------
To check that the build is working, run `docker-compose ps`. This should give you output similar to the below.

```bash
vaas_backend-statuses_1     /wait-for-it.sh uwsgi:3030 ...   Up
vaas_celery-routes-test_1   /entrypoint-celery-routes- ...   Up
vaas_celery-worker_1        /entrypoint-celery-worker.sh     Up
vaas_celery-cron-queue_1    /entrypoint-celery-queue-worek.sh Up
vaas_nginx-0_1              nginx                            Up             80/tcp
vaas_nginx-1_1              nginx                            Up             80/tcp
vaas_nginx-2_1              nginx                            Up             80/tcp
vaas_nginx-3_1              nginx                            Up             80/tcp
vaas_nginx-4_1              nginx                            Up             80/tcp
vaas_nginx-5_1              nginx                            Up             80/tcp
vaas_redis_1                docker-entrypoint.sh redis ...   Up (healthy)   6379/tcp
vaas_uwsgi_1                /entrypoint-uwsgi-dev.sh         Up             0.0.0.0:3030->3030/tcp,:::3030->3030/tcp
vaas_varnish-4.1_1          /start                           Up             6081/tcp, 6082/tcp
vaas_varnish-6.0.2_1        /start                           Up             6081/tcp, 6082/tcp
vaas_varnish-7.0_1          /start                           Up             6081/tcp, 6082/tcp
```


Log in to VaaS
--------------
Point your browser to <http://localhost:3030/> and log in using the following credentials:

    User: admin
    Password: admin

You will see a django admin GUI with tree apps: Cluster, Manager and Router. Configure your sample Varnish servers and VCL templates in Cluster app. Configure your backends, directors and probes in the Manager app. Refer to [GUI](../documentation/gui.md) or [API](../documentation/api.md) documentation to see how to do this.

Current VCL for the test Varnish instances can be previewed by clicking on Cluster -> Varnish servers -> Show vcl. HINT: Freshly after booting up VaaS in Docker Compose, the configuration of the Varnish servers will not be loaded. Make some changes to the test backends or re-enable the test Varnish instances to trigger loading of the configuration.


Developing locally
---------------------

Codebase is shared by using a bind-mount, which simply mounts a host folder on top of the container target folder  `/home/app/vaas`. 
Container named `uwsgi` runs a Django development server which according to [Django docs](https://docs.djangoproject.com/en/4.0/intro/tutorial01/#the-development-server) 
automatically reloads Python code for each request as needed.

Codebase is also mounted into containers with Celery workers. Celery doesn't provide auto reloads on code change,
 you need to do it manually by reloading containers:

 ```bash
 docker-compose restart celery-worker celery-cron-worker celery-routes-test
 ```

Entering container
---------------------
When you need run command manually in container context, you can enter into already running container
using command 
```bash
docker-compose exec uwsgi bash
root@f3483d1c7c8c:~/vaas#
```


Spawn more Varnish instances
----------------------------
You can easily spawn more Varnish instances (as many as your VM's resources will allow) as follows:

    # IP_address - one of the addresses from  subnet 192.168.199.0/24
    # NUMBER - a number to distinguish this instance from other instances
    # Varnish 3
    docker run -d -t -m 104857600b --ip=<IP_address> \
        --expose 6081-6082 --network vaas_vaas \
        --name varnish-3-<NUMBER> allegro/vaas-varnish-3
    # Varnish 4
    docker run -d -t -m 104857600b --ip=<IP_address> \
        --expose 6081-6082 --network vaas_vaas \
        --name varnish-3-<NUMBER> allegro/vaas-varnish-4

You will then need to add the new Varnish instances to your Cluster.

Spawn more Nginx instances
--------------------------
Similarly to new Varnish instances, you can also spawn new Nginx instances:

    # IP_address - one of the addresses from  subnet 192.168.199.0/24
    # NUMBER - a number to distinguish this instance from other instances
    docker run -d -t -m 26214400b --ip=<IP_address> \
        --expose 6081-6082 --network vaas_vaas \
        -v /srv/www/first:/usr/share/nginx/html/first \
        -v /srv/www/second:/usr/share/nginx/html/second \
        --name nginx-<NUMBER> allegro/vaas-nginx

You will need to configure the new Nginx instance in Manager app.