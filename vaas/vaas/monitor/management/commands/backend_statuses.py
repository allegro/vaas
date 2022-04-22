# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from vaas.monitor.health import provide_backend_status_manager


class Command(BaseCommand):
    def handle(self, *args, **options):
        provide_backend_status_manager().refresh_statuses()
