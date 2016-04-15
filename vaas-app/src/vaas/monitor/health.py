# -*- coding: utf-8 -*-

import re
import datetime
import logging

from django.utils.timezone import utc

from vaas.monitor.models import BackendStatus
from vaas.manager.models import Backend
from vaas.cluster.cluster import VarnishApiProvider, VclLoadException, ServerExtractor


class BackendStatusManager(object):
    def __init__(self):
        self.varnish_api_provider = VarnishApiProvider()
        self.logger = logging.getLogger('vaas')

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
                            backend_id = int(backend.group(1).split('_')[-5])
                            status = backend_status[-2]
                            if backend_id not in backend_to_status_map or status == 'Sick':
                                backend_address = backends[backend_id]
                                backend_to_status_map[backend_address] = status

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
