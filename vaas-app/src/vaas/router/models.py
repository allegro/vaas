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
    clusters = models.ManyToManyField(LogicalCluster)
    director = models.ForeignKey(Director, on_delete=models.PROTECT)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    def __str__(self):
        name = "(Priority: %s) if (req.url ~ %s) then %s for %s" % (
            self.priority, self.condition, self.action, str(self.director))
        return name
