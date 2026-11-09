'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const ROOT = path.join(__dirname, '..');

function createHarness() {
  const source = fs.readFileSync(path.join(ROOT, 'app.js'), 'utf8');
  const eventSection = source.indexOf('// ---------------------- Event wiring / initialization ----------------------');
  assert.ok(eventSection >= 0, 'app logic boundary exists');
  const nodes = new Map([
    ['#ollama-url', { value:'http://127.0.0.1:11434' }],
    ['#model-select', { value:'test-model' }]
  ]);
  const store = new Map();
  const sandbox = {
    console, Date, Math, JSON, Map, Set, URL, URLSearchParams,
    localStorage: { getItem:key=>store.has(key)?store.get(key):null, setItem:(key,value)=>store.set(key,value) },
    document: { querySelector:selector=>nodes.get(selector)||null, querySelectorAll:()=>[] },
    window: { scrollTo:()=>{} }, setTimeout, clearTimeout, confirm:()=>true,
    USGSemanticCore:require('../semantic-core.js'),
    USGSemanticComposer:require('../semantic-composer.js')
  };
  vm.createContext(sandbox);
  vm.runInContext(source.slice(0,eventSection) + '\nglobalThis.__test={requestModelInterpretation,generationFailureAudit};', sandbox, {filename:'app.js'});
  return sandbox;
}

async function main() {
  let passed = 0;
  const check = (condition, message) => {
    assert.ok(condition, message);
    passed += 1;
    console.log(`PASS: ${message}`);
  };
  const sandbox = createHarness();
  const serverAudit = {
    status:'generation_request_failed',
    failure:{category:'repetition_abort',message:'prediction aborted, token repeat limit reached'},
    generation:[{phase:'generation',status:'failed',failure_category:'repetition_abort'}],
    generationArtifacts:[{
      phase:'generation',status:'request_failed',failureCategory:'repetition_abort',
      error:'prediction aborted, token repeat limit reached',
      diagnostic:{category:'repetition_abort',httpStatus:500,responseBody:'{"error":"prediction aborted, token repeat limit reached"}',responseReceived:true}
    }]
  };
  const httpPayload = {
    error:'prediction aborted, token repeat limit reached',
    failureCategory:'repetition_abort',
    diagnostic:serverAudit.generationArtifacts[0].diagnostic,
    correctionAudit:serverAudit
  };
  sandbox.fetch = async () => ({
    ok:false,status:502,
    text:async()=>JSON.stringify(httpPayload)
  });
  let httpError;
  try { await sandbox.__test.requestModelInterpretation('The customer needs the tool.'); }
  catch (error) { httpError = error; }
  assert.ok(httpError, 'HTTP error is propagated to the caller');
  check(httpError.failureCategory==='repetition_abort', 'Workbench browser adapter preserves the typed repetition-abort category');
  check(httpError.diagnostic.httpStatus===500 && httpError.diagnostic.bridgeHttpStatus===502, 'adapter preserves both Ollama HTTP status and Workbench bridge HTTP status');
  check(httpError.diagnostic.responseBody.includes('repeat limit reached') && httpError.correctionAudit.generationArtifacts[0].diagnostic.responseBody.includes('repeat limit reached'), 'adapter retains the full Ollama error body and server generation audit');

  sandbox.fetch = async () => { const error=new Error('fetch failed'); error.cause={code:'ECONNREFUSED'}; throw error; };
  let transportError;
  try { await sandbox.__test.requestModelInterpretation('The customer needs the tool.'); }
  catch (error) { transportError = error; }
  assert.ok(transportError, 'transport error is propagated to the caller');
  const transportAudit=sandbox.__test.generationFailureAudit(transportError);
  check(transportError.failureCategory==='connection_or_transport_error', 'bridge transport failure is assigned a distinct category');
  check(transportAudit.generationArtifacts[0].diagnostic.responseReceived===false && transportAudit.generationArtifacts[0].diagnostic.errorCode==='ECONNREFUSED', 'transport fallback audit records no response and the underlying connection error code');

  sandbox.fetch = async () => ({ ok:true,status:200,text:async()=>'{broken-json' });
  let parseError;
  try { await sandbox.__test.requestModelInterpretation('The customer needs the tool.'); }
  catch (error) { parseError = error; }
  assert.ok(parseError, 'invalid bridge response body is rejected');
  check(parseError.failureCategory==='response_parse_error' && parseError.diagnostic.responseBody==='{broken-json', 'invalid bridge response JSON is diagnosed with its complete raw body');

  console.log(`\nApp failure-audit integration tests: ${passed} passed, 0 failed.`);
}

main().catch(error => { console.error(error); process.exitCode=1; });
