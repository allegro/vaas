from unittest.mock import Mock, patch
from django.test import SimpleTestCase

from vaas.metrics.statsd import StatsdMetrics


class TestStatsdMetrics(SimpleTestCase):
    def test_should_send_defined_metrics(self):
        with patch('statsd.StatsClient') as mock_statsd_client:
            mock_statsd_timing, mock_statsd_gauge, mock_statsd_counter = Mock(), Mock(), Mock()
            mock_statsd_client = Mock(timing=mock_statsd_timing, gauge=mock_statsd_gauge, incr=mock_statsd_counter)

            statsd_metrics = StatsdMetrics()
            statsd_metrics.client = mock_statsd_client

            statsd_metrics.sum('test', 1.0)
            mock_statsd_timing.assert_called_once_with('test', 1.0)

            statsd_metrics.gauge('test', 1)
            mock_statsd_gauge.assert_called_once_with('test', 1)

            statsd_metrics.counter('test')
            mock_statsd_counter.assert_called_once_with('test')

    def test_should_not_send_metric_with_empty_name(self):
        with patch('statsd.StatsClient') as mock_statsd_client:
            mock_statsd_timing, mock_statsd_gauge, mock_statsd_counter = Mock(), Mock(), Mock()
            mock_statsd_client = Mock(timing=mock_statsd_timing, gauge=mock_statsd_gauge, counter=mock_statsd_counter)

            statsd_metrics = StatsdMetrics()
            statsd_metrics.client = mock_statsd_client

            statsd_metrics.sum('', 1.0)
            mock_statsd_timing.assert_not_called()

            statsd_metrics.gauge('', 1)
            mock_statsd_gauge.assert_not_called()

            statsd_metrics.counter('')
            mock_statsd_counter.assert_not_called()
