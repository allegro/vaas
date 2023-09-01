# -*- coding: utf-8 -*-

import logging
import time
from typing import List, Dict, Tuple

from django.utils import timezone
from concurrent.futures import ThreadPoolExecutor, Future

from vaas.settings.celery import app
from django.conf import settings

from vaas.api.client import VarnishApi, VarnishApiReadException
from vaas.cluster.exceptions import VclLoadException
from vaas.cluster.models import VarnishServer, LogicalCluster
from vaas.metrics.handler import metrics
from vaas.vcl.loader import VclLoader, VclStatus
from vaas.vcl.renderer import VclRenderer, VclRendererInput, init_processing, collect_processing, Vcl


@app.task(bind=True, soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT_SECONDS)
def load_vcl_task(self, emmit_time, cluster_ids):
    emmit_time_aware = time.perf_counter()
    metrics.time('queue_time_from_order_to_execute_task', time.perf_counter() - emmit_time_aware)

    start_processing_time = timezone.now()
    clusters = LogicalCluster.objects.filter(
        pk__in=cluster_ids, reload_timestamp__lte=emmit_time
    ).prefetch_related('varnishserver_set')
    if len(clusters) > 0:
        varnish_cluster_load_vcl = VarnishCluster().load_vcl(start_processing_time, clusters)
        metrics.counter('events_with_change')
        metrics.time('total_time_of_processing_vcl_task_with_change', time.perf_counter() - emmit_time_aware)
        return varnish_cluster_load_vcl

    metrics.counter('events_without_change')
    metrics.time('total_time_of_processing_vcl_task_without_change', time.perf_counter() - emmit_time_aware)

    return True


@app.task(bind=True, soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT_SECONDS)
def validate_vcl_command(self, vcl_id: int, content: str):
    servers = VarnishServer.objects.exclude(status='disabled').filter(
        template__pk=vcl_id).prefetch_related('dc', 'cluster')
    result = {
        'is_valid': True,
        'servers_num': len(servers),
    }
    if len(servers):
        vcl_name = f'validation_{timezone.now().strftime("%Y%m%d_%H_%M_%S")}'
        try:
            vcl_list = ParallelRenderer(settings.VAAS_RENDERER_MAX_WORKERS).render_vcl_for_servers(
                vcl_name, servers, content
            )
            parallel_loader = ParallelLoader(settings.VAAS_LOADER_MAX_WORKERS)
            parallel_loader.load_vcl_list(vcl_list, True)
        except Exception as e:  # noqa
            result['is_valid'] = False
            result['error'] = {
                'type': str(type(e)),
                'message': str(e)
            }
    return result


@app.task(bind=True, soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT_SECONDS)
def connect_command(self, varnish_ids: List[int]) -> Dict[int, str]:
    result = {}
    if len(varnish_ids) > 0:
        with ThreadPoolExecutor(max_workers=len(varnish_ids)) as executor:
            future_results = []
            for server in VarnishServer.objects.filter(pk__in=varnish_ids):
                future_results.append(
                    tuple([server, executor.submit(connect_status, server)])
                )
            for server, future_result in future_results:
                result[server.pk] = future_result.result()
    return result


def connect_status(server: VarnishServer) -> str:
    if server.status == 'active':
        try:
            return VarnishApiProvider().get_api(server).daemon_version()
        except VclLoadException:
            return 'error'
    return server.status


class VarnishCluster(object):

    def __init__(self, timeout=1):
        self.logger = logging.getLogger(__name__)
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
        parallel_loader = ParallelLoader(self.loader_max_workers)

        try:
            loaded_vcl_list = parallel_loader.load_vcl_list(vcl_list)
            self._update_vcl_versions(clusters, start_processing_time, vcl_list)
        except VclLoadException as e:
            self._handle_load_error(e, clusters, start_processing_time)
        else:
            result = parallel_loader.use_vcl_list(start_processing_time, loaded_vcl_list)
            if result is False:
                metrics.counter('successful_reload_vcl')
            else:
                metrics.counter('successful_reload_vcl')
            return result
        finally:
            for phase, processing in processing_stats.items():
                self.logger.info(
                    "vcl reload phase {}; calls: {}. time: {}".format(phase, processing['calls'], processing['time'])
                )
                if phase in ['render_vcl_for_servers', 'use_vcl_list', '_discard_unused_vcls', '_append_vcl',
                             'extract_servers_by_clusters', 'fetch_render_data']:
                    metrics.time(phase, processing['time'])

    @collect_processing
    def _update_vcl_versions(self, clusters, start_processing_time, vcl_list):
        for cluster in clusters:
            current_vcls = {vcl.version for server, vcl in vcl_list if server.cluster_id == cluster.id}
            cluster.reload_timestamp = start_processing_time
            cluster.current_vcls = current_vcls
            cluster.save()

    @collect_processing
    def _handle_load_error(self, e, clusters, start_processing_time):
        self.logger.error('Loading error: {} - rendered vcl-s not used'.format(e))
        metrics.counter('successful_reload_vcl')

        for cluster in clusters:
            cluster.error_timestamp = start_processing_time
            cluster.last_error_info = str(e)[:400]
            cluster.save()
        raise e


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


class ServerExtractor(object):

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.servers = VarnishServer.objects.exclude(status='disabled').prefetch_related('dc', 'template', 'cluster')

    @collect_processing
    def extract_servers_by_clusters(self, clusters):
        cluster_ids = [cluster.id for cluster in clusters]
        self.logger.debug("Names of cluster used by load_vcl: %s" % ([cluster.name for cluster in clusters]))
        extracted_servers = [server for server in self.servers if server.cluster_id in cluster_ids]
        self.logger.debug("Names of servers used by load_vcl: %s" % ([server.hostname for server in extracted_servers]))

        return extracted_servers


class ParallelExecutor(object):

    def __init__(self, max_workers):
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers


class ParallelRenderer(ParallelExecutor):

    def __init__(self, max_workers=10):
        ParallelExecutor.__init__(self, max_workers)
        self.renderer = VclRenderer()

    @collect_processing
    def render_vcl_for_servers(self, vcl_name, servers, content=None):
        vcl_list = []

        start = time.perf_counter()
        render_input = VclRendererInput()
        self.logger.debug("vcl's prepare input data: %f" % (time.perf_counter() - start))
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_results = []
            for server in servers:
                future_results.append(
                    tuple([server, executor.submit(self.renderer.render, server, vcl_name, render_input, content)])
                )
            for server, future_result in future_results:
                vcl_list.append(tuple([server, future_result.result()]))

        self.logger.debug("vcl's render time: %f" % (time.perf_counter() - start))
        return vcl_list


class ParallelLoader(ParallelExecutor):

    def __init__(self, max_workers=10):
        ParallelExecutor.__init__(self, max_workers)
        self.api_provider = VarnishApiProvider()

    @collect_processing
    def _append_vcl(self, vcl: Vcl, server: VarnishServer, future_results: List, executor: ThreadPoolExecutor) -> None:
        """Suppress exceptions if cannot load vcl for server in maintenance state"""
        try:
            loader = VclLoader(self.api_provider.get_api(server), server.status == 'maintenance')
            future_results.append(tuple([vcl, loader, server, executor.submit(loader.load_new_vcl, vcl)]))
        except VclLoadException as e:
            if server.cluster.partial_reload:
                return
            raise e

    @collect_processing
    def _format_vcl_list(
            self, to_use: List[Tuple[Vcl, VclLoader, VarnishServer]], aggregated_result: bool
    ) -> List[Tuple[Vcl, VclLoader, VarnishServer]]:
        if not aggregated_result:
            raise VclLoadException

        return to_use

    @collect_processing
    def _discard_unused_vcls(
            self,
            server: VarnishServer, loader: VclLoader, executor: ThreadPoolExecutor, discard_results: List[Tuple]
    ) -> List[Tuple]:
        discard_results.append(tuple([server, executor.submit(loader.discard_unused_vcls)]))
        return discard_results

    def _get_load_new_vcl_result(self, server: VarnishServer, result: Future[VclStatus]) -> VclStatus:
        try:
            return result.result()
        except VarnishApiReadException:
            if not server.cluster.partial_reload:
                raise VclLoadException
        return VclStatus.ERROR

    @collect_processing
    def load_vcl_list(
            self, vcl_list: List[Tuple[VarnishServer, Vcl]], force_discard: bool = False
    ) -> List[Tuple[Vcl, VclLoader, VarnishServer]]:
        to_use = []
        start = time.perf_counter()
        aggregated_result = True
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_results = []
            try:
                for server, vcl in vcl_list:
                    self._append_vcl(vcl, server, future_results, executor)
                for vcl, loader, server, future_result in future_results:
                    result = self._get_load_new_vcl_result(server, future_result)
                    """Suppress error if cannot load vcl for server in maintenance state"""
                    if result == VclStatus.ERROR and server.status == 'active' and not server.cluster.partial_reload:
                        aggregated_result = False
                    if result == VclStatus.OK:
                        to_use.append(tuple([vcl, loader, server]))
            except VclLoadException as e:
                self._discard_from_future(executor, future_results)
                raise e

            if force_discard:
                self._discard_from_future(executor, future_results)

        self.logger.debug("vcl's loaded: %f" % (time.perf_counter() - start))
        return self._format_vcl_list(to_use, aggregated_result)

    def _discard_from_future(self, executor, future_results):
        discard_results = []
        for vcl, loader, server, future_result in future_results:
            result = self._get_load_new_vcl_result(server, future_result)
            if result == VclStatus.OK:
                self._discard_unused_vcls(server, loader, executor, discard_results)
        for server, status in discard_results:
            if status.result() is VclStatus.ERROR:
                self.logger.debug("ERROR while discard vcl's on %s" % (server))

    @collect_processing
    def use_vcl_list(self, vcl_name, vcl_loaded_list):
        self.logger.info("Call use vcl for %d servers" % len(vcl_loaded_list))
        result = True
        start = time.perf_counter()

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

        self.logger.debug("vcl's used: %f" % (time.perf_counter() - start))

        return result
