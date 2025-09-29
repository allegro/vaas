# -*- coding: utf-8 -*-

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from taggit.managers import TaggableManager

from vaas.cluster.models import Dc, LogicalCluster
from vaas.manager.fields import generate_choices, NormalizedDecimalField, make_backend_name
from vaas.validators import name_validator

from simple_history.models import HistoricalRecords

class Probe(models.Model):
    history = HistoricalRecords()
    name = models.CharField(max_length=30, validators=[name_validator], unique=True)
    url = models.CharField(max_length=50)
    expected_response = models.PositiveIntegerField(default="200")
    interval = models.PositiveIntegerField(
        default="3",
        choices=[(x, x) for x in range(1, 301)],
        verbose_name="Interval (s)"
    )
    timeout = NormalizedDecimalField(
        default="1",
        decimal_places=1,
        max_digits=4,
        choices=generate_choices(1, 51, 10, 1),
        verbose_name="Timeout (s)"
    )
    window = models.PositiveIntegerField(
        default="5",
        choices=[(x, x) for x in range(1, 6)],
        verbose_name="Window (s)"
    )
    threshold = models.PositiveIntegerField(
        default="3",
        choices=[(x, x) for x in range(1, 301)]
    )
    start_as_healthy = models.BooleanField(
        "Start backend as healthy",
        default=False,
        help_text="<i>New backend is starting with healthy status, there is no need to initial health check pass</i>"
    )

    def __str__(self):
        return "%s (%s)" % (self.name, self.url)


class TimeProfile(models.Model):
    history = HistoricalRecords()
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)
    max_connections = models.PositiveIntegerField(default="5")
    connect_timeout = NormalizedDecimalField(
        default="0.30", decimal_places=2, max_digits=4, verbose_name="Connect timeout (s)"
    )
    first_byte_timeout = NormalizedDecimalField(
        default="5", decimal_places=2, max_digits=5, verbose_name="First byte timeout (s)"
    )
    between_bytes_timeout = NormalizedDecimalField(
        default="1", decimal_places=2, max_digits=5, verbose_name="Between bytes timeout (s)"
    )
    service_mesh_timeout = NormalizedDecimalField(
        default="300", decimal_places=2, max_digits=5, verbose_name="Service mesh timeout (s)"
    )

    @property
    def service_mesh_timeout_ms(self):
        return int(1000 * self.service_mesh_timeout)

    def __str__(self):
        return self.name


class Director(models.Model):
    MODE_CHOICES = (
        ("round-robin", "Round Robin"),
        ("random", "Random"),
        ("hash", "Hash"),
        ("fallback", "Fallback")
    )
    ROUTER_CHOICES = (
        ("req.url", "Path"),
        ("req.http.host", "Domain"),
    )
    HASHING_POLICY_CHOICES = (
        ("req.http.cookie", "Cookie"),
        ("req.url", "Url")
    )
    PROTOCOL_CHOICES = (
        ("http", "HTTP"),
        ("https", "HTTPS"),
        ("both", "BOTH"),
    )
    name = models.CharField(max_length=54, unique=True, validators=[name_validator])
    service = models.CharField(max_length=128, default="")
    service_mesh_label = models.CharField(max_length=128, default="")
    service_tag = models.CharField(max_length=128, default="", blank=True)
    cluster = models.ManyToManyField(LogicalCluster)
    history = HistoricalRecords(m2m_fields=[cluster])
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    protocol = models.CharField(max_length=5, choices=PROTOCOL_CHOICES, default="both")
    hashing_policy = models.CharField(
        max_length=20,
        default="req.url",
        choices=HASHING_POLICY_CHOICES,
        help_text="<i>Hashing policy only respected in Varnish v4 clusters. Hash mode must be selected.</i>"
    )
    router = models.CharField(
        max_length=20,
        default="req.url",
        choices=ROUTER_CHOICES
    )
    route_expression = models.CharField(
        max_length=512,
        verbose_name="Path or domain regex"
    )
    active_active = models.BooleanField(
        "DC aware fallback",
        default=True,
        help_text="<i>If no backends in primary DC available, use backends from other DC(s)</i>"
    )
    probe = models.ForeignKey(Probe, on_delete=models.PROTECT)
    enabled = models.BooleanField(default=True)
    remove_path = models.BooleanField(default=False)
    time_profile = models.ForeignKey(TimeProfile, on_delete=models.PROTECT)
    virtual = models.BooleanField(
        default=False,
        help_text="<i>Virtual director will not be available in routes</i>",
    )
    reachable_via_service_mesh = models.BooleanField(
        default=False,
        help_text="<i>Pass traffic to backends via service mesh if varnish cluster supports it</i>",
    )

    def mode_constructor(self):
        if self.mode == "round-robin":
            return "round_robin()"
        elif self.mode == "random":
            return "random()"
        elif self.mode == "hash":
            return "hash()"
        elif self.mode == "fallback":
            return "fallback()"

    def get_clusters(self):
        return self.cluster.all()

    def __str__(self):
        return self.name


class Backend(models.Model):
    history = HistoricalRecords()
    address = models.GenericIPAddressField(protocol="IPv4")
    port = models.PositiveIntegerField(
        default="80",
        validators=[MinValueValidator(1), MaxValueValidator(65535)]
    )
    weight = models.PositiveIntegerField(
        default="1",
        choices=[(x, x) for x in range(0, 101)]
    )
    dc = models.ForeignKey(Dc, on_delete=models.PROTECT)
    max_connections = models.PositiveIntegerField(
        default="5",
        choices=[(x, x) for x in range(1, 101)]
    )
    connect_timeout = models.DecimalField(
        default=0.30,
        decimal_places=2,
        max_digits=4,
        verbose_name="Connect timeout (s)",
        validators=[MinValueValidator(0.1), MaxValueValidator(1.0)]
    )
    first_byte_timeout = models.DecimalField(
        default=5.00,
        decimal_places=2,
        max_digits=5,
        verbose_name="First byte timeout (s)",
        validators=[MinValueValidator(0.1), MaxValueValidator(80.0)]
    )
    between_bytes_timeout = models.DecimalField(
        default=1.00,
        decimal_places=2,
        max_digits=5,
        verbose_name="Between bytes timeout (s)",
        validators=[MinValueValidator(0.1), MaxValueValidator(80.0)]
    )
    director = models.ForeignKey(
        Director,
        related_name="backends",
        on_delete=models.PROTECT
    )
    enabled = models.BooleanField(default=True)
    tags = TaggableManager(blank=True)
    inherit_time_profile = models.BooleanField(default=False)

    def __str__(self):
        return make_backend_name(self)

    def get_affected_clusters(self):
        if self.director.reachable_via_service_mesh:
            return self.director.cluster.filter(service_mesh_routing=False)
        return self.director.cluster.all()

    class Meta:
        unique_together = (("address", "port", "director"),)


class ReloadTask(object):
    def __init__(self, pk=None, status=None, info=None):
        self.pk = pk
        self.status = status
        self.info = info

    def __eq__(self, other):
        return hasattr(other, "__dict__") and self.__dict__ == other.__dict__

    def __repr__(self):
        return "{}".format(self.__dict__)
