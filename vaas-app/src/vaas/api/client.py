# -*- coding: utf-8 -*-

import varnish
import logging

from django.conf import settings


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)


class VarnishApiReadException(Exception):
    pass


class VarnishApi(varnish.VarnishHandler):
    def __init__(self, host_port_timeout, secret=None, **kwargs):
        self.id = host_port_timeout[0]
        varnish.VarnishHandler.__init__(self, host_port_timeout, secret, **kwargs)

    def vcl_list(self):
        vcls = {}
        for line in self.fetch('vcl.list')[1].splitlines():
            a = line.split()
            vcls[a[-1]] = tuple(a[:-1])
        return vcls

    def vcls(self):
        """List active vcl and available vcls"""
        vcl_list = self.vcl_list()
        available = []
        active = ''
        for vcl in vcl_list.keys():
            if 'active' in vcl_list[vcl]:
                active = vcl
            elif 'available' in vcl_list[vcl]:
                available.append(vcl)

        return {'active': active, 'available': available}

    def vcl_content_active(self):
        """Show content of active vcl"""
        return self.vcl_show(self.vcl_active_name())[1][:-1]

    def vcl_active_name(self):
        return self.vcls()['active']

    def daemon_version(self):
        version = 'unknown'
        _, result = self.fetch('banner')
        for line in result.splitlines():
            if line.startswith('varnish'):
                version = line.split(' ')[0]

        return version

    def vcl_show(self, configname):
        """
        vcl.show configname overloaded due to syntax error in original class
        """
        return self.fetch('vcl.show %s' % configname)

    def vcl_inline(self, configname, vclcontent):
        """
        vcl.inline - overloaded due to use internal fetch() method with configurable timout
        """
        return self.fetch(
            'vcl.inline %s %s' % (configname, vclcontent), timeout=settings.VARNISH_VCL_INLINE_COMMAND_TIMEOUT
        )

    def fetch(self, command, timeout=None):
        """
        Run a command on the Varnish backend and return the result
        return value is a tuple of ((status, length), content)
        """
        self.write(command.encode('utf-8') + b'\n')
        buffer = self.read_until(b'\n', timeout).strip()
        status, length = map(int, buffer.split())
        content = b''
        while len(content) < length:
            content += self.read_until(b'\n', timeout)
        assert status == 200, 'Bad response code: {status} {text} ({command})'.format(
            status=status,
            text=content,
            command=command)
        self.read_eager()
        return (status, length), str(content, 'utf-8')

    def read_until(self, match, timeout=None):
        # override timeout for case when socket is open but process not responding
        if timeout is None:
            timeout = settings.VARNISH_COMMAND_TIMEOUT
        buffer = varnish.VarnishHandler.read_until(self, match, timeout)
        if len(buffer):
            return buffer
        raise VarnishApiReadException(
            'Timeout during varnish.VarnishHandler.read_until(self, {}, {})'.format(match, timeout)
        )
