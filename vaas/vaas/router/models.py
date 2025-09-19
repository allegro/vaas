# -*- coding: utf-8 -*-
import uuid
from typing import Dict
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from vaas.cluster.models import DomainMapping, LogicalCluster
from vaas.manager.models import Director
from typing import Optional


class RedirectAssertion(models.Model):
    given_url = models.URLField()
    expected_location = models.CharField(max_length=512)
    redirect = models.ForeignKey(
        'Redirect', on_delete=models.CASCADE, related_name='assertions',
        related_query_name='redirect_assertions')


class Redirect(models.Model):
    class ResponseStatusCode(models.IntegerChoices):
        MOVE_PERMANENTLY = 301
        FOUND = 302
        TEMPORARY_REDIRECT = 307

    src_domain = models.ForeignKey(DomainMapping, on_delete=models.PROTECT)
    condition = models.CharField(max_length=512)
    rewrite_groups = models.CharField(max_length=512, default='', blank=True)
    destination = models.CharField(max_length=512)
    action = models.IntegerField(choices=ResponseStatusCode.choices, default=301)
    priority = models.PositiveIntegerField()
    preserve_query_params = models.BooleanField(default=True)
    required_custom_header = models.BooleanField(default=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def get_hashed_assertions_pks(self) -> Dict[int, int]:
        return {hash((a.given_url, a.expected_location)): a.pk for a in self.assertions.all()}

    @property
    def final_condition(self):
        if self.required_custom_header:
            return f'{self.condition} && req.http.{settings.REDIRECT_CUSTOM_HEADER}'
        return self.condition


class Route(models.Model):
    condition = models.CharField(max_length=512)
    priority = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(500)])
    clusters = models.ManyToManyField(LogicalCluster)
    director = models.ForeignKey(Director, on_delete=models.PROTECT)
    action = models.CharField(max_length=20)
    clusters_in_sync = models.BooleanField(default=False)

    def get_clusters(self):
        if self.clusters_in_sync:
            return self.director.cluster.all()
        return self.clusters.all()

    def __str__(self) -> str:
        name = "(Priority: %s) if (%s) then %s for %s" % (
            self.priority, self.condition, self.action, str(self.director))
        return name


class PositiveUrl(models.Model):
    url = models.URLField()
    route = models.ForeignKey(
        'Route', on_delete=models.CASCADE, related_name='positive_urls', related_query_name='positive_url'
    )


class RoutesTestTask(object):
    def __init__(self, pk: Optional[str] = None, status: Optional[str] = None, info: Optional[str] = None):
        self.pk = pk
        self.status = status
        self.info = info

    def __eq__(self, other: object):
        return hasattr(other, '__dict__') and self.__dict__ == other.__dict__

    def __repr__(self):
        return '{}'.format(self.__dict__)


class DictEqual(object):
    def __repr__(self):
        return '{}'.format(self.__dict__)

    def __eq__(self, other: object):
        return hasattr(other, '__dict__') and self.__dict__ == other.__dict__


class Left(DictEqual):
    def __init__(self, left: str, name: str):
        self.pk = left
        self.left = left
        self.name = name


class Operator(DictEqual):
    def __init__(self, operator: str, name: str):
        self.pk: str = operator
        self.operator = operator
        self.name = name


class Action(DictEqual):
    def __init__(self, action: str, name: str):
        self.pk = action
        self.action = action
        self.name = name


class RouteConfiguration(DictEqual):
    def __init__(self, lefts: list[Left], operators: list[Operator], actions: list[Action]):
        self.pk = 'configuration'
        self.lefts = lefts
        self.operators = operators
        self.actions = actions


def provide_route_configuration() -> RouteConfiguration:
    return RouteConfiguration(
        [Left(left=k, name=v) for k, v in settings.ROUTES_LEFT_CONDITIONS.items()],
        [
            Operator(operator='==', name='exact'),
            Operator(operator='!=', name='is different'),
            Operator(operator='>', name='greater'),
            Operator(operator='<', name='less'),
            Operator(operator='~', name='match'),
            Operator(operator='!~', name='not match'),
        ],
        [
            Action(action='pass', name='pass route directly'),
            Action(action='pipe', name='bypass the cache')
        ],
    )


class Named(DictEqual):
    def __init__(self, id, name):
        self.id = id
        self.name = name


class RouteContext(DictEqual):
    def __init__(self, route, director):
        self.route = route
        self.director = director


class RedirectContext(DictEqual):
    def __init__(self, redirect, location):
        self.redirect = redirect
        self.location = location


class ValidationResult(DictEqual):
    def __init__(self, url, result, expected, current, error_message):
        self.url = url
        self.result = result
        self.expected = expected
        self.current = current
        self.error_message = error_message


class ValidationReport(object):
    def __init__(self, validation_results, validation_status):
        self.validation_results = validation_results
        self.validation_status = validation_status
        self.task_status = 'Unknown'
