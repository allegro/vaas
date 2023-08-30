from unittest.mock import Mock, call, patch
from django.test import SimpleTestCase, override_settings
from prometheus_client import Gauge, Summary

from vaas.metrics.prometheus import PrometheusClient, PrometheusMetrics


class TestPrometheusClient(SimpleTestCase):
    def test_should_get_or_create_metrics(self):
        client = PrometheusClient()

        metric = client.get_or_create('test_sum', Summary)
        self.assertTrue(isinstance(metric, Summary))
        self.assertEqual(metric._name, 'test_sum')
        self.assertEqual(len(client.metrics_bucket), 1)

        metric = client.get_or_create('test_gauge', Gauge)
        self.assertTrue(isinstance(metric, Gauge))
        self.assertEqual(metric._name, 'test_gauge')
        self.assertEqual(len(client.metrics_bucket), 2)

        metric = client.get_or_create('test_gauge', Gauge)
        self.assertTrue(isinstance(metric, Gauge))
        self.assertEqual(metric._name, 'test_gauge')
        self.assertEqual(len(client.metrics_bucket), 2)

    @override_settings(PROMETHEUS_GATEWAY_HOST='1.2.3.4', PROMETHEUS_GATEWAY_PORT='123', PROMETHEUS_GATEWAY_JOB='')
    @patch('vaas.metrics.prometheus.CollectorRegistry')
    @patch('vaas.metrics.prometheus.push_to_gateway')
    def test_should_push_metrics_to_prometheus_gateway(self, mock_push_to_gateway, registry_mock):
        client = PrometheusClient()
        client.registry = registry_mock
        client.push()
        mock_push_to_gateway.assert_called_with(gateway='1.2.3.4:123', job='', registry=registry_mock)

    @patch('vaas.metrics.prometheus.push_to_gateway', Mock(side_effect=Exception))
    def test_should_continue_after_push_to_gateway_raise_an_exception(self):
        with patch('vaas.metrics.prometheus.logger') as mock_logger:
            mock_logger.exception = Mock()
            client = PrometheusClient()
            client.push()
            mock_logger.exception.assert_called_once()


class TestPrometheusMetrics2(SimpleTestCase):
    def test_should_create_metrics_and_push_them_to_gateway(self):
        with patch('vaas.metrics.prometheus.PrometheusClient') as mock_pronetheus_client:
            mock_summary_observe, mock_gauge_set, mock_pronetheus_client.push = Mock(), Mock(), Mock()
            mock_pronetheus_client.get_or_create.return_value = Mock(observe=mock_summary_observe, set=mock_gauge_set)
            prometheus_metrics = PrometheusMetrics()
            prometheus_metrics.client = mock_pronetheus_client

            self.assertEqual(prometheus_metrics.client.get_or_create, mock_pronetheus_client.get_or_create)

            prometheus_metrics.sum('test', 1.0)
            mock_pronetheus_client.get_or_create.assert_called_with('test', Summary)
            mock_summary_observe.assert_called_with(1.0)

            prometheus_metrics.gauge('test', 1)
            mock_pronetheus_client.get_or_create.assert_called_with('test', Gauge)
            mock_gauge_set.assert_called_with(1)

            mock_pronetheus_client.push.assert_has_calls([call(), call()])

    def test_should_not_create_and_push_metrics_with_empty_names(self):
        with patch('vaas.metrics.prometheus.PrometheusClient') as mock_pronetheus_client:
            mock_pronetheus_client = Mock(get_or_create=Mock(), push=Mock())
            prometheus_metrics = PrometheusMetrics()
            prometheus_metrics.client = mock_pronetheus_client

            self.assertEqual(prometheus_metrics.client.get_or_create, mock_pronetheus_client.get_or_create)

            prometheus_metrics.sum('', 1.0)
            mock_pronetheus_client.get_or_create.assert_not_called()

            prometheus_metrics.gauge('', 1)
            mock_pronetheus_client.get_or_create.assert_not_called()

            mock_pronetheus_client.push.assert_not_called()
