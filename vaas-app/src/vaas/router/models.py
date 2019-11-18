# -*- coding: utf-8 -*-

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from vaas.cluster.models import LogicalCluster
from vaas.manager.models import Director

class Route(models.Model):
    ACTION_CHOICES = (
        ('pass', 'pass route directly'),
    )
    condition = models.CharField(max_length=512)
    priority = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    #cluster = models.ForeignKey(LogicalCluster, on_delete=models.PROTECT)
    # clusters = models.ManyToManyField(LogicalCluster, through='RouteClusters')
    clusters = models.ManyToManyField(LogicalCluster)
    director = models.ForeignKey(Director, on_delete=models.PROTECT)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    def __str__(self):
        name = "(Priority: %s) if (req.url ~ %s) then %s for %s" % (
            self.priority, self.condition, self.action, str(self.director))
        return name

    # class Meta:
    #     # unique_together = (('priority', 'director', 'clusters__cluster_id', 'clusters__route_id'),)
    #     # unique_together = (('priority', 'director'),)

# class RouteClusters(models.Model):
#     route_id = models.ForeignKey(Route, on_delete=models.PROTECT)
#     cluster_id = models.ForeignKey(LogicalCluster, on_delete=models.PROTECT)

#     class Meta:
#         unique_together = (('route_id', 'cluster_id'),)
