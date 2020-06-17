import logging
from itertools import product
from collections import defaultdict
from urllib.parse import urlparse
from http.client import HTTPConnection, BadStatusLine
from concurrent import futures
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
            headers['Host'] = [parsed_url.hostname]
        if headers is None:
            headers = {'Host': [parsed_url.hostname]}
        headers_combinations = self.prepare_headers_combinations(headers)
        data = {'success': defaultdict(list), 'error': defaultdict(list)}
        with futures.ThreadPoolExecutor(max_workers=settings.PURGER_MAX_HTTP_WORKERS) as executor:
            requests_futures = []
            for server in servers:
                for header_combination in headers_combinations:
                    requests_futures.append(executor.submit(self.purge_server,
                                                            url,
                                                            parsed_url,
                                                            data, server,
                                                            header_combination)
                                            )
        for future in futures.as_completed(requests_futures):
            pass

        return self.log_and_return_data(data)

    def purge_server(self, url, parsed_url, data, server, headers):
        try:
            conn = HTTPConnection(server.ip, server.http_port, timeout=settings.PURGER_HTTP_CLIENT_TIMEOUT)
            purge_url = parsed_url.path
            if parsed_url.query:
                purge_url = "{}?{}".format(parsed_url.path, parsed_url.query)
            conn.request("PURGE", purge_url, body='', headers=headers)
            resp = conn.getresponse().status
            data['success'][server.ip].append(
                "varnish http response code: {}, url={}, headers={}, server={}:{}".format(
                    resp, url, sorted(headers.items(), key=lambda x: x[0]), server.ip, server.http_port)
            )
        except BadStatusLine:
            data['error'][server.ip].append(
                "Bad status line from varnish server, url={}, headers={}, server={}:{}".format(
                    url, sorted(headers.items(), key=lambda x: x[0]), server.ip, server.http_port)
            )
        except Exception as e:
            data['error'][server.ip].append(
                "Unexpected error: {}, url={}, headers={}, server={}:{}".format(
                    e, url, sorted(headers.items(), key=lambda x: x[0]), server.ip, server.http_port)
            )

    def prepare_headers_combinations(self, headers):
        keys = headers.keys()
        values = (headers[key] for key in keys)
        combinations = [dict(zip(keys, combination)) for combination in product(*values)]
        return combinations
