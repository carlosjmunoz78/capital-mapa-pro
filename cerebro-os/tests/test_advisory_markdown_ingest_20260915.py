import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.markdown_ingest import build_index, extract_section_text


def test_ingest_preserves_heading_structure_and_ranges(tmp_path):
    source = tmp_path / "repo.md"
    source.write_text("# Root\nintro\n## Child A\na\n### Leaf\nb\n## Child B\nc\n", encoding="utf-8")
    index = build_index("TEST", source)
    assert index.domain == "TEST"
    assert len(index.sections) == 4
    root, child_a, leaf, child_b = index.sections
    assert root.start_line == 1 and root.end_line == 8
    assert child_a.start_line == 3 and child_a.end_line == 6
    assert leaf.start_line == 5 and leaf.end_line == 6
    assert child_b.start_line == 7 and child_b.end_line == 8
    assert extract_section_text(source, child_b) == "## Child B\nc"


def test_ingest_hash_gate_is_fail_closed(tmp_path):
    source = tmp_path / "repo.md"
    source.write_text("# Root\n", encoding="utf-8")
    try:
        build_index("TEST", source, expected_sha256="0" * 64)
    except ValueError as exc:
        assert "hash mismatch" in str(exc)
    else:
        raise AssertionError("hash mismatch must fail closed")


def test_ingest_rejects_missing_source(tmp_path):
    try:
        build_index("TEST", tmp_path / "missing.md")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("missing source must fail closed")
