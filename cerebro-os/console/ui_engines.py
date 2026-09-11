from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

# CONSOLE-001
@dataclass(frozen=True)
class ConsoleSession:
    user_id:str; company_id:str; context_type:str; context_id:str|None; message:str
    def validate(self):
        if not all((self.user_id.strip(),self.company_id.strip(),self.context_type.strip(),self.message.strip())):raise ValueError('console session requires user/company/context/message')

# CHAT-001
@dataclass(frozen=True)
class NormalizedRequest:
    user_id:str; company_id:str; context_ref:str; permissions:frozenset[str]; input_type:str; content_ref:str
    def validate(self):
        if self.input_type not in {'TEXT','FILE','VOICE'}:raise ValueError('unsupported input type')
        if not all((self.user_id.strip(),self.company_id.strip(),self.context_ref.strip(),self.content_ref.strip())):raise ValueError('normalized request fields required')

# CTX-001
@dataclass(frozen=True)
class ContextPackage:
    company_id:str; entity_refs:tuple[str,...]; engine_refs:tuple[str,...]; history_refs:tuple[str,...]; permissions:frozenset[str]; provenance_refs:tuple[str,...]
    def validate(self,max_refs:int=100):
        if not self.company_id.strip() or not self.provenance_refs:raise ValueError('context scope/provenance required')
        if sum(map(len,(self.entity_refs,self.engine_refs,self.history_refs)))>max_refs:raise ValueError('context size limit exceeded')

# CMD-001
COMMAND_RULES={'estado':'STATUS','crear empresa':'CREATE_COMPANY','navegar':'NAVIGATE','analiza':'ANALYZE','ejecuta':'ACTION','cambia regla':'RULE_CHANGE'}
def classify_command(text:str)->tuple[str,str|None]:
    t=text.casefold().strip()
    for prefix,intent in COMMAND_RULES.items():
        if t.startswith(prefix):return 'GREEN',intent
    return 'HUMAN_REQUIRED','LOW_CONFIDENCE'

# ACTGW-001
@dataclass(frozen=True)
class ActionEnvelope:
    request_id:str; company_id:str; engine_id:str; action:str; idempotency_key:str; policy_allowed:bool; iam_allowed:bool; audit_ref:str; preview_required:bool=False; preview_approved:bool=False
    def decision(self):
        if not all((self.request_id.strip(),self.company_id.strip(),self.engine_id.strip(),self.action.strip(),self.idempotency_key.strip(),self.audit_ref.strip())):return 'RED'
        if not self.policy_allowed:return 'HUMAN_REQUIRED'
        if not self.iam_allowed:return 'BLOCKED'
        if self.preview_required and not self.preview_approved:return 'BLOCKED'
        return 'GREEN'

# DIRUI-001
@dataclass(frozen=True)
class DirectorView:
    attention:int; red:int; in_progress:int; done:int; cost_eur:float; next_recommendation:str
    def validate(self):
        if min(self.attention,self.red,self.in_progress,self.done,self.cost_eur)<0 or not self.next_recommendation.strip():raise ValueError('invalid director view')

# TIMELINE-001
@dataclass(frozen=True)
class TimelineEvent:
    company_id:str; engine_id:str; result:str; cost_eur:float; evidence_ref:str; repaired:bool=False

def timeline(events:Iterable[TimelineEvent],company_id:str)->tuple[TimelineEvent,...]:
    rows=tuple(e for e in events if e.company_id==company_id)
    if any(not e.engine_id.strip() or not e.evidence_ref.strip() or e.cost_eur<0 for e in rows):raise ValueError('invalid timeline event')
    return rows

# WHY-001
@dataclass(frozen=True)
class Explanation:
    decision_id:str; rules:tuple[str,...]; sources:tuple[str,...]; data_refs:tuple[str,...]; confidence:float; alternatives:tuple[str,...]; version:str; engine_id:str
    def validate(self):
        if not all((self.decision_id.strip(),self.sources,self.data_refs,self.version.strip(),self.engine_id.strip())):raise ValueError('explanation provenance required')
        if not 0<=self.confidence<=1:raise ValueError('confidence normalized')

# VOICEUI-001
@dataclass(frozen=True)
class VoiceInput:
    company_id:str; audio_ref:str; local_transcript:str; consent:bool
    def to_chat(self):
        if not self.company_id.strip() or not self.audio_ref.strip() or not self.local_transcript.strip():return 'RED',None
        if not self.consent:return 'HUMAN_REQUIRED','LEGAL_REQUIRED'
        return 'GREEN',self.local_transcript
