from unittest.mock import patch
from django.test import SimpleTestCase

from vaas.metrics.handler import MetricsHandler


class MetricsHandlerTest(SimpleTestCase):
    @patch('vaas.metrics.handler.PrometheusMetrics')
    @patch('vaas.metrics.handler.StatsdMetrics')
    def test_should_send_metrics_for_defined_protocols(self, mock_statsd_metrics, mock_prometheus_metrics):
        metrics = MetricsHandler([mock_statsd_metrics, mock_prometheus_metrics])
        self.assertEqual(len(metrics.protocols), 2)

        metrics.time('test', 1.0)
        mock_statsd_metrics.sum.assert_called_with('test', 1.0)
        mock_prometheus_metrics.sum.assert_called_with('test', 1.0)

        metrics.gauge('test', 1)
        mock_statsd_metrics.gauge.assert_called_with('test', 1)
        mock_prometheus_metrics.gauge.assert_called_with('test', 1)

        metrics.counter('test')
        mock_statsd_metrics.counter.assert_called_with('test')
        mock_prometheus_metrics.counter.assert_called_with('test')
