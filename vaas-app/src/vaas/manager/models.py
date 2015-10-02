# -*- coding: utf-8 -*-

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, validate_slug

from vaas.cluster.models import Dc, LogicalCluster
from vaas.manager.fields import generate_choices, NormalizedDecimalField, make_backend_name


class Probe(models.Model):
    name = models.CharField(unique=True, max_length=30, validators=[validate_slug])
    url = models.CharField(max_length=50)
    expected_response = models.PositiveIntegerField(default='200')
    interval = models.PositiveIntegerField(
        default='3',
        choices=[(x, x) for x in range(1, 301)],
        verbose_name=u'Interval (s)'
    )
    timeout = NormalizedDecimalField(
        default='1',
        decimal_places=1,
        max_digits=4,
        choices=generate_choices(1, 51, 10, 1),
        verbose_name=u'Timeout (s)'
    )
    window = models.PositiveIntegerField(
        default='5',
        choices=[(x, x) for x in range(1, 6)],
        verbose_name=u'Window (s)'
    )
    threshold = models.PositiveIntegerField(
        default='3',
        choices=[(x, x) for x in range(1, 301)]
    )

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.url)


class Director(models.Model):
    MODE_CHOICES = (
        ('round-robin', 'Round Robin'),
        ('random', 'Random'),
        ('hash', 'Hash'),
        ('fallback', 'Fallback')
    )
    ROUTER_CHOICES = (
        ('req.url', 'Path'),
        ('req.http.host', 'Domain'),
    )
    HASHING_POLICY_CHOICES = (
        ('req.http.cookie', 'Cookie'),
        ('req.url', 'Url')
    )
    name = models.CharField(unique=True, max_length=50, validators=[validate_slug])
    cluster = models.ManyToManyField(LogicalCluster)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    hashing_policy = models.CharField(
        max_length=20,
        default='req.url',
        choices=HASHING_POLICY_CHOICES,
        help_text='<i>Hashing policy only respected in Varnish v4 clusters. Hash mode must be selected.</i>'
    )
    router = models.CharField(
        max_length=20,
        default='req.url',
        choices=ROUTER_CHOICES
    )
    route_expression = models.CharField(
        max_length='30',
        verbose_name=u'Path or domain regex'
    )
    active_active = models.BooleanField(
        'DC aware fallback',
        default=True,
        help_text='<i>If no backends in primary DC available, use backends from other DC(s)</i>'
    )
    probe = models.ForeignKey(Probe, on_delete=models.PROTECT)
    enabled = models.BooleanField(default=True)
    remove_path = models.BooleanField(default=False)

    def mode_constructor(self):
        if self.mode == 'round-robin':
            return 'round_robin()'
        elif self.mode == 'random':
            return 'random()'
        elif self.mode == 'hash':
            return 'hash()'
        elif self.mode == 'fallback':
            return 'fallback()'

    def __unicode__(self):
        return self.name


class Backend(models.Model):
    address = models.GenericIPAddressField(protocol='IPv4')
    port = models.PositiveIntegerField(
        default='80',
        validators=[MinValueValidator(1), MaxValueValidator(65535)]
    )
    weight = models.PositiveIntegerField(
        default='1',
        choices=[(x, x) for x in range(1, 101)]
    )
    dc = models.ForeignKey(Dc, on_delete=models.PROTECT)
    max_connections = models.PositiveIntegerField(
        default='5',
        choices=[(x, x) for x in range(1, 101)]
    )
    connect_timeout = NormalizedDecimalField(
        default='0.30',
        decimal_places=2,
        max_digits=4,
        choices=generate_choices(1, 101, 100),
        verbose_name=u'Connect timeout (s)'
    )
    first_byte_timeout = NormalizedDecimalField(
        default='5',
        decimal_places=2,
        max_digits=4,
        choices=generate_choices(1, 4501, 100),
        verbose_name=u'First byte timeout (s)'
    )
    between_bytes_timeout = NormalizedDecimalField(
        default='1',
        decimal_places=2,
        max_digits=4,
        choices=generate_choices(1, 4501, 100),
        verbose_name=u'Between bytes timeout (s)'
    )
    director = models.ForeignKey(
        Director,
        related_name='backends',
        on_delete=models.PROTECT
    )
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return make_backend_name(self)

    class Meta:
        unique_together = (('address', 'port', 'director'),)
