import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


obs = load("competitor_observation", "discovery/competitor_observation.py")
collector = load("public_web_collector", "discovery/public_web_collector.py")
policy_mod = load("public_http_policy", "discovery/public_http_policy.py")


class FakeClock:
    def __init__(self):
        self.value = 100.0

    def __call__(self):
        return self.value


class PublicHttpPolicyTests(unittest.TestCase):
    def test_private_dns_and_bad_urls_fail_closed(self):
        with self.assertRaises(ValueError):
            policy_mod.validate_resolved_ips(["127.0.0.1"])
        with self.assertRaises(ValueError):
            policy_mod.validate_resolved_ips(["10.0.0.8"])
        with self.assertRaises(ValueError):
            policy_mod.authorize_fetch(
                "http://localhost/test",
                resolved_ips=["8.8.8.8"],
                robots_txt="User-agent: *\nAllow: /",
                rate_limiter=policy_mod.HostRateLimiter(min_interval_seconds=0),
            )

    def test_robots_and_rate_limit_are_enforced(self):
        clock = FakeClock()
        limiter = policy_mod.HostRateLimiter(min_interval_seconds=5, clock=clock)
        url = "https://example.com/private"
        with self.assertRaises(PermissionError):
            policy_mod.authorize_fetch(
                url,
                resolved_ips=["8.8.8.8"],
                robots_txt="User-agent: *\nDisallow: /private",
                rate_limiter=limiter,
            )
        allowed = policy_mod.authorize_fetch(
            "https://example.com/public",
            resolved_ips=["8.8.8.8"],
            robots_txt="User-agent: *\nAllow: /public",
            rate_limiter=limiter,
        )
        self.assertEqual("https://example.com/public", allowed)
        with self.assertRaises(RuntimeError):
            policy_mod.authorize_fetch(
                "https://example.com/other",
                resolved_ips=["8.8.8.8"],
                robots_txt="User-agent: *\nAllow: /",
                rate_limiter=limiter,
            )
        clock.value += 5
        self.assertEqual(
            "https://example.com/other",
            policy_mod.authorize_fetch(
                "https://example.com/other",
                resolved_ips=["8.8.8.8"],
                robots_txt="User-agent: *\nAllow: /",
                rate_limiter=limiter,
            ),
        )

    def test_fetch_envelope_enforces_redirect_status_type_and_size(self):
        policy = policy_mod.FetchRequestPolicy(max_bytes=100, max_redirects=1)
        good = policy_mod.SafeFetchEnvelope(
            requested_url="https://example.com",
            final_url="https://www.example.com/page",
            status_code=200,
            content_type="text/html; charset=utf-8",
            body=b"<html></html>",
            resolved_ips=("8.8.8.8",),
            redirects=("https://www.example.com/page",),
        )
        good.validate(policy)
        with self.assertRaises(ValueError):
            policy_mod.SafeFetchEnvelope(
                requested_url="https://example.com",
                final_url="https://example.com",
                status_code=200,
                content_type="application/pdf",
                body=b"x",
                resolved_ips=("8.8.8.8",),
            ).validate(policy)
        with self.assertRaises(ValueError):
            policy_mod.SafeFetchEnvelope(
                requested_url="https://example.com",
                final_url="https://example.com",
                status_code=200,
                content_type="text/html",
                body=b"x" * 101,
                resolved_ips=("8.8.8.8",),
            ).validate(policy)


if __name__ == "__main__":
    unittest.main()
