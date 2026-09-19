from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

FORBIDDEN_SECRET_KEYS={"password","token","api_key","secret","secret_value","raw_secret","credential_value"}
CLAIMABLE_STATUSES={"QUEUED","IN_PROGRESS"}
TERMINAL_OR_WAITING={"WAITING","BLOCKED","HUMAN_REQUIRED","COMPLETED"}

def _reject_raw_secrets(value)->None:
    if isinstance(value,dict):
        for key,child in value.items():
            if str(key).lower() in FORBIDDEN_SECRET_KEYS:
                raise ValueError(f"raw secret field forbidden: {key}")
            _reject_raw_secrets(child)
    elif isinstance(value,list):
        for child in value:
            _reject_raw_secrets(child)

@dataclass(frozen=True)
class QueueItem:
    request_id:str
    company_id:str
    version:str
    payload:dict
    status:str
    attempts:int
    lease_until_epoch:int
    last_result:dict|None

class OnboardingQueue:
    def __init__(self,path:str|Path):
        self.path=str(path)
        self._init_schema()

    def _connect(self):
        conn=sqlite3.connect(self.path,timeout=30,isolation_level=None)
        conn.row_factory=sqlite3.Row
        return conn

    def _init_schema(self)->None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS onboarding_requests(
              request_id TEXT PRIMARY KEY,
              company_id TEXT NOT NULL,
              version TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              status TEXT NOT NULL,
              created_at_epoch INTEGER NOT NULL,
              updated_at_epoch INTEGER NOT NULL,
              lease_until_epoch INTEGER NOT NULL DEFAULT 0,
              attempts INTEGER NOT NULL DEFAULT 0,
              last_result_json TEXT
            )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_onboarding_claim ON onboarding_requests(status,lease_until_epoch,created_at_epoch,request_id)")

    def enqueue(self,*,request_id:str,company_id:str,version:str,payload:dict,now_epoch:int)->None:
        if not all(str(x).strip() for x in (request_id,company_id,version)):
            raise ValueError("request_id/company_id/version required")
        if now_epoch<0 or not isinstance(payload,dict):
            raise ValueError("valid payload and timestamp required")
        _reject_raw_secrets(payload)
        payload_company=str(payload.get("company_id",company_id)).strip()
        if payload_company!=company_id:
            raise ValueError("cross-company queue payload denied")
        body={**payload,"company_id":company_id,"version":version}
        encoded=json.dumps(body,sort_keys=True,separators=(",",":"))
        with self._connect() as conn:
            try:
                conn.execute(
                  "INSERT INTO onboarding_requests(request_id,company_id,version,payload_json,status,created_at_epoch,updated_at_epoch,lease_until_epoch,attempts) VALUES(?,?,?,?,?,?,?,?,0)",
                  (request_id,company_id,version,encoded,"QUEUED",now_epoch,now_epoch,0),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("duplicate request_id") from exc

    def claim(self,*,now_epoch:int,lease_seconds:int=300)->QueueItem|None:
        if now_epoch<0 or lease_seconds<1:
            raise ValueError("invalid claim timing")
        conn=self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row=conn.execute(
              """
              SELECT * FROM onboarding_requests
              WHERE status='QUEUED' OR (status='IN_PROGRESS' AND lease_until_epoch<=?)
              ORDER BY created_at_epoch,request_id
              LIMIT 1
              """,
              (now_epoch,),
            ).fetchone()
            if row is None:
                conn.execute("COMMIT")
                return None
            lease_until=now_epoch+lease_seconds
            conn.execute(
              "UPDATE onboarding_requests SET status='IN_PROGRESS',lease_until_epoch=?,attempts=attempts+1,updated_at_epoch=? WHERE request_id=?",
              (lease_until,now_epoch,row["request_id"]),
            )
            conn.execute("COMMIT")
            return self.get(str(row["request_id"]))
        except Exception:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            raise
        finally:
            conn.close()

    def complete(self,*,request_id:str,status:str,result:dict,now_epoch:int)->None:
        status=str(status).upper()
        if status not in TERMINAL_OR_WAITING:
            raise ValueError("unsupported completion status")
        if now_epoch<0 or not isinstance(result,dict):
            raise ValueError("valid result and timestamp required")
        _reject_raw_secrets(result)
        row=self.get(request_id)
        if row is None:
            raise KeyError(request_id)
        if str(result.get("company_id",row.company_id))!=row.company_id:
            raise ValueError("cross-company queue result denied")
        encoded=json.dumps(result,sort_keys=True,separators=(",",":"))
        with self._connect() as conn:
            conn.execute(
              "UPDATE onboarding_requests SET status=?,last_result_json=?,updated_at_epoch=?,lease_until_epoch=0 WHERE request_id=?",
              (status,encoded,now_epoch,request_id),
            )

    def requeue(self,*,request_id:str,payload:dict,now_epoch:int)->None:
        if now_epoch<0 or not isinstance(payload,dict):
            raise ValueError("valid payload and timestamp required")
        row=self.get(request_id)
        if row is None:
            raise KeyError(request_id)
        if row.status not in {"WAITING","BLOCKED"}:
            raise ValueError("only WAITING/BLOCKED requests may be requeued")
        _reject_raw_secrets(payload)
        if str(payload.get("company_id",row.company_id))!=row.company_id:
            raise ValueError("cross-company requeue denied")
        body={**payload,"company_id":row.company_id,"version":row.version}
        encoded=json.dumps(body,sort_keys=True,separators=(",",":"))
        with self._connect() as conn:
            conn.execute(
              "UPDATE onboarding_requests SET payload_json=?,status='QUEUED',updated_at_epoch=?,lease_until_epoch=0 WHERE request_id=?",
              (encoded,now_epoch,request_id),
            )

    def stats(self,*,now_epoch:int)->dict:
        if now_epoch<0:
            raise ValueError("invalid stats timestamp")
        with self._connect() as conn:
            rows=conn.execute(
              "SELECT status,COUNT(*) AS n FROM onboarding_requests GROUP BY status"
            ).fetchall()
            stale=conn.execute(
              "SELECT COUNT(*) AS n FROM onboarding_requests WHERE status='IN_PROGRESS' AND lease_until_epoch<=?",
              (now_epoch,),
            ).fetchone()
        counts={str(row["status"]):int(row["n"]) for row in rows}
        return {
          "total":sum(counts.values()),
          "queued":counts.get("QUEUED",0),
          "in_progress":counts.get("IN_PROGRESS",0),
          "waiting":counts.get("WAITING",0),
          "blocked":counts.get("BLOCKED",0),
          "human_required":counts.get("HUMAN_REQUIRED",0),
          "completed":counts.get("COMPLETED",0),
          "stale_leases":int(stale["n"]) if stale else 0,
        }

    def get(self,request_id:str)->QueueItem|None:
        with self._connect() as conn:
            row=conn.execute("SELECT * FROM onboarding_requests WHERE request_id=?",(request_id,)).fetchone()
        if row is None:
            return None
        return QueueItem(
          request_id=str(row["request_id"]),company_id=str(row["company_id"]),version=str(row["version"]),
          payload=json.loads(row["payload_json"]),status=str(row["status"]),attempts=int(row["attempts"]),
          lease_until_epoch=int(row["lease_until_epoch"]),
          last_result=json.loads(row["last_result_json"]) if row["last_result_json"] else None,
        )
