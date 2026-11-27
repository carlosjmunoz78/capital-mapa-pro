import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {validateCanonicalCatalog,CATALOG_SHA256} from './canonical-catalog-data.mjs';
const bytes=await readFile(new URL('../../registry/canonical_177.json',import.meta.url));
test('real pinned catalog, exact ordered IDs and no certification claim',async()=>{
 const r=await validateCanonicalCatalog(bytes),original=JSON.parse(bytes.toString('utf8'));
 assert.equal(r.count,177);assert.deepEqual(r.engine_ids,original.engine_ids);
 assert.equal(r.source_sha256,CATALOG_SHA256);assert.equal(r.operational_instances_certified,false);
 assert.equal(Object.isFrozen(r.engine_ids),true);assert.equal(Object.isFrozen(r),true);
 assert.equal('deployment_authorized' in r,false);
});
test('reject modified source even if schema valid',async()=>{
 const copy=Buffer.from(bytes);copy[copy.length-1]=32;
 await assert.rejects(validateCanonicalCatalog(copy),/CATALOG_SOURCE_DRIFT/);
});
test('reject synthetic or replacement catalog',async()=>{
 await assert.rejects(validateCanonicalCatalog(new TextEncoder().encode(JSON.stringify({engine_count:177,engine_ids:Array(177).fill('FACT-001')}))),/CATALOG_SOURCE_DRIFT/);
});
test('reject missing or oversized bytes',async()=>{
 for(const input of [null,'{}',new Uint8Array(0),new Uint8Array(65537)])
  await assert.rejects(validateCanonicalCatalog(input),/CATALOG_BYTES_DENIED/);
});
