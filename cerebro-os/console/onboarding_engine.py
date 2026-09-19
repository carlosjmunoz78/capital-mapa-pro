from __future__ import annotations

from runtime.onboarding_queue import OnboardingQueue

class OnboardingQueueEngine:
    def __init__(self,queue:OnboardingQueue,now_epoch_provider):
        if not isinstance(queue,OnboardingQueue):
            raise ValueError("OnboardingQueue required")
        if not callable(now_epoch_provider):
            raise ValueError("now_epoch_provider must be callable")
        self.queue=queue
        self.now_epoch_provider=now_epoch_provider

    def execute(self,command:dict,routed:dict)->dict:
        company_id=str(command.get("company_id","")).strip()
        request_id=str(command.get("request_id","")).strip()
        environment=str(command.get("environment","LAB")).upper()
        version=str(command.get("version","1.0.0")).strip()
        if str(routed.get("engine_id",""))!="COMP-ONB-001":
            raise ValueError("COMP-ONB-001 route required")
        if not company_id or not request_id or not version:
            raise ValueError("company/request/version required")
        if environment=="PROD":
            return {
              "status":"HUMAN_REQUIRED","human_reason":"HIGH_RISK","reason":"PROD_ONBOARDING_SUBMISSION_DENIED",
              "company_id":company_id,"environment":environment,"version":version,"engine_id":"COMP-ONB-001",
              "queued":False,"production_activation_allowed":False,"external_mutation_allowed":False,"cost_eur":0.0,
            }
        if environment not in {"LAB","PREPROD"}:
            raise ValueError("invalid onboarding environment")

        context={}
        context_id=str(command.get("context_id") or "").strip()
        if context_id:
            context["console_context_ref"]=context_id
        payload={
          "company_id":company_id,
          "version":version,
          "context":context,
          "source":{
            "type":"CEREBRO_CONSOLE",
            "user_id":str(command.get("user_id","")),
            "request_id":request_id,
          },
        }
        try:
            self.queue.enqueue(
                request_id=request_id,company_id=company_id,version=version,
                payload=payload,now_epoch=int(self.now_epoch_provider()),
            )
            decision="QUEUED"
        except ValueError as exc:
            if "duplicate request_id" not in str(exc):
                raise
            existing=self.queue.get(request_id)
            if existing is None or existing.company_id!=company_id:
                raise
            decision="ALREADY_QUEUED"

        return {
          "status":"WAITING","decision":decision,
          "company_id":company_id,"environment":environment,"version":version,"engine_id":"COMP-ONB-001",
          "request_id":request_id,"queued":True,
          "external_mutation_allowed":False,"production_activation_allowed":False,"cost_eur":0.0,
        }
