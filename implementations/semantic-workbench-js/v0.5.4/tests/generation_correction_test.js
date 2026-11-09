'use strict';

const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const net = require('node:net');
const http = require('node:http');
const path = require('node:path');
const { diagnoseProposal, normalizeReviewerReport } = require('../generation-correction');
const ROOT = path.join(__dirname, '..');

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      server.close(error => error ? reject(error) : resolve(port));
    });
  });
}
async function waitForHealth(url, child) {
  const deadline = Date.now() + 10000;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error(`Workbench exited early (${child.exitCode}).`);
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(1000) });
      if (response.ok) return response.json();
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error('Workbench did not start.');
}

const claim = (subject, predicate, object, evidence) => ({
  subject: { text: subject, type: 'person' },
  predicate,
  object: { text: object, type: 'artifact' },
  polarity: 'positive', tense: 'present', modality: 'asserted',
  evidence_text: evidence, confidence: 0.9, notes: ''
});
function proposal(includeRefund) {
  const claims = [claim('customer', 'NEEDS', 'tool', 'The customer needs the tool')];
  const entities = [
    { id: 'e1', canonicalText: 'customer', type: 'person' },
    { id: 'e2', canonicalText: 'tool', type: 'artifact' }
  ];
  if (includeRefund) {
    claims.push(claim('customer', 'WANTS', 'refund', 'wants a refund'));
    entities.push({ id: 'e3', canonicalText: 'refund', type: 'artifact' });
  }
  return { intent: 'ASSERTION', interpretation: 'The customer needs a tool and wants a refund.', claims, entities, mentions: [], claimRelations: [], unresolved: [] };
}
function ollamaResponse(content, extra = {}) {
  return { message: { content }, done: true, done_reason: 'stop', eval_count: 100, eval_duration: 1000000000, prompt_eval_count: 200, prompt_eval_duration: 1000000000, total_duration: 2200000000, ...extra };
}

async function main() {
  const manyItems = {intent:'ASSERTION',interpretation:'large proposal',claims:[],entities:[],mentions:[],claimRelations:[],unresolved:[]};
  for (let i = 0; i < 25; i++) {
    manyItems.claims.push(claim(`entity ${i}`, `RELATION_${i}`, `object ${i}`, `source fragment ${i}`));
    manyItems.entities.push({id:`e${i}`,canonicalText:`entity ${i}`,type:'unknown'});
    manyItems.mentions.push({entityId:`e${i}`,surfaceText:`entity ${i}`,canonicalText:`entity ${i}`,mentionType:'noun_phrase',antecedentId:null});
  }
  const largeIssues = diagnoseProposal(manyItems, Array.from({length:25},(_,i)=>`source fragment ${i}`).join('; '));
  assert.equal(largeIssues.filter(x => x.code === 'MISSING_ARRAY').length, 0, 'diagnostics do not impose array-size ceilings');
  const malformedLinks = diagnoseProposal({
    ...manyItems,
    claims:[{...claim('customer','NEEDS','tool','customer needs tool'),id:'c1',conditions:[{
      marker:'unless',effect:'condition_for_assertion',logicalStatus:'conditional_not_asserted',
      proposition:{subject:{text:'prices'},predicate:'INCREASE',polarity:'positive'},evidence_text:'prices increase'
    }]}],
    claimRelations:[{type:'CONTRADICTS',fromClaimId:'c1',toClaimId:'missing'}]
  }, 'customer needs tool unless prices increase');
  assert.ok(malformedLinks.some(x=>x.code==='CONDITION_EFFECT_MISMATCH'));
  assert.ok(malformedLinks.some(x=>x.code==='CONDITION_LOGICAL_STATUS_MISMATCH'));
  assert.ok(malformedLinks.some(x=>x.code==='DANGLING_CLAIM_RELATION'));
  const normalizedMissing = normalizeReviewerReport({overallAssessment:'needs repair',issues:[],missingContent:['A source-grounded clause was omitted.']});
  assert.equal(normalizedMissing.issues[0].severity, 'error', 'reviewer missingContent findings trigger targeted correction');
  console.log('PASS: deterministic diagnosis accepts semantically large collections without item-count caps.');
  console.log('PASS: reviewer missingContent entries are promoted to repair findings.');
  const fakePort = await freePort();
  const appPort = await freePort();
  const requests = [];
  const queue = [
    ollamaResponse('', { done: false, done_reason: 'length', eval_count: 4096 }),
    ollamaResponse(JSON.stringify(proposal(false))),
    ollamaResponse(JSON.stringify({
      overallAssessment: 'NEEDS_REPAIR',
      issues: [{ code: 'MISSING_CLAUSE', severity: 'error', location: 'claims', problem: 'The source also asserts that the customer wants a refund.', recommendedCorrection: 'Add a separate WANTS claim for the refund clause.' }],
      missingContent: ['The customer wants a refund.']
    })),
    ollamaResponse(JSON.stringify(proposal(true))),
    ollamaResponse(JSON.stringify({ overallAssessment: 'SOUND', issues: [], missingContent: [] }))
  ];
  const fakeOllama = http.createServer(async (req, res) => {
    if (req.url === '/api/chat') {
      let raw = '';
      for await (const chunk of req) raw += chunk;
      const body = JSON.parse(raw);
      requests.push(body);
      const next = queue.shift();
      if (next?.rawResponse !== undefined) {
        res.writeHead(next.status || 200, { 'content-type': next.contentType || 'application/json' });
        res.end(next.rawResponse);
        return;
      }
      res.writeHead(next?.error ? 500 : 200, { 'content-type': 'application/json' });
      res.end(JSON.stringify(next || ollamaResponse(JSON.stringify({ overallAssessment: 'SOUND', issues: [], missingContent: [] }))));
      return;
    }
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ models: [] }));
  });
  await new Promise((resolve, reject) => fakeOllama.listen(fakePort, '127.0.0.1', error => error ? reject(error) : resolve()));
  const child = spawn(process.execPath, ['server.js'], {
    cwd: ROOT, env: { ...process.env, USG_PORT: String(appPort), USG_MODEL_TIMEOUT_MS: '10000', USG_MAX_REPAIR_ROUNDS: '1' },
    stdio: ['ignore', 'ignore', 'pipe']
  });
  let logs = '';
  child.stderr.on('data', chunk => { logs += chunk.toString(); });
  try {
    const base = `http://127.0.0.1:${appPort}`;
    const health = await waitForHealth(`${base}/api/health`, child);
    assert.equal(health.version, '0.5.4');
    const response = await fetch(`${base}/api/interpret`, {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ ollamaUrl: `http://127.0.0.1:${fakePort}`, model: 'test-model', text: 'The customer needs the tool, but wants a refund.' }),
      signal: AbortSignal.timeout(30000)
    });
    const payload = await response.json();
    assert.equal(response.status, 200, JSON.stringify(payload));
    assert.equal(payload.result.claims.length, 2, 'repair restores the second source proposition');
    assert.equal(payload.correctionAudit.status, 'repaired');
    assert.equal(payload.correctionAudit.repairRounds, 1);
    assert.equal(payload.correctionAudit.reviewerStatus, 'completed');
    assert.equal(payload.correctionAudit.reviewerMode, 'same_model_second_pass');
    assert.equal(payload.correctionAudit.generation[0].requested_num_predict, 4096);
    assert.equal(payload.correctionAudit.generation[1].requested_num_predict, 8192, 'length termination escalates the output budget');
    assert.equal(payload.correctionAudit.generation[0].rawModelResponse, '', 'partial/empty length-terminated content is retained in the attempt trace');
    assert.equal(payload.correctionAudit.generationArtifacts[0].rawModelResponse, JSON.stringify(proposal(false)), 'the full successful raw model response is preserved');
    assert.deepEqual(payload.correctionAudit.generation.map(x => x.phase), ['generation', 'generation', 'review', 'repair', 'review']);
    assert.equal(requests.length, 5);
    const prompt = requests[0].messages.map(x => x.content).join('\n');
    assert.match(prompt, /Never impose a maximum count/i);
    const repairPrompt = requests[3].messages.map(x => x.content).join('\n');
    assert.match(repairPrompt, /There are NO fixed maximum counts/i);
    console.log('PASS: adaptive output budget retries a length-terminated generation.');
    console.log('PASS: second-pass audit detects omitted source content and triggers targeted repair.');
    console.log('PASS: corrected proposal is re-reviewed by the same model and returned with an audit trace.');
    console.log('PASS: prompts explicitly prohibit semantic item-count limits.');
    console.log('PASS: full raw model responses and partial length-stop outputs are retained for diagnosis.');

    queue.push(ollamaResponse(JSON.stringify(proposal(true))));
    queue.push(ollamaResponse(JSON.stringify({overallAssessment:'UNCERTAIN',issues:[],missingContent:[]})));
    const uncertainResponse = await fetch(`${base}/api/interpret`, {
      method:'POST', headers:{'content-type':'application/json'},
      body:JSON.stringify({ollamaUrl:`http://127.0.0.1:${fakePort}`,model:'test-model',text:'The customer needs the tool, but wants a refund.'}),
      signal:AbortSignal.timeout(30000)
    });
    const uncertainPayload = await uncertainResponse.json();
    assert.equal(uncertainResponse.status, 200, JSON.stringify(uncertainPayload));
    assert.equal(uncertainPayload.correctionAudit.status, 'needs_review', 'an uncertain second-pass assessment must not be marked reviewed');
    assert.equal(uncertainPayload.correctionAudit.reviewerAssessment, 'UNCERTAIN');
    console.log('PASS: uncertain second-pass assessment is surfaced as needs_review.');

    queue.push({error:'prediction aborted, token repeat limit reached'});
    const repeatResponse = await fetch(`${base}/api/interpret`, {
      method:'POST', headers:{'content-type':'application/json'},
      body:JSON.stringify({ollamaUrl:`http://127.0.0.1:${fakePort}`,model:'test-model',text:'The customer needs the tool.'}),
      signal:AbortSignal.timeout(10000)
    });
    const repeatPayload = await repeatResponse.json();
    assert.equal(repeatResponse.status,502);
    assert.equal(repeatPayload.failureCategory,'repetition_abort');
    assert.equal(repeatPayload.correctionAudit.status,'generation_request_failed');
    assert.equal(repeatPayload.correctionAudit.generationArtifacts[0].failureCategory,'repetition_abort');
    assert.equal(repeatPayload.correctionAudit.generationArtifacts[0].diagnostic.httpStatus,500);
    assert.match(repeatPayload.correctionAudit.generationArtifacts[0].diagnostic.responseBody,/repeat limit reached/);
    assert.equal(requests.length,8,'a repeat-limit abort is diagnosed rather than retried as an output-length event');
    console.log('PASS: repetition-limit abort is distinguished from output-token truncation and retains Ollama error details.');

    queue.push({rawResponse:'not-json-from-ollama'});
    const malformedEnvelopeResponse = await fetch(`${base}/api/interpret`, {
      method:'POST', headers:{'content-type':'application/json'},
      body:JSON.stringify({ollamaUrl:`http://127.0.0.1:${fakePort}`,model:'test-model',text:'The customer needs the tool.'}),
      signal:AbortSignal.timeout(10000)
    });
    const malformedEnvelopePayload = await malformedEnvelopeResponse.json();
    assert.equal(malformedEnvelopeResponse.status,502);
    assert.equal(malformedEnvelopePayload.failureCategory,'response_parse_error');
    assert.equal(malformedEnvelopePayload.correctionAudit.generationArtifacts[0].diagnostic.responseBody,'not-json-from-ollama');
    assert.equal(malformedEnvelopePayload.correctionAudit.generationArtifacts[0].diagnostic.responseReceived,true);
    console.log('PASS: malformed Ollama response envelopes are classified as parse failures and retain the full raw body.');

    const missingFieldProposal=proposal(true);
    delete missingFieldProposal.unresolved;
    const soundReview=ollamaResponse(JSON.stringify({overallAssessment:'SOUND',issues:[],missingContent:[]}));
    queue.push(ollamaResponse(JSON.stringify(missingFieldProposal)),soundReview,ollamaResponse(JSON.stringify(missingFieldProposal)),soundReview);
    const contractFailureResponse=await fetch(`${base}/api/interpret`,{
      method:'POST',headers:{'content-type':'application/json'},
      body:JSON.stringify({ollamaUrl:`http://127.0.0.1:${fakePort}`,model:'test-model',text:'The customer needs the tool and wants a refund.'}),
      signal:AbortSignal.timeout(15000)
    });
    const contractFailurePayload=await contractFailureResponse.json();
    assert.equal(contractFailureResponse.status,502);
    assert.equal(contractFailurePayload.failureCategory,'proposal_contract_failure');
    assert.deepEqual(contractFailurePayload.correctionAudit.missingContractFields,['unresolved']);
    assert.equal(contractFailurePayload.correctionAudit.failure.category,'proposal_contract_failure');
    assert.equal(contractFailurePayload.diagnostic.phase,'proposal_contract_validation');
    console.log('PASS: a complete HTTP/JSON response that still omits a required USG field is diagnosed as proposal_contract_failure, not a transport error.');

    queue.push(ollamaResponse('not valid JSON'),ollamaResponse('still not valid JSON'));
    const exhaustedResponse=await fetch(`${base}/api/interpret`,{
      method:'POST',headers:{'content-type':'application/json'},
      body:JSON.stringify({ollamaUrl:`http://127.0.0.1:${fakePort}`,model:'test-model',text:'The customer needs the tool.'}),
      signal:AbortSignal.timeout(15000)
    });
    const exhaustedPayload=await exhaustedResponse.json();
    assert.equal(exhaustedResponse.status,502);
    assert.equal(exhaustedPayload.failureCategory,'proposal_repair_exhausted');
    assert.equal(exhaustedPayload.correctionAudit.failure.category,'proposal_repair_exhausted');
    assert.equal(exhaustedPayload.correctionAudit.generationArtifacts[1].parseStatus,'invalid_json');
    assert.equal(exhaustedPayload.correctionAudit.generationArtifacts[1].rawModelResponse,'still not valid JSON');
    console.log('PASS: exhausted invalid-JSON repair is diagnosed separately and preserves the failed raw repair response.');
  } finally {
    child.kill('SIGTERM');
    await new Promise(resolve => {
      if (child.exitCode !== null) return resolve();
      const timer = setTimeout(() => { child.kill('SIGKILL'); resolve(); }, 3000);
      child.once('exit', () => { clearTimeout(timer); resolve(); });
    });
    await new Promise(resolve => fakeOllama.close(() => resolve()));
    if (logs) process.stderr.write(logs);
  }
}

main().catch(error => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exitCode = 1;
});
