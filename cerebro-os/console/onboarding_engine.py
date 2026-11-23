from __future__ import annotations

from runtime.onboarding_queue import OnboardingQueue

class OnboardingQueueEngine:
    def __init__(self,queue:OnboardingQueue,now_epoch_provider,context_loader=None):
        if not isinstance(queue,OnboardingQueue):
            raise ValueError("OnboardingQueue required")
        if not callable(now_epoch_provider):
            raise ValueError("now_epoch_provider must be callable")
        if context_loader is not None and not callable(context_loader):
            raise ValueError("context_loader must be callable")
        self.queue=queue
        self.now_epoch_provider=now_epoch_provider
        self.context_loader=context_loader

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
            # A company: reference must resolve to the selected company; the
            # business context cannot silently point at a second tenant.
            if context_id.startswith("company:") and context_id != "company:" + company_id:
                raise ValueError("cross-company onboarding context reference denied")
            context["console_context_ref"]=context_id
        if self.context_loader is not None:
            loaded=self.context_loader(company_id,context_id,dict(command))
            if not isinstance(loaded,dict):
                raise ValueError("onboarding context_loader must return object")
            if str(loaded.get("company_id",company_id))!=company_id:
                raise ValueError("cross-company onboarding context denied")
            # The loader is not allowed to retarget a request to a different
            # company/context after the user-supplied ref has been validated.
            if "console_context_ref" in loaded:
                loader_ref=loaded["console_context_ref"]
                if not isinstance(loader_ref,str) or not loader_ref.strip():
                    raise ValueError("invalid loaded onboarding context reference")
                loader_ref=loader_ref.strip()
                if loader_ref.startswith("company:") and loader_ref!="company:"+company_id:
                    raise ValueError("cross-company loaded onboarding context denied")
                if context_id and loader_ref!=context_id:
                    raise ValueError("onboarding context loader reference mismatch")
                loaded["console_context_ref"]=loader_ref
            loaded={k:v for k,v in loaded.items() if k!="company_id"}
            context={**context,**loaded}
        payload={
          "company_id":company_id,
          "version":version,
          "environment":environment,
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
            if existing is None or existing.company_id!=company_id or existing.version!=version:
                raise ValueError("onboarding duplicate scope mismatch") from exc
            # Legacy LAB records predate the environment field, and can be
            # replayed only in LAB with the same identity and context.
            previous=dict(existing.payload)
            if "environment" not in previous and environment=="LAB":
                previous["environment"]="LAB"
            if previous!=payload:
                raise ValueError("onboarding duplicate command evidence conflict") from exc
            decision="ALREADY_QUEUED"

        return {
          "status":"WAITING","decision":decision,
          "company_id":company_id,"environment":environment,"version":version,"engine_id":"COMP-ONB-001",
          "request_id":request_id,"queued":True,
          "external_mutation_allowed":False,"production_activation_allowed":False,"cost_eur":0.0,
        }