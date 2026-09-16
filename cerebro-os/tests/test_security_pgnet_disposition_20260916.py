from pathlib import Path


def test_pgnet_disposition_is_fail_closed_and_non_mutating():
    p = Path('cerebro-os/evidence/security/SUPABASE_PROD_PG_NET_DISPOSITION_20260916.md')
    text = p.read_text(encoding='utf-8')
    assert 'extrelocatable = false' in text
    assert 'PRESERVE_AND_AUDIT' in text
    assert 'No automatic `ALTER EXTENSION ... SET SCHEMA`' in text
    assert 'No function, extension, schema, table, data, RLS policy, App/CRM source, Edge Function, or PROD promotion flag was modified' in text
