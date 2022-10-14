# -*- coding: utf-8 -*-

from django.db import models


class BackendStatus(models.Model):
    backend_id = models.PositiveIntegerField(blank=True, null=True)
    timestamp = models.DateTimeField()
    status = models.CharField(max_length=30)
