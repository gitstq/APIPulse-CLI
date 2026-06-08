"""
APIPulse-CLI - Report generation engine.

Generates health monitoring reports in multiple formats:
JSON, Markdown, and terminal table output.
"""

import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .checker import CheckResult, Status


@dataclass
class MonitorSession:
    """Represents a complete monitoring session with all results."""
    session_id: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    results: List[CheckResult] = field(default_factory=list)
    endpoint_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    total_checks: int = 0
    healthy_count: int = 0
    degraded_count: int = 0
    unhealthy_count: int = 0
    unknown_count: int = 0

    def add_result(self, result: CheckResult):
        """Add a check result and update statistics."""
        self.results.append(result)
        self.total_checks += 1

        if result.status == Status.HEALTHY:
            self.healthy_count += 1
        elif result.status == Status.DEGRADED:
            self.degraded_count += 1
        elif result.status == Status.UNHEALTHY:
            self.unhealthy_count += 1
        else:
            self.unknown_count += 1

        # Update per-endpoint stats
        url = result.url
        if url not in self.endpoint_stats:
            self.endpoint_stats[url] = {
                "total": 0,
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0,
                "unknown": 0,
                "response_times": [],
                "last_status": Status.UNKNOWN.value,
                "consecutive_failures": 0,
            }

        stats = self.endpoint_stats[url]
        stats["total"] += 1
        stats[result.status.value] += 1
        stats["response_times"].append(result.response_time_ms)
        stats["last_status"] = result.status.value

        # Track consecutive failures
        if result.status == Status.UNHEALTHY:
            stats["consecutive_failures"] += 1
        else:
            stats["consecutive_failures"] = 0

    def get_summary(self) -> Dict[str, Any]:
        """Get session summary statistics."""
        avg_response = 0.0
        if self.results:
            avg_response = sum(r.response_time_ms for r in self.results) / len(self.results)

        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time or time.time(),
            "duration": (self.end_time or time.time()) - self.start_time,
            "total_checks": self.total_checks,
            "healthy_count": self.healthy_count,
            "degraded_count": self.degraded_count,
            "unhealthy_count": self.unhealthy_count,
            "unknown_count": self.unknown_count,
            "health_rate": (
                round(self.healthy_count / self.total_checks * 100, 1)
                if self.total_checks > 0
                else 0.0
            ),
            "avg_response_ms": round(avg_response, 2),
            "endpoint_count": len(self.endpoint_stats),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "summary": self.get_summary(),
            "results": [r.to_dict() for r in self.results],
            "endpoint_stats": self.endpoint_stats,
        }

    def to_json(self) -> str:
        """Serialize session to JSON."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class ReportGenerator:
    """Generates reports in various formats."""

    # Terminal colors
    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "gray": "\033[90m",
        "white": "\033[97m",
    }

    STATUS_ICONS = {
        Status.HEALTHY: "✅",
        Status.DEGRADED: "⚠️",
        Status.UNHEALTHY: "❌",
        Status.UNKNOWN: "❓",
    }

    STATUS_COLORS = {
        Status.HEALTHY: "green",
        Status.DEGRADED: "yellow",
        Status.UNHEALTHY: "red",
        Status.UNKNOWN: "gray",
    }

    @staticmethod
    def _color(text: str, color: str) -> str:
        """Apply terminal color to text."""
        c = ReportGenerator.COLORS.get(color, "")
        reset = ReportGenerator.COLORS["reset"]
        return f"{c}{text}{reset}"

    @staticmethod
    def _bold(text: str) -> str:
        """Apply bold formatting."""
        return f"{ReportGenerator.COLORS['bold']}{text}{ReportGenerator.COLORS['reset']}"

    @classmethod
    def format_table(cls, session: MonitorSession) -> str:
        """Format session results as a terminal table."""
        lines = []
        summary = session.get_summary()

        # Header
        lines.append("")
        lines.append(cls._bold("╔══════════════════════════════════════════════════════════╗"))
        lines.append(cls._bold("║          🩺 APIPulse Monitor Report                 ║"))
        lines.append(cls._bold("╚══════════════════════════════════════════════════════════╝"))
        lines.append("")

        # Summary
        lines.append(cls._bold("📊 Summary"))
        lines.append(f"   Total Checks:    {summary['total_checks']}")
        lines.append(
            f"   Health Rate:     {cls._color(str(summary['health_rate']) + '%', 'green' if summary['health_rate'] >= 90 else 'yellow' if summary['health_rate'] >= 70 else 'red')}"
        )
        lines.append(f"   Avg Response:    {summary['avg_response_ms']}ms")
        lines.append(f"   Endpoints:       {summary['endpoint_count']}")
        lines.append(f"   Duration:        {round(summary['duration'], 1)}s")
        lines.append("")

        # Status breakdown
        lines.append(cls._bold("📈 Status Breakdown"))
        lines.append(
            f"   ✅ Healthy:   {cls._color(str(session.healthy_count), 'green'):>5}  ({round(session.healthy_count / max(session.total_checks, 1) * 100, 1)}%)"
        )
        lines.append(
            f"   ⚠️  Degraded:  {cls._color(str(session.degraded_count), 'yellow'):>5}  ({round(session.degraded_count / max(session.total_checks, 1) * 100, 1)}%)"
        )
        lines.append(
            f"   ❌ Unhealthy: {cls._color(str(session.unhealthy_count), 'red'):>5}  ({round(session.unhealthy_count / max(session.total_checks, 1) * 100, 1)}%)"
        )
        lines.append(
            f"   ❓ Unknown:   {cls._color(str(session.unknown_count), 'gray'):>5}  ({round(session.unknown_count / max(session.total_checks, 1) * 100, 1)}%)"
        )
        lines.append("")

        # Per-endpoint details
        if session.endpoint_stats:
            lines.append(cls._bold("🔗 Endpoint Details"))
            lines.append(
                f"   {'URL':<45} {'Status':<12} {'Checks':>7} {'Avg(ms)':>9} {'Fail':>5}"
            )
            lines.append(
                f"   {'─' * 45} {'─' * 12} {'─' * 7} {'─' * 9} {'─' * 5}"
            )

            for url, stats in session.endpoint_stats.items():
                display_url = url[:44] + ".." if len(url) > 46 else url
                status = stats["last_status"]
                icon = cls.STATUS_ICONS.get(Status(status), "❓")
                color = cls.STATUS_COLORS.get(Status(status), "gray")

                avg_time = (
                    round(sum(stats["response_times"]) / len(stats["response_times"]), 1)
                    if stats["response_times"]
                    else 0.0
                )

                lines.append(
                    f"   {cls._color(display_url, color):<45} "
                    f"{icon} {status:<10} "
                    f"{cls._color(str(stats['total']), 'white'):>7} "
                    f"{cls._color(str(avg_time), color):>9} "
                    f"{cls._color(str(stats['consecutive_failures']), 'red' if stats['consecutive_failures'] > 0 else 'green'):>5}"
                )

        lines.append("")

        # Recent results
        if session.results:
            recent = session.results[-10:]  # Show last 10
            lines.append(cls._bold("🕐 Recent Checks"))
            for r in recent:
                icon = cls.STATUS_ICONS.get(r.status, "❓")
                color = cls.STATUS_COLORS.get(r.status, "gray")
                ts = time.strftime("%H:%M:%S", time.localtime(r.timestamp))
                lines.append(
                    f"   [{ts}] {icon} {r.method} {r.url[:50]} → "
                    f"{cls._color(str(r.status_code), color)} "
                    f"({r.response_time_ms}ms)"
                )

        lines.append("")
        return "\n".join(lines)

    @classmethod
    def format_json(cls, session: MonitorSession) -> str:
        """Format session as JSON."""
        return session.to_json()

    @classmethod
    def format_markdown(cls, session: MonitorSession) -> str:
        """Format session as Markdown report."""
        summary = session.get_summary()
        lines = []

        lines.append("# 🩺 APIPulse Monitor Report")
        lines.append("")
        lines.append(f"**Session ID:** `{summary['session_id']}`")
        lines.append(f"**Duration:** {round(summary['duration'], 1)}s")
        lines.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Summary table
        lines.append("## 📊 Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Checks | {summary['total_checks']} |")
        lines.append(f"| Health Rate | {summary['health_rate']}% |")
        lines.append(f"| Avg Response Time | {summary['avg_response_ms']}ms |")
        lines.append(f"| Endpoints Monitored | {summary['endpoint_count']} |")
        lines.append("")

        # Status breakdown
        lines.append("## 📈 Status Breakdown")
        lines.append("")
        lines.append("| Status | Count | Percentage |")
        lines.append("|--------|-------|------------|")
        lines.append(f"| ✅ Healthy | {session.healthy_count} | {round(session.healthy_count / max(session.total_checks, 1) * 100, 1)}% |")
        lines.append(f"| ⚠️ Degraded | {session.degraded_count} | {round(session.degraded_count / max(session.total_checks, 1) * 100, 1)}% |")
        lines.append(f"| ❌ Unhealthy | {session.unhealthy_count} | {round(session.unhealthy_count / max(session.total_checks, 1) * 100, 1)}% |")
        lines.append(f"| ❓ Unknown | {session.unknown_count} | {round(session.unknown_count / max(session.total_checks, 1) * 100, 1)}% |")
        lines.append("")

        # Endpoint details
        if session.endpoint_stats:
            lines.append("## 🔗 Endpoint Details")
            lines.append("")
            lines.append("| URL | Status | Checks | Avg Response | Consecutive Failures |")
            lines.append("|-----|--------|--------|-------------|---------------------|")

            for url, stats in session.endpoint_stats.items():
                avg_time = (
                    round(sum(stats["response_times"]) / len(stats["response_times"]), 1)
                    if stats["response_times"]
                    else 0.0
                )
                status_icon = "✅" if stats["last_status"] == "healthy" else "⚠️" if stats["last_status"] == "degraded" else "❌"
                lines.append(
                    f"| `{url}` | {status_icon} {stats['last_status']} | {stats['total']} | {avg_time}ms | {stats['consecutive_failures']} |"
                )

            lines.append("")

        # Recommendations
        lines.append("## 💡 Recommendations")
        lines.append("")
        if summary["health_rate"] >= 95:
            lines.append("- 🟢 All endpoints are performing well. No action needed.")
        elif summary["health_rate"] >= 80:
            lines.append("- 🟡 Some endpoints show degraded performance. Consider investigating slow responses.")
        else:
            lines.append("- 🔴 Multiple endpoints are unhealthy. Immediate investigation recommended.")

        for url, stats in session.endpoint_stats.items():
            if stats["consecutive_failures"] >= 3:
                lines.append(f"- ⚠️ `{url}` has {stats['consecutive_failures']} consecutive failures. Check connectivity and service status.")

        lines.append("")
        lines.append("---")
        lines.append("*Generated by [APIPulse-CLI](https://github.com/gitstq/APIPulse-CLI)*")
        lines.append("")

        return "\n".join(lines)

    @classmethod
    def format_single_check(cls, result: CheckResult) -> str:
        """Format a single check result for terminal output."""
        icon = cls.STATUS_ICONS.get(result.status, "❓")
        color = cls.STATUS_COLORS.get(result.status, "gray")
        ts = time.strftime("%H:%M:%S", time.localtime(result.timestamp))

        lines = []
        lines.append("")
        lines.append(cls._bold(f"🩺 APIPulse Check Result"))
        lines.append(f"   Time:     {ts}")
        lines.append(f"   URL:      {result.url}")
        lines.append(f"   Method:   {result.method}")
        lines.append(f"   Status:   {cls._color(f'{icon} {result.status.value.upper()}', color)}")
        lines.append(f"   Code:     {cls._color(str(result.status_code), color)}")
        lines.append(f"   Response: {result.response_time_ms}ms")
        lines.append(f"   DNS:      {result.dns_time_ms}ms")
        lines.append(f"   Connect:  {result.connect_time_ms}ms")

        if result.error:
            lines.append(f"   Error:    {cls._color(result.error, 'red')}")

        if result.body_preview:
            preview = result.body_preview[:200].replace("\n", " ")
            lines.append(f"   Body:     {preview}...")

        lines.append("")
        return "\n".join(lines)

    @classmethod
    def generate(cls, session: MonitorSession, fmt: str = "table") -> str:
        """Generate report in specified format."""
        if fmt == "json":
            return cls.format_json(session)
        elif fmt == "markdown":
            return cls.format_markdown(session)
        else:
            return cls.format_table(session)
