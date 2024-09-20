echo "Migrating Scheduler"

exec celery --workdir=/home/app/vaas \
  --app=vaas.settings beat \
  --loglevel=$LOG_LEVEL \
  --scheduler=beatx.schedulers.Scheduler