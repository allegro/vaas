# -*- coding: utf-8 -*-

import re

from django.utils import timezone
from taggit.managers import TaggableManager
from tastypie import fields
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, ValidationError
from simple_history.models import HistoricalRecords

from vaas.validators import vcl_name_validator, vcl_variable_validator


class LogicalCluster(models.Model):
    """Model representing a cluster of varnish servers"""
    name = models.CharField(max_length=100, validators=[vcl_name_validator], unique=True)
    directors = fields.ToManyField('vaas.manager.api.DirectorResource', 'directors')
    reload_timestamp = models.DateTimeField(default=timezone.now)
    error_timestamp = models.DateTimeField(default=timezone.now)
    last_error_info = models.CharField(max_length=400, null=True, blank=True)
    current_vcls = TaggableManager(blank=True)

    def __str__(self):
        return "{} ({})".format(self.name, self.varnish_count())

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        else:
            return False

    def varnish_count(self):
        return VarnishServer.objects.filter(cluster=self).count()


class Dc(models.Model):
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=9, unique=True, validators=[vcl_name_validator])

    def __str__(self):
        return self.symbol


class VclTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True, validators=[vcl_name_validator])
    content = models.TextField()
    version = models.CharField(max_length=3, choices=(('3.0', 'Vcl 3.0'), ('4.0', 'Vcl 4.0')), default='4.0')
    comment = models.CharField(max_length=64)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    def get_template_version(self):
        return self.version

    def clean(self):
        vcl_variable_validator(self.content, self.pk, VclVariable, VarnishServer)


class VarnishServer(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('maintenance', 'Maintenance'),
        ('disabled', 'Disabled')
    )
    ip = models.GenericIPAddressField(protocol='IPv4')
    hostname = models.CharField(max_length=50)
    cluster_weight = models.PositiveIntegerField(default='1',
                                                 validators=[MinValueValidator(1),
                                                             MaxValueValidator(100)])

    http_port = models.PositiveIntegerField(default='80',
                                            validators=[MinValueValidator(1),
                                                        MaxValueValidator(65535)])

    port = models.PositiveIntegerField(default='6082',
                                       validators=[MinValueValidator(1),
                                                   MaxValueValidator(65535)])

    secret = models.CharField(max_length=40)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='disabled')

    dc = models.ForeignKey(Dc, on_delete=models.PROTECT)
    template = models.ForeignKey(VclTemplate, on_delete=models.PROTECT)
    cluster = models.ForeignKey(LogicalCluster, on_delete=models.PROTECT)
    is_canary = models.BooleanField(default=False)

    def __str__(self):
        return "{}:{} ({})".format(self.ip, self.port, self.hostname)

    class Meta:
        unique_together = (('ip', 'port'))


class VclTemplateBlock(models.Model):
    TAG_CHOICES = (
        ('VCL', 'VCL'),
        ('HEADERS', 'VCL/HEADERS'),
        ('ACL', 'VCL/ACL'),
        ('BACKENDS', 'VCL/BACKENDS'),
        ('DIRECTORS', 'VCL/DIRECTORS'),
        ('RECV', 'VCL/RECEIVE'),
        ('ROUTER', 'VCL/RECEIVE/ROUTER'),
        ('PROPER_PROTOCOL_REDIRECT', 'RECEIVE/PROPER_PROTOCOL_REDIRECT'),
        ('OTHER_FUNCTIONS', 'VCL/OTHER_FUNCTIONS'),
    )
    tag = models.CharField(max_length=100, choices=TAG_CHOICES)
    template = models.ForeignKey(VclTemplate, on_delete=models.PROTECT)
    content = models.TextField()
    history = HistoricalRecords()

    def clean(self):
        vcl_variable_validator(self.content, self.template.pk, VclVariable, VarnishServer)

    class Meta:
        unique_together = (('tag', 'template'))


class VclVariable(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=254)
    cluster = models.ForeignKey(LogicalCluster)

    def __str__(self):
        return "{}: {}".format(self.key, self.value)

    class Meta:
        unique_together = (('key', 'cluster'), )
