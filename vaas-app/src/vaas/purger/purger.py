import logging
from urllib.parse import urlparse
from http.client import HTTPConnection, BadStatusLine


class VarnishPurger(object):

    def __init__(self):
        self.logger = logging.getLogger('vaas')

    def log_and_return_data(self, responses_summary):
        self.logger.debug(responses_summary)
        return responses_summary

    def purge_url(self, url, servers):
        parsed_url = urlparse(url)
        headers = {"Host": parsed_url.hostname}
        data = {'success': {}, 'error': {}}

        for server in servers:
                try:
                    conn = HTTPConnection(server.ip, server.http_port)
                    purge_url = parsed_url.path
                    if parsed_url.query:
                        purge_url = "{}?{}".format(parsed_url.path, parsed_url.query)
                    conn.request("PURGE", purge_url, body='', headers=headers)
                    resp = conn.getresponse().status
                    data['success'][server.ip] = "varnish http response code: {}, url={}".format(resp, url)
                except BadStatusLine:
                    data['error'][server.ip] = "Bad status line from varnish server, url={}".format(url)
                except Exception as e:
                    data['error'][server.ip] = "Unexpected error: {}, url={}".format(e, url)

        return self.log_and_return_data(data)
