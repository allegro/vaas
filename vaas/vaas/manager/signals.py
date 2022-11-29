# -*- coding: utf-8 -*-

import logging

from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete, m2m_changed
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from vaas.external.audit import audit_bulk_operations, Auditable
from vaas.external.request import get_current_request
from vaas.cluster.models import VarnishServer, VclTemplate, VclTemplateBlock, VclVariable
from vaas.router.models import Redirect, Route
from vaas.manager.middleware import VclRefreshState
from vaas.manager.models import Director, Backend, Probe, TimeProfile


def switch_state_and_reload(queryset, enabled):
    logger = logging.getLogger(__name__)
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
            for cluster in query.get_affected_clusters():
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

    if audit_bulk_operations:
        old_values = list(queryset.all())
    queryset.update(enabled=enabled)
    if audit_bulk_operations:
        Auditable.bulk_update(sender=queryset.model, old_values=old_values)
    regenerate_and_reload_vcl(clusters_to_refresh)


def switch_status_and_reload(queryset, status):
    logger = logging.getLogger(__name__)
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
    logger = logging.getLogger(__name__)
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
    logger = logging.getLogger(__name__)
    for tag in backend.tags.all():
        if tag.taggit_taggeditem_items.count() < 2:
            tag_name = str(tag.name)
            tag.delete()
            logger.debug("delete_unused_tags(): %s" % tag_name)


@receiver(post_save)
@receiver(post_delete)
def vcl_update(sender, **kwargs):
    logger = logging.getLogger(__name__)

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
        for cluster in instance.get_affected_clusters():
            logger.debug("vcl_update(): %s" % str(cluster))
            if cluster not in clusters_to_refresh:
                clusters_to_refresh.append(cluster)
    # Director
    elif sender is Director:
        if not is_only_cluster_update(instance):
            for cluster in instance.cluster.all():
                logger.debug("vcl_update(): %s", str(cluster))
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
    elif sender is TimeProfile:
        for director in Director.objects.all():
            if director.time_profile.id == instance.id:
                for cluster in director.cluster.all():
                    logger.debug("vcl_update(): %s" % str(cluster))
                    if cluster not in clusters_to_refresh:
                        clusters_to_refresh.append(cluster)
    # VclVariable
    elif sender is VclVariable:
        for varnish_server in VarnishServer.objects.all():
            if varnish_server.cluster == instance.cluster:
                logger.debug("vcl_update(): %s" % str(varnish_server.cluster))
                clusters_to_refresh.append(varnish_server.cluster)
    # Route
    elif sender is Route:
        if instance.clusters_in_sync:
            instance_clusters = instance.director.cluster.all()
        else:
            instance_clusters = instance.clusters.all()
        for instance_cluster in instance_clusters:
            if instance_cluster not in clusters_to_refresh:
                logger.debug("vcl_update(): %s" % str(instance_cluster))
                clusters_to_refresh.append(instance_cluster)

    # Rewrite
    elif sender is Redirect:
        # TODO: Handle behaviour from update, delete create rewrites
        logger.debug("Rewrite vcl_update(): %s" % str(instance))

    regenerate_and_reload_vcl(clusters_to_refresh)
    if sender is Director:
        reset_refreshed_clusters(instance)


@receiver(pre_delete)
def clean_up_tags(sender, **kwargs):
    instance = kwargs['instance']
    if sender is Backend:
        delete_unused_tags(instance)

    if sender in [Route, Director]:
        kwargs['action'] = 'pre_delete'
        model_update(**kwargs)


@receiver(pre_save)
def pre_save_vcl_update(sender, **kwargs):
    logger = logging.getLogger(__name__)

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

    # VclVariable
    if sender is VclVariable:
        try:
            old_instance = VclVariable.objects.get(pk=instance.pk)
            for varnish_server in VarnishServer.objects.all():
                if varnish_server.cluster == old_instance.cluster:
                    logger.debug("vcl_update(): %s" % str(varnish_server.cluster))
                    clusters_to_refresh.append(varnish_server.cluster)
        except ObjectDoesNotExist:
            pass

    # Backend
    elif sender is Backend:
        try:
            old_instance = Backend.objects.get(pk=instance.pk)
            for cluster in old_instance.director.cluster.all():
                if cluster not in clusters_to_refresh:
                    logger.debug("vcl_update(): %s" % str(cluster))
                    clusters_to_refresh.append(cluster)
        except ObjectDoesNotExist:
            pass

    # Route
    elif sender is Route:
        try:
            clusters = []
            old_instance = Route.objects.get(pk=instance.pk)
            if not old_instance.clusters_in_sync and instance.clusters_in_sync:
                clusters = old_instance.clusters.all()
            elif old_instance.clusters_in_sync and not instance.clusters_in_sync:
                clusters = old_instance.director.cluster.all()
            for cluster in clusters:
                if cluster not in clusters_to_refresh:
                    logger.debug("vcl_update(): %s" % str(cluster))
                    clusters_to_refresh.append(cluster)
        except ObjectDoesNotExist:
            pass

    regenerate_and_reload_vcl(clusters_to_refresh)


def model_update(**kwargs):
    logger = logging.getLogger(__name__)
    instance = kwargs['instance']
    action = kwargs['action']

    if action not in ['post_add', 'pre_remove', 'pre_clear', 'pre_delete']:
        return

    clusters_to_refresh = get_clusters_to_refresh(instance)
    logger.debug("[model_update(instance=%s, action=%s)] Clusters to refresh: %s",
                 instance, action, clusters_to_refresh)
    regenerate_and_reload_vcl(clusters_to_refresh)
    mark_cluster_as_refreshed(instance, clusters_to_refresh)


def get_clusters_to_refresh(instance):
    all_clusters = list(instance.get_clusters())
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


m2m_changed.connect(model_update, sender=Director.cluster.through)
m2m_changed.connect(model_update, sender=Route.clusters.through)
