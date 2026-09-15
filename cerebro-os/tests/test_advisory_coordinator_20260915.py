import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.coordinator import coordinate
from advisory.models import DomainOpinion


def test_coordinate_requires_every_routed_domain():
    opinions = (DomainOpinion(domain="FISCAL", status="GREEN", summary="ok", source_refs=("src:fiscal",)),)
    try:
        coordinate("CASE", ("FISCAL", "CONTABLE"), opinions)
    except ValueError as exc:
        assert "missing domain opinions" in str(exc)
    else:
        raise AssertionError("missing specialty opinion must fail closed")


def test_green_opinion_requires_source_refs():
    opinions = (DomainOpinion(domain="FISCAL", status="GREEN", summary="ok", source_refs=()),)
    try:
        coordinate("CASE", ("FISCAL",), opinions)
    except ValueError as exc:
        assert "requires source refs" in str(exc)
    else:
        raise AssertionError("source-less GREEN must fail closed")


def test_overall_status_uses_strictest_specialty():
    opinions = (
        DomainOpinion(domain="FISCAL", status="GREEN", summary="ok", source_refs=("src:fiscal",)),
        DomainOpinion(domain="MERCANTIL", status="HUMAN_REQUIRED", summary="signature needed", source_refs=("src:mercantil",), human_exception="SIGNATURE_REQUIRED"),
    )
    result = coordinate("CASE", ("FISCAL", "MERCANTIL"), opinions, audit_refs=("AUD-1",))
    assert result.overall_status == "HUMAN_REQUIRED"
    assert result.audit_refs == ("AUD-1",)
