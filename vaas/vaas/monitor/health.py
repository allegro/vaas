# -*- coding: utf-8 -*-

import re
import datetime
import logging

from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.utils.timezone import utc

from vaas.monitor.models import BackendStatus
from vaas.manager.models import Backend
from vaas.cluster.cluster import VarnishApiProvider, ServerExtractor
from vaas.cluster.helpers import BaseHelpers


BACKEND_PATTERN = re.compile(r"^((?:.*_){5}[^(\s]*)")


def provide_backend_status_manager():
    return BackendStatusManager(
        VarnishApiProvider(),
        ServerExtractor().servers,
        settings.VAAS_GATHER_STATUSES_CONNECT_TIMEOUT,
        settings.VAAS_GATHER_STATUSES_MAX_WORKERS
    )


class BackendStatusManager(object):

    def __init__(self, varnish_api_provider, servers, connect_timeout=0.1, workers=30):
        self.logger = logging.getLogger(__name__)
        self.varnish_api_provider = varnish_api_provider
        self.servers = servers
        self.backends = {x.pk: f"{x.address}:{x.port}" for x in Backend.objects.all()}
        self.timestamp = datetime.datetime.utcnow().replace(tzinfo=utc, microsecond=0)
        self.CONNECT_TIMEOUT = connect_timeout
        self.WORKERS = workers

    def load_from_varnish(self):
        dc_pattern = BaseHelpers.dynamic_regex_with_datacenters()
        backend_to_status_map = {}
        with ThreadPoolExecutor(max_workers=self.WORKERS) as executor:
            future_results = []
            for server in self.servers:
                future_results.append(
                    executor.submit(self._load_from_single_varnish, dc_pattern, server)
                )
            for future_result in future_results:
                for backend_id, status in future_result.result().items():
                    if backend_to_status_map.get(backend_id) != 'Sick':
                        backend_to_status_map[backend_id] = status
        return backend_to_status_map

    def _load_from_single_varnish(self, dc_pattern, server):
        backend_to_status_map = {}
        try:
            varnish_api = self.varnish_api_provider.get_api(server, self.CONNECT_TIMEOUT)
            backend_statuses = map(lambda x: x.split(), varnish_api.fetch('backend.list')[1].split('\n'))
            for backend_status in backend_statuses:
                if len(backend_status):
                    backend = re.search(BACKEND_PATTERN, backend_status[0])
                    if backend is not None:
                        backend_id = None
                        regex_result = re.findall(dc_pattern, backend.group(1))
                        if len(regex_result) == 1:
                            try:
                                backend_id = int(regex_result[0][0])
                            except ValueError:
                                self.logger.error(
                                    'Mapping backend id failed. Expected parsable string to int, got {}'.format(
                                        regex_result[0][0]))
                        # for varnish v6.0 LTS
                        if len(backend_status) == 10:
                            status = backend_status[-8]
                        else:
                            # for varnish v4
                            status = backend_status[-2]

                        if backend_id and backend_id not in backend_to_status_map or status == 'Sick':
                            backend = self.backends.get(backend_id)
                            if backend is not None:
                                backend_to_status_map[backend_id] = status
        finally:
            return backend_to_status_map

    def store_backend_statuses(self, backend_to_status_map):
        existing_statuses = {f"{s.backend_id}": s for s in BackendStatus.objects.all()}
        to_update = []
        to_add = []

        for backend_id, status in backend_to_status_map.items():
            backend_status = existing_statuses.get(backend_id)
            if backend_status:
                if backend_status.timestamp < self.timestamp:
                    backend_status.status = status
                    backend_status.timestamp = self.timestamp
                    to_update.append(backend_status)
            else:
                to_add.append(BackendStatus(backend_id=backend_id, status=status, timestamp=self.timestamp))
        create_cnt = len(BackendStatus.objects.bulk_create(to_add))

        # TODO: report number of updated records after updating django to 4.0 or higher
        BackendStatus.objects.bulk_update(to_update, ['status', 'timestamp'])
        delete_cnt, _ = BackendStatus.objects.filter(timestamp__lt=self.timestamp).delete()
        self.logger.info(
            f"Backend statuses, created: {create_cnt} entries, deleted: {delete_cnt} entries"
        )

    def refresh_statuses(self):
        self.store_backend_statuses(self.load_from_varnish())
