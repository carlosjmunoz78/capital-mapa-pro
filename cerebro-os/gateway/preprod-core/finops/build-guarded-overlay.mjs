// Deterministic overlay: preserve certified 1.1.0 base and protocol version.
import {readFileSync,writeFileSync,mkdirSync,existsSync,readdirSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
const sha=b=>createHash('sha256').update(b).digest('hex');
const [base,dest,src]=process.argv.slice(2);
if(!base||!dest||!src||existsSync(dest))throw Error('FRESH_DESTINATION_REQUIRED');
const manifest=JSON.parse(readFileSync(join(base,'manifest.json'),'utf8'));
const baseHash=sha(JSON.stringify(manifest));
if(baseHash!=='9987c3fdd1383f75c75e8122ff1ea22c61af922df8ecd5a01631b07736c8463e'||Object.keys(manifest.files).length!==22)throw Error('BASE_MANIFEST_DENIED');
if(readdirSync(base).sort().join('|')!==[...Object.keys(manifest.files),'manifest.json'].sort().join('|'))throw Error('BASE_FILE_SET_DENIED');
const files={};for(const [n,d] of Object.entries(manifest.files)){if(!/^[\w.-]+\.mjs$/.test(n))throw Error('PATH_DENIED');const b=readFileSync(join(base,n));if(sha(b)!==d)throw Error('BASE_DRIFT_'+n);files[n]=b;}
for(const n of ['zero-cost-guard.mjs','guarded-dispatch.mjs','guarded-dispatch.test.mjs','ledger-entry.mjs']){if(n in files)throw Error('COLLISION');files[n]=readFileSync(join(src,n));}
let entry=files['core-dispatch-entry.mjs'].toString('utf8');
const replace=(a,b)=>{if(entry.split(a).length!==2)throw Error('ENTRY_DRIFT');entry=entry.replace(a,b);};
replace("import {dispatchCore,waitComplete","import {submitGuarded} from './guarded-dispatch.mjs';\nimport {waitComplete");
replace("00[1-8]","00[2-8]");
replace("await step.do('machine signed order submission',opts,()=>dispatchCore(this.env,id));","let admission=await step.do('finops guarded machine submission',opts,()=>submitGuarded(this.env,id));if(admission.status==='DEFER'){await step.sleepUntil('finops wait for UTC quota reset',admission.retry_after_epoch*1000);admission=await step.do('finops revalidate after quota reset',opts,()=>submitGuarded(this.env,id));}if(admission.status!=='SUBMITTED')return {...admission,request_id:id};");
files['core-dispatch-entry.mjs']=Buffer.from(entry);
const out={...manifest,base_manifest_sha256:baseHash,artifact_revision:'1.1.0-finops-separated-ledger-candidate',promotion_allowed:false,files:Object.fromEntries(Object.keys(files).sort().map(n=>[n,sha(files[n])]))};
mkdirSync(dest);for(const [n,b] of Object.entries(files))writeFileSync(join(dest,n),b,{flag:'wx'});writeFileSync(join(dest,'manifest.json'),JSON.stringify(out,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:'FINOPS_OVERLAY_BUILT',files:Object.keys(files).length,manifest_sha256:sha(JSON.stringify(out)),base_manifest_sha256:baseHash}));
