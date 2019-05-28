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
    priority = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    cluster = models.ForeignKey(LogicalCluster, on_delete=models.PROTECT)
    director = models.ForeignKey(Director, on_delete=models.PROTECT)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    class Meta:
        unique_together = (('priority', 'cluster', 'director'),)
