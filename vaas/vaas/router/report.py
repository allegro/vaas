from typing import Any, List, Tuple

from celery.result import AsyncResult
from django.conf import settings

from vaas.manager.models import Director
from vaas.router.fetcher import Fetcher, RouteAssertionResponse, RedirectAssertionResponse
from vaas.router.models import RouteContext, Named, PositiveUrl, Route, ValidationReport, ValidationResult, \
    RedirectAssertion, Redirect, RedirectContext
from vaas.settings.celery import app


def to_dict(element):
    result = element
    if hasattr(element, '__dict__'):
        result = {}
        for k, v in element.__dict__.items():
            result[k] = to_dict(v)

    elif isinstance(element, list):
        result = []
        for subelement in element:
            result.append(to_dict(subelement))
    return result


@app.task(bind=True, acks_late=settings.CELERY_TASK_ACKS_LATE,
          reject_on_worker_lost=settings.CELERY_TASK_REJECT_ON_WORKER_LOST,
          soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT_SECONDS)
def fetch_urls_async(self) -> dict:
    return to_dict(Fetcher().check_urls(PositiveUrl.objects.all()))


@app.task(bind=True, acks_late=settings.CELERY_TASK_ACKS_LATE,
          reject_on_worker_lost=settings.CELERY_TASK_REJECT_ON_WORKER_LOST,
          soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT_SECONDS)
def fetch_redirects_async(self) -> dict:
    return to_dict(Fetcher().check_redirects(RedirectAssertion.objects.all()))


def prepare_report_from_task(task_id: str, report_type: str = 'route') -> ValidationReport:
    task = AsyncResult(task_id)
    report = ValidationReport(None, None)
    if task.ready() and task.successful():
        if report_type == 'route':
            report = RouteReportGenerator(Director.objects.all(), Route.objects.all()).generate_report(
                [RouteAssertionResponse(**response_dict) for response_dict in task.get()]
            )
        elif report_type == 'redirect':
            report = RedirectReportGenerator(Redirect.objects.all()).generate_report(
                [RedirectAssertionResponse(**response_dict) for response_dict in task.get()]
            )

    report.task_status = task.status
    report.pk = task_id
    return report


class ReportGenerator:
    def generate_report(self, validation_responses: list) -> ValidationReport:
        tests = [self._prepare_validation_response(vr) for vr in validation_responses]
        status = 'PASS'
        for test in tests:
            if test.result != status:
                status = test.result
                break
        return ValidationReport(tests, status)

    def _prepare_validation_response(self, validation_response: Any) -> ValidationResult:
        status, error_message = self._get_result(validation_response)
        return ValidationResult(
            validation_response.url,
            status,
            self._get_expected_value(validation_response),
            self._get_current_value(validation_response),
            error_message
        )

    def _get_result(self, validation_response: Any) -> Tuple[str, str]:
        raise NotImplementedError()

    def _get_expected_value(self, validation_response: Any) -> Any:
        raise NotImplementedError()

    def _get_current_value(self, validation_response: Any) -> Any:
        raise NotImplementedError()

    def _prepare_error_message_by_http_status(self, status_code: int, url: str, model: str) -> str:
        if status_code <= 0:
            return 'Cannot fetch desired url. Is the url <{}> correct ?'.format(url)
        if status_code != 203:
            return 'Response was not generated via validation system. ' \
                   'Please verify that vcl_template contains proper configuration'
        return f'Url was not handled by any {model}'


class RouteReportGenerator(ReportGenerator):
    def __init__(self, directors: List[Director], routes: List[Route]):
        self.routes = {route.pk: route for route in routes}
        self.director_ids = {director.name: director.pk for director in directors}

    def _get_expected_value(self, validation_response: RouteAssertionResponse) -> RouteContext:
        route_id = validation_response.expected_route
        return RouteContext(
            route=Named(route_id, self._get_route_condition(route_id)),
            director=Named(self.routes[route_id].director.pk, self.routes[route_id].director.name)
        )

    def _get_current_value(self, validation_response: RouteAssertionResponse) -> RouteContext:
        route_id = validation_response.route
        route = None
        director = None
        if route_id > 0:
            route = Named(route_id, self._get_route_condition(route_id))
        director_id = self.director_ids.get(validation_response.director, None)
        if director_id:
            director = Named(director_id, validation_response.director)
        return RouteContext(route=route, director=director)

    def _get_route_condition(self, route_id: int) -> str:
        if route_id in self.routes:
            return self.routes[route_id].condition
        return ''

    def _get_result(self, validation_response: RouteAssertionResponse) -> Tuple[str, str]:
        if validation_response.route > 0:
            if validation_response.route != validation_response.expected_route:
                return 'FAIL', 'Request was routed to improper route'
            return 'PASS', ''
        return 'FAIL', self._prepare_error_message_by_http_status(
            validation_response.status_code, validation_response.url, 'route'
        )


class RedirectReportGenerator(ReportGenerator):
    def __init__(self, redirects: List[Redirect]):
        self.redirects = {r.pk: r for r in redirects}

    def _get_expected_value(self, validation_response: RedirectAssertionResponse) -> RedirectContext:
        return RedirectContext(
            redirect=Named(
                validation_response.expected_redirect,
                self._get_redirect_condition(validation_response.expected_redirect)
            ),
            location=validation_response.expected_location
        )

    def _get_current_value(self, validation_response: RedirectAssertionResponse) -> RedirectContext:
        redirect_id = validation_response.actual_redirect
        redirect = None
        if redirect_id > 0:
            redirect = Named(redirect_id, self._get_redirect_condition(redirect_id))
        return RedirectContext(redirect=redirect, location=validation_response.actual_location)

    def _get_redirect_condition(self, redirect_id: int) -> str:
        if redirect_id in self.redirects:
            return self.redirects[redirect_id].condition
        return ''

    def _get_result(self, validation_response: RedirectAssertionResponse):
        if validation_response.actual_redirect > 0:
            if validation_response.actual_redirect != validation_response.expected_redirect:
                return 'FAIL', 'Request was redirected by improper redirect'
            if validation_response.actual_location != validation_response.expected_location:
                return 'FAIL', 'Request was redirected to improper location'
            return 'PASS', ''
        return 'FAIL', self._prepare_error_message_by_http_status(
            validation_response.status_code, validation_response.url, 'redirect'
        )
