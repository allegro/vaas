# -*- coding: utf-8 -*-

import logging
import time

from django.utils import timezone
from concurrent.futures import ThreadPoolExecutor

from vaas.settings.celery import app
from django.conf import settings

from vaas.api.client import VarnishApi
from vaas.cluster.models import VarnishServer, LogicalCluster
from vaas.vcl.loader import VclLoader, VclStatus
from vaas.vcl.renderer import VclRenderer, VclRendererInput, init_processing, collect_processing
from vaas.cluster.exceptions import VclLoadException
from statsd.defaults.django import statsd
from datetime import datetime


def make_parallel_loader(max_workers=settings.VAAS_LOADER_MAX_WORKERS,
                         partial=settings.VAAS_LOADER_PARTIAL_RELOAD):
    if partial:
        return PartialParallelLoader(max_workers)
    else:
        return ParallelLoader(max_workers)


@app.task(bind=True, soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT_SECONDS)
def load_vcl_task(self, emmit_time, cluster_ids):
    emmit_time_aware = timezone.make_aware(datetime.strptime(emmit_time, "%Y-%m-%dT%H:%M:%S.%fZ"),
                                           timezone=timezone.utc)
    if settings.STATSD_ENABLE:
        queue_time_from_order_to_execute_task = timezone.now() - emmit_time_aware
        statsd.timing('queue_time_from_order_to_execute_task', queue_time_from_order_to_execute_task)

    start_processing_time = timezone.now()
    clusters = LogicalCluster.objects.filter(
        pk__in=cluster_ids, reload_timestamp__lte=emmit_time
    ).prefetch_related('varnishserver_set')
    if len(clusters) > 0:
        varnish_cluster_load_vcl = VarnishCluster().load_vcl(start_processing_time, clusters)
        if settings.STATSD_ENABLE:
            statsd.gauge('events_with_change', 1)
            total_time_of_processing_vcl_task_with_change = timezone.now() - emmit_time_aware
            statsd.timing('total_time_of_processing_vcl_task_with_change',
                          total_time_of_processing_vcl_task_with_change)
        return varnish_cluster_load_vcl

    if settings.STATSD_ENABLE:
        statsd.gauge('events_without_change', 1)
        total_time_of_processing_vcl_task_without_change = timezone.now() - emmit_time_aware
        statsd.timing('total_time_of_processing_vcl_task_without_change',
                      total_time_of_processing_vcl_task_without_change)
    return True


class VarnishCluster(object):

    def __init__(self, timeout=1):
        self.servers = VarnishServer.objects.exclude(status='disabled').prefetch_related('dc', 'template')
        self.logger = logging.getLogger('vaas')
        self.timeout = timeout
        self.renderer_max_workers = settings.VAAS_RENDERER_MAX_WORKERS
        self.loader_max_workers = settings.VAAS_LOADER_MAX_WORKERS

    def get_vcl_content(self, varnish_server_pk):
        return VarnishApiProvider().get_api(VarnishServer.objects.get(pk=varnish_server_pk)).vcl_content_active()

    def load_vcl(self, start_processing_time, clusters):
        processing_stats = init_processing()
        servers = ServerExtractor().extract_servers_by_clusters(clusters)
        vcl_list = ParallelRenderer(self.renderer_max_workers).render_vcl_for_servers(
            start_processing_time.strftime("%Y%m%d_%H_%M_%S"), servers
        )
        parallel_loader = make_parallel_loader(self.loader_max_workers)

        try:
            loaded_vcl_list = parallel_loader.load_vcl_list(vcl_list)
            for cluster in clusters:
                current_vcls = {vcl.version for server, vcl in vcl_list if server.cluster == cluster}
                cluster.reload_timestamp = start_processing_time
                cluster.current_vcls.set(*current_vcls, clear=True)
                cluster.save()
        except VclLoadException as e:
            self.logger.error('Loading error: {} - rendered vcl-s not used'.format(e))
            for cluster in clusters:
                cluster.error_timestamp = start_processing_time
                cluster.last_error_info = str(e)[:400]
                cluster.save()
            raise e
        else:
            return parallel_loader.use_vcl_list(start_processing_time, loaded_vcl_list)
        finally:
            for phase, processing in processing_stats.items():
                self.logger.info(
                    "vcl reload phase {}; calls: {}. time: {}".format(phase, processing['calls'], processing['time'])
                )


class VarnishApiProvider(object):

    def get_api(self, varnish_server, timeout=1):
        try:
            return VarnishApi([varnish_server.ip, varnish_server.port, float(timeout)], str(varnish_server.secret))
        except Exception:
            raise VclLoadException(
                "Cannot connect to varnish server ip: %s, port: %s, cluster: %s" % (
                    varnish_server.ip, varnish_server.port, varnish_server.cluster.name
                )
            )

    def get_varnish_api(self, timeout=1):
        for server in ServerExtractor().servers:
            yield self.get_api(server, timeout)

    def get_connected_varnish_api(self, timeout=1):
        for server in ServerExtractor().servers:
            try:
                varnish_api = self.get_api(server, timeout)
                yield varnish_api
            except VclLoadException:
                continue


class ServerExtractor(object):

    def __init__(self):
        self.logger = logging.getLogger('vaas')
        self.servers = VarnishServer.objects.exclude(status='disabled').prefetch_related('dc', 'template')

    @collect_processing
    def extract_servers_by_clusters(self, clusters):
        cluster_ids = [cluster.id for cluster in clusters]
        self.logger.debug("Names of cluster used by load_vcl: %s" % ([cluster.name for cluster in clusters]))
        extracted_servers = [server for server in self.servers if server.cluster_id in cluster_ids]
        self.logger.debug("Names of servers used by load_vcl: %s" % ([server.hostname for server in extracted_servers]))

        return extracted_servers


class ParallelExecutor(object):

    def __init__(self, max_workers):
        self.logger = logging.getLogger('vaas')
        self.max_workers = max_workers


class ParallelRenderer(ParallelExecutor):

    def __init__(self, max_workers=10):
        ParallelExecutor.__init__(self, max_workers)
        self.renderer = VclRenderer()

    @collect_processing
    def render_vcl_for_servers(self, vcl_name, servers):
        vcl_list = []

        start = time.time()
        render_input = VclRendererInput()
        self.logger.debug("vcl's prepare input data: %f" % (time.time() - start))
        start = time.time()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_results = []
            for server in servers:
                future_results.append(
                    tuple([server, executor.submit(self.renderer.render, server, vcl_name, render_input)])
                )
            for server, future_result in future_results:
                vcl_list.append(tuple([server, future_result.result()]))

        self.logger.debug("vcl's render time: %f" % (time.time() - start))
        return vcl_list


class ParallelLoader(ParallelExecutor):

    def __init__(self, max_workers=10):
        ParallelExecutor.__init__(self, max_workers)
        self.api_provider = VarnishApiProvider()

    @collect_processing
    def _append_vcl(self, vcl, server, future_results, executor):
        """Suppress exceptions if cannot load vcl for server in maintenance state"""
        loader = VclLoader(self.api_provider.get_api(server), server.status == 'maintenance')
        future_results.append(tuple([vcl, loader, server, executor.submit(loader.load_new_vcl, vcl)]))

    @collect_processing
    def _format_vcl_list(self, to_use, aggregated_result):
        if not aggregated_result:
            raise VclLoadException

        return to_use

    @collect_processing
    def _discard_unused_vcls(self, server, loader, executor, discard_results):
        discard_results.append(tuple([server, executor.submit(loader.discard_unused_vcls)]))
        return discard_results

    @collect_processing
    def load_vcl_list(self, vcl_list):
        to_use = []
        start = time.time()
        aggregated_result = True
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_results = []
            try:
                for server, vcl in vcl_list:
                    self._append_vcl(vcl, server, future_results, executor)

                for vcl, loader, server, future_result in future_results:
                    result = future_result.result()
                    """Suppress error if cannot load vcl for server in maintenance state"""
                    if result == VclStatus.ERROR and server.status == 'active':
                        aggregated_result = False
                    if result == VclStatus.OK:
                        to_use.append(tuple([vcl, loader, server]))
            except VclLoadException as e:
                discard_results = []
                for vcl, loader, server, future_result in future_results:
                    self._discard_unused_vcls(server, loader, executor, discard_results)
                for server, status in discard_results:
                    if status.result() is VclStatus.ERROR:
                        self.logger.debug("ERROR while discard vcl's on %s" % (server))

                raise e

        self.logger.debug("vcl's loaded: %f" % (time.time() - start))

        return self._format_vcl_list(to_use, aggregated_result)

    @collect_processing
    def use_vcl_list(self, vcl_name, vcl_loaded_list):
        self.logger.info("Call use vcl for %d servers" % len(vcl_loaded_list))
        result = True
        start = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_results = []
            discard_results = []
            for vcl, loader, server in vcl_loaded_list:
                future_results.append(tuple([vcl_name, server, executor.submit(loader.use_vcl, vcl)]))
            for vcl_name, server, future_result in future_results:
                single_result = future_result.result()
                """Suppress error if cannot use vcl for server in maintenance state"""
                if single_result == VclStatus.ERROR and server.status == 'active':
                    result = False
                    self.logger.error("Cannot use vcl [%s] for server %s", vcl_name, server.ip)
            for vcl, loader, server in vcl_loaded_list:
                self._discard_unused_vcls(server, loader, executor, discard_results)
            for server, status in discard_results:
                if status.result() is VclStatus.ERROR:
                    self.logger.debug("ERROR while discard vcl's on %s" % (server))

        self.logger.debug("vcl's used: %f" % (time.time() - start))

        return result


class PartialParallelLoader(ParallelLoader):
    def _format_vcl_list(self, to_use, aggregated_result):
        return to_use

    def _append_vcl(self, vcl, server, future_results, executor):
        try:
            super(PartialParallelLoader, self)._append_vcl(vcl, server, future_results, executor)
        except VclLoadException:
            pass
