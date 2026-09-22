// Deterministic LAB-only regression. Never opens the real browser or network.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const worker = fs.readFileSync(path.join(__dirname,"../identity/chrome_extension_v1_6_2/service_worker.js"),"utf8");
function command(id) { return {decision:"LAB_COMMAND_AVAILABLE",environment:"LAB",company_id:"fenix",external_mutation_allowed:false,action:"OPEN_LOCAL_TEST_PAGE",command_id:id,target_url:"http://127.0.0.1:8765/lab/test?command_id="+id}; }
async function harness() {
  let current=command("A"), failedReceipt=false, alarm=null, n=0;
  const saved={}, opened=[], receipts=[], warnings=[];
  const chrome={
    runtime:{id:"a".repeat(32),onInstalled:{addListener(){}},onStartup:{addListener(){}}},
    alarms:{onAlarm:{addListener(fn){alarm=fn}},create(){}},
    storage:{local:{
      async get(k){return {[k]:structuredClone(saved[k])}},
      async set(obj){Object.assign(saved,structuredClone(obj))}
    }},
    tabs:{
      async query(){return opened.slice()},
      async create({url}){const item={url,id:++n,status:"complete"};opened.push(item);return item}
    }
  };
  async function fetcher(input){
    const u=new URL(input);let body={},status=200;
    if(u.pathname==="/extension/ping") body={status:"GREEN",service_version:"1.4.1"};
    else if(u.pathname==="/extension/command") body=current;
    else if(u.pathname==="/extension/result") {
      const id=u.searchParams.get("command_id");receipts.push({id,result:u.searchParams.get("result")});
      if(failedReceipt){status=500;body={status:"BLOCKED",decision:"ACK_FAILED"}}
      else body={status:"GREEN",decision:"ACK_ACCEPTED"};
    }else throw Error("unexpected endpoint "+u.pathname);
    return {ok:status===200,async json(){return body}};
  }
  vm.runInNewContext(worker,{chrome,fetch:fetcher,URL,Date,encodeURIComponent,
    console:{warn(...x){warnings.push(x)}},setTimeout});
  // Initial heartbeat starts automatically in the worker.
  await new Promise(resolve=>setTimeout(resolve,50));
  return {saved,opened,receipts,warnings,setCommand(c){current=c},failAck(x){failedReceipt=x},
    async cycle(){await alarm({name:"cerebro-heartbeat"})},clearTabs(){opened.splice(0)}};
}
test("A->B->A replay never reopens closed A even after B was persisted",async()=>{
  const h=await harness();
  assert.equal(h.opened.length,1);
  h.setCommand(command("B")); await h.cycle();
  assert.equal(h.opened.length,2);
  h.clearTabs();
  h.setCommand(command("A")); await h.cycle();
  assert.equal(h.opened.length,0,"replayed A created a duplicate after B replaced it");
  const ledger=h.saved.cerebro_local_test_receipt_ledger_v162;
  assert.equal(ledger["fenix:LAB:A"].phase,"TERMINAL");
  assert.equal(ledger["fenix:LAB:B"].phase,"TERMINAL");
  assert.deepEqual(h.receipts.map(x=>x.id),["A","B","A"]);
});
test("failed ACK retries receipt only, including after an intermediate command",async()=>{
  const h=await harness();
  h.failAck(true);h.setCommand(command("A"));await h.cycle();
  h.setCommand(command("B"));await h.cycle();
  h.clearTabs();h.failAck(false);h.setCommand(command("A"));await h.cycle();
  assert.equal(h.opened.length,0);
  assert.equal(h.receipts.at(-1).result,"COMPLETED");
});
test("CLAIMED ambiguous command fails closed rather than repeating effect",async()=>{
  const h=await harness();const ledger=h.saved.cerebro_local_test_receipt_ledger_v162;
  ledger["fenix:LAB:A"]={phase:"CLAIMED",success:false,created_at:Date.now()};
  h.clearTabs();h.setCommand(command("A"));await h.cycle();
  assert.equal(h.opened.length,0);
  assert.ok(h.warnings.some(w=>w[0]==="CEREBRO_LOCAL_COMMAND_AMBIGUOUS_NO_REPLAY"));
});
