# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from vaas.cluster.models import LogicalCluster
from vaas.manager.models import Director


class Route(models.Model):
    condition = models.CharField(max_length=512)
    priority = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(500)])
    clusters = models.ManyToManyField(LogicalCluster)
    director = models.ForeignKey(Director, on_delete=models.PROTECT)
    action = models.CharField(max_length=20)

    def get_clusters(self):
        return self.clusters.all()

    def __str__(self):
        name = "(Priority: %s) if (%s) then %s for %s" % (
            self.priority, self.condition, self.action, str(self.director))
        return name


class PositiveUrl(models.Model):
    url = models.URLField()
    route = models.ForeignKey(
        'Route', on_delete=models.CASCADE, related_name='positive_urls', related_query_name='positive_url'
    )


class RoutesTestTask(object):
    def __init__(self, pk=None, status=None, info=None):
        self.pk = pk
        self.status = status
        self.info = info

    def __eq__(self, other):
        return hasattr(other, '__dict__') and self.__dict__ == other.__dict__

    def __repr__(self):
        return '{}'.format(self.__dict__)


class DictEqual(object):
    def __repr__(self):
        return '{}'.format(self.__dict__)

    def __eq__(self, other):
        return hasattr(other, '__dict__') and self.__dict__ == other.__dict__


class Left(DictEqual):
    def __init__(self, left, name):
        self.pk = left
        self.left = left
        self.name = name


class Operator(DictEqual):
    def __init__(self, operator, name):
        self.pk = operator
        self.operator = operator
        self.name = name


class Action(DictEqual):
    def __init__(self, action, name):
        self.pk = action
        self.action = action
        self.name = name


class RouteConfiguration(DictEqual):
    def __init__(self, lefts, operators, actions):
        self.pk = 'configuration'
        self.lefts = lefts
        self.operators = operators
        self.actions = actions


def provide_route_configuration():
    return RouteConfiguration(
        [Left(left=k, name=v) for k, v in settings.ROUTES_LEFT_CONDITIONS.items()],
        [
            Operator(operator='==', name='exact'),
            Operator(operator='!=', name='is different'),
            Operator(operator='~', name='match'),
        ],
        [
            Action(action='pass', name='pass route directly'),
        ],
    )


class Named(DictEqual):
    def __init__(self, id, name):
        self.id = id
        self.name = name


class Assertion(DictEqual):
    def __init__(self, route, director):
        self.route = route
        self.director = director


class ValidationResult(DictEqual):
    def __init__(self, url, result, expected, current, error_message):
        self.url = url
        self.result = result
        self.expected = expected
        self.current = current
        self.error_message = error_message


class ValidationReport(object):
    def __init__(self, validation_results, status):
        self.validation_results = validation_results
        self.status = status
