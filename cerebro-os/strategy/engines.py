from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable, Mapping

# STR-001
@dataclass(frozen=True)
class StrategicOption:
    option_id:str; upside:float; downside:float; confidence:float; evidence_refs:tuple[str,...]

def strategy_recommend(options:Iterable[StrategicOption])->tuple[str,str|None]:
    rows=tuple(options)
    if not rows:return 'RED',None
    if any(not x.evidence_refs or x.confidence<.75 for x in rows):return 'HUMAN_REQUIRED','LOW_CONFIDENCE'
    best=max(rows,key=lambda x:(x.upside-x.downside,x.confidence,x.option_id))
    return 'HUMAN_REQUIRED',best.option_id

# FRC-001
def simple_forecast(history:Iterable[float],horizon:int=1)->tuple[float,...]:
    rows=tuple(float(x) for x in history)
    if len(rows)<2 or horizon<1:raise ValueError('history>=2 and horizon>=1 required')
    trend=(rows[-1]-rows[0])/(len(rows)-1)
    return tuple(round(rows[-1]+trend*i,6) for i in range(1,horizon+1))

# CAPA-001
@dataclass(frozen=True)
class CapacitySignal:
    demand:float; capacity:float; buffer_ratio:float
    def status(self):
        if self.demand<0 or self.capacity<0 or self.buffer_ratio<0:raise ValueError('invalid capacity')
        required=self.demand*(1+self.buffer_ratio)
        return ('GREEN',0.0) if self.capacity>=required else ('SCALE_REQUIRED',round(required-self.capacity,6))

# OPP-001
@dataclass(frozen=True)
class Opportunity:
    opportunity_id:str; expected_benefit:float; cost:float; risk:float; evidence_ref:str
    def decision(self,approved_cost:float):
        if not self.evidence_ref.strip():return 'RED',None
        if self.cost>approved_cost:return 'HUMAN_REQUIRED','MONEY_LIMIT'
        roi=self.expected_benefit-self.cost-self.risk
        return ('MVP',self.opportunity_id) if roi>0 else ('DISCARD',self.opportunity_id)

# INN-001
@dataclass(frozen=True)
class InnovationHypothesis:
    hypothesis_id:str; current_cost:float; expected_cost:float; quality_delta:float; evidence_ref:str
    @property
    def worthwhile(self):
        if not self.evidence_ref.strip():raise ValueError('evidence required')
        return self.expected_cost<self.current_cost or self.quality_delta>0

# EXP-001
@dataclass(frozen=True)
class ExperimentResult:
    experiment_id:str; control:tuple[float,...]; treatment:tuple[float,...]; min_effect:float; evidence_ref:str
    def decision(self):
        if not self.control or not self.treatment or not self.evidence_ref.strip():return 'RED'
        effect=mean(self.treatment)-mean(self.control)
        return 'SCALE' if effect>=self.min_effect else 'KILL'

# LAB-* common strict isolation
@dataclass(frozen=True)
class LabRun:
    lab_id:str; environment:str; real_execution:bool; credentials_scope:str; cost:float; cost_limit:float; evidence_ref:str
    def decision(self):
        if self.lab_id not in {'LAB-TRD','LAB-SEO','LAB-MKT','LAB-AI','LAB-AUT'}:raise ValueError('unknown lab')
        if self.environment not in {'LAB','PAPER','PREPROD'}:return 'BLOCKED','HIGH_RISK'
        if self.lab_id=='LAB-TRD' and self.real_execution:return 'BLOCKED','HIGH_RISK'
        if self.cost>self.cost_limit:return 'HUMAN_REQUIRED','MONEY_LIMIT'
        if not self.evidence_ref.strip() or not self.credentials_scope.strip():return 'RED',None
        return 'GREEN',None

# MKT-002
@dataclass(frozen=True)
class MarketSignal:
    key:str; value:float; source_ref:str; confidence:float

def market_intelligence(signals:Iterable[MarketSignal],min_confidence:float=.75)->tuple[str,dict[str,float]]:
    rows=tuple(signals)
    if not rows or any(not x.source_ref.strip() for x in rows):return 'RED',{}
    if any(x.confidence<min_confidence for x in rows):return 'HUMAN_REQUIRED',{}
    return 'GREEN',{x.key:x.value for x in rows}

# EXPAND-001
@dataclass(frozen=True)
class CityScore:
    city:str; demand:float; competition:float; partner_fit:float; seo:float; cost:float; capacity:float

def rank_cities(rows:Iterable[CityScore],weights:Mapping[str,float])->tuple[str,...]:
    required={'demand','competition','partner_fit','seo','cost','capacity'}
    if set(weights)!=required:raise ValueError('explicit expansion weights required')
    def score(x):return x.demand*weights['demand']-x.competition*weights['competition']+x.partner_fit*weights['partner_fit']+x.seo*weights['seo']-x.cost*weights['cost']+x.capacity*weights['capacity']
    return tuple(x.city for x in sorted(rows,key=lambda x:(-score(x),x.city)))

# FRAN-001
@dataclass(frozen=True)
class ReplicationReadiness:
    config_ready:bool; rebuild_verified:bool; tenant_isolation:bool; minimum_engines_green:bool; territory_config_ref:str
    config_evidence_ref:str=''; rebuild_evidence_ref:str=''; tenant_evidence_ref:str=''; engines_evidence_ref:str=''
    @property
    def green(self):
        gates=(self.config_ready,self.rebuild_verified,self.tenant_isolation,self.minimum_engines_green,bool(self.territory_config_ref.strip()))
        evidence=(self.config_evidence_ref,self.rebuild_evidence_ref,self.tenant_evidence_ref,self.engines_evidence_ref)
        return all(gates) and all(str(ref).strip() for ref in evidence)

# VENT-001
@dataclass(frozen=True)
class VentureCase:
    idea:str; research_green:bool; mvp_green:bool; unit_economics:float; experiment_green:bool; requested_cost:float; approved_cost:float
    research_evidence_ref:str=''; mvp_evidence_ref:str=''; experiment_evidence_ref:str=''; economics_evidence_ref:str=''
    def decision(self):
        if self.requested_cost>self.approved_cost:return 'HUMAN_REQUIRED','MONEY_LIMIT'
        if not all((self.idea.strip(),self.research_green,self.mvp_green,self.experiment_green)):return 'RED',None
        evidence=(self.research_evidence_ref,self.mvp_evidence_ref,self.experiment_evidence_ref,self.economics_evidence_ref)
        if not all(str(ref).strip() for ref in evidence):return 'BLOCKED',None
        return ('SCALE',None) if self.unit_economics>0 else ('KILL',None)
