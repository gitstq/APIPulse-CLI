"""
APIPulse-CLI - Alert management system.

Handles alert triggering, notification formatting, and alert history tracking.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum

from .checker import Status


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    RECOVERY = "recovery"


@dataclass
class Alert:
    """Represents a single alert event."""
    endpoint_url: str
    level: AlertLevel
    message: str
    timestamp: float = field(default_factory=time.time)
    consecutive_failures: int = 0
    response_time_ms: float = 0.0
    status_code: int = 0
    acknowledged: bool = False

    def to_dict(self) -> Dict:
        return {
            "endpoint_url": self.endpoint_url,
            "level": self.level.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "consecutive_failures": self.consecutive_failures,
            "response_time_ms": self.response_time_ms,
            "status_code": self.status_code,
            "acknowledged": self.acknowledged,
        }


class AlertManager:
    """
    Manages alert triggering and notification.

    Monitors endpoint health and triggers alerts based on configurable
    thresholds for consecutive failures, response time degradation, and
    status changes.
    """

    # Terminal colors for alerts
    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "cyan": "\033[96m",
    }

    def __init__(
        self,
        failure_threshold: int = 3,
        degraded_threshold_ms: float = 1000.0,
        unhealthy_threshold_ms: float = 5000.0,
        on_alert: Optional[Callable[[Alert], None]] = None,
    ):
        self.failure_threshold = failure_threshold
        self.degraded_threshold_ms = degraded_threshold_ms
        self.unhealthy_threshold_ms = unhealthy_threshold_ms
        self.on_alert = on_alert
        self.alerts: List[Alert] = []
        self._previous_status: Dict[str, Status] = {}
        self._consecutive_failures: Dict[str, int] = {}

    def evaluate(
        self,
        url: str,
        status: Status,
        response_time_ms: float,
        status_code: int,
    ) -> Optional[Alert]:
        """
        Evaluate a check result and trigger alerts if necessary.

        Args:
            url: Endpoint URL
            status: Current health status
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code

        Returns:
            Alert object if an alert was triggered, None otherwise
        """
        alert = None

        # Track consecutive failures
        if status == Status.UNHEALTHY:
            self._consecutive_failures[url] = self._consecutive_failures.get(url, 0) + 1
        else:
            self._consecutive_failures[url] = 0

        # Check for consecutive failure threshold
        failures = self._consecutive_failures.get(url, 0)
        if failures == self.failure_threshold:
            alert = Alert(
                endpoint_url=url,
                level=AlertLevel.CRITICAL,
                message=f"Endpoint has failed {failures} consecutive times",
                consecutive_failures=failures,
                response_time_ms=response_time_ms,
                status_code=status_code,
            )

        # Check for status degradation
        prev_status = self._previous_status.get(url)
        if prev_status is not None and prev_status != status:
            if status == Status.UNHEALTHY and prev_status in (Status.HEALTHY, Status.DEGRADED):
                alert = Alert(
                    endpoint_url=url,
                    level=AlertLevel.CRITICAL,
                    message=f"Endpoint status changed from {prev_status.value} to {status.value}",
                    response_time_ms=response_time_ms,
                    status_code=status_code,
                )
            elif status == Status.DEGRADED and prev_status == Status.HEALTHY:
                alert = Alert(
                    endpoint_url=url,
                    level=AlertLevel.WARNING,
                    message=f"Endpoint performance degraded (response: {response_time_ms}ms)",
                    response_time_ms=response_time_ms,
                    status_code=status_code,
                )
            elif status == Status.HEALTHY and prev_status in (Status.UNHEALTHY, Status.DEGRADED):
                alert = Alert(
                    endpoint_url=url,
                    level=AlertLevel.RECOVERY,
                    message=f"Endpoint recovered to healthy status",
                    response_time_ms=response_time_ms,
                    status_code=status_code,
                )

        # Check for extremely slow responses
        if response_time_ms > self.unhealthy_threshold_ms and status != Status.UNHEALTHY:
            alert = Alert(
                endpoint_url=url,
                level=AlertLevel.WARNING,
                message=f"Slow response detected: {response_time_ms}ms (threshold: {self.unhealthy_threshold_ms}ms)",
                response_time_ms=response_time_ms,
                status_code=status_code,
            )

        # Update previous status
        self._previous_status[url] = status

        if alert:
            self.alerts.append(alert)
            if self.on_alert:
                self.on_alert(alert)

        return alert

    def format_alert(self, alert: Alert) -> str:
        """Format an alert for terminal output."""
        colors = self.COLORS
        level_colors = {
            AlertLevel.INFO: "cyan",
            AlertLevel.WARNING: "yellow",
            AlertLevel.CRITICAL: "red",
            AlertLevel.RECOVERY: "green",
        }
        level_icons = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.CRITICAL: "🚨",
            AlertLevel.RECOVERY: "✅",
        }

        color = colors.get(level_colors.get(alert.level, "cyan"), "")
        icon = level_icons.get(alert.level, "ℹ️")
        ts = time.strftime("%H:%M:%S", time.localtime(alert.timestamp))

        return (
            f"\n{colors['bold']}{color}{icon} [{alert.level.value.upper()}] "
            f"{alert.message}{colors['reset']}\n"
            f"   Endpoint: {alert.endpoint_url}\n"
            f"   Time: {ts} | Failures: {alert.consecutive_failures} | "
            f"Response: {alert.response_time_ms}ms\n"
        )

    def get_summary(self) -> Dict:
        """Get alert summary statistics."""
        critical = sum(1 for a in self.alerts if a.level == AlertLevel.CRITICAL)
        warnings = sum(1 for a in self.alerts if a.level == AlertLevel.WARNING)
        recoveries = sum(1 for a in self.alerts if a.level == AlertLevel.RECOVERY)
        return {
            "total_alerts": len(self.alerts),
            "critical": critical,
            "warnings": warnings,
            "recoveries": recoveries,
            "unacknowledged": sum(1 for a in self.alerts if not a.acknowledged),
        }
