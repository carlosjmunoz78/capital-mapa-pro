from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class SignalInput:
    company_id: str
    engine_id: str
    environment: str
    version: str
    signal_id: str
    title: str
    summary: str
    source: str
    buyer_persona: str
    funnel_phase: str
    objective: str
    recommended_content: str
    avoid_content: str
    priority: str
    recommendation: str
    primary_channel: str = "Blog/Web"
    secondary_channel: str = "General"
    recommended_format: str = "Blog"
    secondary_format: str = "Derivado"
    hook_type: str = "SEO / Blog"
    adaptation: str = "Keyword SEO"
    secondary_adaptation: str = "Landing / recurso"

    def validate(self) -> None:
        required = (
            self.company_id, self.engine_id, self.environment, self.version, self.signal_id,
            self.title, self.summary, self.source, self.buyer_persona, self.funnel_phase,
            self.objective, self.recommended_content, self.avoid_content, self.priority,
            self.recommendation,
        )
        if any(not str(v).strip() for v in required):
            raise ValueError("signal pipeline missing required fields")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")

    @property
    def idempotency_key(self) -> str:
        return f"CEREBRO_SIGNAL:{self.company_id}:{self.environment}:{self.version}:{self.signal_id}"


def build_signal_pipeline_plan(signal: SignalInput, *, duplicate_exists: bool = False) -> dict:
    signal.validate()
    if duplicate_exists:
        return {
            "company_id": signal.company_id,
            "engine_id": signal.engine_id,
            "environment": signal.environment,
            "version": signal.version,
            "signal_id": signal.signal_id,
            "idempotency_key": signal.idempotency_key,
            "status": "BLOCKED_DUPLICATE",
            "external_action_allowed": False,
            "requires_human": False,
        }
    idea = {
        "title": signal.title,
        "summary": f"{signal.summary} | SIGNAL_ID={signal.signal_id}",
        "source": signal.source,
        "state": "Nueva",
        "mode": "Prueba",
        "idea_version": 1,
        "ok_carlos": False,
    }
    funnel = {
        "key": f"{signal.title} · {signal.buyer_persona} · {signal.funnel_phase}",
        "buyer_persona": signal.buyer_persona,
        "funnel_phase": signal.funnel_phase,
        "objective": signal.objective,
        "primary_channel": signal.primary_channel or "Blog/Web",
        "secondary_channel": signal.secondary_channel or "General",
        "formats": [signal.recommended_format or "Blog", signal.secondary_format or "Derivado"],
        "recommended_content": signal.recommended_content,
        "avoid_content": signal.avoid_content,
        "tone": "Educativo",
        "aggressiveness": "Media",
        "base_legal_risk": "Bajo",
        "priority": signal.priority,
    }
    evaluation = {
        "name": f"EVALUACIÓN · {signal.title}",
        "objective": signal.objective,
        "buyer_persona": signal.buyer_persona,
        "funnel_phase": signal.funnel_phase,
        "primary_channel": signal.primary_channel or "Blog/Web",
        "formats": [signal.recommended_format or "Blog", signal.secondary_format or "Derivado"],
        "hook_types": [signal.hook_type or "SEO / Blog"],
        "legal_risk": "OK",
        "saturation": "Fresco",
        "tone": "Educativo",
        "aggressiveness": "Media",
        "frequency": "Alta",
        "adaptations": [signal.adaptation or "Keyword SEO", signal.secondary_adaptation or "Landing / recurso"],
        "recommendation": f"{signal.recommendation} | SIGNAL_ID={signal.signal_id}",
        "decision_state": "En análisis",
        "ok_carlos": False,
    }
    laboratory = {
        "experiment": f"LAB · {signal.title}",
        "signal_id": signal.signal_id,
        "buyer_persona": signal.buyer_persona,
        "funnel_phase": signal.funnel_phase,
        "primary_channel": signal.primary_channel or "Blog/Web",
        "formats": [signal.recommended_format or "Blog", signal.secondary_format or "Derivado"],
        "hypothesis": signal.recommendation,
        "measurable_objective": signal.objective,
        "input_evidence": f"{signal.summary} | Fuente={signal.source} | Contenido={signal.recommended_content} | Evitar={signal.avoid_content}",
        "priority": signal.priority,
        "environment": "TEST",
        "state": "Sin empezar",
        "decision": "Pendiente",
        "type": "Contenido",
        "legal_risk": "Bajo",
        "ok_carlos": False,
        "calendar_ready": False,
        "promoted_to_pattern": False,
    }
    return {
        "company_id": signal.company_id,
        "engine_id": signal.engine_id,
        "environment": signal.environment,
        "version": signal.version,
        "signal_id": signal.signal_id,
        "idempotency_key": signal.idempotency_key,
        "status": "PLAN_READY_NO_EXTERNAL_WRITE",
        "idea": idea,
        "funnel": funnel,
        "evaluation": evaluation,
        "laboratory": laboratory,
        "requires_human": True,
        "external_action_allowed": False,
    }
