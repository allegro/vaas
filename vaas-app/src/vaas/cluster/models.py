# -*- coding: utf-8 -*-

from tastypie import fields
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, validate_slug
from simple_history.models import HistoricalRecords


class LogicalCluster(models.Model):
    """Model representing a cluster of varnish servers"""
    name = models.CharField(max_length=20, validators=[validate_slug])
    directors = fields.ToManyField('vaas.manager.api.DirectorResource', 'directors')

    def __unicode__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        else:
            return False


class Dc(models.Model):
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=9, validators=[validate_slug])

    def __unicode__(self):
        return self.symbol


class VclTemplate(models.Model):
    name = models.CharField(max_length=50, unique=True)
    content = models.TextField()
    version = models.CharField(max_length=3, choices=(('3.0', 'Vcl 3.0'), ('4.0', 'Vcl 4.0')), default='3.0')
    history = HistoricalRecords()

    def __unicode__(self):
        return self.name


class VarnishServer(models.Model):
    ip = models.GenericIPAddressField(protocol='IPv4', unique=True)
    hostname = models.CharField(max_length=50)
    cluster_weight = models.PositiveIntegerField(default='1',
                                                 validators=[MinValueValidator(1),
                                                             MaxValueValidator(100)])

    port = models.PositiveIntegerField(default='6082',
                                       validators=[MinValueValidator(1),
                                                   MaxValueValidator(65535)])

    secret = models.CharField(max_length=40)
    enabled = models.BooleanField(default=False)

    dc = models.ForeignKey(Dc, on_delete=models.PROTECT)
    template = models.ForeignKey(VclTemplate, on_delete=models.PROTECT)
    cluster = models.ForeignKey(LogicalCluster, on_delete=models.PROTECT)


class VclTemplateBlock(models.Model):
    TAG_CHOICES = (
        ('VCL', 'VCL'),
        ('HEADERS', 'VCL/HEADERS'),
        ('ACL', 'VCL/ACL'),
        ('BACKENDS', 'VCL/BACKENDS'),
        ('DIRECTORS', 'VCL/DIRECTORS'),
        ('RECV', 'VCL/RECEIVE'),
        ('ROUTER', 'VCL/RECEIVE/ROUTER'),
        ('OTHER_FUNCTIONS', 'VCL/OTHER_FUNCTIONS'),
    )
    tag = models.CharField(max_length=20, choices=TAG_CHOICES)
    template = models.ForeignKey(VclTemplate, on_delete=models.PROTECT)
    content = models.TextField()
    history = HistoricalRecords()

    class Meta:
        unique_together = (('tag', 'template'))
