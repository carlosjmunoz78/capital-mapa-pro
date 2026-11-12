"""Enroll committed FACT-001 engines through short-lived GitHub OIDC, no GitHub secrets.

Fail closed. Runs exclusively for the LAB factory branch. Never prints JWT values.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

AUDIENCE = "cerebro-fact001-ums001-lab"
ENDPOINT = (
    "https://cerebro-fact001-github-oidc-enroll-lab-eu."
    "carlosj-munozcabeza.workers.dev/v1/factory/engine-created"
)
ENGINE_ID = re.compile(r"^[A-Z][A-Z0-9-]{2,63}$")
SHA = re.compile(r"^[0-9a-f]{40}$")
ENGINE_PATH = re.compile(r"^cerebro-os/engines/([A-Z][A-Z0-9-]{2,63})/manifest\.json$")


def changed_engines(before: str, sha: str) -> list[str]:
    if not SHA.fullmatch(before) or not SHA.fullmatch(sha):
        raise ValueError("Commit IDs not trusted")
    diff = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=AM", before, sha, "--", "cerebro-os/engines/"],
        check=True, capture_output=True, text=True,
    )
    engines = sorted(set(
        found.group(1)
        for path in diff.stdout.splitlines()
        if (found := ENGINE_PATH.fullmatch(path))
    ))
    if len(engines) > 8:
        raise ValueError("Too many engines in one enrollment run")
    return engines


def validate_manifest(engine: str) -> None:
    if not ENGINE_ID.fullmatch(engine):
        raise ValueError("Engine ID denied")
    path = Path("cerebro-os/engines") / engine / "manifest.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    media = obj.get("media_gateway", {})
    if not (
        obj.get("engine_id") == engine
        and obj.get("environment") == "LAB"
        and obj.get("version") == "0.1.0"
        and media.get("provider_engine_id") == "UMS-001"
        and media.get("uses_per_engine_worker") is False
        and media.get("publish_authorized") is False
        and media.get("paid_execution_enabled") is False
        and "IMAGE.SYNTHETIC" in media.get("capabilities", [])
    ):
        raise ValueError(f"FACT media contract invalid: {engine}")


def request_oidc() -> str:
    root = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL", "")
    ephemeral = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")
    if not root.startswith("https://") or not ephemeral:
        raise RuntimeError("GitHub ephemeral OIDC not granted")
    url = root + "&audience=" + quote(AUDIENCE, safe="")
    request = Request(url, headers={"Authorization": "Bearer " + ephemeral})
    with urlopen(request, timeout=12) as reply:
        body = json.loads(reply.read(10000))
    token = body.get("value")
    if not isinstance(token, str) or token.count(".") != 2:
        raise RuntimeError("GitHub OIDC unavailable")
    return token


def enroll(engine: str, sha: str) -> dict:
    token = request_oidc()
    payload = json.dumps({"engine_id": engine, "sha": sha}, separators=(",", ":")).encode()
    req = Request(
        ENDPOINT, method="POST", data=payload,
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            # workers.dev Browser Integrity Check rejects the default Python-urllib UA.
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        },
    )
    try:
        with urlopen(req, timeout=20) as reply:
            result = json.loads(reply.read(6000))
    except HTTPError as exc:
        # Log only our allowlisted error code, never JWTs, headers or response dumps.
        safe = "UNSPECIFIED"
        try:
            denial = json.loads(exc.read(2000))
            name = denial.get("code")
            if isinstance(name, str) and re.fullmatch(r"[A-Z0-9_]{1,75}", name):
                safe = name
        except Exception:
            pass
        kind = str(exc.headers.get("Content-Type", "none")).split(";")[0][:50]
        server = str(exc.headers.get("Server", "none"))[:35]
        via_cf = "yes" if exc.headers.get("CF-Ray") else "no"
        raise RuntimeError(
            f"Gateway rejected HTTP {exc.code}, detail={safe}, type={kind}, server={server}, cf_ray={via_cf}"
        ) from None
    if result.get("state") != "ACTIVE" or result.get("engine_id") != engine:
        raise RuntimeError("Gateway did not certify ACTIVE registration")
    return result


def request_image_lab_canary(engine: str, sha: str) -> dict:
    """One explicit LAB image test for the registered FACT canary; never publishes."""
    if engine != "FACT-OIDC-CANARY-20261112":
        raise RuntimeError("Image canary restricted to fixed FACT test motor")
    token = request_oidc()
    payload = {
        "engine_id": engine, "sha": sha,
        "request_id": "UMS001-LAB-GITHUB-OIDC-IMAGE-20261112-01",
        "prompt": (
            "Create an original realistic editorial photograph of a fictional bright apartment "
            "in Cordoba Spain, warm Mediterranean natural light, tasteful neutral furniture, "
            "premium architectural photography, olive-green accent plants, no people, no logos, "
            "no signs, no captions, no visible writing or watermark."
        ),
    }
    request = Request(
        ENDPOINT.replace("/v1/factory/engine-created", "/v1/factory/image-request"),
        method="POST",
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            result = json.loads(response.read(5000))
    except HTTPError as exc:
        safe = "UNSPECIFIED"
        try:
            error = json.loads(exc.read(2000))
            value = error.get("code")
            if isinstance(value, str) and re.fullmatch(r"[A-Z0-9_]{1,75}", value):
                safe = value
        except Exception:
            pass
        raise RuntimeError(f"LAB image request rejected: HTTP {exc.code} ({safe})") from None
    if result.get("state") != "ACCEPTED" or result.get("engine_id") != engine:
        raise RuntimeError("Private signed image request not accepted")
    return result


def main() -> None:
    if os.environ.get("GITHUB_REPOSITORY") != "carlosjmunoz78/capital-mapa-pro":
        raise RuntimeError("Wrong repository")
    if os.environ.get("GITHUB_REF") != "refs/heads/cerebro-engine-factory-v0":
        raise RuntimeError("Wrong branch")
    if os.environ.get("GITHUB_EVENT_NAME") != "push" or os.environ.get("CEREBRO_COMPANY_ID") != "fenix":
        raise RuntimeError("Non-authorized scope")
    sha = os.environ.get("CEREBRO_FACT_COMMIT_SHA", "")
    engine_ids = changed_engines(os.environ.get("CEREBRO_FACT_COMMIT_BEFORE", ""), sha)
    for engine in engine_ids:
        validate_manifest(engine)
        result = enroll(engine, sha)
        print(f"FACT-001 -> UMS-001 LAB: {engine} state={result['state']} signed_probe={result.get('signed_probe_status')}")
        if engine == "FACT-OIDC-CANARY-20261112":
            job = request_image_lab_canary(engine, sha)
            print(f"FACT-001 -> UMS-001 LAB: signed private image request {job['request_id']} state={job['state']}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as output:
            output.write(f"FACT-001 UMS-001 OIDC LAB: {len(engine_ids)} enrollment(s) processed.\n")
    if not engine_ids:
        print("No new FACT engine manifest in this push. No API calls.")


if __name__ == "__main__":
    main()
