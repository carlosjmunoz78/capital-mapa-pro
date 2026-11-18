import test from "node:test";import assert from "node:assert/strict";import {HTML_B2B,HTML_B2C,META,CANONICAL_DIGESTS} from "../canonical.mjs";import {createHash} from "node:crypto";
test("two editorial HTML canonical integrity and links",()=>{
 for(const [kind,h] of [["b2b",HTML_B2B],["b2c",HTML_B2C]]){
  assert.equal(createHash("sha256").update(h).digest("hex"),CANONICAL_DIGESTS[kind]);
  assert.equal((h.match(/data-block=/g)||[]).length,10);
  assert.equal((h.match(/<a(?:\s|>)/g)||[]).length,13);
  assert.equal((h.match(/<img(?:\s|>)/g)||[]).length,2);
  assert.match(h,/\{\{ unsubscribe \}\}/);
  assert.equal(META[kind].listId,kind==="b2b"?18:17);
 }
});
