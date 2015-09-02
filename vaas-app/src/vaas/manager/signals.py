# -*- coding: utf-8 -*-

import logging

from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.conf import settings

from vaas.external.request import get_current_request
from vaas.cluster.models import VarnishServer
from vaas.manager.middleware import VclRefreshState
from vaas.manager.models import Director, Backend, Probe


def switch_state_and_reload(queryset, enabled):
    logger = logging.getLogger('vaas')
    logger.debug("switch_state_and_reload(): %s" % str(queryset))
    # A list with 'LogicalCluster' objects to refresh.
    clusters_to_refresh = []
    for query in queryset:
        logger.debug("ITERATOR: %s, TYPE: %s" % (str(query), type(query)))
        if isinstance(query, Director):
            logger.debug("query is Director %s" % str(query))
            for cluster in query.cluster.all():
                logger.debug("cluster - type: %s" % str(type(cluster)))
                if cluster not in clusters_to_refresh:
                    clusters_to_refresh.append(cluster)
        elif isinstance(query, Backend):
            logger.debug("query is Backend %s" % str(query))
            for cluster in query.director.cluster.all():
                if cluster not in clusters_to_refresh:
                    clusters_to_refresh.append(cluster)
        elif isinstance(query, Probe):
            logger.debug("TODO - Probe")
        else:
            cluster = query.cluster
            logger.debug("cluster - type: %s" % str(type(cluster)))
            if cluster not in clusters_to_refresh:
                clusters_to_refresh.append(cluster)

    logger.debug("clusters to refresh: %s" % (str(clusters_to_refresh)))
    queryset.update(enabled=enabled)
    regenerate_and_reload_vcl(clusters_to_refresh)


def regenerate_and_reload_vcl(clusters):
    logger = logging.getLogger('vaas')
    logger.debug("regenerate_and_reload_vcl(): %s" % str(clusters))
    request = get_current_request()
    if request is not None:
        if 'action' in request.POST.keys():
            logger.debug("ACTION: %s" % request.POST['action'])
        if '_selected_action' in request.POST.keys():
            logger.debug("SELECTED: %s" % request.POST['_selected_action'])
        logger.debug("PATH: %s" % request.path)

        VclRefreshState.set_refresh(request.id, clusters)


@receiver(post_save)
@receiver(post_delete)
def vcl_update(sender, **kwargs):
    logger = logging.getLogger('vaas')

    if sender not in [Probe, Backend, Director, VarnishServer]:
        return

    if settings.SIGNALS != 'on':
        return

    instance = kwargs['instance']
    logger.debug("sender: " + str(sender))
    logger.debug("instance: " + str(instance))

    # list of clusters to refresh
    clusters_to_refresh = []

    # Probe
    if sender is Probe:
        for director in Director.objects.all():
            if director.probe.id == instance.id:
                for cluster in director.cluster.all():
                    logger.debug("vcl_update(): %s" % str(cluster))
                    if cluster not in clusters_to_refresh:
                        clusters_to_refresh.append(cluster)
    # Backend
    elif sender is Backend:
        for cluster in instance.director.cluster.all():
            logger.debug("vcl_update(): %s" % str(cluster))
            if cluster not in clusters_to_refresh:
                clusters_to_refresh.append(cluster)
    # Director
    elif sender is Director:
        for cluster in instance.cluster.all():
            logger.debug("vcl_update(): %s" % str(cluster))
            if cluster not in clusters_to_refresh:
                clusters_to_refresh.append(cluster)
    # VarnishServer
    elif sender is VarnishServer:
        cluster = instance.cluster
        logger.debug("vcl_update(): %s" % str(cluster))
        clusters_to_refresh.append(cluster)

    regenerate_and_reload_vcl(clusters_to_refresh)
