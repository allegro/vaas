# -*- coding: utf-8 -*-

import logging

from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete, post_delete, m2m_changed
from django.conf import settings

from vaas.external.request import get_current_request
from vaas.cluster.models import VarnishServer, VclTemplate, VclTemplateBlock
from vaas.manager.middleware import VclRefreshState
from vaas.manager.models import Director, Backend, Probe, TimeProfile


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


def switch_status_and_reload(queryset, status):
    logger = logging.getLogger('vaas')
    logger.debug("switch_state_and_reload(): %s" % str(queryset))
    # A list with 'LogicalCluster' objects to refresh.
    clusters_to_refresh = []
    for query in queryset:
        cluster = query.cluster
        logger.debug("cluster - type: %s" % str(type(cluster)))
        if cluster not in clusters_to_refresh:
            clusters_to_refresh.append(cluster)

        logger.debug("clusters to refresh: %s" % (str(clusters_to_refresh)))
        queryset.update(status=status)
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


def delete_unused_tags(backend):
    logger = logging.getLogger('vaas')
    for tag in backend.tags.all():
        if tag.taggit_taggeditem_items.count() < 2:
            tag_name = str(tag.name)
            tag.delete()
            logger.debug("delete_unused_tags(): %s" % tag_name)


@receiver(post_save)
@receiver(post_delete)
def vcl_update(sender, **kwargs):
    logger = logging.getLogger('vaas')

    if sender is None:
        return

    if sender.__name__ not in settings.REFRESH_TRIGGERS_CLASS:
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
        if not is_only_cluster_update(instance):
            for cluster in instance.cluster.all():
                logger.debug("vcl_update(): %s" % str(cluster))
                if cluster not in clusters_to_refresh:
                    clusters_to_refresh.append(cluster)
    # VarnishServer
    elif sender is VarnishServer:
        cluster = instance.cluster
        logger.debug("vcl_update(): %s" % str(cluster))
        clusters_to_refresh.append(cluster)
    # VclTemplate
    elif sender is VclTemplate:
        for varnish in VarnishServer.objects.filter(template=instance):
            if varnish.cluster not in clusters_to_refresh:
                logger.debug("vcl_update(): %s" % str(varnish.cluster))
                clusters_to_refresh.append(varnish.cluster)
    # VclTemplateBlock
    elif sender is VclTemplateBlock:
        for varnish in VarnishServer.objects.filter(template=instance.template):
            if varnish.cluster not in clusters_to_refresh:
                logger.debug("vcl_update(): %s" % str(varnish.cluster))
                clusters_to_refresh.append(varnish.cluster)
    # TimeProfile
    if sender is TimeProfile:
        for director in Director.objects.all():
            if director.time_profile.id == instance.id:
                for cluster in director.cluster.all():
                    logger.debug("vcl_update(): %s" % str(cluster))
                    if cluster not in clusters_to_refresh:
                        clusters_to_refresh.append(cluster)

    regenerate_and_reload_vcl(clusters_to_refresh)
    if sender is Director:
        reset_refreshed_clusters(instance)


@receiver(pre_delete)
def clean_up_tags(sender, **kwargs):
    instance = kwargs['instance']
    if sender is Backend:
        delete_unused_tags(instance)


def director_update(**kwargs):
    logger = logging.getLogger('vaas')
    instance = kwargs['instance']
    action = kwargs['action']

    if action not in ['post_add', 'pre_remove', 'pre_clear']:
        return

    clusters_to_refresh = get_clusters_to_refresh(instance)
    logger.info("[director_update(instance={}, action={})] Clusters to refresh: {}"
                .format(instance, action, clusters_to_refresh))
    regenerate_and_reload_vcl(clusters_to_refresh)
    mark_cluster_as_refreshed(instance, clusters_to_refresh)


def get_clusters_to_refresh(instance):
    all_clusters = list(instance.cluster.all())
    try:
        new_clusters_set = set(instance.new_clusters)
        old_clusters_set = set(instance.old_clusters)
        diff_clusters_set = old_clusters_set.symmetric_difference(new_clusters_set)
        try:
            clusters_to_refresh_set = diff_clusters_set.difference(instance.refreshed_clusters)
        except AttributeError:
            clusters_to_refresh_set = diff_clusters_set
        return list(clusters_to_refresh_set.intersection(set(all_clusters)))
    except (AttributeError, TypeError):
        return all_clusters


def mark_cluster_as_refreshed(director, clusters):
    try:
        director.refreshed_clusters |= set(clusters)
    except AttributeError:
        director.refreshed_clusters = set(clusters)


def reset_refreshed_clusters(director):
    director.refreshed_clusters = set()


def is_only_cluster_update(instance):
    try:
        return set(instance.new_data.keys()) == {'cluster'}
    except AttributeError:
        return False


m2m_changed.connect(director_update, sender=Director.cluster.through)
