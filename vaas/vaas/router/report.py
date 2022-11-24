from celery.result import AsyncResult
from django.conf import settings

from vaas.manager.models import Director
from vaas.router.fetcher import Fetcher, RouteAssertionResponse
from vaas.router.models import Assertion, Named, PositiveUrl, Route, ValidationReport, ValidationResult, \
    RedirectAssertion
from vaas.settings.celery import app


def _to_dict(element):
    result = element
    if hasattr(element, '__dict__'):
        result = {}
        for k, v in element.__dict__.items():
            result[k] = _to_dict(v)

    elif type(element) == list:
        result = []
        for subelement in element:
            result.append(_to_dict(subelement))
    return result


@app.task(bind=True, soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT_SECONDS)
def fetch_urls_async(self) -> dict:
    return _to_dict(Fetcher().check_urls(PositiveUrl.objects.all()))


@app.task(bind=True, soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT_SECONDS)
def fetch_redirects_async(self) -> dict:
    return _to_dict(Fetcher().check_redirects(RedirectAssertion.objects.all()))


def prepare_report_from_task(task_id):
    task = AsyncResult(task_id)
    report = ValidationReport(None, None)
    if task.ready() and task.successful():
        validation_responses = [RouteAssertionResponse(**response_dict) for response_dict in task.get()]
        directors = Director.objects.all()
        routes = Route.objects.all()
        report = ReportGenerator(directors, routes).generate_report(
            validation_responses
        )
    report.task_status = task.status
    report.pk = task_id
    return report


class ReportGenerator(object):
    def __init__(self, directors, routes):
        self.routes = {route.pk: route for route in routes}
        self.director_ids = {director.name: director.pk for director in directors}

    def generate_report(self, validation_responses):
        tests = [self._prepare_validation_response(vr) for vr in validation_responses]
        status = 'PASS'
        for test in tests:
            if test.result != status:
                status = test.result
                break
        return ValidationReport(tests, status)

    def _prepare_validation_response(self, validation_response):
        status, error_message = self._get_result(validation_response)
        return ValidationResult(
            validation_response.url,
            status,
            self._get_expected_assertion(validation_response.expected_route),
            self._get_current_assertion(validation_response.route, validation_response.director),
            error_message
        )

    def _get_expected_assertion(self, route_id):
        return Assertion(
            route=Named(route_id, self._get_route_condition(route_id)),
            director=Named(self.routes[route_id].director.pk, self.routes[route_id].director.name)
        )

    def _get_current_assertion(self, route_id, director_name):
        route = None
        director = None
        try:
            current_id = int(route_id)
            route = Named(current_id, self._get_route_condition(current_id))
        finally:
            director_id = self.director_ids.get(director_name, None)
            if director_id:
                director = Named(director_id, director_name)
            return Assertion(route=route, director=director)

    def _get_route_condition(self, route_id):
        if route_id in self.routes:
            return self.routes[route_id].condition
        return ''

    def _get_result(self, validation_response):
        try:
            current_route = int(validation_response.route)
            if current_route != validation_response.expected_route:
                return 'FAIL', 'Request was routed to improper route'
            return 'PASS', ''
        except Exception:
            return 'FAIL', self._prepare_error_message_for_no_route(validation_response)

    def _prepare_error_message_for_no_route(self, validation_response):
        if validation_response.status_code == -1:
            return 'Cannot fetch desired url. Is the url <{}> correct ?'.format(validation_response.url)
        if validation_response.status_code != 203:
            return 'Response was not generated via validation system. ' \
                   'Please verify that vcl_template contains proper configuration'
        return 'Url was not routed to any route. Probably url is routed directly to director in vcl_template'
