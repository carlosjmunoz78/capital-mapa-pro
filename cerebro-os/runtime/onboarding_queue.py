from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

FORBIDDEN_SECRET_KEYS={"password","token","api_key","secret","secret_value","raw_secret","credential_value"}
CLAIMABLE_STATUSES={"QUEUED","IN_PROGRESS"}
TERMINAL_OR_WAITING={"WAITING","BLOCKED","HUMAN_REQUIRED","COMPLETED","DEAD_LETTER"}

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
    priority:int=100
    next_attempt_epoch:int=0
    dead_letter_reason:str|None=None

class OnboardingQueue:
    def __init__(self,path:str|Path):
        self.path=str(path)
        self._init_schema()

    def _connect(self):
        conn=sqlite3.connect(self.path,timeout=30,isolation_level=None)
        conn.row_factory=sqlite3.Row
        return conn

    @contextmanager
    def _managed_connection(self):
        """Close SQLite connections after commit or rollback.

        sqlite3.Connection.__exit__ does not itself close a handle. claim()
        retains its explicit BEGIN IMMEDIATE / COMMIT / close discipline.
        """
        conn=self._connect()
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    @staticmethod
    def _ensure_column(conn,name:str,ddl:str)->None:
        cols={str(row["name"]) for row in conn.execute("PRAGMA table_info(onboarding_requests)").fetchall()}
        if name not in cols:
            conn.execute(f"ALTER TABLE onboarding_requests ADD COLUMN {ddl}")

    def _init_schema(self)->None:
        Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self._managed_connection() as conn:
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
              last_result_json TEXT,
              priority INTEGER NOT NULL DEFAULT 100,
              next_attempt_epoch INTEGER NOT NULL DEFAULT 0,
              dead_letter_reason TEXT
            )
            """)
            self._ensure_column(conn,"priority","priority INTEGER NOT NULL DEFAULT 100")
            self._ensure_column(conn,"next_attempt_epoch","next_attempt_epoch INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(conn,"dead_letter_reason","dead_letter_reason TEXT")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_onboarding_claim ON onboarding_requests(status,next_attempt_epoch,lease_until_epoch,priority,created_at_epoch,request_id)")

    def enqueue(self,*,request_id:str,company_id:str,version:str,payload:dict,now_epoch:int,priority:int=100)->None:
        if not all(str(x).strip() for x in (request_id,company_id,version)):
            raise ValueError("request_id/company_id/version required")
        if now_epoch<0 or not isinstance(payload,dict):
            raise ValueError("valid payload and timestamp required")
        if not 0<=int(priority)<=1000:
            raise ValueError("priority must be between 0 and 1000")
        _reject_raw_secrets(payload)
        payload_company=str(payload.get("company_id",company_id)).strip()
        if payload_company!=company_id:
            raise ValueError("cross-company queue payload denied")
        body={**payload,"company_id":company_id,"version":version}
        encoded=json.dumps(body,sort_keys=True,separators=(",",":"))
        with self._managed_connection() as conn:
            try:
                conn.execute(
                  """INSERT INTO onboarding_requests(
                       request_id,company_id,version,payload_json,status,created_at_epoch,updated_at_epoch,
                       lease_until_epoch,attempts,last_result_json,priority,next_attempt_epoch,dead_letter_reason
                     ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (request_id,company_id,version,encoded,"QUEUED",now_epoch,now_epoch,0,0,None,int(priority),now_epoch,None),
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
              WHERE (status='QUEUED' AND next_attempt_epoch<=?)
                 OR (status='IN_PROGRESS' AND lease_until_epoch<=?)
              ORDER BY priority DESC,created_at_epoch,request_id
              LIMIT 1
              """,
              (now_epoch,now_epoch),
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

    def complete(self,*,request_id:str,status:str,result:dict,now_epoch:int,claim_attempts:int|None=None)->None:
        status=str(status).upper()
        if status not in TERMINAL_OR_WAITING:
            raise ValueError("unsupported completion status")
        if now_epoch<0 or not isinstance(result,dict):
            raise ValueError("valid result and timestamp required")
        # CP80: no legacy caller may finalize or retry another worker's claim.
        if type(claim_attempts) is not int or claim_attempts<1:
            raise PermissionError("onboarding claim_attempts required")
        _reject_raw_secrets(result)
        encoded=json.dumps(result,sort_keys=True,separators=(",",":"))
        dead_reason=str(result.get("reason") or "") if status=="DEAD_LETTER" else None
        with self._managed_connection() as conn:
            # CP77: authoritative state and attempt must be read inside the
            # same write transaction that records the final result.
            conn.execute("BEGIN IMMEDIATE")
            row=conn.execute(
                "SELECT company_id,status,attempts FROM onboarding_requests WHERE request_id=?",
                (request_id,),
            ).fetchone()
            if row is None:
                raise KeyError(request_id)
            if str(result.get("company_id",row["company_id"]))!=row["company_id"]:
                raise ValueError("cross-company queue result denied")
            if row["status"]!="IN_PROGRESS":
                raise PermissionError("onboarding completion requires active claim")
            if claim_attempts is not None and row["attempts"]!=claim_attempts:
                raise PermissionError("stale onboarding claim completion denied")
            n=conn.execute(
                """UPDATE onboarding_requests
                   SET status=?,last_result_json=?,updated_at_epoch=?,lease_until_epoch=0,
                       dead_letter_reason=?,next_attempt_epoch=?
                   WHERE request_id=? AND status='IN_PROGRESS' AND attempts=?""",
                (status,encoded,now_epoch,dead_reason,now_epoch,request_id,row["attempts"]),
            ).rowcount
            if n!=1:
                raise PermissionError("onboarding completion lost claim")

    def retry_or_dead_letter(
        self,*,request_id:str,result:dict,now_epoch:int,max_attempts:int=3,
        base_backoff_seconds:int=60,max_backoff_seconds:int=3600,
        claim_attempts:int|None=None,
    )->dict:
        if now_epoch<0 or max_attempts<1 or base_backoff_seconds<1 or max_backoff_seconds<base_backoff_seconds:
            raise ValueError("invalid retry policy")
        if not isinstance(result,dict):
            raise ValueError("result must be object")
        # CP80: no legacy caller may finalize or retry another worker's claim.
        if type(claim_attempts) is not int or claim_attempts<1:
            raise PermissionError("onboarding claim_attempts required")
        _reject_raw_secrets(result)
        encoded=json.dumps(result,sort_keys=True,separators=(",",":"))
        with self._managed_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row=conn.execute(
                "SELECT company_id,status,attempts FROM onboarding_requests WHERE request_id=?",
                (request_id,),
            ).fetchone()
            if row is None:
                raise KeyError(request_id)
            if str(result.get("company_id",row["company_id"]))!=row["company_id"]:
                raise ValueError("cross-company retry result denied")
            if row["status"]!="IN_PROGRESS":
                raise PermissionError("onboarding retry requires active claim")
            if claim_attempts is not None and row["attempts"]!=claim_attempts:
                raise PermissionError("stale onboarding retry denied")
            if row["attempts"]>=max_attempts:
                reason=str(result.get("reason") or "MAX_ATTEMPTS_EXCEEDED")
                n=conn.execute(
                    """UPDATE onboarding_requests
                       SET status='DEAD_LETTER',last_result_json=?,updated_at_epoch=?,lease_until_epoch=0,
                           next_attempt_epoch=?,dead_letter_reason=?
                       WHERE request_id=? AND status='IN_PROGRESS' AND attempts=?""",
                    (encoded,now_epoch,now_epoch,reason,request_id,row["attempts"]),
                ).rowcount
                if n!=1:
                    raise PermissionError("onboarding dead letter lost claim")
                return {"status":"DEAD_LETTER","request_id":request_id,"attempts":row["attempts"],"reason":reason}
            exponent=max(0,row["attempts"]-1)
            delay=min(max_backoff_seconds,base_backoff_seconds*(2**exponent))
            next_attempt=now_epoch+delay
            n=conn.execute(
                """UPDATE onboarding_requests
                   SET status='QUEUED',last_result_json=?,updated_at_epoch=?,lease_until_epoch=0,
                       next_attempt_epoch=?,dead_letter_reason=NULL
                   WHERE request_id=? AND status='IN_PROGRESS' AND attempts=?""",
                (encoded,now_epoch,next_attempt,request_id,row["attempts"]),
            ).rowcount
            if n!=1:
                raise PermissionError("onboarding retry lost claim")
            return {
              "status":"RETRY_SCHEDULED","request_id":request_id,"attempts":row["attempts"],
              "delay_seconds":delay,"next_attempt_epoch":next_attempt,
            }

    def requeue(self,*,request_id:str,payload:dict,now_epoch:int,priority:int|None=None)->None:
        if now_epoch<0 or not isinstance(payload,dict):
            raise ValueError("valid payload and timestamp required")
        _reject_raw_secrets(payload)
        with self._managed_connection() as conn:
            # CP78: lock, inspect and transition as ONE operation. A second
            # redrive must not overwrite a job another worker already queued.
            conn.execute("BEGIN IMMEDIATE")
            row=conn.execute(
                "SELECT company_id,version,payload_json,status,priority FROM onboarding_requests WHERE request_id=?",
                (request_id,),
            ).fetchone()
            if row is None:
                raise KeyError(request_id)
            if row["status"] not in {"WAITING","BLOCKED","DEAD_LETTER"}:
                raise ValueError("only WAITING/BLOCKED/DEAD_LETTER requests may be requeued")
            company_id=str(row["company_id"])
            version=str(row["version"])
            if str(payload.get("company_id",company_id))!=company_id:
                raise ValueError("cross-company requeue denied")
            if str(payload.get("version",version))!=version:
                raise ValueError("cross-version requeue denied")
            prior=json.loads(row["payload_json"])
            prior_environment=str(prior.get("environment","LAB")).upper()
            if "environment" in payload and str(payload["environment"]).upper()!=prior_environment:
                raise ValueError("cross-environment requeue denied")
            # CP79: redrive may update task metadata, but it may not
            # reinterpret the authenticated submitting identity or context.
            prior_source=prior.get("source")
            if prior_source is not None and not isinstance(prior_source,dict):
                raise ValueError("invalid original onboarding source")
            if "source" in payload and (
                prior_source is None or payload["source"]!=prior_source
            ):
                raise ValueError("onboarding requeue source immutable")
            previous_context=prior.get("context")
            if previous_context is not None and not isinstance(previous_context,dict):
                raise ValueError("invalid original onboarding context")
            if "context" in payload:
                incoming_context=payload["context"]
                if not isinstance(incoming_context,dict):
                    raise ValueError("onboarding context must be object")
            else:
                incoming_context={}
            context={**(previous_context or {}),**incoming_context}
            previous_ref=(previous_context or {}).get("console_context_ref")
            ref=context.get("console_context_ref")
            if ref is not None and (not isinstance(ref,str) or
                    not ref.strip() or
                    (ref.startswith("company:") and ref!="company:"+company_id)):
                raise ValueError("cross-company onboarding requeue context denied")
            if previous_ref is not None and ref!=previous_ref:
                raise ValueError("onboarding requeue context reference immutable")
            chosen_priority=int(row["priority"]) if priority is None else int(priority)
            if not 0<=chosen_priority<=1000:
                raise ValueError("priority must be between 0 and 1000")
            body={**payload,"company_id":company_id,"version":version,"environment":prior_environment}
            if previous_context is not None or "context" in payload:
                body["context"]=context
            if prior_source is not None:
                body["source"]=prior_source
            encoded=json.dumps(body,sort_keys=True,separators=(",",":"))
            n=conn.execute(
              """UPDATE onboarding_requests
                 SET payload_json=?,status='QUEUED',updated_at_epoch=?,lease_until_epoch=0,
                     next_attempt_epoch=?,dead_letter_reason=NULL,priority=?
                 WHERE request_id=? AND status=?""",
              (encoded,now_epoch,now_epoch,chosen_priority,request_id,row["status"]),
            ).rowcount
            if n!=1:
                raise PermissionError("onboarding requeue lost state")

    def stats(self,*,now_epoch:int)->dict:
        if now_epoch<0:
            raise ValueError("invalid stats timestamp")
        with self._managed_connection() as conn:
            rows=conn.execute("SELECT status,COUNT(*) AS n FROM onboarding_requests GROUP BY status").fetchall()
            stale=conn.execute(
              "SELECT COUNT(*) AS n FROM onboarding_requests WHERE status='IN_PROGRESS' AND lease_until_epoch<=?",
              (now_epoch,),
            ).fetchone()
            retry=conn.execute(
              "SELECT COUNT(*) AS n FROM onboarding_requests WHERE status='QUEUED' AND next_attempt_epoch>?",
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
          "dead_letter":counts.get("DEAD_LETTER",0),
          "retry_scheduled":int(retry["n"]) if retry else 0,
          "stale_leases":int(stale["n"]) if stale else 0,
        }

    def next_due_epoch(self,*,now_epoch:int)->int|None:
        if now_epoch<0:
            raise ValueError("invalid due timestamp")
        with self._managed_connection() as conn:
            queued=conn.execute(
              "SELECT MIN(next_attempt_epoch) AS due FROM onboarding_requests WHERE status='QUEUED'"
            ).fetchone()
            leased=conn.execute(
              "SELECT MIN(lease_until_epoch) AS due FROM onboarding_requests WHERE status='IN_PROGRESS'"
            ).fetchone()
        values=[]
        for row in (queued,leased):
            if row is not None and row["due"] is not None:
                values.append(int(row["due"]))
        if not values:
            return None
        due=min(values)
        return now_epoch if due<=now_epoch else due

    def by_company(self,company_id:str)->tuple[QueueItem,...]:
        if not company_id.strip():
            raise ValueError("company_id required")
        with self._managed_connection() as conn:
            rows=conn.execute(
              "SELECT request_id FROM onboarding_requests WHERE company_id=? ORDER BY updated_at_epoch DESC,created_at_epoch DESC,request_id",
              (company_id,),
            ).fetchall()
        items=[]
        for row in rows:
            item=self.get(str(row["request_id"]))
            if item is not None:
                items.append(item)
        return tuple(items)

    def get(self,request_id:str)->QueueItem|None:
        with self._managed_connection() as conn:
            row=conn.execute("SELECT * FROM onboarding_requests WHERE request_id=?",(request_id,)).fetchone()
        if row is None:
            return None
        return QueueItem(
          request_id=str(row["request_id"]),company_id=str(row["company_id"]),version=str(row["version"]),
          payload=json.loads(row["payload_json"]),status=str(row["status"]),attempts=int(row["attempts"]),
          lease_until_epoch=int(row["lease_until_epoch"]),
          last_result=json.loads(row["last_result_json"]) if row["last_result_json"] else None,
          priority=int(row["priority"]),next_attempt_epoch=int(row["next_attempt_epoch"]),
          dead_letter_reason=str(row["dead_letter_reason"]) if row["dead_letter_reason"] is not None else None,
        )