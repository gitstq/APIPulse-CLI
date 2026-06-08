"""
Unit tests for APIPulse-CLI.

Tests core functionality: health checking, configuration parsing,
report generation, and alert management.
"""

import json
import os
import sys
import tempfile
import time
import unittest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from healthpulse.checker import HealthChecker, CheckResult, Status
from healthpulse.config import ConfigParser, EndpointConfig, MonitorConfig
from healthpulse.reporter import ReportGenerator, MonitorSession
from healthpulse.alerts import AlertManager, AlertLevel


class TestCheckResult(unittest.TestCase):
    """Test CheckResult dataclass."""

    def test_default_values(self):
        result = CheckResult(url="https://example.com")
        self.assertEqual(result.url, "https://example.com")
        self.assertEqual(result.method, "GET")
        self.assertEqual(result.status_code, 0)
        self.assertEqual(result.status, Status.UNKNOWN)
        self.assertIsNone(result.error)

    def test_to_dict(self):
        result = CheckResult(
            url="https://example.com",
            status_code=200,
            response_time_ms=150.5,
            status=Status.HEALTHY,
        )
        d = result.to_dict()
        self.assertEqual(d["url"], "https://example.com")
        self.assertEqual(d["status_code"], 200)
        self.assertEqual(d["status"], "healthy")
        self.assertEqual(d["response_time_ms"], 150.5)

    def test_to_json(self):
        result = CheckResult(url="https://example.com", status_code=200)
        j = result.to_json()
        data = json.loads(j)
        self.assertEqual(data["url"], "https://example.com")


class TestHealthChecker(unittest.TestCase):
    """Test HealthChecker class."""

    def test_evaluate_status_healthy(self):
        checker = HealthChecker()
        status = checker._evaluate_status(200, 500)
        self.assertEqual(status, Status.HEALTHY)

    def test_evaluate_status_degraded(self):
        checker = HealthChecker()
        status = checker._evaluate_status(200, 2000)
        self.assertEqual(status, Status.DEGRADED)

    def test_evaluate_status_unhealthy_slow(self):
        checker = HealthChecker()
        status = checker._evaluate_status(200, 6000)
        self.assertEqual(status, Status.UNHEALTHY)

    def test_evaluate_status_unhealthy_code(self):
        checker = HealthChecker()
        status = checker._evaluate_status(500, 100)
        self.assertEqual(status, Status.UNHEALTHY)

    def test_evaluate_status_expected_code(self):
        checker = HealthChecker(expected_status=201)
        status = checker._evaluate_status(201, 100)
        self.assertEqual(status, Status.HEALTHY)

    def test_evaluate_status_unexpected_code(self):
        checker = HealthChecker(expected_status=201)
        status = checker._evaluate_status(200, 100)
        self.assertEqual(status, Status.UNHEALTHY)

    def test_check_sync_real_url(self):
        checker = HealthChecker(timeout=10, degraded_threshold_ms=5000, unhealthy_threshold_ms=30000)
        result = checker.check_sync("https://httpbin.org/status/200")
        self.assertEqual(result.status_code, 200)
        self.assertIn(result.status, [Status.HEALTHY, Status.DEGRADED])
        self.assertGreater(result.response_time_ms, 0)

    def test_check_sync_404(self):
        checker = HealthChecker(timeout=10)
        result = checker.check_sync("https://httpbin.org/status/404")
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.status, Status.UNHEALTHY)

    def test_check_sync_invalid_url(self):
        checker = HealthChecker(timeout=5)
        result = checker.check_sync("https://this-domain-does-not-exist-12345.com")
        self.assertEqual(result.status, Status.UNHEALTHY)
        self.assertIsNotNone(result.error)

    def test_check_sync_timeout(self):
        checker = HealthChecker(timeout=0.001)
        result = checker.check_sync("https://httpbin.org/delay/5")
        self.assertIn(result.status, [Status.UNHEALTHY, Status.UNKNOWN])


class TestConfigParser(unittest.TestCase):
    """Test configuration parsing."""

    def test_parse_json(self):
        content = json.dumps({
            "interval": 60,
            "duration": 300,
            "endpoints": [
                {
                    "name": "Test API",
                    "url": "https://httpbin.org/status/200",
                    "method": "GET",
                    "timeout": 5,
                }
            ],
        })
        config = ConfigParser.parse_json(content)
        self.assertEqual(config.interval, 60)
        self.assertEqual(config.duration, 300)
        self.assertEqual(len(config.endpoints), 1)
        self.assertEqual(config.endpoints[0].name, "Test API")
        self.assertEqual(config.endpoints[0].url, "https://httpbin.org/status/200")

    def test_parse_yaml(self):
        content = """
interval: 30
duration: 0
endpoints:
  - name: Test
    url: https://example.com
    method: GET
    timeout: 10
    tags:
      - test
"""
        config = ConfigParser.parse_yaml(content)
        self.assertEqual(config.interval, 30)
        self.assertEqual(len(config.endpoints), 1)
        self.assertEqual(config.endpoints[0].name, "Test")
        self.assertEqual(config.endpoints[0].tags, ["test"])

    def test_global_headers_merge(self):
        content = json.dumps({
            "global_headers": {"X-Custom": "value"},
            "endpoints": [
                {"name": "Test", "url": "https://example.com", "headers": {"X-Local": "local"}},
            ],
        })
        config = ConfigParser.parse_json(content)
        self.assertIn("X-Custom", config.endpoints[0].headers)
        self.assertIn("X-Local", config.endpoints[0].headers)

    def test_generate_sample_config(self):
        sample = ConfigParser.generate_sample_config()
        self.assertIn("APIPulse", sample)
        self.assertIn("endpoints", sample)

    def test_load_json_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"interval": 45, "endpoints": []}, f)
            f.flush()
            config = ConfigParser.load_file(f.name)
            self.assertEqual(config.interval, 45)
        os.unlink(f.name)

    def test_disabled_endpoints_filtered(self):
        content = json.dumps({
            "endpoints": [
                {"name": "Enabled", "url": "https://a.com", "enabled": True},
                {"name": "Disabled", "url": "https://b.com", "enabled": False},
            ],
        })
        config = ConfigParser.parse_json(content)
        enabled = config.get_enabled_endpoints()
        self.assertEqual(len(enabled), 1)
        self.assertEqual(enabled[0].name, "Enabled")


class TestMonitorSession(unittest.TestCase):
    """Test MonitorSession tracking."""

    def test_add_result_updates_counts(self):
        session = MonitorSession()
        r1 = CheckResult(url="https://a.com", status=Status.HEALTHY, status_code=200, response_time_ms=100)
        r2 = CheckResult(url="https://a.com", status=Status.DEGRADED, status_code=200, response_time_ms=2000)
        r3 = CheckResult(url="https://b.com", status=Status.UNHEALTHY, status_code=500, response_time_ms=100)

        session.add_result(r1)
        session.add_result(r2)
        session.add_result(r3)

        self.assertEqual(session.total_checks, 3)
        self.assertEqual(session.healthy_count, 1)
        self.assertEqual(session.degraded_count, 1)
        self.assertEqual(session.unhealthy_count, 1)
        self.assertEqual(len(session.endpoint_stats), 2)

    def test_get_summary(self):
        session = MonitorSession()
        session.add_result(CheckResult(url="https://a.com", status=Status.HEALTHY, status_code=200, response_time_ms=100))
        summary = session.get_summary()
        self.assertEqual(summary["total_checks"], 1)
        self.assertEqual(summary["health_rate"], 100.0)

    def test_consecutive_failures_tracking(self):
        session = MonitorSession()
        session.add_result(CheckResult(url="https://a.com", status=Status.UNHEALTHY, status_code=500, response_time_ms=100))
        session.add_result(CheckResult(url="https://a.com", status=Status.UNHEALTHY, status_code=500, response_time_ms=100))
        session.add_result(CheckResult(url="https://a.com", status=Status.UNHEALTHY, status_code=500, response_time_ms=100))
        self.assertEqual(session.endpoint_stats["https://a.com"]["consecutive_failures"], 3)

    def test_consecutive_failures_reset(self):
        session = MonitorSession()
        session.add_result(CheckResult(url="https://a.com", status=Status.UNHEALTHY, status_code=500, response_time_ms=100))
        session.add_result(CheckResult(url="https://a.com", status=Status.HEALTHY, status_code=200, response_time_ms=100))
        self.assertEqual(session.endpoint_stats["https://a.com"]["consecutive_failures"], 0)


class TestAlertManager(unittest.TestCase):
    """Test AlertManager."""

    def test_no_alert_on_healthy(self):
        manager = AlertManager(failure_threshold=3)
        alert = manager.evaluate("https://a.com", Status.HEALTHY, 100, 200)
        self.assertIsNone(alert)

    def test_alert_on_consecutive_failures(self):
        manager = AlertManager(failure_threshold=3)
        manager.evaluate("https://a.com", Status.UNHEALTHY, 100, 500)
        manager.evaluate("https://a.com", Status.UNHEALTHY, 100, 500)
        alert = manager.evaluate("https://a.com", Status.UNHEALTHY, 100, 500)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.level, AlertLevel.CRITICAL)

    def test_alert_on_status_change_to_unhealthy(self):
        manager = AlertManager(failure_threshold=3)
        manager.evaluate("https://a.com", Status.HEALTHY, 100, 200)
        alert = manager.evaluate("https://a.com", Status.UNHEALTHY, 100, 500)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.level, AlertLevel.CRITICAL)

    def test_alert_on_recovery(self):
        manager = AlertManager(failure_threshold=3)
        manager.evaluate("https://a.com", Status.UNHEALTHY, 100, 500)
        alert = manager.evaluate("https://a.com", Status.HEALTHY, 100, 200)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.level, AlertLevel.RECOVERY)

    def test_alert_summary(self):
        manager = AlertManager(failure_threshold=1)
        manager.evaluate("https://a.com", Status.UNHEALTHY, 100, 500)
        summary = manager.get_summary()
        self.assertEqual(summary["total_alerts"], 1)
        self.assertEqual(summary["critical"], 1)


class TestReportGenerator(unittest.TestCase):
    """Test report generation."""

    def test_format_json(self):
        session = MonitorSession(session_id="test123")
        session.add_result(CheckResult(url="https://a.com", status=Status.HEALTHY, status_code=200, response_time_ms=100))
        report = ReportGenerator.format_json(session)
        data = json.loads(report)
        self.assertIn("summary", data)
        self.assertIn("results", data)

    def test_format_markdown(self):
        session = MonitorSession(session_id="test123")
        session.add_result(CheckResult(url="https://a.com", status=Status.HEALTHY, status_code=200, response_time_ms=100))
        report = ReportGenerator.format_markdown(session)
        self.assertIn("APIPulse", report)

    def test_format_table(self):
        session = MonitorSession(session_id="test123")
        session.add_result(CheckResult(url="https://a.com", status=Status.HEALTHY, status_code=200, response_time_ms=100))
        report = ReportGenerator.format_table(session)
        self.assertIn("APIPulse", report)

    def test_format_single_check(self):
        result = CheckResult(
            url="https://example.com",
            status_code=200,
            response_time_ms=150.5,
            status=Status.HEALTHY,
        )
        report = ReportGenerator.format_single_check(result)
        self.assertIn("example.com", report)
        self.assertIn("200", report)


if __name__ == "__main__":
    unittest.main()
