from __future__ import annotations

import json
import sqlite3
from pathlib import Path

FORBIDDEN_SECRET_KEYS={"password","token","api_key","secret","secret_value","raw_secret","credential_value"}

def _reject_raw_secrets(value)->None:
    if isinstance(value,dict):
        for key,child in value.items():
            if str(key).lower() in FORBIDDEN_SECRET_KEYS:
                raise ValueError(f"raw secret field forbidden: {key}")
            _reject_raw_secrets(child)
    elif isinstance(value,(list,tuple)):
        for child in value:
            _reject_raw_secrets(child)

class ConsoleStore:
    """Zero-cost persistent Console audit/history store.

    Stores metadata/evidence references only. Raw credentials are forbidden.
    """

    def __init__(self,path:str|Path):
        self.path=str(path)
        Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        self._init_schema()

    def _connect(self):
        conn=sqlite3.connect(self.path,timeout=30,isolation_level=None)
        conn.row_factory=sqlite3.Row
        return conn

    def _init_schema(self)->None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS console_audit(
              request_id TEXT PRIMARY KEY,
              company_id TEXT NOT NULL,
              user_id TEXT NOT NULL,
              engine_id TEXT NOT NULL,
              action TEXT NOT NULL,
              result TEXT NOT NULL,
              evidence_ref TEXT NOT NULL DEFAULT '',
              environment TEXT NOT NULL,
              version TEXT NOT NULL,
              timestamp_epoch INTEGER NOT NULL,
              metadata_json TEXT NOT NULL
            )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_console_audit_company ON console_audit(company_id,timestamp_epoch,request_id)")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS console_history(
              request_id TEXT PRIMARY KEY,
              company_id TEXT NOT NULL,
              engine_id TEXT NOT NULL,
              status TEXT NOT NULL,
              evidence_ref TEXT NOT NULL DEFAULT '',
              environment TEXT NOT NULL,
              version TEXT NOT NULL,
              timestamp_epoch INTEGER NOT NULL
            )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_console_history_company ON console_history(company_id,timestamp_epoch,request_id)")

    def record(self,audit:dict,*,now_epoch:int)->None:
        if now_epoch<0 or not isinstance(audit,dict):
            raise ValueError("valid audit and timestamp required")
        _reject_raw_secrets(audit)
        required=("request_id","company_id","user_id","environment","version")
        if any(not str(audit.get(k,"")).strip() for k in required):
            raise ValueError("audit scope fields required")
        environment=str(audit["environment"]).upper()
        if environment not in {"LAB","PREPROD","PROD"}:
            raise ValueError("invalid audit environment")
        engine_id=str(audit.get("engine_id") or "GATEWAY")
        result=str(audit.get("result") or audit.get("engine_status") or audit.get("gateway_status") or "UNKNOWN").upper()
        action=str(audit.get("action") or "COMMAND")
        evidence_ref=str(audit.get("evidence_ref") or "")
        metadata=json.dumps(audit,sort_keys=True,separators=(",",":"))
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                  """INSERT INTO console_audit(request_id,company_id,user_id,engine_id,action,result,evidence_ref,environment,version,timestamp_epoch,metadata_json)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?)
                     ON CONFLICT(request_id) DO UPDATE SET
                       company_id=excluded.company_id,user_id=excluded.user_id,engine_id=excluded.engine_id,
                       action=excluded.action,result=excluded.result,evidence_ref=excluded.evidence_ref,
                       environment=excluded.environment,version=excluded.version,
                       timestamp_epoch=excluded.timestamp_epoch,metadata_json=excluded.metadata_json""",
                  (str(audit["request_id"]),str(audit["company_id"]),str(audit["user_id"]),engine_id,action,result,evidence_ref,environment,str(audit["version"]),now_epoch,metadata),
                )
                conn.execute(
                  """INSERT INTO console_history(request_id,company_id,engine_id,status,evidence_ref,environment,version,timestamp_epoch)
                     VALUES(?,?,?,?,?,?,?,?)
                     ON CONFLICT(request_id) DO UPDATE SET
                       company_id=excluded.company_id,engine_id=excluded.engine_id,status=excluded.status,
                       evidence_ref=excluded.evidence_ref,environment=excluded.environment,
                       version=excluded.version,timestamp_epoch=excluded.timestamp_epoch""",
                  (str(audit["request_id"]),str(audit["company_id"]),engine_id,result,evidence_ref,environment,str(audit["version"]),now_epoch),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def audit_by_company(self,company_id:str)->tuple[dict,...]:
        if not company_id.strip():
            raise ValueError("company_id required")
        with self._connect() as conn:
            rows=conn.execute(
              "SELECT request_id,company_id,engine_id,action,result,evidence_ref,timestamp_epoch FROM console_audit WHERE company_id=? ORDER BY timestamp_epoch,request_id",
              (company_id,),
            ).fetchall()
        return tuple({
          "request_id":str(r["request_id"]),"company_id":str(r["company_id"]),"engine_id":str(r["engine_id"]),
          "action":str(r["action"]),"result":str(r["result"]),"evidence_ref":str(r["evidence_ref"]),
          "timestamp":str(r["timestamp_epoch"]),
        } for r in rows)

    def history_by_company(self,company_id:str)->tuple[dict,...]:
        if not company_id.strip():
            raise ValueError("company_id required")
        with self._connect() as conn:
            rows=conn.execute(
              "SELECT request_id,company_id,engine_id,status,evidence_ref,environment,version FROM console_history WHERE company_id=? ORDER BY timestamp_epoch,request_id",
              (company_id,),
            ).fetchall()
        return tuple({
          "request_id":str(r["request_id"]),"company_id":str(r["company_id"]),"engine_id":str(r["engine_id"]),
          "status":str(r["status"]),"evidence_ref":str(r["evidence_ref"]),
          "environment":str(r["environment"]),"version":str(r["version"]),
        } for r in rows)

    def counts(self)->dict:
        with self._connect() as conn:
            audit=int(conn.execute("SELECT COUNT(*) FROM console_audit").fetchone()[0])
            history=int(conn.execute("SELECT COUNT(*) FROM console_history").fetchone()[0])
        return {"audit":audit,"history":history}
