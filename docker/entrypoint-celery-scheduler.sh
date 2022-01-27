echo "Migrating Scheduler"
python /home/app/vaas/manage.py migrate django_celery_beat

exec celery --workdir=/home/app/vaas \
  --app=vaas.settings beat \
  --loglevel=DEBUG \
  --scheduler=django_celery_beat.schedulers:DatabaseScheduler