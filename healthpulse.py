#!/usr/bin/env python3
"""
APIPulse-CLI - Lightweight Terminal API Health Monitoring Engine

A zero-dependency, pure Python CLI tool for monitoring API endpoint health,
tracking response times, detecting anomalies, and generating reports.

Usage:
    apipulse check <url> [--method METHOD] [--headers HEADERS] [--body BODY]
                       [--timeout TIMEOUT] [--expected-status STATUS]
                       [--interval INTERVAL] [--count COUNT]
    apipulse monitor <config_file> [--interval INTERVAL] [--duration DURATION]
                       [--alert-threshold THRESHOLD] [--output FORMAT]
    apipulse report <results_file> [--format FORMAT] [--output FILE]
    apipulse init [--output FILE]
    apipulse list
    apipulse version

Examples:
    apipulse check https://api.example.com/health
    apipulse check https://api.example.com/health --interval 5 --count 10
    apipulse monitor endpoints.yaml --interval 30 --duration 300
    apipulse init --output my_endpoints.yaml
    apipulse report results.json --format markdown --output report.md
"""

import sys
import os

# Add src to path for direct execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from healthpulse.cli import main

if __name__ == "__main__":
    main()
