// FACT-001 canonical catalog data validation for the existing JS runtime.
// Pure data operation: no entrypoint, authorization, grant, transport or storage.
// The existing authorized execution boundary must enforce scope, audit and release
// before any externally visible result. Never use this module as that boundary.
export const CATALOG_SHA256='1c566602c5ecc7df815c7653d77f8dad65b5e12eca8017d060b5764e7d488b03';
const hex=b=>Array.from(new Uint8Array(b),v=>v.toString(16).padStart(2,'0')).join('');
export async function validateCanonicalCatalog(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.byteLength<1||bytes.byteLength>65536)throw Error('CATALOG_BYTES_DENIED');
 const copy=new Uint8Array(bytes);
 if(hex(await crypto.subtle.digest('SHA-256',copy))!==CATALOG_SHA256)throw Error('CATALOG_SOURCE_DRIFT');
 const data=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(copy));
 const ids=data?.engine_ids;
 if(data?.schema_version!=='1.0.1'||data.engine_count!==177||!Array.isArray(ids)||ids.length!==177||new Set(ids).size!==177||!ids.every(x=>typeof x==='string'&&/^[A-Z0-9]+(?:-[A-Z0-9]+)+$/.test(x)))throw Error('CATALOG_SCHEMA_DENIED');
 return Object.freeze({source_schema:data.schema_version,source_sha256:CATALOG_SHA256,
  catalog_scope:'GLOBAL_LOGICAL_DEFINITIONS',engine_ids:Object.freeze([...ids]),count:177,
  operational_instances_certified:false});
}
