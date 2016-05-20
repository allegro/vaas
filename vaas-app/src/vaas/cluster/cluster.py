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
from vaas.vcl.renderer import VclRenderer, VclRendererInput


def make_parallel_loader(max_workers=settings.VAAS_LOADER_MAX_WORKERS,
                         partial=settings.VAAS_LOADER_PARTIAL_RELOAD):
    if partial:
        return PartialParallelLoader(max_workers)
    else:
        return ParallelLoader(max_workers)


class VclLoadException(Exception):
    pass


@app.task(bind=True)
def load_vcl_task(self, emmit_time, cluster_ids):
    start_processing_time = timezone.now()
    clusters = LogicalCluster.objects.filter(pk__in=cluster_ids, reload_timestamp__lte=emmit_time)
    return VarnishCluster().load_vcl(start_processing_time, clusters)


class VarnishCluster(object):

    def __init__(self, timeout=1, max_workers=30):
        self.servers = VarnishServer.objects.filter(enabled=True).prefetch_related('dc', 'template', 'cluster')
        self.logger = logging.getLogger('vaas')
        self.timeout = timeout
        self.max_workers = max_workers

    def get_vcl_content(self, varnish_server_pk):
        return VarnishApiProvider().get_api(VarnishServer.objects.get(pk=varnish_server_pk)).vcl_content_active()

    def load_vcl(self, start_processing_time, clusters):
        servers = ServerExtractor().extract_servers_by_clusters(clusters)
        vcl_list = ParallelRenderer(self.max_workers).render_vcl_for_servers(start_processing_time.isoformat(), servers)
        parallel_loader = make_parallel_loader(self.max_workers)

        try:
            loaded_vcl_list = parallel_loader.load_vcl_list(vcl_list)
            for cluster in clusters:
                cluster.reload_timestamp = start_processing_time
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
        self.servers = VarnishServer.objects.filter(enabled=True).prefetch_related('dc', 'template', 'cluster')

    def extract_servers_by_clusters(self, clusters):
        self.logger.debug("Names of cluster used by load_vcl: %s" % ([cluster.name for cluster in clusters]))
        extracted_servers = [server for server in self.servers if server.cluster in clusters]
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

    def _append_vcl(self, vcl, server, future_results, executor):
        loader = VclLoader(self.api_provider.get_api(server))
        future_results.append(tuple([vcl, loader, server, executor.submit(loader.load_new_vcl, vcl)]))

    def _format_vcl_list(self, to_use, aggregated_result):
        if not aggregated_result:
            raise VclLoadException

        return to_use

    def load_vcl_list(self, vcl_list):
        to_use = []
        start = time.time()
        aggregated_result = True
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_results = []

            for server, vcl in vcl_list:
                self._append_vcl(vcl, server, future_results, executor)

            for vcl, loader, server, future_result in future_results:
                result = future_result.result()
                if result == VclStatus.ERROR:
                    aggregated_result = False
                if result == VclStatus.OK:
                    to_use.append(tuple([vcl, loader, server]))

        self.logger.debug("vcl's loaded: %f" % (time.time() - start))

        return self._format_vcl_list(to_use, aggregated_result)

    def use_vcl_list(self, vcl_name, vcl_loaded_list):
        self.logger.info("Call use vcl for %d servers" % len(vcl_loaded_list))
        result = True
        start = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_results = []
            for vcl, loader, server in vcl_loaded_list:
                future_results.append(tuple([vcl_name, server.ip, executor.submit(loader.use_vcl, vcl)]))
            for vcl_name, server_ip, future_result in future_results:
                single_result = future_result.result()
                if single_result == VclStatus.ERROR:
                    result = False
                    self.logger.error("Cannot use vcl [%s] for server %s", vcl_name, server_ip)
            for vcl, loader, server in vcl_loaded_list:
                executor.submit(loader.discard_unused_vcls())

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
