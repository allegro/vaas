# -*- coding: utf-8 -*-

import varnish
import logging


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)


class VarnishApi(varnish.VarnishHandler):
    def __init__(self, host_port_timeout, secret=None, **kwargs):
        self.id = host_port_timeout[0]
        varnish.VarnishHandler.__init__(self, host_port_timeout, secret, **kwargs)

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

    def vcl_show(self, configname):
        """
        vcl.show configname overloaded due to syntax error in original class
        """
        return self.fetch('vcl.show %s' % configname)
