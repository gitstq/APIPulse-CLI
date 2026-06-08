"""
APIPulse-CLI - Configuration management.

Handles loading, validating, and managing endpoint configurations
from YAML-like config files or direct dictionary input.
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class EndpointConfig:
    """Configuration for a single API endpoint."""
    name: str = ""
    url: str = ""
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    timeout: float = 10.0
    expected_status: Optional[int] = None
    degraded_threshold_ms: float = 1000.0
    unhealthy_threshold_ms: float = 5000.0
    tags: List[str] = field(default_factory=list)
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "body": self.body,
            "timeout": self.timeout,
            "expected_status": self.expected_status,
            "degraded_threshold_ms": self.degraded_threshold_ms,
            "unhealthy_threshold_ms": self.unhealthy_threshold_ms,
            "tags": self.tags,
            "enabled": self.enabled,
        }


@dataclass
class MonitorConfig:
    """Global monitoring configuration."""
    endpoints: List[EndpointConfig] = field(default_factory=list)
    interval: float = 30.0
    duration: float = 0.0  # 0 means run indefinitely
    alert_threshold: int = 3  # consecutive failures before alert
    output_format: str = "table"  # table, json, markdown
    ssl_verify: bool = True
    global_headers: Dict[str, str] = field(default_factory=dict)
    global_timeout: float = 10.0
    report_file: Optional[str] = None

    def get_enabled_endpoints(self) -> List[EndpointConfig]:
        """Return only enabled endpoints."""
        return [ep for ep in self.endpoints if ep.enabled]


class ConfigParser:
    """
    Parses configuration from JSON files.

    Supports a simple JSON format for endpoint definitions.
    Also supports a YAML-like format parsed manually (without PyYAML dependency).
    """

    @staticmethod
    def parse_json(content: str) -> MonitorConfig:
        """Parse JSON configuration content."""
        data = json.loads(content)
        return ConfigParser._parse_dict(data)

    @staticmethod
    def parse_yaml(content: str) -> MonitorConfig:
        """
        Parse a simplified YAML-like configuration.

        Supports basic YAML syntax: key-value pairs, lists, indented blocks.
        Does NOT require PyYAML - uses a lightweight manual parser.
        """
        data = ConfigParser._simple_yaml_to_dict(content)
        return ConfigParser._parse_dict(data)

    @staticmethod
    def _simple_yaml_to_dict(content: str) -> Dict[str, Any]:
        """
        Convert simplified YAML to dictionary.
        Handles basic YAML structures: mappings, lists, strings, numbers, booleans.
        """
        lines = content.split("\n")
        result = ConfigParser._parse_yaml_lines(lines, 0, 0)[0]
        return result

    @staticmethod
    def _get_indent(line: str) -> int:
        """Get indentation level of a line."""
        return len(line) - len(line.lstrip())

    @staticmethod
    def _parse_yaml_lines(lines: List[str], start: int, base_indent: int):
        """Recursively parse YAML lines into Python objects."""
        result = {}
        list_key = None  # Track which key is currently a list
        current_list_item = None  # Track current list item dict being built
        i = start

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                i += 1
                continue

            indent = ConfigParser._get_indent(line)

            if indent < base_indent:
                break

            if indent > base_indent:
                # This is nested content under the current key or list item
                if current_list_item is not None:
                    # Nested content under a list item
                    nested, i = ConfigParser._parse_yaml_lines(lines, i, indent)
                    current_list_item.update(nested)
                    continue
                elif list_key is not None:
                    # Nested list items
                    nested, i = ConfigParser._parse_yaml_lines(lines, i, indent)
                    if isinstance(nested, dict) and "_list_" in nested:
                        result[list_key].extend(nested["_list_"])
                    continue
                else:
                    i += 1
                    continue

            # List item at base_indent
            if stripped.startswith("- "):
                value_part = stripped[2:].strip()

                # Determine which key this list belongs to
                # If the value_part contains ":", it's a dict item in the list
                if ":" in value_part:
                    colon_pos = value_part.index(":")
                    item_key = value_part[:colon_pos].strip()
                    item_value = value_part[colon_pos + 1:].strip()
                    current_list_item = {item_key: ConfigParser._parse_yaml_value(item_value) if item_value else None}
                else:
                    current_list_item = ConfigParser._parse_yaml_value(value_part)

                # Find or create the list in result
                if list_key is None:
                    # Try to infer the list key from context (use a generic one)
                    list_key = "_list_"
                if list_key not in result:
                    result[list_key] = []
                result[list_key].append(current_list_item)
                i += 1
                continue

            # Non-list line resets list context
            current_list_item = None

            # Key-value pair
            if ":" in stripped:
                colon_pos = stripped.index(":")
                key = stripped[:colon_pos].strip()
                value_part = stripped[colon_pos + 1:].strip()

                if not value_part:
                    # Look ahead for nested content
                    i += 1
                    if i < len(lines):
                        next_indent = ConfigParser._get_indent(lines[i])
                        if next_indent > indent:
                            nested, i = ConfigParser._parse_yaml_lines(lines, i, next_indent)
                            if isinstance(nested, dict) and "_list_" in nested:
                                result[key] = nested["_list_"]
                                list_key = key  # Track this key as a list key
                            else:
                                result[key] = nested
                            continue
                    result[key] = None
                else:
                    result[key] = ConfigParser._parse_yaml_value(value_part)

            i += 1

        return result, i

    @staticmethod
    def _parse_yaml_value(value: str) -> Any:
        """Parse a YAML scalar value."""
        # Remove quotes
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]

        # Boolean
        if value.lower() in ("true", "yes", "on"):
            return True
        if value.lower() in ("false", "no", "off"):
            return False

        # None
        if value.lower() in ("null", "none", "~", ""):
            return None

        # Number
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        return value

    @staticmethod
    def _parse_dict(data: Dict[str, Any]) -> MonitorConfig:
        """Parse a dictionary into MonitorConfig."""
        config = MonitorConfig()

        # Global settings
        config.interval = data.get("interval", 30.0)
        config.duration = data.get("duration", 0.0)
        config.alert_threshold = data.get("alert_threshold", 3)
        config.output_format = data.get("output_format", "table")
        config.ssl_verify = data.get("ssl_verify", True)
        config.global_headers = data.get("global_headers", {})
        config.global_timeout = data.get("global_timeout", 10.0)
        config.report_file = data.get("report_file", None)

        # Parse endpoints
        endpoints_data = data.get("endpoints", [])
        for ep_data in endpoints_data:
            if isinstance(ep_data, dict):
                ep = EndpointConfig(
                    name=ep_data.get("name", ""),
                    url=ep_data.get("url", ""),
                    method=ep_data.get("method", "GET"),
                    headers={**config.global_headers, **ep_data.get("headers", {})},
                    body=ep_data.get("body", None),
                    timeout=ep_data.get("timeout", config.global_timeout),
                    expected_status=ep_data.get("expected_status", None),
                    degraded_threshold_ms=ep_data.get("degraded_threshold_ms", 1000.0),
                    unhealthy_threshold_ms=ep_data.get("unhealthy_threshold_ms", 5000.0),
                    tags=ep_data.get("tags", []),
                    enabled=ep_data.get("enabled", True),
                )
                config.endpoints.append(ep)

        return config

    @staticmethod
    def load_file(filepath: str) -> MonitorConfig:
        """
        Load configuration from a file.
        Auto-detects format based on file extension.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        ext = os.path.splitext(filepath)[1].lower()

        if ext in (".yaml", ".yml"):
            return ConfigParser.parse_yaml(content)
        elif ext == ".json":
            return ConfigParser.parse_json(content)
        else:
            # Try JSON first, then YAML
            try:
                return ConfigParser.parse_json(content)
            except (json.JSONDecodeError, ValueError):
                return ConfigParser.parse_yaml(content)

    @staticmethod
    def generate_sample_config() -> str:
        """Generate a sample configuration file content."""
        return """# APIPulse-CLI Configuration
# 轻量级终端API健康监控引擎 配置文件

# Global settings
interval: 30          # Check interval in seconds
duration: 0          # Total monitoring duration (0 = infinite)
alert_threshold: 3   # Consecutive failures before alert
output_format: table # Output format: table, json, markdown
ssl_verify: true     # Verify SSL certificates
global_timeout: 10   # Default request timeout in seconds
report_file: health_results.json  # Auto-save results to file

# Global headers applied to all endpoints
global_headers:
  User-Agent: APIPulse-CLI/1.0.0
  Accept: application/json

# Endpoint definitions
endpoints:
  - name: Google DNS
    url: https://dns.google/resolve?name=example.com
    method: GET
    timeout: 5
    expected_status: 200
    degraded_threshold_ms: 500
    unhealthy_threshold_ms: 2000
    tags:
      - dns
      - external

  - name: HTTPBin Status
    url: https://httpbin.org/status/200
    method: GET
    timeout: 10
    expected_status: 200
    tags:
      - test
      - external

  - name: GitHub API
    url: https://api.github.com/zen
    method: GET
    timeout: 10
    expected_status: 200
    degraded_threshold_ms: 1000
    unhealthy_threshold_ms: 5000
    tags:
      - api
      - external
"""
