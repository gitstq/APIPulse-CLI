"""
APIPulse-CLI - Command-line interface.

Provides the main CLI entry point with subcommands for health checking,
monitoring, report generation, and configuration management.
"""

import argparse
import asyncio
import json
import os
import sys
import time
import uuid

from .__init__ import __version__
from .checker import HealthChecker, CheckResult, Status
from .config import ConfigParser, MonitorConfig, EndpointConfig
from .reporter import ReportGenerator, MonitorSession
from .alerts import AlertManager, Alert


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for APIPulse CLI."""
    parser = argparse.ArgumentParser(
        prog="apipulse",
        description="🩺 APIPulse-CLI - Lightweight Terminal API Health Monitoring Engine\n"
                    "轻量级终端API健康监控引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  apipulse check https://api.example.com/health
  apipulse check https://api.example.com/health --interval 5 --count 10
  apipulse monitor endpoints.yaml --interval 30 --duration 300
  apipulse init --output my_endpoints.yaml
  apipulse report results.json --format markdown --output report.md
  apipulse version
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'check' subcommand
    check_parser = subparsers.add_parser(
        "check",
        help="Perform a health check against a single endpoint",
        description="Check the health of a single API endpoint",
    )
    check_parser.add_argument("url", help="URL of the endpoint to check")
    check_parser.add_argument("--method", "-m", default="GET", help="HTTP method (default: GET)")
    check_parser.add_argument("--headers", "-H", help="Custom headers (JSON format)")
    check_parser.add_argument("--body", "-b", help="Request body for POST/PUT")
    check_parser.add_argument("--timeout", "-t", type=float, default=10.0, help="Timeout in seconds (default: 10)")
    check_parser.add_argument("--expected-status", "-e", type=int, help="Expected HTTP status code")
    check_parser.add_argument("--interval", "-i", type=float, default=0, help="Repeat interval in seconds (0 = single check)")
    check_parser.add_argument("--count", "-n", type=int, default=1, help="Number of checks (default: 1)")
    check_parser.add_argument("--output", "-o", help="Output format: table, json (default: table)")
    check_parser.add_argument("--no-ssl-verify", action="store_true", help="Disable SSL verification")

    # 'monitor' subcommand
    monitor_parser = subparsers.add_parser(
        "monitor",
        help="Monitor multiple endpoints from a config file",
        description="Continuously monitor multiple API endpoints",
    )
    monitor_parser.add_argument("config", help="Path to configuration file (YAML/JSON)")
    monitor_parser.add_argument("--interval", "-i", type=float, help="Override check interval")
    monitor_parser.add_argument("--duration", "-d", type=float, help="Total monitoring duration in seconds")
    monitor_parser.add_argument("--alert-threshold", "-a", type=int, help="Consecutive failures before alert")
    monitor_parser.add_argument("--output", "-o", default="table", help="Output format: table, json, markdown")
    monitor_parser.add_argument("--report-file", "-r", help="Save results to file")

    # 'report' subcommand
    report_parser = subparsers.add_parser(
        "report",
        help="Generate a report from saved results",
        description="Generate a formatted report from a JSON results file",
    )
    report_parser.add_argument("results_file", help="Path to JSON results file")
    report_parser.add_argument("--format", "-f", default="table", help="Report format: table, markdown")
    report_parser.add_argument("--output", "-o", help="Output file path (default: stdout)")

    # 'init' subcommand
    init_parser = subparsers.add_parser(
        "init",
        help="Generate a sample configuration file",
        description="Create a sample configuration file for endpoint monitoring",
    )
    init_parser.add_argument("--output", "-o", default="apipulse_config.yaml", help="Output file path")

    # 'list' subcommand
    subparsers.add_parser(
        "list",
        help="List available subcommands",
        description="Show all available APIPulse commands",
    )

    # 'version' subcommand
    subparsers.add_parser(
        "version",
        help="Show version information",
        description="Display APIPulse-CLI version",
    )

    return parser


def cmd_check(args):
    """Execute the 'check' subcommand."""
    # Parse custom headers
    custom_headers = {}
    if args.headers:
        try:
            custom_headers = json.loads(args.headers)
        except json.JSONDecodeError:
            print(f"⚠️  Invalid JSON headers format: {args.headers}", file=sys.stderr)
            sys.exit(1)

    checker = HealthChecker(
        timeout=args.timeout,
        expected_status=args.expected_status,
        custom_headers=custom_headers,
        custom_body=args.body,
        ssl_verify=not args.no_ssl_verify,
    )

    session = MonitorSession(session_id=str(uuid.uuid4())[:8])

    count = max(args.count, 1)
    interval = max(args.interval, 0)

    try:
        for i in range(count):
            result = checker.check_sync(args.url, args.method)
            session.add_result(result)

            if args.output == "json":
                print(result.to_json())
            else:
                print(ReportGenerator.format_single_check(result))

            if interval > 0 and i < count - 1:
                time.sleep(interval)

    except KeyboardInterrupt:
        print("\n⚠️  Monitoring interrupted by user")

    # Print summary if multiple checks
    if count > 1:
        print(ReportGenerator.format_table(session))


def cmd_monitor(args):
    """Execute the 'monitor' subcommand."""
    # Load configuration
    try:
        config = ConfigParser.load_file(args.config)
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {args.config}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to parse configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Apply CLI overrides
    if args.interval is not None:
        config.interval = args.interval
    if args.duration is not None:
        config.duration = args.duration
    if args.alert_threshold is not None:
        config.alert_threshold = args.alert_threshold
    if args.report_file:
        config.report_file = args.report_file

    endpoints = config.get_enabled_endpoints()
    if not endpoints:
        print("⚠️  No enabled endpoints found in configuration", file=sys.stderr)
        sys.exit(1)

    # Setup alert manager
    alert_manager = AlertManager(
        failure_threshold=config.alert_threshold,
        on_alert=lambda alert: print(alert_manager.format_alert(alert)),
    )

    # Setup session
    session = MonitorSession(session_id=str(uuid.uuid4())[:8])

    print(f"\n🩺 APIPulse Monitor Started")
    print(f"   Endpoints: {len(endpoints)}")
    print(f"   Interval:  {config.interval}s")
    print(f"   Duration:  {'∞' if config.duration == 0 else f'{config.duration}s'}")
    print(f"   Format:    {args.output}")
    print(f"   Press Ctrl+C to stop\n")

    start_time = time.time()
    check_count = 0

    try:
        while True:
            # Check duration limit
            if config.duration > 0 and (time.time() - start_time) >= config.duration:
                print(f"\n⏰ Duration limit reached ({config.duration}s)")
                break

            # Perform checks for all endpoints
            for ep in endpoints:
                checker = HealthChecker(
                    timeout=ep.timeout,
                    expected_status=ep.expected_status,
                    degraded_threshold_ms=ep.degraded_threshold_ms,
                    unhealthy_threshold_ms=ep.unhealthy_threshold_ms,
                    custom_headers=ep.headers,
                    custom_body=ep.body,
                    ssl_verify=config.ssl_verify,
                )

                result = checker.check_sync(ep.url, ep.method)
                session.add_result(result)

                # Evaluate alerts
                alert_manager.evaluate(
                    url=ep.url,
                    status=result.status,
                    response_time_ms=result.response_time_ms,
                    status_code=result.status_code,
                )

            check_count += 1

            # Print live status line
            summary = session.get_summary()
            healthy_pct = summary["health_rate"]
            icon = "✅" if healthy_pct >= 90 else "⚠️" if healthy_pct >= 70 else "❌"
            ts = time.strftime("%H:%M:%S")
            print(
                f"\r[{ts}] {icon} Check #{check_count} | "
                f"Healthy: {healthy_pct}% | "
                f"Avg: {summary['avg_response_ms']}ms | "
                f"Alerts: {alert_manager.get_summary()['total_alerts']}",
                end="", flush=True,
            )

            # Save intermediate results
            if config.report_file and check_count % 5 == 0:
                try:
                    with open(config.report_file, "w", encoding="utf-8") as f:
                        f.write(session.to_json())
                except Exception:
                    pass

            # Wait for next interval
            if config.interval > 0:
                time.sleep(config.interval)

    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring stopped by user")

    # Final report
    session.end_time = time.time()
    print(ReportGenerator.generate(session, args.output))

    # Save final results
    if config.report_file:
        try:
            with open(config.report_file, "w", encoding="utf-8") as f:
                f.write(session.to_json())
            print(f"💾 Results saved to: {config.report_file}")
        except Exception as e:
            print(f"⚠️  Failed to save results: {e}")


def cmd_report(args):
    """Execute the 'report' subcommand."""
    try:
        with open(args.results_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Results file not found: {args.results_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in results file: {e}", file=sys.stderr)
        sys.exit(1)

    # Reconstruct session from data
    session = MonitorSession(session_id=data.get("summary", {}).get("session_id", ""))
    session.start_time = data.get("summary", {}).get("start_time", 0)
    session.end_time = data.get("summary", {}).get("end_time", 0)

    for r_data in data.get("results", []):
        result = CheckResult(
            url=r_data.get("url", ""),
            method=r_data.get("method", "GET"),
            status_code=r_data.get("status_code", 0),
            response_time_ms=r_data.get("response_time_ms", 0),
            status=Status(r_data.get("status", "unknown")),
            error=r_data.get("error"),
            headers=r_data.get("headers", {}),
            body_length=r_data.get("body_length", 0),
            body_preview=r_data.get("body_preview", ""),
            timestamp=r_data.get("timestamp", 0),
            dns_time_ms=r_data.get("dns_time_ms", 0),
            connect_time_ms=r_data.get("connect_time_ms", 0),
            tls_time_ms=r_data.get("tls_time_ms", 0),
        )
        session.add_result(result)

    # Rebuild endpoint stats
    for url, stats in data.get("endpoint_stats", {}).items():
        session.endpoint_stats[url] = stats

    report = ReportGenerator.generate(session, args.format)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"📄 Report saved to: {args.output}")
    else:
        print(report)


def cmd_init(args):
    """Execute the 'init' subcommand."""
    content = ConfigParser.generate_sample_config()
    output_path = args.output

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Sample configuration created: {output_path}")
        print(f"   Edit this file to add your endpoints, then run:")
        print(f"   apipulse monitor {output_path}")
    except Exception as e:
        print(f"❌ Failed to create config file: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args):
    """Execute the 'list' subcommand."""
    print("""
🩺 APIPulse-CLI - Available Commands
═══════════════════════════════════════

  check      Perform a health check against a single endpoint
  monitor    Monitor multiple endpoints from a config file
  report     Generate a report from saved results
  init       Generate a sample configuration file
  list       Show this help message
  version    Show version information

═══════════════════════════════════════
Run 'apipulse <command> --help' for detailed usage.
""")


def cmd_version(args):
    """Execute the 'version' subcommand."""
    print(f"""
🩺 APIPulse-CLI v{__version__}
   Lightweight Terminal API Health Monitoring Engine
   轻量级终端API健康监控引擎

   Python: {sys.version.split()[0]}
   Platform: {sys.platform}
""")


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "check": cmd_check,
        "monitor": cmd_monitor,
        "report": cmd_report,
        "init": cmd_init,
        "list": cmd_list,
        "version": cmd_version,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
