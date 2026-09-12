from __future__ import annotations

from dataclasses import dataclass, field
import ipaddress
import time
from typing import Callable, Iterable
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from public_web_collector import MAX_HTML_BYTES, validate_public_url

DEFAULT_USER_AGENT = "CEREBRO-OS-CompetitorObserver/1.0 (+public-research; contact=ops@fenixcapital.es)"
MAX_TIMEOUT_SECONDS = 10.0
MAX_REDIRECTS = 3
MIN_HOST_INTERVAL_SECONDS = 5.0


def validate_resolved_ips(ips: Iterable[str]) -> tuple[str, ...]:
    checked: list[str] = []
    for raw in ips:
        ip = ipaddress.ip_address(str(raw).strip())
        if not ip.is_global:
            raise ValueError("resolved address is not globally routable")
        checked.append(str(ip))
    if not checked:
        raise ValueError("DNS resolution returned no addresses")
    return tuple(sorted(set(checked)))


def robots_allowed(url: str, robots_txt: str, user_agent: str = DEFAULT_USER_AGENT) -> bool:
    safe_url = validate_public_url(url)
    parsed = urlparse(safe_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(robots_txt.splitlines())
    return parser.can_fetch(user_agent, safe_url)


@dataclass
class HostRateLimiter:
    min_interval_seconds: float = MIN_HOST_INTERVAL_SECONDS
    clock: Callable[[], float] = time.monotonic
    _last_by_host: dict[str, float] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.min_interval_seconds < 0:
            raise ValueError("min_interval_seconds cannot be negative")

    def remaining(self, url: str) -> float:
        safe_url = validate_public_url(url)
        host = (urlparse(safe_url).hostname or "").lower()
        now = float(self.clock())
        last = self._last_by_host.get(host)
        if last is None:
            return 0.0
        return max(0.0, self.min_interval_seconds - (now - last))

    def acquire(self, url: str) -> None:
        safe_url = validate_public_url(url)
        host = (urlparse(safe_url).hostname or "").lower()
        wait = self.remaining(safe_url)
        if wait > 0:
            raise RuntimeError(f"rate limit active for host; retry_after={wait:.3f}")
        self._last_by_host[host] = float(self.clock())


@dataclass(frozen=True)
class FetchRequestPolicy:
    timeout_seconds: float = 8.0
    max_bytes: int = MAX_HTML_BYTES
    max_redirects: int = MAX_REDIRECTS
    user_agent: str = DEFAULT_USER_AGENT
    respect_robots: bool = True

    def validate(self) -> None:
        if not 0 < self.timeout_seconds <= MAX_TIMEOUT_SECONDS:
            raise ValueError("timeout_seconds outside safe range")
        if not 1 <= self.max_bytes <= MAX_HTML_BYTES:
            raise ValueError("max_bytes outside safe range")
        if not 0 <= self.max_redirects <= MAX_REDIRECTS:
            raise ValueError("max_redirects outside safe range")
        if not self.user_agent.strip():
            raise ValueError("user_agent is required")


@dataclass(frozen=True)
class SafeFetchEnvelope:
    requested_url: str
    final_url: str
    status_code: int
    content_type: str
    body: bytes
    resolved_ips: tuple[str, ...]
    redirects: tuple[str, ...] = ()

    def validate(self, policy: FetchRequestPolicy) -> None:
        policy.validate()
        validate_public_url(self.requested_url)
        validate_public_url(self.final_url)
        if len(self.redirects) > policy.max_redirects:
            raise ValueError("redirect limit exceeded")
        for redirect in self.redirects:
            validate_public_url(redirect)
        validate_resolved_ips(self.resolved_ips)
        if self.status_code < 200 or self.status_code >= 300:
            raise ValueError("HTTP response is not successful")
        if len(self.body) > policy.max_bytes:
            raise ValueError("response body exceeds byte limit")
        if "html" not in self.content_type.lower():
            raise ValueError("collector only accepts HTML responses")


def authorize_fetch(
    url: str,
    *,
    resolved_ips: Iterable[str],
    robots_txt: str,
    rate_limiter: HostRateLimiter,
    policy: FetchRequestPolicy = FetchRequestPolicy(),
) -> str:
    policy.validate()
    safe_url = validate_public_url(url)
    validate_resolved_ips(resolved_ips)
    if policy.respect_robots and not robots_allowed(safe_url, robots_txt, policy.user_agent):
        raise PermissionError("robots policy denies collection")
    rate_limiter.acquire(safe_url)
    return safe_url
