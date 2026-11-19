'use strict';
/**
 * CEREBRO LAB knowledge capability binding.
 *
 * Deliberately NOT a web server. The trusted Gateway runtime must supply all
 * authentication, route policy, authorized grants, Google tokens, and durable audit.
 * No new public surface, no keys, no PROD capability, no automatic deployment.
 */
const {createLabKnowledgeReader} = require('./gateway_sheets_lab.cjs');

const CAPABILITY = 'KNOWLEDGE.READ';
const CONNECTOR_ID = 'KNOWLEDGE-GOOGLE-SHEETS-LAB-001';
const SERVICE_ACCOUNT = 'cerebro-knowledge-reader-lab@cerebro-forge.iam.gserviceaccount.com';
const REQUIRED_SCOPE = 'https://www.googleapis.com/auth/spreadsheets.readonly';

function mandatory(name, value) {
  if (typeof value !== 'function') throw new TypeError('TRUSTED_RUNTIME_DEPENDENCY_MISSING:' + name);
  return value;
}

function createLabGatewayKnowledgeCapability({
  enabled = false,
  authenticateRuntime,
  readTrustedGrants,
  routeGateway,
  policyCheck,
  googleAccessToken,
  persistAudit,
  fetchImpl = fetch,
} = {}) {
  // No defaults to owner identity, API keys, user-supplied grants, or ALLOW.
  mandatory('authenticateRuntime', authenticateRuntime);
  mandatory('readTrustedGrants', readTrustedGrants);
  mandatory('routeGateway', routeGateway);
  mandatory('policyCheck', policyCheck);
  mandatory('googleAccessToken', googleAccessToken);
  mandatory('persistAudit', persistAudit);
  mandatory('fetchImpl', fetchImpl);
  if (enabled !== true) {
    return Object.freeze({
      capability: CAPABILITY,
      status: 'DISABLED_LAB',
      async read() { throw new Error('KNOWLEDGE_LAB_BINDING_DISABLED'); },
    });
  }

  const reader = createLabKnowledgeReader({
    authenticate: async trustedContext => {
      // This callback must authenticate on a trusted boundary, not deserialize a
      // consumer object from an HTTP request. The input is opaque to the reader.
      const principal = await authenticateRuntime(trustedContext);
      if (principal?.verified !== true || principal.environment !== 'LAB' ||
          typeof principal.id !== 'string' || !principal.id ||
          principal.service_account_email !== SERVICE_ACCOUNT) {
        throw new Error('GATEWAY_LAB_RUNTIME_IDENTITY_NOT_VERIFIED');
      }
      const grants = await readTrustedGrants(principal);
      if (!Array.isArray(grants)) throw new Error('GATEWAY_LAB_GRANTS_NOT_VERIFIED');
      // The grants come exclusively from the trusted registry, never the caller.
      return {id: principal.id, grants};
    },
    policyCheck: async (principal, requestedScope) => {
      const routed = await routeGateway({
        company_id: requestedScope.company_id,
        engine_id: requestedScope.engine_id,
        capability: CAPABILITY,
        environment: requestedScope.environment,
        version: requestedScope.version,
      });
      // The existing Gateway may ROUTE, but only its exact dedicated LAB
      // connector is accepted. A general fallback route must not be sufficient.
      if (routed?.status !== 'ROUTED' ||
          routed.company_id !== requestedScope.company_id ||
          routed.engine_id !== requestedScope.engine_id ||
          routed.environment !== 'LAB' ||
          routed.version !== requestedScope.version ||
          routed.connector_id !== CONNECTOR_ID) return false;
      return (await policyCheck(principal, requestedScope, routed)) === true;
    },
    googleAccessToken: () => googleAccessToken({
      service_account_email: SERVICE_ACCOUNT,
      requested_scope: REQUIRED_SCOPE,
      environment: 'LAB',
    }),
    audit: event => persistAudit(Object.freeze({
      ...event,
      environment: 'LAB',
      connector_id: CONNECTOR_ID,
      capability: CAPABILITY,
    })),
    fetchImpl,
  });

  return Object.freeze({
    capability: CAPABILITY,
    status: 'READY_FOR_TRUSTED_RUNTIME_BINDING_NOT_DEPLOYED',
    read: (trustedContext, request) => reader(trustedContext, request),
  });
}

/**
 * Keyless token provider for a Google-hosted runtime actually running AS
 * SERVICE_ACCOUNT. Metadata service availability is never inferred locally.
 * No operator impersonation, service-account key, environment variable secret,
 * or public Apps Script web app.
 *
 * Google-managed tokens can have platform scopes broader than Sheets readonly;
 * the effective Drive permission must remain Reader on the single private Sheet.
 */
function createGoogleManagedReaderTokenProvider({fetchImpl = fetch} = {}) {
  mandatory('fetchImpl', fetchImpl);
  const root = 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/';
  const headers = {'Metadata-Flavor': 'Google'};
  let identityVerified = false;
  async function get(path) {
    const res = await fetchImpl(root + path, {
      method: 'GET', headers, redirect: 'error', signal: AbortSignal.timeout(5000),
    });
    if (!res || res.ok !== true) throw new Error('GOOGLE_MANAGED_IDENTITY_UNAVAILABLE');
    return res;
  }
  return async function googleAccessToken({service_account_email, environment} = {}) {
    if (environment !== 'LAB' || service_account_email !== SERVICE_ACCOUNT) {
      throw new Error('GOOGLE_READER_SCOPE_DENIED');
    }
    if (!identityVerified) {
      const email = (await (await get('email')).text()).trim();
      if (email !== SERVICE_ACCOUNT) throw new Error('GOOGLE_MANAGED_SERVICE_ACCOUNT_MISMATCH');
      identityVerified = true;
    }
    const payload = await (await get('token')).json();
    if (payload?.token_type !== 'Bearer' || typeof payload.access_token !== 'string' ||
        !payload.access_token || /\s/.test(payload.access_token) ||
        !Number.isInteger(payload.expires_in) || payload.expires_in <= 0) {
      throw new Error('GOOGLE_MANAGED_TOKEN_INVALID');
    }
    return payload.access_token;
  };
}

module.exports = {
  CAPABILITY, CONNECTOR_ID, SERVICE_ACCOUNT, REQUIRED_SCOPE,
  createLabGatewayKnowledgeCapability, createGoogleManagedReaderTokenProvider,
};