import logging
from urlparse import urlparse
from httplib import HTTPConnection, BadStatusLine


class VarnishPurger(object):

    def __init__(self):
        self.logger = logging.getLogger('vaas')

    def log_and_return_data(self, responses_summary):
        self.logger.debug(responses_summary)
        return responses_summary

    def purge_url(self, url, servers):
        headers = {"Host": urlparse(url).hostname}
        data = {'success': {}, 'error': {}}

        for server in servers:
                try:
                    conn = HTTPConnection(server.ip, 80)
                    conn.request("PURGE", urlparse(url).path, body='', headers=headers)
                    resp = conn.getresponse().status
                    data['success'][server.ip] = "varnish http response code: {}, url={}".format(resp, url)
                except BadStatusLine:
                    data['error'][server.ip] = "Bad status line from varnish server, url={}".format(url)
                except Exception as e:
                    data['error'][server.ip] = "Unexpected error: {}, url={}".format(e, url)

        return self.log_and_return_data(data)
