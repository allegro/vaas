echo "Migrating Scheduler"

exec celery --workdir=/home/app/vaas \
  --app=vaas.settings beat \
  --loglevel=DEBUG \
  --scheduler=beatx.schedulers.Scheduler