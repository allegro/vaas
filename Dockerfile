# pull official base image
FROM ubuntu:noble


# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# create directory for the app
RUN mkdir -p /home/app
ENV HOME=/home/app

# set work directory
ENV APP_HOME=/home/app/vaas
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

# create directory for the plugins
RUN mkdir $HOME/plugins
ENV PYTHONPATH=/home/app/plugins

VOLUME ["/home/app/plugins"]

RUN apt update \
  && apt install -y --no-install-recommends \
    curl \
    git \
    default-libmysqlclient-dev \
    build-essential \
    default-mysql-client \
    pkg-config \
    libxml2  \
    libxml2-dev \
    libxslt1 \
    libxslt1-dev \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    python3-setuptools \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python3.12 -m venv /opt/venv

# Activate virtual environment and install pip packages
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip setuptools wheel

COPY ./vaas/requirements /home/app/vaas/requirements

RUN pip install -r ./requirements/base.txt

#copy uwsgi config
COPY ./docker/uwsgi.cfg /etc/

#copy mime types used by uwsgi
COPY ./docker/mime.types /etc/

# copy project
COPY ./vaas /home/app/vaas

# copy entrypoints.sh
COPY \
  docker/entrypoint-uwsgi.sh \
  docker/entrypoint-uwsgi-dev.sh \
  docker/entrypoint-celery-worker.sh \
  docker/entrypoint-celery-routes-test.sh \
  docker/entrypoint-celery-scheduler.sh \
  docker/entrypoint-celery-cron-worker.sh \
  docker/wait-for-it.sh \
  /

# run entrypoint.sh
ENTRYPOINT ["/entrypoint-uwsgi-dev.sh"]
