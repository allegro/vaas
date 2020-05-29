import logging
from urllib.parse import urlparse
from http.client import HTTPConnection, BadStatusLine
from concurrent.futures import ThreadPoolExecutor as PoolExecutor
from functools import partial
from django.conf import settings



class VarnishPurger(object):

    def __init__(self):
        self.logger = logging.getLogger('vaas')

    def log_and_return_data(self, responses_summary):
        self.logger.debug(responses_summary)
        return responses_summary

    def purge_url(self, url, servers, headers=None):
        parsed_url = urlparse(url)
        if headers is not None and 'Host' not in headers.keys():
            headers['Host'] = parsed_url.hostname
        if headers is None:
            headers = {'Host':parsed_url.hostname}
        data = {'success': {}, 'error': {}}
        with PoolExecutor(max_workers=len(servers)) as executor:
            for _ in executor.map(partial(self.purge_server, url, parsed_url, headers, data), servers):
                pass
        return self.log_and_return_data(data)

    def purge_server(self, url, parsed_url, headers, data, server):
        try:
            conn = HTTPConnection(server.ip, server.http_port, timeout=settings.PURGER_HTTP_CLIENT_TIMEOUT)
            purge_url = parsed_url.path
            if parsed_url.query:
                purge_url = "{}?{}".format(parsed_url.path, parsed_url.query)
            conn.request("PURGE", purge_url, body='', headers=headers)
            resp = conn.getresponse().status
            data['success'][server.ip] = "varnish http response code: {}, url={}, headers={}, server={}:{}".format(
                resp, url, sorted(headers.items(), key=lambda x: x[0]), server.ip, server.http_port
            )
        except BadStatusLine:
            data['error'][server.ip] = "Bad status line from varnish server, url={}, headers={}, server={}:{}".format(
                url, sorted(headers.items(), key=lambda x: x[0]), server.ip, server.http_port
            )
        except Exception as e:
            data['error'][server.ip] = "Unexpected error: {}, url={}, headers={}, server={}:{}".format(
                e, url, sorted(headers.items(), key=lambda x: x[0]), server.ip, server.http_port
            )
