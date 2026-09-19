from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path


def _probe(url: str) -> dict:
    started = time.monotonic()
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "CEREBRO-AvailabilityObserver/1.0 (+public-read-only)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            code = int(response.status)
            body = response.read(4096)
            elapsed_ms = round((time.monotonic() - started) * 1000, 3)
            return {"reachable": True, "status_code": code, "latency_ms": elapsed_ms, "body_nonempty": bool(body)}
    except urllib.error.HTTPError as exc:
        elapsed_ms = round((time.monotonic() - started) * 1000, 3)
        return {"reachable": True, "status_code": int(exc.code), "latency_ms": elapsed_ms, "body_nonempty": True}
    except Exception as exc:
        elapsed_ms = round((time.monotonic() - started) * 1000, 3)
        return {
            "reachable": False,
            "status_code": 0,
            "latency_ms": elapsed_ms,
            "body_nonempty": False,
            "error": type(exc).__name__,
        }


def _healthy(kind: str, probe: dict) -> bool:
    if not probe.get("reachable"):
        return False
    code = int(probe.get("status_code", 0))
    if kind == "gateway":
        return code in {200, 400, 401, 403, 405}
    return 200 <= code < 400


def collect() -> list[Path]:
    config_path = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_BUSINESS_SOURCES",
        "cerebro-os/config/improvement_business_sources.lab.json",
    ))
    evidence_root = Path(os.environ.get(
        "CEREBRO_IMPROVEMENT_EVIDENCE_ROOT",
        ".cerebro-runtime/evidence",
    ))
    evidence_root.mkdir(parents=True, exist_ok=True)
    configs = json.loads(config_path.read_text(encoding="utf-8"))
    written: list[Path] = []

    for config in configs:
        if not config.get("enabled", True):
            continue
        company_id = str(config["company_id"])
        targets: list[tuple[str, str]] = []
        urls = config.get("official_web_urls") or []
        if urls:
            targets.append(("website", str(urls[0])))
        app_url = str(config.get("app_url", "")).strip()
        gateway_url = str(config.get("gateway_url", "")).strip()
        wordpress_base = str(config.get("wordpress_rest_base", "")).strip()
        if app_url:
            targets.append(("app", app_url))
        if gateway_url:
            targets.append(("gateway", gateway_url))
        if wordpress_base:
            targets.append(("wordpress_rest", wordpress_base.rstrip("/") + "/pages?per_page=1&_fields=id"))

        if not targets:
            continue

        results: dict[str, dict] = {}
        failures: list[str] = []
        for kind, url in targets:
            probe = _probe(url)
            probe["url"] = url
            probe["healthy"] = _healthy(kind, probe)
            results[kind] = probe
            if not probe["healthy"]:
                failures.append(kind)

        checked = bool(results)
        evidence_ref = next((item["url"] for item in results.values()), f"evidence://{company_id}/availability")
        payload = {
            "company_id": company_id,
            "checked": checked,
            "source": "PUBLIC_SERVICE_AVAILABILITY",
            "evidence_ref": evidence_ref,
            "status": "PROPOSAL_READY" if failures else "NO_CHANGE",
            "confidence": 0.95 if checked else 0.0,
            "summary": "unhealthy=" + ",".join(failures) if failures else "all configured public services reachable",
            "facts": {
                "failures": failures,
                "targets": results,
            },
        }
        target = evidence_root / f"{company_id}.availability.json"
        target.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target)

    return written


if __name__ == "__main__":
    for path in collect():
        print(path)
