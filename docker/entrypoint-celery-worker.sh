#!/usr/bin/env bash

exec celery --workdir=/home/app/vaas \
  -A vaas.settings worker \
  --loglevel=$LOG_LEVEL \
  --concurrency=1 \
  -Q worker_queue
