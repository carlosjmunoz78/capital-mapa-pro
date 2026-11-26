import { DurableObject } from "cloudflare:workers";

const QUEUE = "cerebro-facebook-w24-read-canary-lab-eu";
const AUDIT_FIELDS = ["request_id", "consumer_id", "company_id", "engine_id", "version", "source_id", "sha256", "result", "denial"];
const DENIALS = new Set(["IDENTITY_DENIED", "COMPANY_DENIED", "VERSION_DENIED", "INTEGRITY_DENIED", "CAPABILITY_DISABLED", "AUDIT_TEST_CONFLICT"]);
const LABEL = /^[A-Za-z0-9][A-Za-z0-9._:/-]{0,95}$/;
const HASH = /^[a-f0-9]{64}$/;

function validate(event) {
  if (!event || Object.keys(event).length !== AUDIT_FIELDS.length + 1 || event.environment !== "LAB") {
    throw new Error("AUDIT_SCHEMA_DENIED");
  }
  for (const key of AUDIT_FIELDS.slice(0, 6)) {
    if (typeof event[key] !== "string" || !LABEL.test(event[key])) throw new Error("AUDIT_SCHEMA_DENIED");
  }
  const success = ["ALLOWED", "STORAGE_TEST"].includes(event.result);
  if ((success && (event.denial !== null || typeof event.sha256 !== "string" || !HASH.test(event.sha256))) ||
      (!success && (event.result !== "DENIED" || event.sha256 !== null || !DENIALS.has(event.denial)))) {
    throw new Error("AUDIT_SCHEMA_DENIED");
  }
  return JSON.stringify(Object.fromEntries([...AUDIT_FIELDS, "environment"].map(key => [key, event[key]])));
}

export class KnowledgeAudit extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.boot = crypto.randomUUID();
    this.db = ctx.storage.sql;
    this.db.exec(`CREATE TABLE IF NOT EXISTS audit (
      request_id TEXT PRIMARY KEY, event_json TEXT NOT NULL,
      recorded_at TEXT NOT NULL) STRICT`);
  }

  append(event) {
    const json = validate(event);
    const rows = this.db.exec(
      "INSERT INTO audit VALUES (?, ?, ?) ON CONFLICT(request_id) DO NOTHING RETURNING recorded_at",
      event.request_id, json, new Date().toISOString()
    ).toArray();
    if (rows.length) return { status: "INSERTED", ...rows[0] };
    const row = this.db.exec(
      "SELECT event_json, recorded_at FROM audit WHERE request_id = ?", event.request_id
    ).one();
    if (row.event_json !== json) throw new Error("AUDIT_IDEMPOTENCY_CONFLICT");
    return { status: "EXISTING", recorded_at: row.recorded_at };
  }

  read(requestId) {
    if (typeof requestId !== "string" || !LABEL.test(requestId)) throw new Error("AUDIT_SCHEMA_DENIED");
    const records = this.db.exec(
      "SELECT event_json, recorded_at FROM audit WHERE request_id = ?", requestId
    ).toArray();
    return { boot: this.boot, records };
  }

  restartTestInstance() {
    this.ctx.abort("KNOWLEDGE_AUDIT_TEST_RESTART");
  }
}

const TEST_ID = "knowledge-audit-storage-v1-20261119";
async function storageTest(getStub, command) {
  const stub = getStub();
  if (command === "VERIFY") {
    const seen = await stub.read(TEST_ID);
    if (seen.records.length !== 1) throw new Error("AUDIT_STORAGE_MISSING");
    return { phase: command, boot: seen.boot, count: 1, request_id: TEST_ID,
      recorded_at: seen.records[0].recorded_at };
  }
  const event = {
    request_id: TEST_ID, consumer_id: "storage-test", company_id: "lab-test",
    engine_id: "knowledge-audit", version: "v1", source_id: "operational-test",
    sha256: Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",
      new TextEncoder().encode(TEST_ID))), b => b.toString(16).padStart(2, "0")).join(""),
    result: "STORAGE_TEST", denial: null, environment: "LAB"
  };
  const first = await stub.append(event);
  const retry = await stub.append(event);
  const before = await stub.read(TEST_ID);
  let conflict = false;
  try {
    await stub.append({ ...event, result: "DENIED", sha256: null, denial: "AUDIT_TEST_CONFLICT" });
  } catch (error) {
    conflict = error.message.includes("AUDIT_IDEMPOTENCY_CONFLICT");
  }
  let secretRejected = false;
  try {
    await stub.append({ ...event, authorization: "TEST_FIELD" });
  } catch (error) {
    secretRejected = error.message.includes("AUDIT_SCHEMA_DENIED");
  }
  try {
    await stub.restartTestInstance();
  } catch {
    // The runtime rejects this RPC as it resets the instance.
  }
  const after = await getStub().read(TEST_ID);
  if (retry.status !== "EXISTING" || first.recorded_at !== retry.recorded_at ||
      !conflict || !secretRejected || before.boot === after.boot ||
      after.records.length !== 1 || JSON.stringify(before.records) !== JSON.stringify(after.records)) {
    throw new Error("AUDIT_STORAGE_VERIFICATION_FAILED");
  }
  return { phase: "WRITE_RESTART_READ", request_id: TEST_ID, first: first.status, retry: retry.status,
    count: 1, before: before.boot, after: after.boot, recorded_at: first.recorded_at,
    conflict_denied: conflict, unexpected_field_denied: secretRejected };
}

export default {
  fetch() {
    return new Response(null, { status: 404 });
  },
  async queue(batch, env) {
    for (const message of batch.messages) {
      const command = message.body?.command;
      if (batch.queue !== QUEUE || message.body?.type !== "KNOWLEDGE_AUDIT_STORAGE_TEST" ||
          !["WRITE_RESTART_READ", "VERIFY"].includes(command)) {
        message.retry();
        continue;
      }
      const namespace = env.AUDIT.jurisdiction("eu");
      console.log(JSON.stringify(await storageTest(() => namespace.getByName("storage-verification-v1"), command)));
      message.ack();
    }
  }
};
