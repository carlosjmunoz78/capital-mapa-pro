"""Shared UMS001 GitOps client: one GitHub OIDC workflow for all registered FACT engines."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from oidc_enroll_changed_engines import request_oidc, validate_manifest, ENDPOINT

ROOT = "cerebro-os/media-requests/"
ENG = re.compile(r"^[A-Z][A-Z0-9-]{2,63}$")
REQ = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
SHA = re.compile(r"^[a-f0-9]{40}$")
PATH = re.compile(r"^cerebro-os/media-requests/([A-Z][A-Z0-9-]{2,63})/([A-Za-z0-9][A-Za-z0-9._:-]{7,127})\.json$")
FIELDS = {"company_id", "engine_id", "environment", "request_id", "capability_id", "prompt", "rights_profile", "publish_requested"}
UA = "Mozilla/5.0 (compatible; CEREBRO-UMS001-LAB/1.0)"

def changed_paths(before: str, after: str, runner=subprocess.run) -> list[str]:
    if not SHA.fullmatch(before or "") or not SHA.fullmatch(after or ""):
        raise ValueError("Untrusted git SHA")
    r = runner(["git", "diff", "--name-only", "--diff-filter=A", before, after, "--", ROOT],
               capture_output=True, text=True, check=True)
    found = sorted(set(r.stdout.splitlines()))
    if len(found) < 1 or len(found) > 2 or any(not PATH.fullmatch(x) for x in found):
        raise ValueError("Require one or two new immutable media requests")
    return found

def validate(path: str, obj: object) -> dict:
    m = PATH.fullmatch(path)
    if not m or not isinstance(obj, dict) or set(obj) != FIELDS:
        raise ValueError("Invalid request format")
    engine, request_id = m.groups()
    if not (obj["company_id"] == "fenix" and obj["environment"] == "LAB"
            and obj["engine_id"] == engine and obj["request_id"] == request_id
            and obj["capability_id"] == "IMAGE.SYNTHETIC"
            and obj["rights_profile"] == "SYNTHETIC_ORIGINAL"
            and obj["publish_requested"] is False):
        raise ValueError("Image scope denied")
    prompt = obj["prompt"]
    if not isinstance(prompt, str) or not 40 <= len(prompt) <= 630 or prompt != prompt.strip() or re.search(
        r"api[._ -]?key|access[._ -]?token|password\s*:", prompt, re.I
    ):
        raise ValueError("Invalid prompt")
    return obj

def call(path: str, body: dict, binary=False):
    jwt = request_oidc()
    req = Request(ENDPOINT.replace("/v1/factory/engine-created", path),
                  data=json.dumps(body, separators=(",", ":")).encode("utf-8"),
                  method="POST", headers={
                      "Authorization": "Bearer " + jwt,
                      "Content-Type": "application/json",
                      "Accept": "image/jpeg" if binary else "application/json",
                      "User-Agent": UA,
                  })
    try:
        with urlopen(req, timeout=25) as resp:
            result = resp.read(4500001 if binary else 6000)
            if binary:
                if len(result) > 4500000 or resp.headers.get("Content-Type","").split(";")[0] != "image/jpeg":
                    raise ValueError("Image response rejected")
                return result, resp.headers.get("X-Cerebro-Asset-Sha256", "")
            return json.loads(result)
    except HTTPError as exc:
        raise RuntimeError("CEREBRO private media API returned HTTP " + str(exc.code)) from None

def dimensions(jpeg: bytes) -> tuple[int,int]:
    if len(jpeg)<4000 or jpeg[:2]!=b"\xff\xd8" or jpeg[-2:]!=b"\xff\xd9":
        raise ValueError("Invalid JPEG envelope")
    i=2
    while i<len(jpeg)-12:
        if jpeg[i]!=255:
            i+=1
            continue
        marker=jpeg[i+1]
        length=int.from_bytes(jpeg[i+2:i+4],"big")
        if marker in {192,193,194,195,198,199,201,202,203,205,206,207}:
            return int.from_bytes(jpeg[i+7:i+9],"big"),int.from_bytes(jpeg[i+5:i+7],"big")
        if length<2:
            break
        i+=length+2
    raise ValueError("JPEG dimensions not found")

def run_one(path: str, sha: str, output: Path) -> dict:
    item=validate(path,json.loads(Path(path).read_text(encoding="utf-8")))
    engine, rid=item["engine_id"],item["request_id"]
    validate_manifest(engine)
    common={"engine_id":engine,"request_id":rid,"sha":sha}
    ack=call("/v1/factory/image-request",{**common,"prompt":item["prompt"]})
    if ack.get("state")!="ACCEPTED" or ack.get("engine_id")!=engine:
        raise RuntimeError("Gateway rejected media request")
    receipt=None
    for _ in range(20):
        time.sleep(3)
        receipt=call("/v1/factory/image-status",common)
        if receipt.get("state")=="PRIVATE_ASSET_RECEIVED":
            break
        if receipt.get("state")!="QUEUED_OR_PROCESSING":
            raise RuntimeError("Media receipt rejected")
    if not receipt or receipt.get("state")!="PRIVATE_ASSET_RECEIVED":
        raise RuntimeError("Media delivery not confirmed")
    image,header_sha=call("/v1/factory/image-download",common,binary=True)
    actual=hashlib.sha256(image).hexdigest()
    if actual!=header_sha or actual!=receipt.get("asset_sha256") or dimensions(image)!=(1024,1024):
        raise RuntimeError("Media integrity or dimensions failed")
    output.mkdir(parents=True,exist_ok=True)
    (output/(engine+"-"+rid+".jpg")).write_bytes(image)
    result={"state":"PRIVATE_ASSET_RECEIVED","company_id":"fenix","engine_id":engine,
            "request_id":rid,"sha256":actual,"bytes":len(image),"format":"JPEG_1024_1024",
            "visual_qa":"PENDING","brand_qa":"PENDING","publication":False}
    (output/(engine+"-"+rid+".receipt.json")).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result

def main() -> None:
    if (os.environ.get("GITHUB_REPOSITORY")!="carlosjmunoz78/capital-mapa-pro"
            or os.environ.get("GITHUB_REF")!="refs/heads/cerebro-engine-factory-v0"
            or os.environ.get("GITHUB_EVENT_NAME")!="push"
            or os.environ.get("CEREBRO_COMPANY_ID")!="fenix"):
        raise RuntimeError("Non-authorized FACT runtime")
    sha=os.environ["CEREBRO_FACT_COMMIT_SHA"]
    target=Path(os.environ["RUNNER_TEMP"])/"cerebro-ums001-images"
    for path in changed_paths(os.environ["CEREBRO_FACT_COMMIT_BEFORE"],sha):
        r=run_one(path,sha,target)
        print("UMS001 LAB",r["engine_id"],r["state"],"SHA256",r["sha256"],"NO_PUBLICATION")
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as f:
                f.write("UMS001 LAB / "+r["engine_id"]+" / PRIVATE_ASSET_RECEIVED / no publication\n")

if __name__=="__main__":
    main()
