"""LAB-only SQLite spool: single durable discovery/review queue, no sending API."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path

class DiscoveryQueue:
    """Persistent, idempotent and reopenable; status cannot become SENDABLE."""
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(self.path))
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS prospects (
          idempotency_key TEXT PRIMARY KEY,
          company_id TEXT NOT NULL CHECK (company_id='fenix'),
          engine_id TEXT NOT NULL CHECK (engine_id='B2B-PROSPECT-001'),
          environment TEXT NOT NULL CHECK (environment='LAB'),
          priority INTEGER NOT NULL CHECK(priority BETWEEN 1 AND 15),
          ine_code TEXT NOT NULL,
          municipality TEXT NOT NULL,
          business_name TEXT NOT NULL,
          source_url TEXT NOT NULL DEFAULT '',
          state TEXT NOT NULL DEFAULT 'DISCOVERED_ONLY'
            CHECK(state IN ('DISCOVERED_ONLY','REVIEW_PENDING','REJECTED')),
          send_authorized INTEGER NOT NULL DEFAULT 0 CHECK(send_authorized=0),
          added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_b2b_spool ON prospects(priority,municipality,business_name);
        CREATE TABLE IF NOT EXISTS progress (
          scope TEXT PRIMARY KEY,
          last_reviewed_key TEXT NOT NULL,
          reviewed_count INTEGER NOT NULL DEFAULT 0,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );""")

    def ingest(self, prepared):
        if prepared.get("state") != "LAB_PLANNED_NO_SEND" or prepared.get("emails_sent") != 0:
            raise ValueError("LAB planner input required")
        added = 0
        with self.db:
            for row in prepared["queue"]:
                if row.get("send_authorized") is not False or row.get("company_id") != "fenix" or row.get("environment") != "LAB":
                    raise ValueError("write outside LAB no-send contract")
                c = self.db.execute("""
                  INSERT OR IGNORE INTO prospects
                    (idempotency_key,company_id,engine_id,environment,priority,ine_code,municipality,business_name,source_url)
                  VALUES (?,?,?,?,?,?,?,?,?)""",(
                    row["idempotency_key"],row["company_id"],row["engine_id"],row["environment"],
                    row["priority"],row["ine_code"],row["municipality"],row["business_name"],row["source_url"]))
                added += c.rowcount
        return {"inserted":added,"already_present":len(prepared["queue"])-added,"sent":0}

    def next_review(self, n=10):
        if type(n) is not int or n<1 or n>100:
            raise ValueError("review batch must be 1..100")
        return [dict(r) for r in self.db.execute("""
          SELECT idempotency_key,priority,ine_code,municipality,business_name,source_url,state
          FROM prospects WHERE state='DISCOVERED_ONLY'
          ORDER BY priority,municipality,business_name,idempotency_key LIMIT ?""",(n,))]

    def mark_reviewed(self, idempotency_key, *, decision):
        if decision not in ("REVIEW_PENDING","REJECTED"):
            raise ValueError("commercial sending cannot be activated in LAB")
        with self.db:
            row=self.db.execute("SELECT state FROM prospects WHERE idempotency_key=?",(idempotency_key,)).fetchone()
            if row is None:
                raise KeyError("unknown prospect")
            if row["state"] == "DISCOVERED_ONLY":
                self.db.execute("UPDATE prospects SET state=? WHERE idempotency_key=?",(decision,idempotency_key))
                self.db.execute("""
                  INSERT INTO progress(scope,last_reviewed_key,reviewed_count)
                  VALUES('fenix/B2B-PROSPECT-001/LAB',?,1)
                  ON CONFLICT(scope) DO UPDATE SET last_reviewed_key=excluded.last_reviewed_key,
                    reviewed_count=progress.reviewed_count+1,updated_at=CURRENT_TIMESTAMP""",(idempotency_key,))
                return True
            return False

    def report(self):
        counts={r["state"]:r["total"] for r in self.db.execute(
            "SELECT state,count(*) total FROM prospects GROUP BY state")}
        progress=self.db.execute("SELECT last_reviewed_key,reviewed_count,updated_at FROM progress WHERE scope=?",
                                 ("fenix/B2B-PROSPECT-001/LAB",)).fetchone()
        return {"company_id":"fenix","engine_id":"B2B-PROSPECT-001","environment":"LAB",
                "state":"LAB_NO_SEND", "counts":counts,"cursor":dict(progress) if progress else None,
                "emails_sent":0,"extra_cost_eur":0}

    def export_checkpoint(self, filename):
        """Export only summary evidence (not prospect emails/PII)."""
        target=Path(filename)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(self.report(),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        return target

    def close(self):
        self.db.close()
