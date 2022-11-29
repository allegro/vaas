from django.test import TestCase
from vaas.manager.models import Director
from vaas.router.fetcher import RouteAssertionResponse, RedirectAssertionResponse
from vaas.router.models import RouteContext, Named, Route, ValidationResult, Redirect, RedirectContext
from vaas.router.report import RouteReportGenerator, RedirectReportGenerator


class TestReport(TestCase):
    def _assert_tests_equal(self, expected_tests, current_tests):
        self.assertEqual(len(expected_tests), len(current_tests), "Number of expected and current tests is different")
        for i in range(0, len(current_tests)):
            self.assertEqual(expected_tests[i], current_tests[i])


class TestRouteReportGenerator(TestReport):
    def _prepare_report_generator_with_directors_and_routes(self):
        directors = [
            Director(pk=1, name='first'),
            Director(pk=2, name='second')
        ]
        routes = [
            Route(pk=1, condition='req.url ~ "/first"', director=directors[0]),
            Route(pk=2, condition='req.url ~ "/second"', director=directors[1]),
        ]
        return RouteReportGenerator(directors, routes)

    def _assert_tests_equal(self, expected_tests, current_tests):
        self.assertEqual(len(expected_tests), len(current_tests), "Number of expected and current tests is different")
        for i in range(0, len(current_tests)):
            self.assertEqual(expected_tests[i], current_tests[i])

    def test_should_return_passed_report_if_all_validation_response_are_correct(self):
        expected_tests = [
            ValidationResult(
                url='https://example.com/first',
                result='PASS',
                expected=RouteContext(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                current=RouteContext(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                error_message=''
            ),
            ValidationResult(
                url='https://example.com/second',
                result='PASS',
                expected=RouteContext(
                    route=Named(id=2, name='req.url ~ "/second"'), director=Named(id=2, name='second')
                ),
                current=RouteContext(
                    route=Named(id=2, name='req.url ~ "/second"'), director=Named(id=2, name='second')
                ),
                error_message=''
            )
        ]
        validation_responses = [
            RouteAssertionResponse('https://example.com/first', 'first', 1, 203, 1),
            RouteAssertionResponse('https://example.com/second', 'second', 2, 203, 2)
        ]
        report_generator = self._prepare_report_generator_with_directors_and_routes()
        report = report_generator.generate_report(validation_responses)
        self.assertEqual('PASS', report.validation_status)
        self._assert_tests_equal(expected_tests, report.validation_results)

    def test_should_return_failed_report_if_one_validation_response_is_incorrect(self):
        expected_tests = [
            ValidationResult(
                url='https://example.com/first',
                result='PASS',
                expected=RouteContext(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                current=RouteContext(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                error_message=''
            ),
            ValidationResult(
                url='https://example.com/first-with-suffix',
                result='FAIL',
                expected=RouteContext(
                    route=Named(id=2, name='req.url ~ "/second"'), director=Named(id=2, name='second')
                ),
                current=RouteContext(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                error_message='Request was routed to improper route'
            )
        ]
        validation_responses = [
            RouteAssertionResponse('https://example.com/first', 'first', 1, 203, 1),
            RouteAssertionResponse('https://example.com/first-with-suffix', 'first', 1, 203, 2)
        ]
        report_generator = self._prepare_report_generator_with_directors_and_routes()
        report = report_generator.generate_report(validation_responses)
        self.assertEqual('FAIL', report.validation_status)
        self._assert_tests_equal(expected_tests, report.validation_results)

    def test_should_return_provided_different_error_messages_for_different_fails(self):
        expected_tests = [
            ValidationResult(
                url='https://unrouteable.com/first',
                result='FAIL',
                expected=RouteContext(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                current=RouteContext(route=None, director=None),
                error_message='Cannot fetch desired url. Is the url <https://unrouteable.com/first> correct ?'
            ),
            ValidationResult(
                url='https://external-domain.com/first',
                result='FAIL',
                expected=RouteContext(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                current=RouteContext(route=None, director=None),
                error_message='Response was not generated via validation system. '
                              'Please verify that vcl_template contains proper configuration'
            ),
            ValidationResult(
                url='https://example.com/direct-route-in-vcl',
                result='FAIL',
                expected=RouteContext(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                current=RouteContext(route=None, director=Named(id=1, name='first')),
                error_message='Url was not handled by any route'
            )
        ]
        validation_responses = [
            RouteAssertionResponse('https://unrouteable.com/first', '', 0, 0, 1),
            RouteAssertionResponse('https://external-domain.com/first', '', 0, 404, 1),
            RouteAssertionResponse('https://example.com/direct-route-in-vcl', 'first', 0, 203, 1),
        ]
        report_generator = self._prepare_report_generator_with_directors_and_routes()
        report = report_generator.generate_report(validation_responses)
        self.assertEqual('FAIL', report.validation_status)
        self._assert_tests_equal(expected_tests, report.validation_results)


class TestRedirectReportGenerator(TestReport):
    REDIRECT_ID_ONE = 1
    REDIRECT_ID_TWO = 2

    def _prepare_report_generator_with_redirects(self):
        redirects = [
            Redirect(pk=1, condition='req.http.host == "redirect-one.me"', destination='/one'),
            Redirect(pk=2, condition='req.http.host == "redirect-two.me"', destination='/two')
        ]
        return RedirectReportGenerator(redirects)

    def test_should_return_passed_report_if_all_validation_response_are_correct(self):

        expected_tests = [
            ValidationResult(
                url='https://redirect-one.me/',
                result='PASS',
                expected=RedirectContext(
                    redirect=Named(id=1, name='req.http.host == "redirect-one.me"'), location='/one'
                ),
                current=RedirectContext(
                    redirect=Named(id=1, name='req.http.host == "redirect-one.me"'), location='/one'
                ),
                error_message=''
            ),
            ValidationResult(
                url='https://redirect-two.me/',
                result='PASS',
                expected=RedirectContext(
                    redirect=Named(id=2, name='req.http.host == "redirect-two.me"'), location='/two'
                ),
                current=RedirectContext(
                    redirect=Named(id=2, name='req.http.host == "redirect-two.me"'), location='/two'
                ),
                error_message=''
            )
        ]
        validation_responses = [
            RedirectAssertionResponse(
                'https://redirect-one.me/', '/one', self.REDIRECT_ID_ONE, '/one', self.REDIRECT_ID_ONE, 203
            ),
            RedirectAssertionResponse(
                'https://redirect-two.me/', '/two', self.REDIRECT_ID_TWO, '/two', self.REDIRECT_ID_TWO, 203
            )
        ]
        report_generator = self._prepare_report_generator_with_redirects()
        report = report_generator.generate_report(validation_responses)
        self.assertEqual('PASS', report.validation_status)
        self._assert_tests_equal(expected_tests, report.validation_results)

    def test_should_return_failed_report_if_any_validation_response_is_incorrect(self):
        expected_tests = [
            ValidationResult(
                url='https://redirect-one.me/',
                result='PASS',
                expected=RedirectContext(
                    redirect=Named(id=1, name='req.http.host == "redirect-one.me"'), location='/one'
                ),
                current=RedirectContext(
                    redirect=Named(id=1, name='req.http.host == "redirect-one.me"'), location='/one'
                ),
                error_message=''
            ),
            ValidationResult(
                url='https://redirect-three.me/',
                result='FAIL',
                expected=RedirectContext(
                    redirect=Named(id=2, name='req.http.host == "redirect-two.me"'), location='/two'
                ),
                current=RedirectContext(
                    redirect=Named(id=1, name='req.http.host == "redirect-one.me"'), location='/one'
                ),
                error_message='Request was redirected by improper redirect'
            ),
            ValidationResult(
                url='https://redirect-four.me/',
                result='FAIL',
                expected=RedirectContext(
                    redirect=Named(id=2, name='req.http.host == "redirect-two.me"'), location='/two'
                ),
                current=RedirectContext(
                    redirect=Named(id=2, name='req.http.host == "redirect-two.me"'), location='/four'
                ),
                error_message='Request was redirected to improper location'
            )
        ]
        validation_responses = [
            RedirectAssertionResponse(
                'https://redirect-one.me/', '/one', self.REDIRECT_ID_ONE, '/one', self.REDIRECT_ID_ONE, 203
            ),
            RedirectAssertionResponse(
                'https://redirect-three.me/', '/one', self.REDIRECT_ID_ONE, '/two', self.REDIRECT_ID_TWO, 203
            ),
            RedirectAssertionResponse(
                'https://redirect-four.me/', '/four', self.REDIRECT_ID_TWO, '/two', self.REDIRECT_ID_TWO, 203
            )
        ]
        report_generator = self._prepare_report_generator_with_redirects()
        report = report_generator.generate_report(validation_responses)
        self.assertEqual('FAIL', report.validation_status)
        self._assert_tests_equal(expected_tests, report.validation_results)

    def test_should_return_provided_different_error_messages_for_different_fails(self):
        expected_tests = [
            ValidationResult(
                url='https://unrouteable.com/',
                result='FAIL',
                expected=RedirectContext(
                    redirect=Named(id=1, name='req.http.host == "redirect-one.me"'), location='/one'
                ),
                current=RedirectContext(redirect=None, location=''),
                error_message='Cannot fetch desired url. Is the url <https://unrouteable.com/> correct ?'
            ),
            ValidationResult(
                url='https://external-domain.com/',
                result='FAIL',
                expected=RedirectContext(
                    redirect=Named(id=1, name='req.http.host == "redirect-one.me"'), location='/one'
                ),
                current=RedirectContext(redirect=None, location=''),
                error_message='Response was not generated via validation system. '
                              'Please verify that vcl_template contains proper configuration'
            ),
            ValidationResult(
                url='https://redirect-not-defined.com/',
                result='FAIL',
                expected=RedirectContext(
                    redirect=Named(id=1, name='req.http.host == "redirect-one.me"'), location='/one'
                ),
                current=RedirectContext(redirect=None, location=''),
                error_message='Url was not handled by any redirect'
            ),
        ]
        validation_responses = [
            RedirectAssertionResponse('https://unrouteable.com/', '', 0, '/one', self.REDIRECT_ID_ONE, 0),
            RedirectAssertionResponse('https://external-domain.com/', '', 0, '/one', self.REDIRECT_ID_ONE, 404),
            RedirectAssertionResponse('https://redirect-not-defined.com/', '', 0, '/one', self.REDIRECT_ID_ONE, 203),
        ]
        report_generator = self._prepare_report_generator_with_redirects()
        report = report_generator.generate_report(validation_responses)
        self.assertEqual('FAIL', report.validation_status)
        self._assert_tests_equal(expected_tests, report.validation_results)
