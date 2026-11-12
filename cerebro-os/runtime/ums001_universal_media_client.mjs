/**
 * CEREBRO OS / UMS-001 · Common Cloudflare runtime SDK, LAB.
 * A single FACT Gateway binding per runtime; new engines require no new Worker.
 * The gateway alone authenticates runtime token, prefix/tenant and signed engine registry.
 * This module never publishes and does not contain credentials.
 */
const ENGINE=/^[A-Z][A-Z0-9-]{2,63}$/;
const RUNTIME=/^[A-Z][A-Z0-9-]{2,63}$/;
const REQUEST=/^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$/;
const HASH=/^[0-9a-f]{64}$/;

function ensureRequestId(value) {
  if(typeof value!=='string'||!REQUEST.test(value)) throw Error('UMS001_INVALID_REQUEST_ID');
  return value;
}
export class CEREBROUniversalMediaClient {
  constructor({gateway,runtimeId,engineId,runtimeToken,companyId='fenix',environment='LAB'}={}) {
    if(!gateway||typeof gateway.universalImageFromRuntime!=='function'||
       !RUNTIME.test(runtimeId||'')||!ENGINE.test(engineId||'')||
       typeof runtimeToken!=='string'||runtimeToken.length<48||runtimeToken.length>256||
       companyId!=='fenix'||environment!=='LAB')
      throw Error('UMS001_RUNTIME_IAM_NOT_READY');
    this.gateway=gateway;
    this.runtimeId=runtimeId;
    this.engineId=engineId;
    this.runtimeToken=runtimeToken;
  }
  async #call(action,command){
    return this.gateway.universalImageFromRuntime(
      this.runtimeId,this.engineId,action,command,this.runtimeToken
    );
  }
  async capability(){
    const result=await this.#call('CAPABILITY',null);
    if(result?.engine_id!==this.engineId||result?.provider!=='UMS-001'||
       result?.environment!=='LAB'||result?.publish_authorized!==false||
       !['READY_AUTHENTICATED','PENDING_FACTORY_IAM'].includes(result?.status))
      throw Error('UMS001_INVALID_CAPABILITY_RECEIPT');
    return result;
  }
  async request({request_id,prompt}={}){
    ensureRequestId(request_id);
    if(typeof prompt!=='string'||prompt.length<40||prompt.length>630||
       prompt!==prompt.trim()||/api[._ -]?key|access[._ -]?token|password\s*:/i.test(prompt))
      throw Error('UMS001_INVALID_PROMPT');
    const result=await this.#call('REQUEST',{request_id,prompt});
    if(result?.state!=='ACCEPTED'||result?.engine_id!==this.engineId||
       result?.request_id!==request_id||result?.environment!=='LAB'||
       result?.publish_authorized!==false)
      throw Error('UMS001_IMAGE_NOT_ACCEPTED');
    return result;
  }
  async status(request_id){
    ensureRequestId(request_id);
    const result=await this.#call('STATUS',{request_id});
    if(result?.engine_id!==this.engineId||result?.request_id!==request_id||
       !['PRIVATE_ASSET_RECEIVED','QUEUED_OR_PROCESSING'].includes(result?.state))
      throw Error('UMS001_INVALID_IMAGE_STATUS');
    if(result?.state==='PRIVATE_ASSET_RECEIVED'&&(!HASH.test(result.sha256||'')||
       result.publish_authorized!==false))throw Error('UMS001_INVALID_IMAGE_RECEIPT');
    return result;
  }
  async privateJPEG(request_id){
    ensureRequestId(request_id);
    const result=await this.#call('DOWNLOAD',{request_id});
    if(result?.state==='QUEUED_OR_PROCESSING')return {state:result.state};
    if(result?.state!=='PRIVATE_ASSET_RECEIVED'||result?.mime!=='image/jpeg'||
       result?.engine_id!==this.engineId||result?.request_id!==request_id||
       result?.publish_authorized!==false||!HASH.test(result?.sha256||''))throw Error('UMS001_INVALID_PRIVATE_MEDIA');
    const bytes=result.bytes instanceof Uint8Array?result.bytes:
      result.bytes instanceof ArrayBuffer?new Uint8Array(result.bytes):null;
    if(!bytes||bytes.byteLength<4000||bytes.byteLength>4500000||
       bytes[0]!==255||bytes[1]!==216||bytes[bytes.length-2]!==255||bytes[bytes.length-1]!==217)
      throw Error('UMS001_INVALID_JPEG');
    const observed=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))]
      .map(x=>x.toString(16).padStart(2,'0')).join('');
    if(observed!==result.sha256)throw Error('UMS001_SHA_MISMATCH');
    return {state:'PRIVATE_ASSET_RECEIVED',mime:'image/jpeg',bytes,
      sha256:observed,request_id,engine_id:this.engineId,publish_authorized:false};
  }
}
/** All engines in one authenticated runtime share this factory and binding, not each other's tokens. */
export function createUniversalMediaClient(env,{runtimeId,engineId,companyId='fenix',environment='LAB'}){
  return new CEREBROUniversalMediaClient({
    gateway:env?.CEREBRO_MEDIA_GATEWAY,runtimeToken:env?.CEREBRO_RUNTIME_TOKEN,
    runtimeId,engineId,companyId,environment
  });
}
