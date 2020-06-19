from django.test import TestCase
from vaas.manager.models import Director
from vaas.router.fetcher import ValidationResponse
from vaas.router.models import Assertion, Named, Route, ValidationResult
from vaas.router.report import ReportGenerator


class TestReportGenerator(TestCase):
    def _prepare_raport_generator_with_directors_and_routes(self):
        directors = [
            Director(pk=1, name='first'),
            Director(pk=2, name='second')
        ]
        routes = [
            Route(pk=1, condition='req.url ~ "/first"', director=directors[0]),
            Route(pk=2, condition='req.url ~ "/second"', director=directors[1]),
        ]
        return ReportGenerator(directors, routes)

    def _assert_tests_equal(self, expected_tests, current_tests):
        self.assertEqual(len(expected_tests), len(current_tests), "Number of expected and current tests is different")
        for i in range(0, len(current_tests)):
            self.assertEqual(expected_tests[i], current_tests[i])

    def test_should_return_passed_report_if_all_validation_response_are_correct(self):
        expected_tests = [
            ValidationResult(
                url='https://example.com/first',
                result='PASS',
                expected=Assertion(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                current=Assertion(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                error_message=''
            ),
            ValidationResult(
                url='https://example.com/second',
                result='PASS',
                expected=Assertion(route=Named(id=2, name='req.url ~ "/second"'), director=Named(id=2, name='second')),
                current=Assertion(route=Named(id=2, name='req.url ~ "/second"'), director=Named(id=2, name='second')),
                error_message=''
            )
        ]
        validation_responses = [
            ValidationResponse('https://example.com/first', 'first', '1', 203, 1),
            ValidationResponse('https://example.com/second', 'second', '2', 203, 2)
        ]
        report_generator = self._prepare_raport_generator_with_directors_and_routes()
        report = report_generator.generate_report(validation_responses)
        self.assertEqual('PASS', report.status)
        self._assert_tests_equal(expected_tests, report.validation_results)

    def test_should_return_failed_report_if_one_validation_response_is_incorrect(self):
        expected_tests = [
            ValidationResult(
                url='https://example.com/first',
                result='PASS',
                expected=Assertion(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                current=Assertion(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                error_message=''
            ),
            ValidationResult(
                url='https://example.com/first-with-suffix',
                result='FAIL',
                expected=Assertion(route=Named(id=2, name='req.url ~ "/second"'), director=Named(id=2, name='second')),
                current=Assertion(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                error_message='Request was routed to improper route'
            )
        ]
        validation_responses = [
            ValidationResponse('https://example.com/first', 'first', '1', 203, 1),
            ValidationResponse('https://example.com/first-with-suffix', 'first', '1', 203, 2)
        ]
        report_generator = self._prepare_raport_generator_with_directors_and_routes()
        report = report_generator.generate_report(validation_responses)
        self.assertEqual('FAIL', report.status)
        self._assert_tests_equal(expected_tests, report.validation_results)

    def test_should_return_provided_different_error_messages_for_different_fails(self):
        expected_tests = [
            ValidationResult(
                url='https://unrouteable.com/first',
                result='FAIL',
                expected=Assertion(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                current=Assertion(route=None, director=None),
                error_message='Cannot fetch desired url. Is the url <https://unrouteable.com/first> correct ?'
            ),
            ValidationResult(
                url='https://external-domain.com/first',
                result='FAIL',
                expected=Assertion(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                current=Assertion(route=None, director=None),
                error_message='Response was not generated via validation system. '
                              'Please verify that vcl_template contains proper configuration'
            ),
            ValidationResult(
                url='https://example.com/direct-route-in-vcl',
                result='FAIL',
                expected=Assertion(route=Named(id=1, name='req.url ~ "/first"'), director=Named(id=1, name='first')),
                current=Assertion(route=None, director=Named(id=1, name='first')),
                error_message='Url was not routed to any route. '
                              'Probably url is routed directly to director in vcl_template'
            )
        ]
        validation_responses = [
            ValidationResponse('https://unrouteable.com/first', None, None, -1, 1),
            ValidationResponse('https://external-domain.com/first', None, None, 404, 1),
            ValidationResponse('https://example.com/direct-route-in-vcl', 'first', None, 203, 1),
        ]
        report_generator = self._prepare_raport_generator_with_directors_and_routes()
        report = report_generator.generate_report(validation_responses)
        self.assertEqual('FAIL', report.status)
        self._assert_tests_equal(expected_tests, report.validation_results)
