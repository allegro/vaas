FROM ubuntu:16.04
RUN add-apt-repository ppa:deadsnakes/ppa &&\
    apt-get update &&\
    apt-get install -y git python3.9 python3-pip libxml2-dev libxslt1-dev python3.9-dev python3-venv sqlite3 libssl-dev libtool libssl-dev libsasl2-dev libmysqlclient-dev libcurl4-openssl-dev nginx redis-server &&\
    apt-get clean &&\
    rm -rf /var/lib/apt/lists/* &&\
    rm /etc/nginx/sites-enabled/default

RUN useradd -d /home/vagrant vagrant &&\
    mkdir /home/vagrant

ADD ./docker/vaas.conf /etc/nginx/sites-enabled/vaas.conf
ADD ./docker/start.sh /var/tmp/start.sh
ADD ./docker/backend_statuses.sh /var/tmp/backend_statuses.sh
ADD ./vaas-app/ /home/vagrant/vaas-app/

RUN chown -R vagrant:vagrant /home/vagrant &&\
    chmod 755 /var/tmp/*.sh

USER vagrant

RUN cd /home/vagrant &&\
    python3.9 -m venv prod-env &&\
    . prod-env/bin/activate &&\
    cd /home/vagrant/vaas-app &&\
    touch src/vaas/settings/__init__.py &&\
    pip install --upgrade pip &&\
    pip install uwsgi importlib-metadata &&\
    python setup.py install &&\
    cd &&\
    rm -r vaas-app

USER root
ENTRYPOINT ["/var/tmp/start.sh"]
CMD ["admin", "admin@domain.example.com", "admin", "admin"]
