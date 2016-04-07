# -*- coding: utf-8 -*-

import re
import datetime
import logging

from django.utils.timezone import utc

from vaas.monitor.models import BackendStatus
from vaas.cluster.cluster import VarnishApiProvider, VclLoadException, ServerExtractor


class BackendStatusManager(object):
    def __init__(self):
        self.varnish_api_provider = VarnishApiProvider()
        self.logger = logging.getLogger('vaas')

    def load_from_varnish(self):
        pattern = re.compile("\((\d+\.\d+\.\d+\.\d+),[^,]*,(\d+)\)\s+\w+\s+\w+\s+(\w+)")
        backend_to_status_map = {}

        try:
            for varnish_api in self.varnish_api_provider.get_connected_varnish_api():
                backend_statuses = varnish_api.fetch('backend.list')[1][0:].split('\n')

                for backend in backend_statuses:
                    ips = re.search(pattern, backend)
                    if ips is not None:
                        backend_address = str(ips.group(1)) + ':' + str(ips.group(2))

                        if backend_address not in backend_to_status_map or ips.group(3) == 'Sick':
                            backend_to_status_map[backend_address] = ips.group(3)

        except VclLoadException as e:
            self.logger.warning("Some backends' status could not be refreshed: %s" % e)

        return backend_to_status_map

    def store_backend_statuses(self, backend_to_status_map):
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        for key, status in backend_to_status_map.items():
            address, port = key.split(":")
            try:
                backend_status = BackendStatus.objects.get(address=address, port=port)
                backend_status.status = status
                backend_status.timestamp = now
                backend_status.save()
            except BackendStatus.DoesNotExist:
                BackendStatus.objects.create(address=address, port=port, status=status, timestamp=now)

        BackendStatus.objects.filter(timestamp__lt=now).delete()

    def refresh_statuses(self):
        self.store_backend_statuses(self.load_from_varnish())
