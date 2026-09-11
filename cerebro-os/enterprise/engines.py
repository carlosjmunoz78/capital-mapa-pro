from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable, Mapping

HUMAN = {"LEGAL_REQUIRED","SIGNATURE_REQUIRED","LOW_CONFIDENCE","HIGH_RISK","POLICY_CONFLICT","SECURITY_INCIDENT","MONEY_LIMIT","CUSTOMER_HUMAN_REQUEST"}

# HR-001
@dataclass(frozen=True)
class EmployeeProfile:
    employee_id: str
    role: str
    active: bool
    skills: frozenset[str]
    evidence_ref: str
    def validate(self):
        if not all((self.employee_id.strip(),self.role.strip(),self.evidence_ref.strip())): raise ValueError("employee identity/evidence required")

# HR-002
@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    scores: tuple[tuple[str,float],...]
    evidence_ref: str

def rank_candidates(candidates: Iterable[Candidate], weights: Mapping[str,float]) -> tuple[str,...]:
    rows=[]
    for c in candidates:
        if not c.candidate_id.strip() or not c.evidence_ref.strip(): raise ValueError("candidate evidence required")
        values=dict(c.scores)
        if not set(weights).issubset(values): raise ValueError("missing candidate score")
        rows.append((sum(values[k]*weights[k] for k in weights),c.candidate_id))
    return tuple(cid for _,cid in sorted(rows,key=lambda x:(-x[0],x[1])))

# HR-003
ONBOARDING=("ACCOUNTS","PERMISSIONS","TRAINING","SHADOWING","READINESS")
class EmployeeOnboarding:
    def __init__(self):
        self.done=set()
        self.evidence={}
    def complete(self,step:str,evidence_ref:str|None=None):
        if step not in ONBOARDING: raise ValueError("unknown onboarding step")
        i=ONBOARDING.index(step)
        if any(x not in self.done for x in ONBOARDING[:i]): raise ValueError("onboarding dependency incomplete")
        if not evidence_ref or not evidence_ref.strip(): raise ValueError("onboarding completion requires evidence_ref")
        self.evidence[step]=evidence_ref.strip()
        self.done.add(step)
    def next(self): return next((x for x in ONBOARDING if x not in self.done),None)

# HR-004
@dataclass(frozen=True)
class SkillCertification:
    employee_id:str; skill:str; score:float; pass_mark:float; critical:bool; evidence_ref:str
    def decision(self):
        if not self.evidence_ref.strip(): return "RED",None
        if self.score < self.pass_mark: return "RED",None
        if self.critical: return "HUMAN_REQUIRED","HIGH_RISK"
        return "GREEN",None

# HR-005
@dataclass(frozen=True)
class PerformanceSignal:
    employee_id:str; metric:str; actual:float; target:float; evidence_ref:str
    @property
    def gap(self): return self.target-self.actual

def coaching_actions(signals:Iterable[PerformanceSignal])->tuple[str,...]:
    rows=[]
    for s in signals:
        if not s.evidence_ref.strip(): raise ValueError("performance evidence required")
        if s.gap>0: rows.append(f"COACH:{s.employee_id}:{s.metric}")
    return tuple(sorted(rows))

# HR-006
@dataclass(frozen=True)
class WorkforceCandidate:
    employee_id:str; load:float; specialty_fit:float; performance:float; zone_fit:float; risk:float

def assign_case(candidates:Iterable[WorkforceCandidate],weights:Mapping[str,float])->str:
    required={"load","specialty_fit","performance","zone_fit","risk"}
    if set(weights)!=required: raise ValueError("explicit workforce weights required")
    rows=tuple(candidates)
    if not rows: raise ValueError("candidate required")
    def score(x): return -x.load*weights['load']+x.specialty_fit*weights['specialty_fit']+x.performance*weights['performance']+x.zone_fit*weights['zone_fit']-x.risk*weights['risk']
    return max(rows,key=lambda x:(score(x),x.employee_id)).employee_id

# LEG-001
@dataclass(frozen=True)
class LegalFinding:
    topic:str; conclusion:str; official_source_ref:str; effective_date:str; confidence:float; high_risk:bool
    def decision(self):
        if not self.official_source_ref.strip() or not self.effective_date.strip(): return "RED",None
        if self.confidence<.8: return "HUMAN_REQUIRED","LOW_CONFIDENCE"
        if self.high_risk: return "HUMAN_REQUIRED","LEGAL_REQUIRED"
        return "GREEN",None

# TAX-001
@dataclass(frozen=True)
class TaxRule:
    rule_id:str; version:str; official_source_ref:str; rate:Decimal
    def validate(self):
        if not all((self.rule_id.strip(),self.version.strip(),self.official_source_ref.strip())) or self.rate<0: raise ValueError("invalid tax rule")
def calculate_tax(base:Decimal,rule:TaxRule)->Decimal:
    rule.validate();
    if base<0: raise ValueError("negative tax base")
    return (base*rule.rate).quantize(Decimal("0.01"))

# CMP-002
@dataclass(frozen=True)
class ComplianceControl:
    control_id:str; required:bool; passed:bool; evidence_ref:str

def compliance_status(controls:Iterable[ComplianceControl])->str:
    rows=tuple(controls)
    if not rows or any(not c.evidence_ref.strip() for c in rows): return "RED"
    return "GREEN" if all((not c.required) or c.passed for c in rows) else "HUMAN_REQUIRED"

# DPO-001
@dataclass(frozen=True)
class PrivacyRequest:
    request_type:str; identity_verified:bool; lawful_basis:bool; sensitive:bool; identity_evidence_ref:str=''; lawful_basis_evidence_ref:str=''
    def decision(self):
        if not self.identity_verified or not self.lawful_basis: return "BLOCKED",None
        if not self.identity_evidence_ref.strip() or not self.lawful_basis_evidence_ref.strip(): return "BLOCKED",None
        if self.sensitive or self.request_type in {"DELETE","EXPORT"}: return "HUMAN_REQUIRED","LEGAL_REQUIRED"
        return "GREEN",None

# CONS-001
@dataclass(frozen=True)
class ConsentDocument:
    document_id:str; generated:bool; sent:bool; signed:bool; archived:bool; human_signature_required:bool; generated_evidence_ref:str=''; sent_evidence_ref:str=''; signed_evidence_ref:str=''; archived_evidence_ref:str=''
    def status(self):
        if not self.document_id.strip(): return "RED",None
        if self.human_signature_required and not self.signed: return "HUMAN_REQUIRED","SIGNATURE_REQUIRED"
        flags=(self.generated,self.sent,self.signed,self.archived)
        refs=(self.generated_evidence_ref,self.sent_evidence_ref,self.signed_evidence_ref,self.archived_evidence_ref)
        return (("GREEN",None) if all(flags) and all(x.strip() for x in refs) else ("RED",None))

# INV-001
@dataclass(frozen=True)
class Invoice:
    invoice_id:str; case_ref:str; net:Decimal; tax:Decimal; paid:Decimal; evidence_ref:str
    @property
    def total(self): return self.net+self.tax
    @property
    def balance(self): return self.total-self.paid
    def status(self):
        if not all((self.invoice_id.strip(),self.case_ref.strip(),self.evidence_ref.strip())): return "RED"
        return "GREEN" if self.net>=0 and self.tax>=0 and self.paid>=0 else "RED"

# COL-001
@dataclass(frozen=True)
class Receivable:
    invoice_id:str; due_at:str; balance:Decimal; reminders:int
    def action(self,now:datetime):
        due=datetime.fromisoformat(self.due_at.replace('Z','+00:00'))
        if self.balance<=0:return "CLOSED"
        if now<=due:return "WAIT"
        return "ESCALATE" if self.reminders>=3 else "REMIND"

# TRE-001
@dataclass(frozen=True)
class CashFlow:
    opening:Decimal; inflows:Decimal; outflows:Decimal; committed:Decimal
    @property
    def forecast(self): return self.opening+self.inflows-self.outflows-self.committed
    def status(self,min_cash:Decimal): return "GREEN" if self.forecast>=min_cash else "HUMAN_REQUIRED"

# ACC-001
@dataclass(frozen=True)
class AccountingItem:
    document_ref:str; category:str; amount:Decimal; reconciled:bool

def accounting_package(items:Iterable[AccountingItem])->tuple[str,tuple[str,...]]:
    rows=tuple(items)
    if any(not x.document_ref.strip() or not x.category.strip() for x in rows): return "RED",()
    unresolved=tuple(sorted(x.document_ref for x in rows if not x.reconciled))
    return ("GREEN" if not unresolved else "DOCUMENTED_PARTIAL",unresolved)

# VEN-001
@dataclass(frozen=True)
class VendorHealth:
    vendor_id:str; service_ok:bool; dependency_score:float; renewal_at:str; alternative_exists:bool; evidence_ref:str
    def status(self):
        if not self.evidence_ref.strip() or not 0<=self.dependency_score<=1:return "RED"
        if not self.service_ok or (self.dependency_score>.8 and not self.alternative_exists):return "HUMAN_REQUIRED"
        return "GREEN"

# BUY-001
@dataclass(frozen=True)
class ProcurementOption:
    option_id:str; cost:Decimal; benefit:Decimal; risk:float; evidence_ref:str

def procurement_decision(options:Iterable[ProcurementOption],limit:Decimal)->tuple[str,str|None]:
    rows=tuple(options)
    if not rows:return "RED",None
    affordable=[x for x in rows if x.cost<=limit and x.evidence_ref.strip()]
    if not affordable:return "HUMAN_REQUIRED","MONEY_LIMIT"
    best=max(affordable,key=lambda x:((x.benefit-x.cost)-Decimal(str(x.risk)),x.option_id))
    return "GREEN",best.option_id

# VREP-001
@dataclass(frozen=True)
class VendorReplacement:
    current_vendor:str; alternative_vendor:str; simulated:bool; rollback_ready:bool; critical:bool; evidence_ref:str
    def decision(self):
        if not self.evidence_ref.strip() or not self.simulated or not self.rollback_ready:return "BLOCKED",None
        if self.critical:return "HUMAN_REQUIRED","HIGH_RISK"
        return "GREEN",None

# VCON-001
@dataclass(frozen=True)
class VendorContract:
    vendor_id:str; renewal_at:str; permanence_end:str; clauses_reviewed:bool; evidence_ref:str
    def action(self,now:datetime,alert_days:int=30):
        if not self.evidence_ref.strip() or not self.clauses_reviewed:return "RED"
        renewal=datetime.fromisoformat(self.renewal_at.replace('Z','+00:00'))
        days=(renewal-now).total_seconds()/86400
        return "REVIEW_RENEWAL" if days<=alert_days else "GREEN"
