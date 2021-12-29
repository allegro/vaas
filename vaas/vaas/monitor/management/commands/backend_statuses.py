# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from vaas.monitor.health import BackendStatusManager


class Command(BaseCommand):
    def handle(self, *args, **options):
        BackendStatusManager().refresh_statuses()
