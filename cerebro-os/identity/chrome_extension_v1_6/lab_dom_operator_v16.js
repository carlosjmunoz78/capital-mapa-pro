/* LAB-only DOM operator; no arbitrary URL or selector execution.
 * Designed for injection ONLY into the bridge-controlled localhost fixture.
 * No production, external pages, cookies, credentials, files or form submission.
 */
"use strict";

const LAB_SELECTORS = Object.freeze({
  name: "#cerebro-lab-name",
  role: "#cerebro-lab-role",
  toggle: "#cerebro-lab-toggle",
  output: "#cerebro-lab-output"
});
const LAB_VALUES = Object.freeze({ name: "CEREBRO LAB", role: "AUDITOR" });
const MAX_RECEIPT_LENGTH = 120;

function verifyLabFixture(url, expectedOrigin) {
  if (typeof url !== "string" || typeof expectedOrigin !== "string") return false;
  try {
    const parsed = new URL(url);
    const origin = new URL(expectedOrigin);
    return origin.hostname === "127.0.0.1"
      && /^\\d+$/.test(origin.port)
      && parsed.origin === origin.origin
      && parsed.pathname === "/lab/operator-fixture"
      && parsed.search === ""
      && parsed.hash === "";
  } catch (_) { return false; }
}

function executeLabFixture(documentRef, locationHref, expectedOrigin) {
  const deny = reason => Object.freeze({
    status: "BLOCKED", decision: reason, fixture_verified: false,
    click_verified: false, type_verified: false, select_verified: false,
    read_verified: false, external_mutation_performed: false,
    secret_value_included: false
  });
  if (!verifyLabFixture(locationHref, expectedOrigin)) return deny("FIXTURE_ORIGIN_MISMATCH");
  if (!documentRef || !documentRef.querySelector) return deny("NO_DOCUMENT");
  const name = documentRef.querySelector(LAB_SELECTORS.name);
  const role = documentRef.querySelector(LAB_SELECTORS.role);
  const toggle = documentRef.querySelector(LAB_SELECTORS.toggle);
  const output = documentRef.querySelector(LAB_SELECTORS.output);
  if (!name || name.tagName !== "INPUT" || name.type !== "text"
      || !role || role.tagName !== "SELECT"
      || !toggle || toggle.tagName !== "BUTTON" || !output
      || output.tagName !== "OUTPUT"
      || documentRef.title !== "CEREBRO OPERATOR LAB") {
    return deny("FIXTURE_DOM_MISMATCH");
  }
  if (![...role.options].some(x => x.value === LAB_VALUES.role)) return deny("FIXTURE_OPTIONS_MISMATCH");
  // One deterministic, bounded, reversible local fixture operation.
  name.value = LAB_VALUES.name;
  name.dispatchEvent(new Event("input", {bubbles: true}));
  role.value = LAB_VALUES.role;
  role.dispatchEvent(new Event("change", {bubbles: true}));
  toggle.click();
  const clickVerified = toggle.getAttribute("aria-pressed") === "true";
  const typeVerified = name.value === LAB_VALUES.name;
  const selectVerified = role.value === LAB_VALUES.role;
  const readVerified = output.textContent.trim().slice(0, MAX_RECEIPT_LENGTH)
    === "CEREBRO LAB / AUDITOR / ON";
  const verified = clickVerified && typeVerified && selectVerified && readVerified;
  return Object.freeze({
    status: verified ? "COMPLETED" : "FAILED",
    decision: verified ? "LAB_DOM_OPERATIONS_VERIFIED" : "LAB_DOM_READBACK_FAILED",
    fixture_verified: true,
    click_verified: clickVerified, type_verified: typeVerified,
    select_verified: selectVerified, read_verified: readVerified,
    output: readVerified ? "CEREBRO LAB / AUDITOR / ON" : "",
    external_mutation_performed: false, secret_value_included: false
  });
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { LAB_SELECTORS, LAB_VALUES, verifyLabFixture, executeLabFixture };
}
