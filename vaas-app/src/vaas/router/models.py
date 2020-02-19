# -*- coding: utf-8 -*-

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from vaas.cluster.models import LogicalCluster
from vaas.manager.models import Director


class Route(models.Model):
    ACTION_CHOICES = (
        ('pass', 'pass route directly'),
    )
    condition = models.CharField(max_length=512)
    priority = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(500)])
    clusters = models.ManyToManyField(LogicalCluster)
    director = models.ForeignKey(Director, on_delete=models.PROTECT)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    def __str__(self):
        name = "(Priority: %s) if (%s) then %s for %s" % (
            self.priority, self.condition, self.action, str(self.director))
        return name


class Left(object):
    def __init__(self, left, name):
        self.pk = left
        self.left = left
        self.name = name


class Operator(object):
    def __init__(self, operator, name):
        self.pk = operator
        self.operator = operator
        self.name = name


class Action(object):
    def __init__(self, action, name):
        self.pk = action
        self.action = action
        self.name = name


class RouteConfiguration(object):
    def __init__(self, lefts, operators, actions):
        self.pk = 'configuration'
        self.lefts = lefts
        self.operators = operators
        self.actions = actions

    def __eq__(self, other):
        return hasattr(other, '__dict__') and self.__dict__ == other.__dict__

    def __repr__(self):
        return '{}'.format(self.__dict__)
