# -*- coding: utf-8 -*-

from django.utils import timezone
from django.conf import settings
import logging
import time
from tastypie.http import HttpApplicationError
from celery.exceptions import SoftTimeLimitExceeded

from vaas.cluster.cluster import load_vcl_task


class VclRefreshState(object):
    # dictionary with requests id to refresh
    refresh = {}
    logger = logging.getLogger(__name__)

    @classmethod
    def set_refresh(cls, req_id, clusters):
        """
        For request id set refresh for selected varnish clusters.
        cls - global static class
        req_id - request id - string
        clusters - list with clusters to update
        """
        if req_id in cls.refresh.keys():
            # merge clusters if we have got multiple signals per request id
            cls.refresh[req_id] = list(set(cls.refresh[req_id] + clusters))
        else:
            cls.refresh[req_id] = clusters

    @classmethod
    def get_refresh(cls, req_id):
        """
        Returns a list of varnish clusters to refresh.
        req_id - request id - string
        """
        # return empty list if no clusters to update
        result = []
        if req_id in cls.refresh:
            result = cls.refresh[req_id]
            del cls.refresh[req_id]

        return result


class VclRefreshMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(self, 'process_request'):
            self.process_request(request)
        response = self.get_response(request)
        if hasattr(self, 'process_response'):
            response = self.process_response(request, response)
        return response

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
            start = time.perf_counter()
            try:
                result = load_vcl_task.delay(
                    timezone.now(),
                    [cluster.id for cluster in clusters]
                )

                if 'tastypie' in str(type(response)) and 'respond-async' in request.META.get('HTTP_PREFER', ''):
                    response.status_code = 202
                    response['Location'] = '/api/v0.1/task/{}/'.format(result.id)
                else:
                    if settings.ENABLE_UWSGI_SWITCH_CONTEXT:
                        try:
                            import uwsgi
                            while not result.ready():
                                uwsgi.async_sleep(1)
                                uwsgi.suspend()
                        except:  # noqa
                            pass
                    logging.info("Task with %s has been finished with status: %s." % (result.id, result.get()))
            except SoftTimeLimitExceeded:
                logging.error("Time for finish the task has been reached: The task with id {} will be killed.".format(
                    result.id))
            except Exception as e:
                logging.info("Error while reloading cluster: %s (%s)" % (e, type(response)))
                if 'tastypie' in str(type(response)):
                    return HttpApplicationError("%s: %s" % (e.__class__.__name__, str(e)[:400]))
                request.session['error_message'] = "%s: %s" % (e.__class__.__name__, unescape_exception(e))

            logging.info("cluster reload time: %f" % (time.perf_counter() - start))
        return response


def unescape_exception(e):
    error_string = str(e)
    return error_string.encode('latin-1', 'backslashreplace').decode('unicode-escape')
