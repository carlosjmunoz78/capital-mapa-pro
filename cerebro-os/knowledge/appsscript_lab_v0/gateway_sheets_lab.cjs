'use strict';
const {createHash} = require('node:crypto');
const {readFileSync} = require('node:fs');
const {join} = require('node:path');
const {Script, createContext} = require('node:vm');

const scopes = ['company_id', 'department_id', 'engine_id', 'agent_id', 'subagent_id', 'environment', 'version'];
const tabs = ['Config', 'Departamentos', 'Agentes', 'Especialistas', 'Biblioteca', 'Asignaciones', 'Entregas_LAB'];
const spreadsheetId = '1mzG1X15gkD7-zWpoq6I76MNm0ejCprb9_quyIQjR9Lc';
const pinnedResolver = 'befa122e30c51554003680f0eb5c6941d6eea1a97fcee2a90aa8e15e2b22c5ae';
const hash = value => createHash('sha256').update(value).digest('hex');
const code = readFileSync(join(__dirname, 'Code.gs'), 'utf8').replace(/\r\n/g, '\n');
if (hash(code) !== pinnedResolver) throw new Error('RESOLVER_VERSION_MISMATCH');
const resolver = new Script(code + '\nconst idx = cerebroIndex_(); const key = cerebroKey_(cerebroKey_(request.company_id, request.engine_id, request.environment), request.subagent_id); cerebroResolve_(idx,key);');

function entitlementMatches(grant, request) {
  return scopes.every(field => grant?.[field] === request[field]);
}

function resolveFromRows(rows, request) {
  const sheet = {
    getSheetByName(name) {
      const data = rows.get(name);
      return data ? {getParent: () => sheet, getDataRange: () => ({getValues: () => data})} : null;
    },
  };
  const context = createContext({SpreadsheetApp: {getActiveSpreadsheet: () => sheet}, request});
  const bundle = resolver.runInContext(context, {timeout: 5000});
  if (!entitlementMatches(bundle, request)) throw new Error('BUNDLE_SCOPE_MISMATCH');
  const sha = hash(JSON.stringify(bundle));
  const receipt = rows.get('Entregas_LAB').slice(1).find(row =>
    row[1] === request.company_id && row[2] === request.environment &&
    row[3] === request.subagent_id && row[4] === 'RESOLVED_LAB' && row[5] === sha);
  if (!receipt) throw new Error('DELIVERY_RECEIPT_PENDING');
  return {bundle, sha256: sha};
}

async function readSheets(googleAccessToken, fetchImpl) {
  const url = new URL('https://sheets.googleapis.com/v4/spreadsheets/' + spreadsheetId + '/values:batchGet');
  tabs.forEach(tab => url.searchParams.append('ranges', tab + '!A1:Q'));
  url.searchParams.set('valueRenderOption', 'UNFORMATTED_VALUE');
  url.searchParams.set('dateTimeRenderOption', 'FORMATTED_STRING');
  const token = await googleAccessToken();
  if (typeof token !== 'string' || !token || /\s/.test(token)) throw new Error('GOOGLE_IDENTITY_UNAVAILABLE');
  const response = await fetchImpl(url, {
    method: 'GET',
    redirect: 'error',
    headers: {Authorization: 'Bearer ' + token},
    signal: AbortSignal.timeout(20000),
  });
  if (!response.ok) throw new Error('GOOGLE_SHEETS_HTTP_' + response.status);
  const data = await response.json();
  if (data.spreadsheetId !== spreadsheetId || data.valueRanges?.length !== tabs.length) throw new Error('SHEET_RESPONSE_MISMATCH');
  return new Map(tabs.map((tab, i) => {
    const item = data.valueRanges[i];
    if (item.range?.split('!')[0].replace(/^'|'$/g, '') !== tab || !Array.isArray(item.values)) throw new Error('SHEET_RANGE_MISMATCH');
    return [tab, item.values];
  }));
}

// Authenticate and check Gateway policy at the trusted runtime boundary. The caller supplies
// an opaque context, never the identity or grants. Persist audit records before returning data.
function createLabKnowledgeReader({authenticate, policyCheck, googleAccessToken, audit, fetchImpl = fetch}) {
  for (const required of [authenticate, policyCheck, googleAccessToken, audit]) {
    if (typeof required !== 'function') throw new TypeError('MISSING_TRUSTED_GATEWAY_DEPENDENCY');
  }
  return async (context, input) => {
    const request = Object.fromEntries(scopes.map(field=>[field, input?.[field]]));
    let consumerId;
    let outcome = 'DENIED';
    let digest;
    try {
      if (request.environment !== 'LAB' || scopes.some(field => typeof request[field] !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$/.test(request[field]))) {
        throw new Error('INVALID_LAB_SCOPE');
      }
      const consumer = await authenticate(context);
      if (typeof consumer?.id !== 'string' || !consumer.id) throw new Error('UNAUTHENTICATED_CONSUMER');
      consumerId = consumer.id;
      if (!Array.isArray(consumer.grants) || !consumer.grants.some(grant=>entitlementMatches(grant, request)) ||
          await policyCheck(consumer, request) !== true) throw new Error('SCOPE_DENIED');
      outcome = 'FAILED';
      const result = resolveFromRows(await readSheets(googleAccessToken, fetchImpl), request);
      digest = result.sha256;
      outcome = 'READ_VERIFIED';
      return result;
    } finally {
      await audit({event: 'KNOWLEDGE_LAB_READ', timestamp: new Date().toISOString(),
        consumer_id: consumerId, scope: Object.fromEntries(scopes.filter(field=>typeof request[field]==='string'&&/^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$/.test(request[field])).map(field=>[field,request[field]])),
        outcome, sha256: digest});
    }
  };
}

module.exports = {createLabKnowledgeReader};
