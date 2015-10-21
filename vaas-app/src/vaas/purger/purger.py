import logging
from urlparse import urlparse
from vaas.cluster.models import LogicalCluster
from vaas.cluster.cluster import ServerExtractor
from httplib import HTTPConnection, BadStatusLine
from sys import exc_info


class VarnishPurger(object):

    def __init__(self):
        self.logger = logging.getLogger('vaas')

    def log_and_return_data(self, responses_summary):
        self.logger.debug(responses_summary)
        return responses_summary

    def purge_url(self, url, clusters):
        servers = ServerExtractor().extract_servers_by_clusters(LogicalCluster.objects.filter(name=clusters))
        headers = {"Host": urlparse(url).hostname}
        data = {}

        for server in servers:
                try:
                    conn = HTTPConnection(server.ip, 80)
                    conn.request("PURGE", urlparse(url).path, body='', headers=headers)
                    resp = conn.getresponse().status
                    data[server.ip] = "varnish http response code: {}, url={}".format(resp, url)
                except BadStatusLine:
                    data[server.ip] = "Bad status line from varnish server, url={}".format(url)
                except:
                    data[server.ip] = "Unexpected error: {}, url={}".format(exc_info()[0], url)

        return self.log_and_return_data(data)
