from __future__ import annotations

import hashlib
import json
import os
import tarfile
import tempfile
from pathlib import Path

INCLUDE_DIRS=(
    "knowledge-inventory","knowledge-lab-ledger","rag-index","digital-twin",
    "learning-outcomes","meta-learning","incidents","self-heal","red-team-summary",
)

def _sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def build_backup(company_id:str)->dict:
    runtime_root=Path(os.environ.get("CEREBRO_RUNTIME_ROOT",".cerebro-runtime"))
    out_root=Path(os.environ.get("CEREBRO_BACKUP_ROOT",".cerebro-runtime/backups"))
    out_root.mkdir(parents=True,exist_ok=True)
    files=[]
    for dirname in INCLUDE_DIRS:
        base=runtime_root/dirname
        if not base.exists(): continue
        for path in sorted(base.rglob("*")):
            if not path.is_file(): continue
            name=path.name
            # Company-scoped filename or nested company namespace.
            rel=path.relative_to(runtime_root)
            parts=rel.parts
            scoped=(company_id in parts) or name.startswith(company_id+".") or name==f"{company_id}.json" or name==f"{company_id}.jsonl" or name==f"{company_id}.snapshot.json" or name==f"{company_id}.summary.json"
            if not scoped: continue
            files.append({
                "path":str(rel),
                "sha256":_sha256(path),
                "size":path.stat().st_size,
            })
    manifest={
        "record_type":"company_backup_manifest",
        "company_id":company_id,
        "engine_id":"DR-001",
        "files":files,
        "file_count":len(files),
        "restore_mode":"ISOLATED_REHEARSAL_ONLY",
        "live_overwrite_allowed":False,
        "external_mutation_allowed":False,
        "cost_eur":0.0,
    }
    manifest_path=out_root/f"{company_id}.manifest.json"
    manifest_path.write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    archive_path=out_root/f"{company_id}.backup.tar.gz"
    with tarfile.open(archive_path,"w:gz") as tar:
        tar.add(manifest_path,arcname="manifest.json")
        for item in files:
            tar.add(runtime_root/item["path"],arcname=item["path"])
    return {**manifest,"manifest_path":str(manifest_path),"archive_path":str(archive_path),"archive_sha256":_sha256(archive_path)}

def restore_rehearsal(company_id:str)->dict:
    out_root=Path(os.environ.get("CEREBRO_BACKUP_ROOT",".cerebro-runtime/backups"))
    archive=out_root/f"{company_id}.backup.tar.gz"
    if not archive.exists():
        raise ValueError("backup archive missing")
    with tempfile.TemporaryDirectory() as td:
        restore_root=Path(td)
        with tarfile.open(archive,"r:gz") as tar:
            members=tar.getmembers()
            for member in members:
                target=(restore_root/member.name).resolve()
                if restore_root.resolve() not in target.parents and target!=restore_root.resolve():
                    raise ValueError("unsafe archive path")
            tar.extractall(restore_root)
        manifest=json.loads((restore_root/"manifest.json").read_text(encoding="utf-8"))
        if str(manifest.get("company_id",""))!=company_id:
            raise ValueError("backup company mismatch")
        verified=0
        for item in manifest.get("files") or []:
            path=restore_root/str(item["path"])
            if not path.exists() or _sha256(path)!=str(item["sha256"]):
                raise ValueError("restore checksum mismatch")
            verified+=1
        return {
            "record_type":"restore_rehearsal_result",
            "company_id":company_id,
            "engine_id":"DR-001",
            "status":"GREEN",
            "verified_files":verified,
            "live_restore_performed":False,
            "external_mutation_allowed":False,
            "cost_eur":0.0,
        }

def run()->list[Path]:
    cfg_path=Path(os.environ.get("CEREBRO_IMPROVEMENT_COMPANIES","cerebro-os/config/improvement_companies.lab.json"))
    result_root=Path(os.environ.get("CEREBRO_BACKUP_RESULT_ROOT",".cerebro-runtime/backup-results"))
    result_root.mkdir(parents=True,exist_ok=True)
    configs=json.loads(cfg_path.read_text(encoding="utf-8"))
    written=[]
    for cfg in configs:
        if not cfg.get("enabled",True): continue
        company_id=str(cfg["company_id"])
        backup=build_backup(company_id)
        rehearsal=restore_rehearsal(company_id)
        target=result_root/f"{company_id}.json"
        target.write_text(json.dumps({
            "company_id":company_id,
            "engine_id":"DR-001",
            "backup":backup,
            "rehearsal":rehearsal,
            "status":"GREEN",
            "live_restore_performed":False,
            "cost_eur":0.0,
        },sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
