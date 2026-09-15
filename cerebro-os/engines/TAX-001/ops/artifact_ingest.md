# TAX-001 · Canonical artifact ingest · LAB

Purpose: bind AW/AV/BH only from physical JSON artifacts, never from memory, manifests, prose summaries or manually inferred hashes.

## Preconditions
- AW, AV and BH must exist as local files.
- Each file must be valid UTF-8 JSON.
- AW must expose exactly the canonical case ID set `FISC-G001..FISC-G077`.
- BH must expose exactly 21 unique pending IDs and every one must belong to AW.
- AV must identify itself semantically as the provenance/placeholder audit artifact.

## Command

```bash
python cerebro-os/engines/TAX-001/ops/artifact_ingest.py \
  --aw /path/to/AW.json \
  --av /path/to/AV.json \
  --bh /path/to/BH.json \
  --out /tmp/tax001_corpus_lock.json
```

The command computes SHA-256 directly from bytes and writes a `BOUND` lock only after all structural validations pass. Any missing/malformed/inconsistent artifact exits fail-closed and must not mutate the canonical repository lock.

## Promotion rule
The generated lock is evidence, not automatic promotion. Before replacing `config/corpus_lock.json`, compare hashes and artifact semantics against the physical transfer package, preserve the source package, run the complete TAX-001 test suite, and rerun the capability tribunal.

No App/CRM/PROD mutation is part of this process.
