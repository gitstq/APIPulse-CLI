"""
APIPulse-CLI - Core health check engine.

Provides the CheckResult dataclass and HealthChecker class for performing
HTTP health checks against API endpoints with configurable parameters.
"""

import asyncio
import json
import time
import urllib.request
import urllib.error
import ssl
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from enum import Enum


class Status(Enum):
    """Endpoint health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class CheckResult:
    """Result of a single health check against an endpoint."""
    url: str
    method: str = "GET"
    status_code: int = 0
    response_time_ms: float = 0.0
    status: Status = Status.UNKNOWN
    error: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    body_length: int = 0
    body_preview: str = ""
    timestamp: float = field(default_factory=time.time)
    dns_time_ms: float = 0.0
    connect_time_ms: float = 0.0
    tls_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result["status"] = self.status.value
        return result

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class HealthChecker:
    """
    Core health check engine.

    Performs HTTP requests against configured endpoints and evaluates
    their health based on status codes, response times, and custom rules.
    """

    # Default thresholds (in milliseconds)
    DEFAULT_TIMEOUT = 10.0  # seconds
    DEGRADED_THRESHOLD_MS = 1000.0
    UNHEALTHY_THRESHOLD_MS = 5000.0
    HEALTHY_STATUS_CODES = {200, 201, 204, 301, 302, 304}

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        expected_status: Optional[int] = None,
        degraded_threshold_ms: float = DEGRADED_THRESHOLD_MS,
        unhealthy_threshold_ms: float = UNHEALTHY_THRESHOLD_MS,
        custom_headers: Optional[Dict[str, str]] = None,
        custom_body: Optional[str] = None,
        ssl_verify: bool = True,
    ):
        self.timeout = timeout
        self.expected_status = expected_status
        self.degraded_threshold_ms = degraded_threshold_ms
        self.unhealthy_threshold_ms = unhealthy_threshold_ms
        self.custom_headers = custom_headers or {}
        self.custom_body = custom_body
        self.ssl_verify = ssl_verify

    def _create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Create SSL context based on verification setting."""
        if not self.ssl_verify:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx
        return None

    def _evaluate_status(self, status_code: int, response_time_ms: float) -> Status:
        """
        Evaluate endpoint health based on status code and response time.

        Args:
            status_code: HTTP response status code
            response_time_ms: Response time in milliseconds

        Returns:
            Status enum indicating health level
        """
        # Check expected status code first
        if self.expected_status is not None:
            if status_code != self.expected_status:
                return Status.UNHEALTHY
        elif status_code not in self.HEALTHY_STATUS_CODES:
            return Status.UNHEALTHY

        # Evaluate based on response time
        if response_time_ms > self.unhealthy_threshold_ms:
            return Status.UNHEALTHY
        elif response_time_ms > self.degraded_threshold_ms:
            return Status.DEGRADED
        else:
            return Status.HEALTHY

    def check_sync(self, url: str, method: str = "GET") -> CheckResult:
        """
        Perform a synchronous health check against a URL.

        Args:
            url: Target URL to check
            method: HTTP method (GET, POST, PUT, DELETE, HEAD, OPTIONS)

        Returns:
            CheckResult with full check details
        """
        result = CheckResult(url=url, method=method.upper())
        start_time = time.time()

        try:
            # Build request
            req_data = None
            if self.custom_body and method.upper() in ("POST", "PUT", "PATCH"):
                req_data = self.custom_body.encode("utf-8")

            req = urllib.request.Request(
                url,
                data=req_data,
                method=method.upper(),
                headers={
                    "User-Agent": "APIPulse-CLI/1.0.0",
                    "Accept": "*/*",
                    **self.custom_headers,
                },
            )

            ssl_ctx = self._create_ssl_context()

            # Measure DNS + Connect + TLS
            connect_start = time.time()
            with urllib.request.urlopen(req, timeout=self.timeout, context=ssl_ctx) as resp:
                connect_end = time.time()
                result.status_code = resp.getcode()
                result.headers = dict(resp.getheaders())
                body = resp.read()
                result.body_length = len(body)
                result.body_preview = body[:500].decode("utf-8", errors="replace")

            end_time = time.time()
            total_ms = (end_time - start_time) * 1000
            result.response_time_ms = round(total_ms, 2)
            result.dns_time_ms = round((connect_start - start_time) * 1000, 2)
            result.connect_time_ms = round((connect_end - connect_start) * 1000, 2)
            result.tls_time_ms = round(result.connect_time_ms * 0.3, 2)  # Approximate

            result.status = self._evaluate_status(result.status_code, result.response_time_ms)

        except urllib.error.HTTPError as e:
            end_time = time.time()
            result.response_time_ms = round((end_time - start_time) * 1000, 2)
            result.status_code = e.code
            result.error = f"HTTP {e.code}: {e.reason}"
            result.status = Status.UNHEALTHY

        except urllib.error.URLError as e:
            end_time = time.time()
            result.response_time_ms = round((end_time - start_time) * 1000, 2)
            result.error = f"Connection error: {e.reason}"
            result.status = Status.UNHEALTHY

        except TimeoutError:
            end_time = time.time()
            result.response_time_ms = round((end_time - start_time) * 1000, 2)
            result.error = f"Timeout after {self.timeout}s"
            result.status = Status.UNHEALTHY

        except Exception as e:
            end_time = time.time()
            result.response_time_ms = round((end_time - start_time) * 1000, 2)
            result.error = f"Unexpected error: {str(e)}"
            result.status = Status.UNKNOWN

        return result

    async def check_async(self, url: str, method: str = "GET") -> CheckResult:
        """
        Perform an asynchronous health check.

        Args:
            url: Target URL to check
            method: HTTP method

        Returns:
            CheckResult with full check details
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.check_sync, url, method)

    async def check_batch(
        self, endpoints: List[Dict[str, Any]]
    ) -> List[CheckResult]:
        """
        Perform concurrent health checks against multiple endpoints.

        Args:
            endpoints: List of dicts with 'url' and optional 'method' keys

        Returns:
            List of CheckResult objects
        """
        tasks = []
        for ep in endpoints:
            url = ep.get("url", "")
            method = ep.get("method", "GET")
            tasks.append(self.check_async(url, method))
        return await asyncio.gather(*tasks, return_exceptions=True)
