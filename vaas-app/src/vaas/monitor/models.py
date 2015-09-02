# -*- coding: utf-8 -*-

from django.db import models


class BackendStatus(models.Model):
    address = models.GenericIPAddressField(protocol='IPv4')
    port = models.PositiveIntegerField()
    timestamp = models.DateTimeField()
    status = models.CharField(max_length=30)

    class Meta:
        unique_together = (('address', 'port'),)
