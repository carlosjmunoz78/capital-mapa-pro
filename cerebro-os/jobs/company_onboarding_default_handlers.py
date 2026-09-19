from __future__ import annotations

import hashlib
import json

from jobs.company_onboarding_executor import EngineHandler,OnboardingHandlerRegistry
from jobs.bootstrap_company_access import bootstrap_company_access
from jobs.scan_company_digital_footprint import scan_company
from jobs.discover_business_model import discover_business_model
from jobs.discover_company_processes import discover_processes
from jobs.audit_company_website import audit_website
from jobs.discover_company_keywords import discover_keywords
from jobs.audit_company_social import audit_social
from jobs.audit_company_local_presence import audit_local_presence
from jobs.map_company_competitors import map_competitors
from jobs.bootstrap_company_knowledge import bootstrap_company_knowledge
from jobs.bootstrap_company_seo import bootstrap_seo
from jobs.bootstrap_company_social import bootstrap_social
from jobs.bootstrap_company_marketing import bootstrap_marketing
from jobs.activate_company_engine_matrix import activate_matrix
from jobs.bootstrap_company_crm import bootstrap_crm
from jobs.bootstrap_company_app import bootstrap_app
from jobs.bootstrap_company_automations import bootstrap_automations
from jobs.bootstrap_company_training import bootstrap_training
from jobs.create_company_supervisor_scope import create_supervisor_scope
from jobs.create_company_backup_rebuild_pack import create_backup_rebuild_pack
from jobs.evaluate_company_preprod_readiness import evaluate_preprod_readiness
from jobs.evaluate_company_production_activation import evaluate_production_activation

def _ctx(payload:dict)->dict:
    value=payload.get("context") or {}
    if not isinstance(value,dict):
        raise ValueError("onboarding context must be object")
    return value

def _prior(payload:dict,engine_id:str)->dict:
    row=(_ctx(payload).get("engine_results") or {}).get(engine_id)
    if not isinstance(row,dict):
        raise ValueError(f"required prior engine result missing: {engine_id}")
    if str(row.get("company_id",""))!=str(payload["company_id"]):
        raise ValueError("cross-company prior engine result denied")
    return row

def _context_list(payload:dict,key:str)->list:
    value=_ctx(payload).get(key,[])
    if not isinstance(value,list):
        raise ValueError(f"{key} must be list")
    return value

def _registration(payload:dict)->dict:
    ctx=_ctx(payload)
    profile=ctx.get("company_profile") or {}
    if not isinstance(profile,dict):
        raise ValueError("company_profile must be object")
    company_id=str(payload["company_id"])
    legal_name=str(profile.get("legal_name","")).strip()
    evidence_ref=str(profile.get("evidence_ref","")).strip()
    if not legal_name or not evidence_ref:
        return {
          "record_type":"company_registration_candidate","company_id":company_id,"engine_id":"COMP-REG-001",
          "environment":"LAB","version":payload["version"],"status":"PARTIAL",
          "reason":"LEGAL_NAME_AND_EVIDENCE_REQUIRED","external_mutation_allowed":False,"cost_eur":0.0,
        }
    canonical=json.dumps({"company_id":company_id,"legal_name":legal_name,"evidence_ref":evidence_ref},sort_keys=True,separators=(",",":"))
    return {
      "record_type":"company_registration_candidate","company_id":company_id,"engine_id":"COMP-REG-001",
      "environment":"LAB","version":payload["version"],"status":"GREEN","legal_name":legal_name,
      "evidence_ref":evidence_ref,"external_mutation_allowed":False,"cost_eur":0.0,
      "evidence_hash":"sha256:"+hashlib.sha256(canonical.encode()).hexdigest(),
    }

def _access(payload:dict)->dict:
    ctx=_ctx(payload)
    return bootstrap_company_access({
      "company_id":payload["company_id"],"environment":"LAB","version":payload["version"],
      "requirements":_context_list(payload,"access_requirements"),
      "requirements_inventory_complete":bool(_ctx(payload).get("access_requirements_inventory_complete",False)),
      "existing_accounts":_context_list(payload,"existing_accounts"),
      "existing_connectors":_context_list(payload,"existing_connectors"),
      "session_observations":_context_list(payload,"session_observations"),
    })

def _scan(payload:dict)->dict:
    return scan_company({
      "company_id":payload["company_id"],"version":payload["version"],
      "domains":_context_list(payload,"domains"),
    })

def _bmd(payload:dict)->dict:
    ctx=_ctx(payload)
    return discover_business_model({
      "company_id":payload["company_id"],"environment":"LAB","version":payload["version"],
      "facts":dict(ctx.get("business_facts") or {}),"evidence":_context_list(payload,"business_evidence"),
    })

def _proc(payload:dict)->dict:
    return discover_processes({
      "company_id":payload["company_id"],"version":payload["version"],
      "process_candidates":_context_list(payload,"process_candidates"),
    })

def _waud(payload:dict)->dict:
    return audit_website({
      "company_id":payload["company_id"],"version":payload["version"],
      "scan_result":_prior(payload,"SCAN-001"),
    })

def _kw(payload:dict)->dict:
    ctx=_ctx(payload)
    return discover_keywords({
      "company_id":payload["company_id"],"version":payload["version"],
      "source_texts":_context_list(payload,"source_texts"),
      "seed_keywords":_context_list(payload,"seed_keywords"),
      "geographies":_context_list(payload,"geographies"),
    })

def _soc(payload:dict)->dict:
    return audit_social({
      "company_id":payload["company_id"],"version":payload["version"],
      "profiles":_context_list(payload,"social_profiles"),
    })

def _local(payload:dict)->dict:
    return audit_local_presence({
      "company_id":payload["company_id"],"version":payload["version"],
      "listings":_context_list(payload,"local_listings"),
    })

def _compet(payload:dict)->dict:
    return map_competitors({
      "company_id":payload["company_id"],"version":payload["version"],
      "competitors":_context_list(payload,"competitors"),
    })

def _kboot(payload:dict)->dict:
    ids=("BMD-001","PROC-001","WAUD-001","KW-001","SOCAUD-001","LOCALP-001","COMPET-001")
    return bootstrap_company_knowledge({
      "company_id":payload["company_id"],"version":payload["version"],
      "inputs":[_prior(payload,eid) for eid in ids],
    })

def _seoboot(payload:dict)->dict:
    return bootstrap_seo({
      "company_id":payload["company_id"],"version":payload["version"],
      "inputs":[_prior(payload,"WAUD-001"),_prior(payload,"KW-001")],
    })

def _socboot(payload:dict)->dict:
    return bootstrap_social({
      "company_id":payload["company_id"],"version":payload["version"],
      "inputs":[_prior(payload,"SOCAUD-001"),_prior(payload,"BMD-001")],
    })

def _mktboot(payload:dict)->dict:
    return bootstrap_marketing({
      "company_id":payload["company_id"],"version":payload["version"],
      "inputs":[_prior(payload,"BMD-001"),_prior(payload,"KW-001")],
    })

def _all_evidence(payload:dict)->list[dict]:
    ctx=_ctx(payload)
    rows=list((ctx.get("engine_results") or {}).values())
    extra=_context_list(payload,"gate_evidence")
    return rows+extra

def _engact(payload:dict)->dict:
    return activate_matrix({
      "company_id":payload["company_id"],"version":payload["version"],
      "engine_evidence":_all_evidence(payload),
    })

def _crm(payload:dict)->dict:
    ctx=_ctx(payload)
    return bootstrap_crm({
      "company_id":payload["company_id"],"version":payload["version"],
      "existing_contract_refs":_context_list(payload,"crm_contract_refs"),
      "entities":_context_list(payload,"crm_entities"),"pipeline":_context_list(payload,"crm_pipeline"),
    })

def _app(payload:dict)->dict:
    return bootstrap_app({
      "company_id":payload["company_id"],"version":payload["version"],
      "existing_contract_refs":_context_list(payload,"app_contract_refs"),
      "roles":_context_list(payload,"app_roles"),"modules":_context_list(payload,"app_modules"),
    })

def _aut(payload:dict)->dict:
    return bootstrap_automations({
      "company_id":payload["company_id"],"version":payload["version"],
      "existing_automation_refs":_context_list(payload,"existing_automation_refs"),
      "workflow_candidates":_context_list(payload,"workflow_candidates"),
    })

def _trn(payload:dict)->dict:
    return bootstrap_training({
      "company_id":payload["company_id"],"version":payload["version"],
      "knowledge_sources":_context_list(payload,"training_knowledge_sources"),
      "evaluation_cases":_context_list(payload,"training_evaluation_cases"),
    })

def _supervisor(payload:dict)->dict:
    return create_supervisor_scope({
      "company_id":payload["company_id"],"environment":"PREPROD","version":payload["version"],
      "engine_evidence":_all_evidence(payload),
      "required_engines":_ctx(payload).get("supervisor_required_engines") or None,
    })

def _backup(payload:dict)->dict:
    ctx=_ctx(payload)
    return create_backup_rebuild_pack({
      "company_id":payload["company_id"],"environment":"PREPROD","version":payload["version"],
      "backup_evidence":dict(ctx.get("backup_evidence") or {}),
      "rebuild_evidence":dict(ctx.get("rebuild_evidence") or {}),
    })

def _preprod(payload:dict)->dict:
    return evaluate_preprod_readiness({
      "company_id":payload["company_id"],"version":payload["version"],
      "engine_evidence":_all_evidence(payload),
    })

def _prod(payload:dict)->dict:
    return evaluate_production_activation({
      "company_id":payload["company_id"],"version":payload["version"],
      "preprod_readiness":_prior(payload,"COMP-DEP-001"),
    })

def build_default_onboarding_registry()->OnboardingHandlerRegistry:
    reg=OnboardingHandlerRegistry()
    bindings=(
      ("COMP-REG-001",_registration,("LOCAL_DETERMINISTIC",)),
      ("ACCESSBOOT-001",_access,("LOCAL_DETERMINISTIC",)),
      ("SCAN-001",_scan,("READ_ONLY",)),
      ("BMD-001",_bmd,("READ_ONLY",)),
      ("PROC-001",_proc,("READ_ONLY",)),
      ("WAUD-001",_waud,("READ_ONLY",)),
      ("KW-001",_kw,("READ_ONLY",)),
      ("SOCAUD-001",_soc,("READ_ONLY",)),
      ("LOCALP-001",_local,("READ_ONLY",)),
      ("COMPET-001",_compet,("READ_ONLY",)),
      ("KBOOT-001",_kboot,("LOCAL_DETERMINISTIC",)),
      ("SEOBOOT-001",_seoboot,("LOCAL_DETERMINISTIC",)),
      ("SOCBOOT-001",_socboot,("LOCAL_DETERMINISTIC",)),
      ("MKTBOOT-001",_mktboot,("LOCAL_DETERMINISTIC",)),
      ("ENGACT-001",_engact,("LOCAL_DETERMINISTIC",)),
      ("CRMBOOT-001",_crm,("PREPROD_ONLY",)),
      ("APPBOOT-001",_app,("PREPROD_ONLY",)),
      ("AUTBOOT-001",_aut,("PREPROD_ONLY",)),
      ("TRNBOOT-001",_trn,("PREPROD_ONLY",)),
      ("COMP-HLT-001",_supervisor,("PREPROD_ONLY",)),
      ("COMP-BKP-001",_backup,("PREPROD_ONLY",)),
      ("COMP-DEP-001",_preprod,("PREPROD_ONLY",)),
      ("COMP-ONB-001",_prod,("GATE_ONLY",)),
    )
    for engine_id,fn,modes in bindings:
        reg.register(EngineHandler(engine_id,fn,modes))
    return reg
