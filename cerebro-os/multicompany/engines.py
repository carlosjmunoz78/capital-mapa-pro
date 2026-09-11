from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, Mapping

# COMP-REG-001
@dataclass(frozen=True)
class CompanyManifest:
    company_id:str; name:str; domains:tuple[str,...]; sector:str; country:str; owner:str; environments:tuple[str,...]; active_engines:tuple[str,...]
    def validate(self):
        if not all((self.company_id.strip(),self.name.strip(),self.sector.strip(),self.country.strip(),self.owner.strip())): raise ValueError('company identity required')
        if not self.environments or any(e not in {'LAB','PREPROD','PROD'} for e in self.environments): raise ValueError('invalid environments')

# COMP-ONB-001
ONBOARDING_PHASES=('SCAN','KNOWLEDGE','SEO','SOCIAL','MARKETING','CRM','APP','AUTOMATIONS','TRAINING','SUPERVISOR','BACKUP')
class CompanyOnboarding:
    def __init__(self,company_id:str): self.company_id=company_id;self.states={x:'PENDING' for x in ONBOARDING_PHASES}
    def next(self): return next((x for x in ONBOARDING_PHASES if self.states[x]!='GREEN'),None)
    def update(self,phase:str,status:str):
        if phase not in self.states or status not in {'GREEN','RED','BLOCKED','HUMAN_REQUIRED'}:raise ValueError('invalid phase/status')
        i=ONBOARDING_PHASES.index(phase)
        if status=='GREEN' and any(self.states[x]!='GREEN' for x in ONBOARDING_PHASES[:i]):raise ValueError('phase dependency incomplete')
        self.states[phase]=status

# SCAN-001
@dataclass(frozen=True)
class FootprintFinding:
    kind:str; value:str; source_ref:str; observed_at:str; confidence:float
    def validate(self):
        if not all((self.kind.strip(),self.value.strip(),self.source_ref.strip(),self.observed_at.strip())) or not 0<=self.confidence<=1:raise ValueError('invalid footprint finding')

# KW-001
@dataclass(frozen=True)
class KeywordIdea:
    keyword:str; intent:str; location:str; opportunity:float; target_url:str|None; evidence_ref:str

def rank_keywords(rows:Iterable[KeywordIdea])->tuple[str,...]:
    items=tuple(rows)
    if any(not x.keyword.strip() or not x.intent.strip() or not x.evidence_ref.strip() for x in items):raise ValueError('keyword evidence required')
    return tuple(x.keyword for x in sorted(items,key=lambda x:(-x.opportunity,x.keyword)))

# WAUD-001
@dataclass(frozen=True)
class WebAuditCheck:
    check_id:str; passed:bool; impact:int; evidence_ref:str

def web_audit_score(rows:Iterable[WebAuditCheck])->tuple[float,tuple[str,...]]:
    items=tuple(rows)
    if not items or any(not x.evidence_ref.strip() for x in items):raise ValueError('audit evidence required')
    total=sum(max(0,x.impact) for x in items); passed=sum(max(0,x.impact) for x in items if x.passed)
    backlog=tuple(x.check_id for x in sorted((x for x in items if not x.passed),key=lambda x:(-x.impact,x.check_id)))
    return (1.0 if total==0 else round(passed/total,6),backlog)

# SOCAUD-001
@dataclass(frozen=True)
class SocialProfile:
    network:str; profile_ref:str; posts_per_month:int; engagement:float; evidence_ref:str
    def validate(self):
        if not all((self.network.strip(),self.profile_ref.strip(),self.evidence_ref.strip())) or self.posts_per_month<0 or self.engagement<0:raise ValueError('invalid social profile')

# LOCALP-001
@dataclass(frozen=True)
class LocalPresence:
    nap_consistent:bool; categories_ok:bool; services_ok:bool; reviews_monitored:bool; source_refs:tuple[str,...]
    @property
    def status(self): return 'GREEN' if self.source_refs and all((self.nap_consistent,self.categories_ok,self.services_ok,self.reviews_monitored)) else 'RED'

# BMD-001
@dataclass(frozen=True)
class BusinessFact:
    key:str; value:str; confirmed:bool; source_ref:str

def business_model_status(facts:Iterable[BusinessFact],critical_keys:Iterable[str])->tuple[str,tuple[str,...]]:
    rows=tuple(facts);confirmed={x.key for x in rows if x.confirmed and x.source_ref.strip()};missing=tuple(sorted(set(critical_keys)-confirmed))
    return ('GREEN' if not missing else 'HUMAN_REQUIRED',missing)

# PROC-001
@dataclass(frozen=True)
class ProcessNode:
    node_id:str; owner:str; system:str; outputs:tuple[str,...]

def process_map_status(nodes:Iterable[ProcessNode])->str:
    rows=tuple(nodes)
    if not rows:return 'RED'
    return 'GREEN' if all(x.node_id.strip() and x.owner.strip() and x.system.strip() for x in rows) else 'HUMAN_REQUIRED'

# KBOOT-001
@dataclass(frozen=True)
class BootstrapKnowledge:
    company_id:str; namespace:str; source_refs:tuple[str,...]; rules_count:int; glossary_count:int
    @property
    def green(self): return bool(self.company_id.strip() and self.namespace.startswith(self.company_id+':') and self.source_refs and self.rules_count>=0 and self.glossary_count>=0)

# SEOBOOT-001
@dataclass(frozen=True)
class SeoBootstrap:
    keyword_map_ready:bool; architecture_ready:bool; technical_backlog_ready:bool; local_ready:bool; measurement_ready:bool; publish_gate_ref:str
    @property
    def green(self):return all((self.keyword_map_ready,self.architecture_ready,self.technical_backlog_ready,self.local_ready,self.measurement_ready,bool(self.publish_gate_ref.strip())))

# SOCBOOT-001
@dataclass(frozen=True)
class SocialBootstrap:
    pillars:tuple[str,...]; tone_ref:str; calendar_ref:str; metric_refs:tuple[str,...]; publish_permission:bool
    def status(self):
        if not self.pillars or not self.tone_ref.strip() or not self.calendar_ref.strip() or not self.metric_refs:return 'RED'
        return 'GREEN' if self.publish_permission else 'PLAN_GREEN'

# MKTBOOT-001
@dataclass(frozen=True)
class MarketingBootstrap:
    funnel_ref:str; personas_ref:str; tracking_ready:bool; organic_plan_ref:str; paid_budget:float; approved_paid_budget:float
    def status(self):
        if not all((self.funnel_ref.strip(),self.personas_ref.strip(),self.organic_plan_ref.strip(),self.tracking_ready)):return 'RED'
        return 'HUMAN_REQUIRED' if self.paid_budget>self.approved_paid_budget else 'GREEN'

# CRMBOOT-001 / APPBOOT-001 / AUTBOOT-001 shared scaffold
@dataclass(frozen=True)
class CompanyScaffold:
    company_id:str; kind:str; config_ref:str; tenant_isolated:bool; tests_green:bool; environment:str
    def status(self):
        if self.kind not in {'CRM','APP','AUTOMATION'}:raise ValueError('invalid scaffold kind')
        if self.environment=='PROD':return 'BLOCKED'
        return 'GREEN' if self.company_id.strip() and self.config_ref.strip() and self.tenant_isolated and self.tests_green else 'RED'

# TRNBOOT-001
@dataclass(frozen=True)
class TrainingBootstrap:
    company_id:str; dataset_ref:str; vocabulary_ref:str; scorecard_ref:str; cross_company_data:bool
    @property
    def status(self):
        if self.cross_company_data:return 'BLOCKED'
        return 'GREEN' if all((self.company_id.strip(),self.dataset_ref.strip(),self.vocabulary_ref.strip(),self.scorecard_ref.strip())) else 'RED'

# ENGACT-001
@dataclass(frozen=True)
class ActivationRule:
    sector:str; required:tuple[str,...]; optional:tuple[str,...]

def activation_matrix(sector:str,rules:Iterable[ActivationRule])->tuple[tuple[str,...],tuple[str,...]]:
    matches=[x for x in rules if x.sector==sector or x.sector=='*']
    required=tuple(sorted({e for x in matches for e in x.required}));optional=tuple(sorted({e for x in matches for e in x.optional if e not in required}))
    return required,optional

# COMP-DEP-001
@dataclass(frozen=True)
class CompanyDeployment:
    preprod_green:bool; tests_green:bool; integrations_green:bool; rollback_verified:bool; health_green:bool
    @property
    def promotable(self): return all((self.preprod_green,self.tests_green,self.integrations_green,self.rollback_verified,self.health_green))

# COMP-HLT-001
@dataclass(frozen=True)
class CompanyHealth:
    company_id:str; sla_green:bool; errors_green:bool; cost_green:bool; engines_green:bool
    @property
    def status(self):return 'GREEN' if self.company_id.strip() and all((self.sla_green,self.errors_green,self.cost_green,self.engines_green)) else 'RED'

# COMP-BKP-001
@dataclass(frozen=True)
class CompanyBackupPack:
    company_id:str; manifest_ref:str; config_ref:str; schema_ref:str; knowledge_ref:str; restore_verified:bool
    @property
    def digest(self):
        if not all((self.company_id.strip(),self.manifest_ref.strip(),self.config_ref.strip(),self.schema_ref.strip(),self.knowledge_ref.strip())):raise ValueError('backup pack incomplete')
        return sha256(repr((self.company_id,self.manifest_ref,self.config_ref,self.schema_ref,self.knowledge_ref)).encode()).hexdigest()
    @property
    def green(self): return bool(self.restore_verified and self.digest)

# COMP-OFF-001
@dataclass(frozen=True)
class OffboardingPlan:
    company_id:str; export_ref:str; accesses_revoked:bool; jobs_stopped:bool; audit_retained:bool; retention_policy_ref:str; final_approval:bool
    def status(self):
        if not self.final_approval:return 'HUMAN_REQUIRED'
        return 'GREEN' if all((self.company_id.strip(),self.export_ref.strip(),self.accesses_revoked,self.jobs_stopped,self.audit_retained,self.retention_policy_ref.strip())) else 'RED'
