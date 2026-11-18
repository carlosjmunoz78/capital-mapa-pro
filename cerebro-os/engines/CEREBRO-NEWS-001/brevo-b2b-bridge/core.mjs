// NEWS001 B2B - read-only audit, safe to import in Node and Deno.
// No writes, no sending, no contact data in result.
const LISTS=[9,13,12,6];
export function clean(v){return String(v??"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase();}
export function salinas(c){
  const a=(c&&typeof c.attributes==="object"&&c.attributes)||{};
  for(const f of ["COMPANY","EMPRESA","AGENCIA","COMPANY_NAME","NOMBRE_EMPRESA","NOM","PRENOM","LASTNAME","FIRSTNAME","NAME","nombre_alias"]){
    if(typeof a[f]==="string"&&/\bsalinas\b/.test(clean(a[f])))return true;
  }
  return typeof c?.email==="string"&&/(^|[^a-z])salinas([^a-z]|$)/.test(clean(c.email));
}
export function classify(c){
  if(!c||typeof c!=="object")return "HOLD_INVALID_CONTACT";
  if(salinas(c))return "EXCLUDE_SALINAS";
  if(c.emailBlacklisted===true||c.smsBlacklisted===true)return "EXCLUDE_BLOCKED";
  if(c.emailBlacklisted!==false)return "HOLD_UNKNOWN_BLOCKING";
  if(!Number.isInteger(c.id)||c.id<1)return "HOLD_INVALID_ID";
  const a=(c.attributes&&typeof c.attributes==="object")?c.attributes:{};
  const agency=a.COMPANY||a.EMPRESA||a.AGENCIA||a.COMPANY_NAME||a.NOMBRE_EMPRESA;
  if(typeof agency!=="string"||agency.trim().length<3)return "HOLD_UNKNOWN_COMPANY";
  return "CANDIDATE_CONSENT_NOT_PROVEN";
}
export function allowed(path){
 return typeof path==="string"&&/^\/contacts\/lists\/(?:9|13|12|6)\/contacts\?limit=50&offset=\d+$/.test(path);
}
export async function audit(read,{maxPages=10}={}){
 const status=new Map();const sourceCounts=[];let duplicateMemberships=0;
 for(const id of LISTS){
  let count=0,ended=false;
  for(let p=0;p<maxPages;p++){
   const path="/contacts/lists/"+id+"/contacts?limit=50&offset="+p*50;
   if(!allowed(path))throw new Error("UNSAFE_PATH");
   const response=await read(path);
   if(!response||!Array.isArray(response.contacts)||response.contacts.length>50)throw new Error("BAD_API_RESPONSE");
   for(const c of response.contacts){
    if(!Number.isInteger(c.id)||c.id<1)throw new Error("BAD_CONTACT_ID");
    count++;
    const value=classify(c),prior=status.get(c.id);
    if(prior!==undefined)duplicateMemberships++;
    const rank={EXCLUDE_SALINAS:0,EXCLUDE_BLOCKED:1,HOLD_UNKNOWN_BLOCKING:2,HOLD_UNKNOWN_COMPANY:3,HOLD_INVALID_ID:4,CANDIDATE_CONSENT_NOT_PROVEN:5};
    if(prior===undefined||(rank[value]??4)<(rank[prior]??4))status.set(c.id,value);
   }
   if(response.contacts.length<50){ended=true;break;}
  }
  if(!ended)throw new Error("PAGINATION_LIMIT");
  sourceCounts.push({list_id:id,contact_memberships:count});
 }
 const reasons={};for(const s of status.values())reasons[s]=(reasons[s]||0)+1;
 return {state:"READ_ONLY_CANDIDATES_NOT_SENDABLE",company_id:"fenix",engine_id:"CEREBRO-NEWS-001",
  environment:"LAB",version:"0.3.0",source_counts:sourceCounts,unique_contact_ids:status.size,
  duplicate_memberships:duplicateMemberships,reasons,brevo_target_b2b_id:18,brevo_target_b2c_id:17,
  consent_verified:false,send_authorized:false,contact_write_authorized:false,
  includes_personal_data:false};
}
