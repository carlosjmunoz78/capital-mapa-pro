import {resolve} from 'node:path';
import {execute} from './weekly.mjs';
const dir=resolve(process.argv[2]||'../editor/out');
const mode=process.env.NEWS001_MODE||'dry-run';
try{
  const result=await execute({dir,mode,key:process.env.BREVO_API_KEY||'',releasePath:process.env.NEWS001_RELEASE_PROOF_PATH||'',releaseSha256:process.env.NEWS001_RELEASE_PROOF_SHA256||'',log:(e)=>console.log(JSON.stringify(e))});
  console.log(JSON.stringify(result));
}catch(e){console.error(String(e.message||'HOLD_UNEXPECTED'));process.exitCode=1;}