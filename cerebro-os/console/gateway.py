from dataclasses import dataclass

@dataclass(frozen=True)
class GatewayRequest:
    user_id: str
    company_id: str
    context: str
    command: str
    request_id: str

    def validate(self):
        if not all([self.user_id,self.company_id,self.context,self.command,self.request_id]):
            raise ValueError("missing gateway field")
        return True

class GatewayRouter:
    def __init__(self, engine_map): self.engine_map=dict(engine_map)
    def route(self, request: GatewayRequest):
        request.validate()
        engine_id=self.engine_map.get(request.command)
        if not engine_id: return {"status":"HUMAN_REQUIRED","reason":"LOW_CONFIDENCE"}
        return {"status":"ROUTED","company_id":request.company_id,"engine_id":engine_id,"request_id":request.request_id}
