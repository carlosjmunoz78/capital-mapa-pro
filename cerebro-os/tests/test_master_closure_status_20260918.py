from pathlib import Path

DOC = Path("cerebro-os/evidence/CEREBRO_OS_CIERRE_MAESTRO_20260918.md")


def test_master_closure_is_fail_closed():
    text = DOC.read_text()
    assert "Global PROD/autonomy permanece `false`" in text
    assert "fenix-document-existing-backfill" in text
    assert "MONEY_LIMIT" in text
    assert "SECURITY_INCIDENT" in text
    assert "FINOPS" in text
    assert "FORGE PREPROD #39: SUCCESS" in text
    assert "sha256:d4d5d9d1c232f7998671979962b9e6e55d184e9ae689782dbeccfa079d623609" in text
