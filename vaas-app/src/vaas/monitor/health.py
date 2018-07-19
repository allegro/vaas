# -*- coding: utf-8 -*-

import re
import datetime
import logging

from django.utils.timezone import utc

from vaas.monitor.models import BackendStatus
from vaas.manager.models import Backend
from vaas.cluster.cluster import VarnishApiProvider, VclLoadException, ServerExtractor
from vaas.cluster.helpers import BaseHelpers


class BackendStatusManager(object):
    def __init__(self):
        self.varnish_api_provider = VarnishApiProvider()
        self.logger = logging.getLogger('vaas')
        self.timestamp = datetime.datetime.utcnow().replace(tzinfo=utc, microsecond=0)

    def load_from_varnish(self):
        pattern = re.compile("^((?:.*_){5}[^(\s]*)")
        backend_to_status_map = {}
        backends = {x.pk: "{}:{}".format(x.address, x.port) for x in Backend.objects.all()}

        try:
            for varnish_api in self.varnish_api_provider.get_connected_varnish_api():
                backend_statuses = map(lambda x: x.split(), varnish_api.fetch('backend.list')[1][0:].split('\n'))

                for backend_status in backend_statuses:
                    if len(backend_status):
                        backend = re.search(pattern, backend_status[0])

                        if backend is not None:
                            regex_result = re.findall(BaseHelpers.dynamic_regex_with_datacenters(), backend.group(1))
                            if len(regex_result) > 1:
                                backend_id = None
                                self.logger.error('Found multiple regex patterns for possible backend id: {} '
                                                  '(dc name found in director name)'.format(regex_result))
                            else:
                                backend_id = int(regex_result[0][0])

                            status = backend_status[-2]
                            if backend_id and backend_id not in backend_to_status_map or status == 'Sick':
                                backend_address = backends.get(backend_id)
                                if backend_address is not None:
                                    backend_to_status_map[backend_address] = status

        except VclLoadException as e:
            self.logger.warning("Some backends' status could not be refreshed: %s" % e)

        return backend_to_status_map

    def store_backend_statuses(self, backend_to_status_map):
        for key, status in backend_to_status_map.items():
            address, port = key.split(":")
            try:
                backend_status = BackendStatus.objects.get(address=address, port=port)
                if backend_status.timestamp < self.timestamp:
                    backend_status.status = status
                    backend_status.timestamp = self.timestamp
                    backend_status.save()
            except BackendStatus.DoesNotExist:
                BackendStatus.objects.create(address=address, port=port, status=status, timestamp=self.timestamp)

        BackendStatus.objects.filter(timestamp__lt=self.timestamp).delete()

    def refresh_statuses(self):
        self.store_backend_statuses(self.load_from_varnish())
