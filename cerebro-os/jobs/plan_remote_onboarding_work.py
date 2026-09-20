from __future__ import annotations
from jobs.assess_remote_onboarding_gaps import assess_remote_onboarding_gaps

def plan_remote_work(result:dict)->dict:
    assessment=assess_remote_onboarding_gaps(result)
    classification=assessment["classification"]
    if classification=="REMOTE_SAFE":
        work={
          "execution_mode":"READ_ONLY_OR_LOCAL_DETERMINISTIC",
          "may_use_browser_bridge":False,
          "may_use_computer_use":False,
          "may_mutate_prod":False,
          "requires_local_pc":False,
        }
    elif classification=="REMOTE_PREPROD_SAFE":
        work={
          "execution_mode":"PREPROD_ONLY",
          "may_use_browser_bridge":False,
          "may_use_computer_use":False,
          "may_mutate_prod":False,
          "requires_local_pc":False,
        }
    else:
        work={
          "execution_mode":"NO_AUTONOMOUS_EXECUTION",
          "may_use_browser_bridge":False,
          "may_use_computer_use":False,
          "may_mutate_prod":False,
          "requires_local_pc":bool(assessment["local_pc_required"]),
        }
    return {
      "record_type":"remote_onboarding_work_plan",
      "company_id":assessment["company_id"],
      "engine_id":"ONB-RMT-001",
      "environment":assessment["environment"],
      "version":assessment["version"],
      "status":"GREEN" if assessment["remotely_actionable"] else assessment["status"],
      "assessment":assessment,
      "work":work,
      "next_action":assessment["next_action"],
      "external_mutation_allowed":False,
      "production_activation_allowed":False,
      "cost_eur":0.0,
    }
