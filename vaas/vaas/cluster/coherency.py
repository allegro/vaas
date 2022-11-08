import requests

from vaas.cluster.models import VarnishServer


class OutdatedServer(object):
    def __init__(self, id=None, ip=None, port=None, dc=None, cluster=None, current_vcl=None):
        self.id = id
        self.ip = ip
        self.port = port
        self.dc = dc
        self.cluster = cluster
        self.current_vcl = current_vcl

    def __eq__(self, other):
        return hasattr(other, '__dict__') and self.__dict__ == other.__dict__

    def __repr__(self):
        return '{}'.format(self.__dict__)


class OutdatedServerManager(object):

    def load(self, cluster=None):
        if cluster:
            servers = VarnishServer.objects.filter(
                status='active', cluster__name=cluster
            ).prefetch_related('dc', 'cluster')
        else:
            servers = VarnishServer.objects.filter(status='active').prefetch_related('dc', 'cluster')
        return [self._map(server, current_vcl) for server, current_vcl in self.filter(servers)]

    def filter(self, servers, outdated=True):
        result = []
        for server in servers:
            current_vcl = self._fetch_current_vcl_version(server)
            if self._is_outdated(server, current_vcl) == outdated:
                result.append((server, current_vcl))
        return result

    def _map(self, server, current_vcl):
        return OutdatedServer(server.id, server.ip, server.port, server.dc.symbol, server.cluster.name, current_vcl)

    def _is_outdated(self, server, current_vcl):
        return current_vcl not in server.cluster.current_vcls

    def _fetch_current_vcl_version(self, server):
        url = 'http://{}:{}/vaas/'.format(server.ip, server.http_port)
        try:
            return requests.get(url).json()['vcl_version']
        except:  # noqa
            return None
