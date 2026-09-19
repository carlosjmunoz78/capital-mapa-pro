from __future__ import annotations

import json
import os
from pathlib import Path

PERMISSIONS={"READ","WRITE","EXECUTE","APPROVE","DENY"}

def authorize(identity:dict, *, company_id:str, action_scope:str)->dict:
    identity_id=str(identity.get("identity_id","")).strip()
    identity_company=str(identity.get("company_id","")).strip()
    scopes={str(x).upper() for x in (identity.get("scopes") or [])}
    if not identity_id or not identity_company:
        raise ValueError("identity scope required")
    if identity_company not in {company_id,"GLOBAL"}:
        return {"engine_id":"IAM-001","decision":"DENY","reason":"CROSS_COMPANY_DENIED","identity_id":identity_id,"company_id":company_id}
    if not scopes.issubset(PERMISSIONS):
        raise ValueError("unsupported IAM scope")
    required=str(action_scope).upper()
    if required not in PERMISSIONS:
        raise ValueError("unsupported action scope")
    decision="ALLOW" if required in scopes else "DENY"
    return {"engine_id":"IAM-001","decision":decision,"reason":"SCOPE_PRESENT" if decision=="ALLOW" else "SCOPE_MISSING","identity_id":identity_id,"company_id":company_id}

def audit_secret_metadata(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    items=payload.get("secrets")
    if not company_id or not isinstance(items,list):
        raise ValueError("company_id and secret metadata list required")
    findings=[]
    for item in items:
        if not isinstance(item,dict): raise ValueError("secret metadata item must be object")
        name=str(item.get("name","")).strip()
        provider=str(item.get("provider","")).strip()
        location=str(item.get("location","")).strip()
        has_value=any(k in item for k in ("value","secret","token","password","api_key"))
        if not name or not provider or not location:
            findings.append({"name":name or "UNKNOWN","finding":"METADATA_INCOMPLETE","severity":"MEDIUM"})
        if has_value:
            findings.append({"name":name or "UNKNOWN","finding":"SECRET_VALUE_PRESENT_IN_METADATA","severity":"CRITICAL"})
        if str(item.get("scope","")).upper()=="GLOBAL" and company_id!="GLOBAL":
            findings.append({"name":name or "UNKNOWN","finding":"OVERBROAD_SCOPE","severity":"HIGH"})
    critical=any(f["severity"]=="CRITICAL" for f in findings)
    return {
        "record_type":"secret_metadata_audit",
        "company_id":company_id,
        "engine_id":"SEC-002",
        "status":"HUMAN_REQUIRED" if critical else "ATTENTION" if findings else "GREEN",
        "human_reason":"SECURITY_INCIDENT" if critical else None,
        "findings":findings,
        "secret_values_collected":False,
        "rotation_performed":False,
        "external_mutation_allowed":False,
        "cost_eur":0.0,
    }

def finops_guard(payload:dict)->dict:
    company_id=str(payload.get("company_id","")).strip()
    if not company_id: raise ValueError("company_id required")
    estimated=float(((payload.get("facts") or {}).get("estimated_additional_cost_eur",0.0)))
    latest=float(((payload.get("facts") or {}).get("latest_duration_seconds",0.0)))
    baseline=float(((payload.get("facts") or {}).get("baseline_median_seconds",0.0)))
    cost_status="GREEN" if estimated<=0 else "HUMAN_REQUIRED"
    duration_ratio=(latest/baseline) if baseline>0 else 1.0
    performance_status="ATTENTION" if duration_ratio>2.0 else "GREEN"
    return {
        "record_type":"finops_guard_result",
        "company_id":company_id,
        "engine_id":"FINOPS-001",
        "estimated_additional_cost_eur":estimated,
        "duration_ratio":round(duration_ratio,4),
        "status":"HUMAN_REQUIRED" if cost_status=="HUMAN_REQUIRED" else performance_status,
        "human_reason":"MONEY_LIMIT" if estimated>0 else None,
        "automatic_spend_allowed":False,
        "cost_target_eur":0.0,
        "external_mutation_allowed":False,
    }

def security_posture(company_id:str)->dict:
    red_root=Path(os.environ.get("CEREBRO_RED_TEAM_SUMMARY_ROOT",".cerebro-runtime/red-team-summary"))
    inc_root=Path(os.environ.get("CEREBRO_INCIDENT_ROOT",".cerebro-runtime/incidents"))
    red_status="UNKNOWN"; incident_security=0
    rp=red_root/f"{company_id}.json"
    if rp.exists():
        p=json.loads(rp.read_text(encoding="utf-8"))
        if str(p.get("company_id",""))!=company_id: raise ValueError("cross-company red summary denied")
        red_status=str(p.get("status","UNKNOWN")).upper()
    ip=inc_root/f"{company_id}.json"
    if ip.exists():
        p=json.loads(ip.read_text(encoding="utf-8"))
        if str(p.get("company_id",""))!=company_id: raise ValueError("cross-company incident summary denied")
        incident_security=sum(1 for x in (p.get("incidents") or []) if str(x.get("human_reason",""))=="SECURITY_INCIDENT")
    status="GREEN" if red_status=="GREEN" and incident_security==0 else "HUMAN_REQUIRED" if incident_security else "ATTENTION"
    return {
        "record_type":"security_posture",
        "company_id":company_id,
        "engine_id":"SEC-001",
        "red_team_status":red_status,
        "security_incident_count":incident_security,
        "status":status,
        "human_reason":"SECURITY_INCIDENT" if incident_security else None,
        "policy_weakening_allowed":False,
        "permission_escalation_allowed":False,
        "external_mutation_allowed":False,
        "cost_eur":0.0,
    }

def observability_snapshot(company_id:str, environment:str, version:str)->dict:
    roots={
        "incident":Path(os.environ.get("CEREBRO_INCIDENT_ROOT",".cerebro-runtime/incidents"))/f"{company_id}.json",
        "self_heal":Path(os.environ.get("CEREBRO_SELF_HEAL_ROOT",".cerebro-runtime/self-heal"))/f"{company_id}.json",
        "backup":Path(os.environ.get("CEREBRO_BACKUP_RESULT_ROOT",".cerebro-runtime/backup-results"))/f"{company_id}.json",
        "rebuild":Path(os.environ.get("CEREBRO_REBUILD_RESULT_ROOT",".cerebro-runtime/rebuild-results"))/f"{company_id}.json",
        "continuity":Path(os.environ.get("CEREBRO_CONTINUITY_RESULT_ROOT",".cerebro-runtime/continuity-results"))/f"{company_id}.json",
        "crisis":Path(os.environ.get("CEREBRO_CRISIS_ROOT",".cerebro-runtime/crisis"))/f"{company_id}.json",
    }
    components={}
    attention=[]
    for name,path in roots.items():
        if not path.exists():
            components[name]={"status":"MISSING","evidence_ref":str(path)}
            attention.append(name)
            continue
        p=json.loads(path.read_text(encoding="utf-8"))
        if str(p.get("company_id",""))!=company_id: raise ValueError("cross-company observability evidence denied")
        status=str(p.get("status","UNKNOWN")).upper()
        components[name]={"status":status,"evidence_ref":str(path)}
        if status in {"RED","BLOCKED","HUMAN_REQUIRED","ATTENTION","DEGRADED"}:
            attention.append(name)
    return {
        "record_type":"company_observability_snapshot",
        "company_id":company_id,
        "engine_id":"OBSERV-001",
        "environment":environment,
        "version":version,
        "components":components,
        "attention_components":attention,
        "status":"GREEN" if not attention else "ATTENTION",
        "correlation_id_required":True,
        "external_mutation_allowed":False,
        "cost_eur":0.0,
    }

def run()->list[Path]:
    cfg_path=Path(os.environ.get("CEREBRO_IMPROVEMENT_COMPANIES","cerebro-os/config/improvement_companies.lab.json"))
    evidence_root=Path(os.environ.get("CEREBRO_IMPROVEMENT_EVIDENCE_ROOT",".cerebro-runtime/evidence"))
    out_root=Path(os.environ.get("CEREBRO_CONTROL_PLANE_ROOT",".cerebro-runtime/control-plane"))
    out_root.mkdir(parents=True,exist_ok=True)
    configs=json.loads(cfg_path.read_text(encoding="utf-8"))
    written=[]
    for cfg in configs:
        if not cfg.get("enabled",True): continue
        cid=str(cfg["company_id"]); env=str(cfg["environment"]); ver=str(cfg["version"])
        finops_path=evidence_root/f"{cid}.finops.json"
        finops=finops_guard(json.loads(finops_path.read_text(encoding="utf-8"))) if finops_path.exists() else {"engine_id":"FINOPS-001","company_id":cid,"status":"UNKNOWN","cost_target_eur":0.0}
        body={
            "record_type":"control_plane_snapshot",
            "company_id":cid,
            "environment":env,
            "version":ver,
            "engines":{
                "OBSERV-001":observability_snapshot(cid,env,ver),
                "FINOPS-001":finops,
                "SEC-001":security_posture(cid),
            },
            "external_mutation_allowed":False,
            "cost_eur":0.0,
        }
        target=out_root/f"{cid}.json"
        target.write_text(json.dumps(body,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        written.append(target)
    return written

if __name__=="__main__":
    for p in run(): print(p)
