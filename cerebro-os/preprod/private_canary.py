"""Private FORGE PREPROD canary. Existing dedicated queue; no provision or production."""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PROJECT = "cerebro-forge"
REGION = "europe-southwest1"
QREGION = "europe-west1"
SERVICE = "cerebro-advisory-preprod"
QUEUE = "forge-private-canary-20261124"
SA = "cerebro-forge-canary-invoker@cerebro-forge.iam.gserviceaccount.com"
DEPLOYER = "cerebro-forge-deployer@cerebro-forge.iam.gserviceaccount.com"
TAG = "forge-private-canary"
QPATH = f"projects/{PROJECT}/locations/{QREGION}/queues/{QUEUE}"
SPATH = f"projects/{PROJECT}/locations/{REGION}/services/{SERVICE}"
PERMS = {"cloudtasks.queues.get", "cloudtasks.queues.pause", "cloudtasks.queues.resume",
         "cloudtasks.tasks.create", "cloudtasks.tasks.list", "cloudtasks.tasks.delete"}

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def gcloud(*args):
    p = subprocess.run(["gcloud", *args, "--project="+PROJECT, "--quiet", "--format=json"],
                       capture_output=True, text=True, timeout=90)
    require(p.returncode == 0, "GCLOUD_FAILED:"+" ".join(args[:3]))
    return json.loads(p.stdout) if p.stdout.strip() else None

def rest(host, path, body):
    token = subprocess.check_output(["gcloud", "auth", "print-access-token", "--quiet"], text=True, timeout=20).strip()
    req = urllib.request.Request("https://"+host+path, data=json.dumps(body).encode(),
             headers={"Authorization": "Bearer "+token, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.load(res)

def service():
    return gcloud("run", "services", "describe", SERVICE, "--region="+REGION)

def queue():
    return gcloud("tasks", "queues", "describe", QUEUE, "--location="+QREGION)

def tasks():
    return gcloud("tasks", "list", "--queue="+QUEUE, "--location="+QREGION) or []

def validate_queue(q):
    require(q.get("name") == QPATH and q.get("state") == "PAUSED", "QUEUE_NOT_PAUSED")
    r=q.get("rateLimits",{}); retry=q.get("retryConfig",{})
    require(r.get("maxConcurrentDispatches")==1 and r.get("maxDispatchesPerSecond")==1
            and retry.get("maxAttempts")==1 and q.get("stackdriverLoggingConfig",{}).get("samplingRatio")==1,
            "QUEUE_BOUNDARY_DENIED")

def validate_service(s, old=None, candidate=None):
    require(s.get("metadata",{}).get("name")==SERVICE and
            s["metadata"].get("annotations",{}).get("run.googleapis.com/ingress")=="internal",
            "SERVICE_BOUNDARY_DENIED")
    status=s.get("status",{}); base=status.get("url","")
    require(bool(re.fullmatch(r"https://[a-z0-9.-]+\.run\.app",base)), "URL_DENIED")
    traffic=status.get("traffic",[])
    active=[t for t in traffic if t.get("percent",0)>0]
    require(len(active)==1 and active[0].get("percent")==100 and
            (old is None or active[0].get("revisionName")==old), "TRAFFIC_DRIFT")
    tags=[t for t in traffic if t.get("tag")]
    if candidate is None:
        require(not tags,"UNEXPECTED_TAGS")
        return base,None
    require(len(tags)==1 and tags[0].get("tag")==TAG and tags[0].get("revisionName")==candidate
            and tags[0].get("percent",0)==0, "TAG_DRIFT")
    target=tags[0].get("url","")
    require(target==base.replace("https://","https://"+TAG+"---",1),"TAG_URL_DENIED")
    return base,target

def preflight():
    a=gcloud("auth","list","--filter=status:ACTIVE")
    require(len(a)==1 and a[0].get("account")==DEPLOYER, "DEPLOYER_IDENTITY_DENIED")
    validate_service(service()); validate_queue(queue()); require(not tasks(),"QUEUE_NOT_EMPTY")
    q=rest("cloudtasks.googleapis.com","/v2/"+QPATH+":testIamPermissions",{"permissions":sorted(PERMS)})
    require(PERMS.issubset(q.get("permissions",[])),"QUEUE_PERMISSIONS_DENIED")
    a=rest("iam.googleapis.com","/v1/projects/"+PROJECT+"/serviceAccounts/"+SA+":testIamPermissions",
           {"permissions":["iam.serviceAccounts.actAs"]})
    require("iam.serviceAccounts.actAs" in a.get("permissions",[]),"INVOKER_ACTAS_DENIED")
    print("FORGE_PRIVATE_CANARY_PREFLIGHT_PASS")

def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

def logs(filter_):
    return gcloud("logging","read",filter_,"--limit=100") or []

def accepted(task_name, candidate, started, target):
    q=logs(f'resource.type="cloud_tasks_queue" AND resource.labels.queue_id="{QUEUE}" AND timestamp>="{started}" AND jsonPayload.task="{task_name}"')
    responses=[x["jsonPayload"]["attemptResponseLog"] for x in q if x.get("jsonPayload",{}).get("attemptResponseLog")]
    if not responses:
        return False
    require(len(responses)==1,"TASK_RESPONSE_AMBIGUOUS")
    response=responses[0]
    require(response.get("status")=="OK" and str(response.get("dispatchCount"))=="1"
            and response.get("targetAddress")=="GET "+target+"/ready","TASK_RESPONSE_DENIED")
    r=logs(f'resource.type="cloud_run_revision" AND resource.labels.revision_name="{candidate}" AND timestamp>="{started}" AND httpRequest.requestMethod="GET"')
    matches=[x for x in r if x.get("httpRequest",{}).get("requestUrl")==target+"/ready"]
    if not matches:
        return False
    require(len(matches)==1 and matches[0]["httpRequest"].get("status")==200,"CANDIDATE_RESPONSE_DENIED")
    return True

def invoke(serving=False):
    preflight()
    old=os.environ["FORGE_OLD_REVISION"]; candidate=os.environ["FORGE_EXPECTED_REVISION"]
    tid=os.environ["FORGE_CANARY_ID"]
    require((old==candidate==SERVICE+"-00266-xnc" if serving else old!=candidate)
            and all(re.fullmatch(SERVICE+r"-[a-z0-9-]+",s) for s in (old,candidate))
            and bool(re.fullmatch(r"forge-[0-9]+-[0-9]+",tid)),"CANARY_SCOPE_DENIED")
    validate_service(service(),old)
    name=QPATH+"/tasks/"+tid; started=utcnow()
    Path("forge-evidence").mkdir(exist_ok=True)
    journal=Path("forge-evidence/private-canary.json")
    require(not journal.exists(),"CANARY_ALREADY_RESERVED")
    rec={"state":"RESERVED","task":name,"candidate":candidate,"old":old,"started":started}
    journal.write_text(json.dumps(rec,indent=2))
    submission_attempted=False
    try:
        if serving:
            base,_=validate_service(service(),old)
            target=base
        else:
            gcloud("run","services","update-traffic",SERVICE,"--region="+REGION,"--update-tags="+TAG+"="+candidate)
            base,target=validate_service(service(),old,candidate)
        validate_queue(queue()); require(not tasks(),"QUEUE_NOT_EMPTY")
        # Exact named create; no retry after ambiguous response.
        submission_attempted=True
        out=gcloud("tasks","create-http-task",tid,"--queue="+QUEUE,"--location="+QREGION,
                   "--url="+target+"/ready","--method=GET","--oidc-service-account-email="+SA,
                   "--oidc-token-audience="+base)
        require(out.get("name")==name,"TASK_ID_DENIED")
        pending=tasks()
        require(len(pending)==1 and pending[0].get("name")==name,"TASK_QUEUE_DRIFT")
        gcloud("tasks","queues","resume",QUEUE,"--location="+QREGION)
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            if accepted(name,candidate,started,target):
                rec["state"]="PRIVATE_CANARY_PASS"; break
            time.sleep(5)
        require(rec["state"]=="PRIVATE_CANARY_PASS","TASK_EVIDENCE_TIMEOUT")
    finally:
        # Cleanup is deliberately fail closed. No new task, no grant widening, no traffic promotion here.
        if submission_attempted:
            gcloud("tasks","queues","pause",QUEUE,"--location="+QREGION)
            validate_queue(queue())
            pending=tasks()
            require(all(t.get("name")==name for t in pending),"FOREIGN_TASK_HOLD")
            if pending:
                gcloud("tasks","delete",tid,"--queue="+QUEUE,"--location="+QREGION)
            require(not tasks(),"TASK_CLEANUP_FAILED")
        current=service()
        if not serving and any(t.get("tag")==TAG and t.get("revisionName")==candidate for t in current.get("status",{}).get("traffic",[])):
            validate_service(current,old,candidate)
            gcloud("run","services","update-traffic",SERVICE,"--region="+REGION,"--remove-tags="+TAG)
        validate_service(service(),old)
        validate_queue(queue())
        rec["cleanup_verified"]=True
        journal.write_text(json.dumps(rec,indent=2))
    require(rec["state"]=="PRIVATE_CANARY_PASS","CANARY_HOLD")
    with open(os.environ["GITHUB_ENV"],"a") as f:
        f.write("FORGE_CANARY_STARTED="+started+"\n")
    print("FORGE_PRIVATE_CANARY_PASS")

if __name__=="__main__":
    require(len(sys.argv)==2 and sys.argv[1] in {"preflight","invoke","invoke-serving"},"COMMAND_DENIED")
    {"preflight":preflight,"invoke":invoke,"invoke-serving":lambda:invoke(serving=True)}[sys.argv[1]]()
