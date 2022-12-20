# -*- coding: utf-8 -*-
import json

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from simple_history.models import HistoricalRecords
from tastypie import fields

from vaas.validators import vcl_variable_validator, vcl_variable_key_validator, \
    vcl_template_comment_validator, name_validator, dc_symbol_validator


class LogicalCluster(models.Model):
    """Model representing a cluster of varnish servers"""
    name = models.CharField(max_length=100, validators=[name_validator], unique=True)
    directors = fields.ToManyField('vaas.manager.api.DirectorResource', 'directors')
    reload_timestamp = models.DateTimeField(default=timezone.now)
    error_timestamp = models.DateTimeField(default=timezone.now)
    last_error_info = models.CharField(max_length=400, null=True, blank=True)
    current_vcl_versions = models.CharField(max_length=400, default='[]')
    labels_list = models.CharField(max_length=500, default='[]')
    partial_reload = models.BooleanField(default=False)
    service_mesh_routing = models.BooleanField(default=False)
    _current_vcls = None
    _labels = None

    @property
    def current_vcls(self):
        return self._get_parsed_field(self._current_vcls, self.current_vcl_versions)

    @current_vcls.setter
    def current_vcls(self, versions):
        self._current_vcls, self.current_vcl_versions = self._prepare_set_and_json(versions)

    @property
    def labels(self):
        return self._get_parsed_field(self._labels, self.labels_list)

    @labels.setter
    def labels(self, labels):
        self._labels, self.labels_list = self._prepare_set_and_json(labels)

    def _get_parsed_field(self, field, values):
        if field is None:
            try:
                field = set(json.loads(values))
            except:  # noqa
                field = set()
        return field

    def _prepare_set_and_json(self, field):
        if isinstance(field, set):
            field = list(field)
        if isinstance(field, list):
            return set(field), json.dumps(field)
        return None, None

    def __str__(self) -> str:
        return "{} ({})".format(self.name, self.varnish_count())

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        else:
            return False

    def __hash__(self):
        return hash(self.name)

    def varnish_count(self):
        return self.varnishserver_set.count()


class Dc(models.Model):
    name = models.CharField(max_length=50)
    symbol = models.CharField(
        max_length=25, unique=True, validators=[dc_symbol_validator, ]
    )

    @property
    def normalized_symbol(self):
        return self.symbol.replace("-", "_")

    def __str__(self) -> str:
        return self.symbol

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude)
        if exclude is None:
            exclude = []
        if 'symbol' not in exclude:
            for dc in Dc.objects.exclude(id=self.id):
                if dc.normalized_symbol == self.normalized_symbol:
                    raise ValidationError(
                        message=_("%(model_name)s with this %(field_labels)s already exists."),
                        code='unique_together',
                        params={
                            'model_name': 'Dc',
                            'field_labels': 'symbol'
                        },
                    )


class DomainMapping(models.Model):
    TYPE_CHOICES = (
        ('static', 'Static'),
        ('dynamic', 'Dynamic')
    )
    domain = models.CharField(max_length=128, unique=True)
    mapping = models.CharField(max_length=128)
    type = models.CharField(max_length=7, choices=TYPE_CHOICES, default='static')
    clusters = models.ManyToManyField(LogicalCluster)

    def __str__(self) -> str:
        return f'{self.domain}'


class VclTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True, validators=[name_validator])
    content = models.TextField()
    version = models.CharField(max_length=3, choices=(('4.0', 'Vcl 4.0'),), default='4.0')
    comment = models.CharField(max_length=64, validators=[vcl_template_comment_validator])
    history = HistoricalRecords()

    def __str__(self) -> str:
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

    def __str__(self) -> str:
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
        ('EMPTY_DIRECTOR_SYNTH', 'VCL/EMPTY_DIRECTOR_SYNTH'),
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
    key = models.CharField(max_length=100, validators=[vcl_variable_key_validator])
    value = models.CharField(max_length=254)
    cluster = models.ForeignKey(LogicalCluster, on_delete=models.DO_NOTHING)

    def __str__(self) -> str:
        return "{}: {}".format(self.key, self.value)

    class Meta:
        unique_together = (('key', 'cluster'), )
