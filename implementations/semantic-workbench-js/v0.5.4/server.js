'use strict';

// Local-only static server + Ollama adapter. Uses Node's built-in modules only.
// The server binds to loopback and rejects non-loopback Ollama destinations.
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { diagnoseProposal, normalizeReviewerReport, shouldRepair, buildReviewMessages, buildRepairMessages, parseModelJson } = require('./generation-correction');

const HOST = '127.0.0.1';
const PORT = Number(process.env.USG_PORT || 8765);
const ROOT = __dirname;
const MAX_BODY = 1_500_000;
const DEFAULT_MODEL_TIMEOUT_MS = 180_000;
const MIN_MODEL_TIMEOUT_MS = 1_000;
const MAX_MODEL_TIMEOUT_MS = 600_000;
const requestedModelTimeout = Number(process.env.USG_MODEL_TIMEOUT_MS);
const MODEL_TIMEOUT_MS = Number.isSafeInteger(requestedModelTimeout)
  && requestedModelTimeout >= MIN_MODEL_TIMEOUT_MS
  && requestedModelTimeout <= MAX_MODEL_TIMEOUT_MS
  ? requestedModelTimeout
  : DEFAULT_MODEL_TIMEOUT_MS;
const MAX_REPAIR_ROUNDS = Number.isSafeInteger(Number(process.env.USG_MAX_REPAIR_ROUNDS))
  ? Math.max(0, Math.min(3, Number(process.env.USG_MAX_REPAIR_ROUNDS)))
  : 2;
const GENERATION_TOKEN_BUDGETS = [4096, 8192, 16384];
const MODEL_GENERATION_OPTIONS = { temperature:0, top_p:0.9, repeat_penalty:1.10, repeat_last_n:128 };
const MIME = {
  '.html':'text/html; charset=utf-8', '.css':'text/css; charset=utf-8', '.js':'text/javascript; charset=utf-8',
  '.json':'application/json; charset=utf-8', '.svg':'image/svg+xml', '.png':'image/png', '.ico':'image/x-icon'
};

function send(res, status, data, contentType = 'application/json; charset=utf-8') {
  res.writeHead(status, { 'Content-Type':contentType, 'Cache-Control':'no-store', 'X-Content-Type-Options':'nosniff' });
  res.end(contentType.startsWith('application/json') ? JSON.stringify(data) : data);
}
function readJson(req) {
  return new Promise((resolve, reject) => {
    let raw = '';
    req.on('data', chunk => {
      raw += chunk;
      if (raw.length > MAX_BODY) { reject(new Error('Request body is too large.')); req.destroy(); }
    });
    req.on('end', () => {
      try { resolve(raw ? JSON.parse(raw) : {}); }
      catch { reject(new Error('Request body must be valid JSON.')); }
    });
    req.on('error', reject);
  });
}
function localOllamaBase(input) {
  let url;
  try { url = new URL(input || 'http://127.0.0.1:11434'); }
  catch { throw new Error('Ollama address is not a valid URL.'); }
  const host = url.hostname.toLowerCase().replace(/^\[|\]$/g, '');
  if (!['127.0.0.1','localhost','::1'].includes(host)) throw new Error('For privacy, this prototype only connects to Ollama on this PC (localhost).');
  if (url.protocol !== 'http:' && url.protocol !== 'https:') throw new Error('Ollama address must use HTTP or HTTPS.');
  if (url.username || url.password) throw new Error('Do not put credentials in the Ollama address.');
  return url.origin;
}
function classifyGenerationFailure(error, responseBody = '') {
  const message = `${error?.message || ''} ${responseBody || ''}`.toLowerCase();
  if (/repeat(?:ition)?(?: token)? limit|token repeat limit|repetition abort/.test(message)) return 'repetition_abort';
  if (/aborterror|timed out|did not respond within/.test(message)) return 'timeout';
  if (/econnrefused|fetch failed|could not reach ollama/.test(message)) return 'connection_or_transport_error';
  if (/json|unexpected token|unterminated|stringify|parse/.test(message)) return 'response_parse_error';
  if (error?.diagnostic?.httpStatus || error?.httpStatus) return 'ollama_http_error';
  return 'model_request_error';
}

async function ollamaFetch(base, endpoint, options = {}, phase = 'request') {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), MODEL_TIMEOUT_MS);
  const requestStartedAt = new Date().toISOString();
  const startedMs = Date.now();
  try {
    const response = await fetch(`${base}${endpoint}`, { ...options, signal:controller.signal });
    const bodyText = await response.text();
    let body;
    try { body = bodyText ? JSON.parse(bodyText) : {}; }
    catch (parseError) {
      const error = new Error(`Ollama returned invalid JSON during ${phase}: ${parseError.message}`);
      error.failureCategory = 'response_parse_error';
      error.diagnostic = {
        phase, endpoint, category:'response_parse_error',
        httpStatus:response.status, responseBody:bodyText,
        originalErrorName:parseError.name, originalErrorMessage:parseError.message,
        requestStartedAt, requestEndedAt:new Date().toISOString(),
        durationMs:Date.now()-startedMs, timeoutMs:MODEL_TIMEOUT_MS,
        responseReceived:true
      };
      throw error;
    }
    if (!response.ok) {
      const message = body.error || body.message || `Ollama returned HTTP ${response.status}.`;
      const error = new Error(message);
      error.diagnostic = {
        phase, endpoint, category:classifyGenerationFailure(error, bodyText),
        httpStatus:response.status, responseBody:bodyText,
        requestStartedAt, requestEndedAt:new Date().toISOString(),
        durationMs:Date.now()-startedMs, timeoutMs:MODEL_TIMEOUT_MS
      };
      throw error;
    }
    return body;
  } catch (error) {
    if (error.name === 'AbortError') {
      const seconds = Math.ceil(MODEL_TIMEOUT_MS / 1000);
      const wrapped = new Error(`The local model did not respond within ${seconds} second${seconds === 1 ? '' : 's'}.`);
      wrapped.diagnostic = {
        phase, endpoint, category:'timeout', originalErrorName:error.name,
        originalErrorMessage:error.message, requestStartedAt,
        requestEndedAt:new Date().toISOString(), durationMs:Date.now()-startedMs,
        timeoutMs:MODEL_TIMEOUT_MS, responseReceived:false
      };
      throw wrapped;
    }
    if (!error.diagnostic && (error.cause?.code === 'ECONNREFUSED' || /fetch failed/i.test(error.message))) {
      const wrapped = new Error('Could not reach Ollama. Is Ollama installed and running on this PC?');
      wrapped.diagnostic = {
        phase, endpoint, category:'connection_or_transport_error',
        originalErrorName:error.name, originalErrorMessage:error.message,
        errorCode:error.cause?.code || error.code || null,
        requestStartedAt, requestEndedAt:new Date().toISOString(),
        durationMs:Date.now()-startedMs, timeoutMs:MODEL_TIMEOUT_MS,
        responseReceived:false
      };
      throw wrapped;
    }
    if (!error.diagnostic) error.diagnostic = {
      phase, endpoint, category:classifyGenerationFailure(error),
      originalErrorName:error.name, originalErrorMessage:error.message,
      errorCode:error.cause?.code || error.code || null,
      requestStartedAt, requestEndedAt:new Date().toISOString(),
      durationMs:Date.now()-startedMs, timeoutMs:MODEL_TIMEOUT_MS,
      responseReceived:false
    };
    throw error;
  } finally { clearTimeout(timer); }
}
function buildMessages(text, knowledge) {
  const knowledgeText = Array.isArray(knowledge) ? knowledge.map((item,i) => `${i+1}. ${item.subject} — ${item.predicate} — ${item.object ?? '∅'} [${item.polarity || 'positive'}]`).join('\n') : 'No existing knowledge supplied.';
  const system = `You are the language interpretation component of an experimental semantic system called USG. Your task is to propose a structured representation of the given source sentence, not to answer it and not to invent facts.

Return ONLY one valid JSON object with these keys:
{
  "intent": "ASSERTION|QUESTION|COMMAND|OTHER|UNRESOLVED",
  "interpretation": "plain-language account of what the source states; preserve ambiguity",
  "claims": [
    {
      "subject": {"text": "...", "type": "person|class|individual|artifact|event|property|instrument|unknown"},
      "predicate": "UPPER_SNAKE_CASE_RELATION",
      "object": {"text": "...", "type": "..."} or null,
      "polarity": "positive|negative",
      "tense": "past|present|future|unknown",
      "modality": "asserted|possible|necessary|obligatory|possible_or_ability|expected|unknown",
      "modalScope": {"operator":"MIGHT|MAY|MUST|SHOULD|CAN|WILL|EXPECTED|ASSERTED", "force":"epistemic_possibility|necessity|deontic|ability|assertion|unknown", "scope":"proposition", "surfaceText":"source modal word"},
      "time": {"grammaticalTense":"past|present|future|unknown", "aspect":"simple|progressive|perfect|habitual|unknown", "referenceTime":"past|present|future|unspecified"},
      "quantifierScope": {"operator":"NOT|NO|...", "quantifier":"FORALL|EXISTS|...", "variable":"x", "restrictor":{"predicate":"INSTANCE_OF","entity":{"text":"...","type":"class"}}, "scope":"claim", "logicalForm":"explicit scope expression"},
      "comparisonFrame": {"reference":null, "comparisonSet":null, "status":"context_dependent"},
      "eventAttributes": [{"type":"frequency|duration|manner|...", "value":"...", "normalizedValue":"...", "surfaceText":"exact source phrase", "scope":"event"}],
      "conditions": [
        {"marker":"if|when|unless|although|because|...", "proposition":{"subject":{"text":"...","type":"..."}, "predicate":"...", "object":null or {"text":"...","type":"..."}, "polarity":"positive|negative", "tense":"past|present|future|unknown", "modality":"...", "modalScope":{"operator":"...","force":"...","scope":"proposition","surfaceText":"..."}, "time":{"grammaticalTense":"...","aspect":"...","referenceTime":"..."}}, "scope":"claim", "effect":"condition_for_assertion|exception_to_assertion|...", "consequence":"unspecified|...", "evidence_text":"exact words copied from source"}
      ],
      "evidence_text": "exact contiguous words copied from source that support this claim",
      "confidence": 0.0,
      "notes": "ambiguity or assumptions; never conceal uncertainty"
    }
  ],
  "entities": [{"id":"...", "canonicalText":"...", "type":"..."}],
  "mentions": [{"entityId":"...", "surfaceText":"...", "canonicalText":"...", "mentionType":"noun_phrase|pronoun", "antecedentId":"..."}],
  "claimRelations": [{"type":"CONTRADICTS|SUPPORTS|ATTACKS|...", "fromClaimId":"...", "toClaimId":"...", "scope":"...", "status":"candidate"}],
  "unresolved": ["specific part that cannot be determined from source"]
}

Rules:
- Ground every claim in the source sentence. Do not use the existing knowledge list to add facts not stated by the source.
- Preserve negation scope, tense, modality, quantifiers, comparison, coreference, and conditional/subordinate clauses. Attach conditions to the proposition they modify; do not absorb a condition into an entity name. Every condition has its own nested proposition and its own tense/modality. For BUT, OR, AND, and ALTHOUGH, emit each clause as a separate claim and link them with the appropriate relation; do not collapse two predicates into one object. For IF, UNLESS, and WHEN, preserve the subordinate clause as a nested proposition. For BECAUSE, emit a separate cause claim and source-attributed CAUSE relation.
- Treat polarity as independent of predicate identity: “does not like” is LIKE with negative polarity, not DISLIKES with negative polarity. Do not replace a predicate with an antonym merely because the sentence is negated.
- Only populate quantifierScope when an overt quantifier or quantifier-negation is present (e.g. all, every, no, not every, some, most). Omit quantifierScope entirely otherwise; never return an empty object or UNKNOWN placeholder. Omit eventAttributes when none are expressed. Never emit template/example placeholders such as "...", "exact source phrase", or "frequency|duration|manner|...". Every event attribute surfaceText must be an exact phrase in the source.
- Treat "is expected to" as an epistemic expectation operator EXPECTED, not a deontic MUST.
- Keep the source wording authoritative when the proposed relation conflicts with it. In particular, for “does not like” use LIKE with negative polarity even if a lexical antonym such as DISLIKES seems plausible. “Does not dislike” is a different construction and must not be rewritten as “does not like”.
- Do not encode negation in the predicate name (for example, use LIKE with polarity=negative, not DOES_NOT_LIKE). Keep quantifier negation in quantifierScope; “not every customer” is NOT(FORALL...), not “no customer”.
- For a sentence with “because”, represent the cause clause as its own claim and connect it to the effect claim with an explicit source-attributed causal explanation. Do not imply that the sentence's causal assertion has been independently verified. Assign tense separately to each clause. Resolve pronouns only when a clear antecedent is present, and preserve both the surface mention and canonical entity reference.
- Preserve determiners in subject/object surface text (a/an/the) so the adapter can retain indefinite/definite reference separately from the normalized entity label.
- If a DIFFER statement does not state what or which set is being compared, do not invent a comparison target. Keep the proposition with object=null and comparisonFrame.status=context_dependent; do not mark the entire sentence unresolved only because the comparison target is implicit. A later task that requires pairwise comparison or calculation must report that missing context.
- Do not strengthen a negative statement into inability, incapacity, impossibility, or a general rule unless the source explicitly states that stronger meaning.
- For “A does not need B unless condition P”, represent the negative NEEDS proposition with an “unless” exception condition. Set the exception consequence to “unspecified” unless the sentence explicitly states what happens when P holds. Do NOT infer “A needs B when P” from that wording alone.
- A condition is a separate proposition, not an object phrase. If its internal predicate is unclear, place it in unresolved rather than guessing.
- Distinguish subclass from instance: “a sparrow is a kind of bird” is SUBCLASS_OF; “Tweety is a sparrow” is INSTANCE_OF.
- Do not mistake descriptive noun phrases for asserted relations. If no claim is safely supported, return an empty claims array and explain why in unresolved.
- Types are provisional labels. Use “unknown” rather than inventing a type.
- Evidence_text must be an exact quote from the source. Confidence is an informal estimate, not a calibrated probability. Preserve event frequency such as “every day” as an event attribute, not as part of an object label. Keep apparently contradictory clauses as separate claims; only add a contradiction relation when predicate, arguments, temporal frame, modal operator, quantifier scope, event attributes, and conditions match.
- Never impose a maximum count on claims, entities, mentions, relations, conditions, event attributes, or unresolved items. Include every distinct source-grounded semantic item required to represent the source. Do not truncate or summarize away meaning.
- Never repeat a claim or semantic object merely to fill space. Reuse entity identities consistently.
- Output valid JSON, no markdown fences, no extra commentary.`;
  const user = `SOURCE SENTENCE:\n${text}\n\nEXISTING KNOWLEDGE (context only; do not treat as proof of this sentence):\n${knowledgeText}\n\nReturn the JSON interpretation now.`;
  return [{role:'system',content:system},{role:'user',content:user}];
}


async function requestModel(base, model, messages, phase='generation') {
  const budgets = phase === 'review' ? [4096, 8192] : GENERATION_TOKEN_BUDGETS;
  const attempts = [];
  for (let index = 0; index < budgets.length; index++) {
    const numPredict = budgets[index];
    const payload = { model, messages, stream:false, format:'json', options:{...MODEL_GENERATION_OPTIONS, num_predict:numPredict} };
    const attemptStartedAt = new Date().toISOString();
    const attemptStartedMs = Date.now();
    let result;
    try {
      result = await ollamaFetch(base, '/api/chat', {
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)
      }, phase);
    } catch (error) {
      const diagnostic = error.diagnostic || {category:classifyGenerationFailure(error),originalErrorMessage:error.message};
      attempts.push({
        phase, attempt:index+1, requested_num_predict:numPredict,
        status:'failed', failure_category:diagnostic.category || classifyGenerationFailure(error),
        error:error.message, diagnostic
      });
      error.generationAttempts = attempts;
      error.failureCategory = diagnostic.category || classifyGenerationFailure(error);
      throw error;
    }
    const content = result.message && typeof result.message.content === 'string' ? result.message.content : '';
    const metrics = {
      phase, attempt:index+1, requested_num_predict:numPredict, status:'response_received',
      done:result.done ?? null, done_reason:result.done_reason ?? null,
      requestStartedAt:attemptStartedAt, requestEndedAt:new Date().toISOString(),
      request_duration_ms:Date.now()-attemptStartedMs,
      prompt_eval_count:Number.isFinite(Number(result.prompt_eval_count))?Number(result.prompt_eval_count):null,
      eval_count:Number.isFinite(Number(result.eval_count))?Number(result.eval_count):null,
      prompt_eval_duration_ms:Number.isFinite(Number(result.prompt_eval_duration))?Math.round(Number(result.prompt_eval_duration)/1e6):null,
      eval_duration_ms:Number.isFinite(Number(result.eval_duration))?Math.round(Number(result.eval_duration)/1e6):null,
      total_duration_ms:Number.isFinite(Number(result.total_duration))?Math.round(Number(result.total_duration)/1e6):null,
      tokens_per_second:Number.isFinite(Number(result.eval_count)) && Number(result.eval_duration)>0?Number((Number(result.eval_count)/(Number(result.eval_duration)/1e9)).toFixed(2)):null,
      response_chars:content.length
    };
    attempts.push(metrics);
    const exhausted = result.done_reason === 'length' || result.done === false;
    if (exhausted) {
      metrics.failure_category = 'output_token_limit';
      metrics.rawModelResponse = content;
      metrics.retry_action = index < budgets.length - 1 ? 'increase_output_budget' : 'reject_truncated_response';
    }
    if (exhausted && index < budgets.length - 1) continue;
    if (exhausted) {
      const error = new Error(`The model repeatedly reached the output-token resource boundary during ${phase}; no truncated proposal was accepted.`);
      error.modelOutput = content; error.generationAttempts = attempts;
      error.failureCategory = 'output_token_limit';
      throw error;
    }
    if (!content.trim()) {
      const error = new Error(`The model returned an empty response during ${phase}.`);
      error.generationAttempts = attempts;
      error.failureCategory = 'empty_response';
      throw error;
    }
    return { content, metrics:attempts };
  }
  throw new Error(`No complete model response was produced during ${phase}.`);
}

async function reviewProposal(base, model, sourceText, proposal, diagnostics, generationTrace, generationArtifacts) {
  let response;
  try {
    response = await requestModel(base, model, buildReviewMessages(sourceText, proposal, diagnostics), 'review');
    generationTrace.push(...response.metrics);
    const artifact = { phase:'review', status:'response_received', rawModelResponse:response.content };
    generationArtifacts.push(artifact);
    try {
      const report = parseModelJson(response.content);
      artifact.parseStatus = 'valid_json';
      return normalizeReviewerReport(report);
    } catch (parseError) {
      artifact.parseStatus = 'invalid_json';
      artifact.parseError = parseError.message;
      return { status:'unavailable', overallAssessment:'unknown', issues:[], error:`Reviewer returned invalid JSON: ${parseError.message}` };
    }
  } catch (error) {
    if (Array.isArray(error.generationAttempts)) generationTrace.push(...error.generationAttempts);
    generationArtifacts.push({
      phase:'review', status:'request_failed',
      failureCategory:error.failureCategory || classifyGenerationFailure(error),
      error:error.message, diagnostic:error.diagnostic || null,
      partialModelResponse:error.modelOutput ?? null
    });
    return { status:'unavailable', overallAssessment:'unknown', issues:[], error:error.message, failureCategory:error.failureCategory || classifyGenerationFailure(error) };
  }
}

async function generateCorrectedProposal(base, model, sourceText, knowledge) {
  const generationTrace = [];
  const generationArtifacts = [];
  let proposal = null;
  let rawCandidate = null;
  let diagnostics = [];
  let initialDiagnostics = [];
  let initialReviewer = {status:'not_run', overallAssessment:'unknown', issues:[]};
  let reviewer = {status:'not_run', overallAssessment:'unknown', issues:[]};
  let repairRounds = 0;
  let parseFailure = null;

  const requestTracked = async (phase, messages) => {
    try {
      const response = await requestModel(base, model, messages, phase);
      generationTrace.push(...response.metrics);
      generationArtifacts.push({phase,status:'response_received',rawModelResponse:response.content});
      return response;
    } catch (error) {
      if (Array.isArray(error.generationAttempts)) generationTrace.push(...error.generationAttempts);
      generationArtifacts.push({
        phase, status:'request_failed',
        failureCategory:error.failureCategory || classifyGenerationFailure(error),
        error:error.message, diagnostic:error.diagnostic || null,
        partialModelResponse:error.modelOutput ?? null
      });
      throw error;
    }
  };
  const failureAudit = (status, error) => ({
    status, repairRounds, initialDiagnostics, initialReviewer,
    finalDiagnostics:diagnostics, reviewer,
    reviewerMode:'same_model_second_pass', generation:generationTrace,
    generationArtifacts, parseFailure,
    failure:error ? {
      category:error.failureCategory || classifyGenerationFailure(error),
      message:error.message, diagnostic:error.diagnostic || null
    } : null,
    resourceNote:'Output-token budgets are adaptive runtime safeguards. They do not impose limits on semantic item counts.'
  });

  let first;
  try {
    first = await requestTracked('generation', buildMessages(sourceText, knowledge));
  } catch (error) {
    error.correctionAudit = failureAudit('generation_request_failed', error);
    throw error;
  }
  try { proposal = parseModelJson(first.content); }
  catch (error) {
    parseFailure = error.message; rawCandidate = first.content;
    generationArtifacts[generationArtifacts.length-1].parseStatus = 'invalid_json';
    generationArtifacts[generationArtifacts.length-1].parseError = error.message;
    diagnostics = [{code:'INVALID_JSON',severity:'error',location:'$',problem:'The model response was not valid JSON.',recommendedCorrection:'Return one complete valid JSON object matching the USG proposal structure.'}];
  }
  if (proposal) {
    generationArtifacts[generationArtifacts.length-1].parseStatus = 'valid_json';
    diagnostics = diagnoseProposal(proposal, sourceText);
    reviewer = await reviewProposal(base, model, sourceText, proposal, diagnostics, generationTrace, generationArtifacts);
  }
  initialDiagnostics = diagnostics.map(x => ({...x}));
  initialReviewer = {...reviewer, issues:[...(reviewer.issues || [])]};

  while (repairRounds < MAX_REPAIR_ROUNDS && (parseFailure || shouldRepair(diagnostics, reviewer))) {
    repairRounds += 1;
    const candidate = proposal || {unparsedModelOutput:String(rawCandidate || '')};
    let response;
    try {
      response = await requestTracked('repair', buildRepairMessages(sourceText, candidate, diagnostics, reviewer));
    } catch (error) {
      error.correctionAudit = failureAudit('repair_request_failed', error);
      throw error;
    }
    try {
      proposal = parseModelJson(response.content);
      generationArtifacts[generationArtifacts.length-1].parseStatus = 'valid_json';
      parseFailure = null; rawCandidate = null;
    } catch (error) {
      generationArtifacts[generationArtifacts.length-1].parseStatus = 'invalid_json';
      generationArtifacts[generationArtifacts.length-1].parseError = error.message;
      proposal = null; rawCandidate = response.content; parseFailure = error.message;
      diagnostics = [{code:'REPAIR_INVALID_JSON',severity:'error',location:'$',problem:'The repair response was not valid JSON.',recommendedCorrection:'Return one complete valid JSON object, preserving the entire source-grounded semantic representation.'}];
      reviewer = {status:'not_run',overallAssessment:'unknown',issues:[]};
      continue;
    }
    diagnostics = diagnoseProposal(proposal, sourceText);
    reviewer = await reviewProposal(base, model, sourceText, proposal, diagnostics, generationTrace, generationArtifacts);
  }

  if (!proposal) {
    const error = new Error('USG could not obtain a parseable semantic proposal after targeted repair. The incomplete response was not accepted.');
    error.failureCategory = 'proposal_repair_exhausted';
    error.diagnostic = {
      phase:'proposal_finalization', category:error.failureCategory,
      repairRounds, parseFailure, responseReceived:generationArtifacts.some(x=>x.status==='response_received'),
      lastGenerationArtifact:generationArtifacts[generationArtifacts.length-1] || null
    };
    error.correctionAudit = failureAudit('unrepaired', error);
    throw error;
  }
  const requiredArrays = ['claims','entities','mentions','claimRelations','unresolved'];
  const missingContractFields = requiredArrays.filter(key => !Array.isArray(proposal[key]));
  if (missingContractFields.length) {
    const error = new Error(`USG could not repair required proposal fields: ${missingContractFields.join(', ')}. The proposal was not accepted.`);
    error.failureCategory = 'proposal_contract_failure';
    error.diagnostic = {
      phase:'proposal_contract_validation', category:error.failureCategory,
      missingFields:missingContractFields, repairRounds, responseReceived:true,
      proposalClaimCount:Array.isArray(proposal.claims)?proposal.claims.length:null,
      proposalEntityCount:Array.isArray(proposal.entities)?proposal.entities.length:null
    };
    error.correctionAudit = failureAudit('unrepaired', error);
    error.correctionAudit.missingContractFields = missingContractFields;
    throw error;
  }
  const remainingErrors = diagnostics.filter(x => x.severity === 'error');
  const reviewerErrors = reviewer.status === 'completed' ? reviewer.issues.filter(x => x.severity === 'error' || x.severity === 'critical') : [];
  const reviewerConclusive = reviewer.status === 'completed' && reviewer.overallAssessment === 'SOUND';
  const reviewerUncertain = reviewer.status === 'completed' && !reviewerConclusive;
  const status = remainingErrors.length || reviewerErrors.length || reviewerUncertain
    ? 'needs_review'
    : (repairRounds ? 'repaired' : (reviewerConclusive ? 'reviewed' : 'review_unavailable'));
  return {
    proposal,
    correctionAudit:{
      status,repairRounds,initialDiagnostics,initialReviewer,finalDiagnostics:diagnostics,
      reviewerMode:'same_model_second_pass',reviewerStatus:reviewer.status,
      reviewerAssessment:reviewer.overallAssessment,reviewerIssues:reviewer.issues,
      reviewerError:reviewer.error||null,generation:generationTrace,generationArtifacts,
      resourceNote:'Output-token budgets are adaptive runtime safeguards. They do not impose limits on semantic item counts.'
    }
  };
}

const server = http.createServer(async (req, res) => {
  const requestUrl = new URL(req.url, `http://${HOST}:${PORT}`);
  const pathname = decodeURIComponent(requestUrl.pathname);
  if (req.method === 'GET' && pathname === '/api/health') return send(res,200,{ok:true,runtime:'node-local-bridge',version:'0.5.4',modelTimeoutMs:MODEL_TIMEOUT_MS});

  if (req.method === 'GET' && pathname === '/api/models') {
    try {
      const base = localOllamaBase(requestUrl.searchParams.get('base'));
      const data = await ollamaFetch(base,'/api/tags');
      const models = Array.isArray(data.models) ? data.models.map(m=>m.name).filter(Boolean) : [];
      return send(res,200,{ok:true,models});
    } catch (error) { return send(res,502,{ok:false,error:error.message}); }
  }

  if (req.method === 'POST' && pathname === '/api/interpret') {
    try {
      const body = await readJson(req);
      const text = String(body.text || '').trim();
      const model = String(body.model || '').trim();
      if (!text) return send(res,400,{error:'Source text is required.'});
      if (text.length > 12000) return send(res,413,{error:'Please keep the sentence or passage below 12,000 characters for this prototype.'});
      if (!model) return send(res,400,{error:'Choose an installed local model first.'});
      const base = localOllamaBase(body.ollamaUrl);
      const corrected = await generateCorrectedProposal(base,model,text,body.knowledge);
      return send(res,200,{ok:true,result:corrected.proposal,model,correctionAudit:corrected.correctionAudit});
    } catch (error) {
      return send(res,502,{ok:false,error:error.message,correctionAudit:error.correctionAudit||null,generationAttempts:error.generationAttempts||null,modelOutput:error.modelOutput??null,failureCategory:error.failureCategory||null,diagnostic:error.diagnostic||null});
    }
  }

  if (req.method !== 'GET' && req.method !== 'HEAD') return send(res,405,{error:'Method not allowed.'});
  const requested = pathname === '/' ? '/index.html' : pathname;
  const filePath = path.resolve(ROOT, `.${requested}`);
  if (!filePath.startsWith(ROOT + path.sep) && filePath !== path.join(ROOT,'index.html')) return send(res,403,{error:'Forbidden.'});
  fs.stat(filePath,(statErr,stat)=>{
    if (statErr || !stat.isFile()) return send(res,404,{error:'File not found.'});
    const contentType = MIME[path.extname(filePath).toLowerCase()] || 'application/octet-stream';
    res.writeHead(200,{'Content-Type':contentType,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});
    if (req.method === 'HEAD') return res.end();
    const stream=fs.createReadStream(filePath);
    stream.on('error',()=>{if(!res.headersSent)send(res,500,{error:'Could not read file.'});else res.destroy();});
    stream.pipe(res);
  });
});

server.listen(PORT,HOST,()=>{
  console.log('');
  console.log('  USG Semantic Workbench v0.5.4');
  console.log(`  Model request timeout: ${MODEL_TIMEOUT_MS} ms`);
  console.log(`  Open: http://${HOST}:${PORT}`);
  console.log('  Local bridge: ready');
  console.log('  Ollama: optional (configure it in the Local model page)');
  console.log('  Press Ctrl+C to stop.');
  console.log('');
});
server.on('error',error=>{
  if(error.code==='EADDRINUSE') console.error(`Port ${PORT} is already in use. Close the other server or set USG_PORT to a different port.`);
  else console.error(error);
  process.exitCode=1;
});
