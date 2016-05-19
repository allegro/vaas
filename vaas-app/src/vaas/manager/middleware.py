# -*- coding: utf-8 -*-

from django.utils import timezone
import logging
import time
from tastypie.http import HttpApplicationError

from vaas.cluster.cluster import load_vcl_task


class VclRefreshState(object):
    # dictionary with requests id to refresh
    refresh = {}
    logger = logging.getLogger('vaas')

    @classmethod
    def set_refresh(cls, req_id, clusters):
        """
        For request id set refresh for selected varnish clusters.
        cls - global static class
        req_id - request id - string
        clusters - list with clusters to update
        """
        cls.logger.debug("set_refresh() - request id: " + req_id)
        if req_id in cls.refresh.keys():
            # merge clusters if we have got multiple signals per request id
            cls.refresh[req_id] = list(set(cls.refresh[req_id] + clusters))
        else:
            cls.refresh[req_id] = clusters

        cls.logger.debug("cls.refresh[req_id]: " + str(cls.refresh[req_id]))

    @classmethod
    def get_refresh(cls, req_id):
        """
        Returns a list of varnish clusters to refresh.
        req_id - request id - string
        """
        # return empty list if no clusters to update
        result = []
        cls.logger.debug("get_refresh() - request id: " + req_id)

        if req_id in cls.refresh:
            result = cls.refresh[req_id]
            del cls.refresh[req_id]

        cls.logger.debug("get_refresh() - result: " + str(result))
        return result


class VclRefreshMiddleware(object):
    def process_request(self, request):
        """
        Method used with every HTTP request.
        """
        VclRefreshState.set_refresh(request.id, [])
        return None

    def process_response(self, request, response):
        # clusters - a list with varnish clusters to refresh
        clusters = VclRefreshState.get_refresh(request.id)
        if 'error_message' in request.session:
            del request.session['error_message']

        if len(clusters) > 0:
            start = time.time()
            try:
                result = load_vcl_task.delay(
                    timezone.now(),
                    [cluster.id for cluster in clusters]
                )

                if 'tastypie' in str(type(response)):
                    if 'respond-async' in request.META.get('HTTP_PREFER', ''):
                        response.status_code = 202
                else:
                    result.get()

                    if isinstance(result.result, Exception):
                        raise result.result
            except Exception as e:
                logging.info("Error while reloading cluster: %s (%s)" % (e, type(response)))
                if 'tastypie' in str(type(response)):
                    return HttpApplicationError("%s: %s" % (e.__class__.__name__, str(e)[:400]))
                request.session['error_message'] = "%s: %s" % (e.__class__.__name__, str(e)[:400])

            logging.info("cluster reload time: %f" % (time.time() - start))
        return response
