# -*- coding: utf-8 -*-

import logging
import time
from enum import Enum
from vaas.vcl.renderer import VclRenderer
from vaas.cluster.exceptions import VclLoadException


class VclStatus(Enum):
    NO_CHANGES = 1
    OK = 2
    ERROR = 3


class VclLoader(object):

    def __init__(self, varnish_api, suppress_load_errors=False):
        self.varnish_api = varnish_api
        self.vcl_renderer = VclRenderer()
        self.suppress_load_errors = suppress_load_errors
        self.logger = logging.getLogger(__name__)

    def vcl_has_changed(self, vcl):
        """Compare version embedded in names"""
        return vcl.compare_version(self.varnish_api.vcl_active_name()) is False

    def load_new_vcl(self, vcl):
        try:
            start = time.perf_counter()
            """Load and use newest vcl"""
            if self.vcl_has_changed(vcl) is True:
                self.logger.debug(
                    "[%s] vcl '%s' has changed: %f" % (self.varnish_api.id, vcl.name, time.perf_counter() - start)
                )
                start = time.perf_counter()
                if self.varnish_api.vcl_inline(vcl.name, '<< EOF\n' + str(vcl) + 'EOF')[0][0] == 200:
                    self.logger.debug(
                        "[%s] vcl '%s' has loaded: %f" % (self.varnish_api.id, vcl.name, time.perf_counter() - start)
                    )
                    return VclStatus.OK
                return VclStatus.ERROR
            else:
                self.logger.debug(
                    "[%s] vcl '%s' has no changes: %f" % (self.varnish_api.id, vcl.name, time.perf_counter() - start)
                )
                return VclStatus.NO_CHANGES
        except Exception as e:
            if self.suppress_load_errors:
                return VclStatus.NO_CHANGES
            raise VclLoadException(e)

    def use_vcl(self, vcl):
        start = time.perf_counter()
        if self.varnish_api.vcl_use(vcl.name)[0][0] == 200:
            self.logger.debug(
                "[%s] vcl '%s' used: %f" % (self.varnish_api.id, vcl.name, time.perf_counter() - start)
            )
            return VclStatus.OK
        return VclStatus.ERROR

    def discard_unused_vcls(self):
        """Discard unused vcls"""
        start = time.perf_counter()
        vcls = self.varnish_api.vcls()['available']
        return_value = VclStatus.NO_CHANGES.value
        for vcl in vcls:
            try:
                if self.varnish_api.vcl_discard(vcl)[0][0] == 200:
                    return_value = max(return_value, VclStatus.OK.value)
                    self.logger.info("VCL %s discarded." % vcl)
                else:
                    return_value = max(return_value, VclStatus.ERROR.value)
                    self.logger.warning("VCL %s not discarded." % vcl)
            except AssertionError:
                self.logger.warning("VCL %s not discarded." % vcl)
                return_value = max(return_value, VclStatus.ERROR.value)

        self.logger.debug(
            "[%s] old vcl discarded: %f" % (self.varnish_api.id, time.perf_counter() - start)
        )
        return VclStatus(return_value)
