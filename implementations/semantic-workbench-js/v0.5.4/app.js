'use strict';

const STORAGE_KEY = 'usg_semantic_workbench_v02';
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function uid(prefix = 'id') {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`;
}
function cleanLabel(value) {
  return String(value ?? '').trim().replace(/[.!?,;:]+$/g, '').replace(/\s+/g, ' ');
}
function norm(value) { return cleanLabel(value).toLocaleLowerCase(); }
function normalizeEntity(value) { return cleanLabel(value).replace(/^(?:a|an|the)\s+/i, '').trim(); }
function detectReference(value) {
  const match = String(value ?? '').trim().match(/^(a|an|the)\s+/i);
  if (!match) return 'unmarked';
  return match[1].toLowerCase() === 'the' ? 'definite' : 'indefinite';
}
function cap(value) { return cleanLabel(value).replace(/\b\w/g, c => c.toUpperCase()); }
function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[ch]));
}
function nowIso() { return new Date().toISOString(); }

function buildClaim(subject, predicate, object, options = {}) {
  return {
    id: options.id || uid('k'),
    subject: { text: normalizeEntity(subject), surfaceText: cleanLabel(subject), type: options.subjectType || 'unknown', reference: options.subjectReference || detectReference(subject), entityId: options.subjectEntityId || null },
    predicate: String(predicate || 'RELATED_TO').toUpperCase(),
    object: options.objectIsNull ? null : { text: normalizeEntity(object), surfaceText: cleanLabel(object), type: options.objectType || 'unknown', reference: options.objectReference || detectReference(object), entityId: options.objectEntityId || null },
    polarity: options.polarity || 'positive',
    tense: options.tense || 'present',
    modality: options.modality || 'asserted',
    modalScope: options.modalScope || null,
    time: options.time || null,
    quantifierScope: options.quantifierScope || null,
    comparisonFrame: options.comparisonFrame || null,
    eventAttributes: options.eventAttributes || [],
    conditions: Array.isArray(options.conditions) ? options.conditions : [],
    causalLinks: Array.isArray(options.causalLinks) ? options.causalLinks : [],
    completeness: options.completeness && typeof options.completeness === 'object'
      ? { status: options.completeness.status || 'complete', missingRoles: Array.isArray(options.completeness.missingRoles) ? options.completeness.missingRoles : [], note: options.completeness.note || '' }
      : { status: 'complete', missingRoles: [], note: '' },
    evidence: options.evidence || { sourceText: options.sourceText || '', quote: options.quote || options.sourceText || '', start: 0, end: (options.sourceText || options.quote || '').length, verified: true },
    provenance: options.provenance || 'demo_seed',
    sourceKind: options.sourceKind || 'observation',
    ruleId: options.ruleId || null,
    confidence: Number.isFinite(options.confidence) ? options.confidence : 1,
    createdAt: options.createdAt || nowIso(),
    note: options.note || ''
  };
}

function createInitialState() {
  const seed = [
    buildClaim('Bird', 'SUBCLASS_OF', 'Animal', { id:'k1', subjectType:'class', objectType:'class', sourceText:'Seed observation: Birds are animals.', provenance:'demo_seed' }),
    buildClaim('Sparrow', 'SUBCLASS_OF', 'Bird', { id:'k2', subjectType:'class', objectType:'class', sourceText:'Seed observation: A sparrow is a bird.', provenance:'demo_seed' }),
    buildClaim('Tweety', 'INSTANCE_OF', 'Sparrow', { id:'k3', subjectType:'individual', objectType:'class', sourceText:'Seed observation: Tweety is a sparrow.', provenance:'demo_seed' }),
    buildClaim('Thermometer', 'MEASURES', 'Temperature', { id:'k4', subjectType:'instrument', objectType:'measurable_property', sourceText:'Seed observation: A thermometer measures temperature.', provenance:'demo_seed' }),
    buildClaim('Scale', 'MEASURES', 'Weight', { id:'k5', subjectType:'instrument', objectType:'measurable_property', sourceText:'Seed observation: A scale measures weight.', provenance:'demo_seed' }),
    buildClaim('Speedometer', 'MEASURES', 'Speed', { id:'k6', subjectType:'instrument', objectType:'measurable_property', sourceText:'Seed observation: A speedometer measures speed.', provenance:'demo_seed' })
  ];
  return {
    schemaVersion: 2,
    claims: seed,
    patterns: [
      { id:'p1', predicate:'MEASURES', schema:'MEASURES(instrument → measurable_property)', description:'An instrument measures a property or quantity.', supportIds:['k4','k5','k6'], supportCount:3, accepted:true, origin:'starter_schema', acceptedAt:nowIso() },
      { id:'p2', predicate:'SUBCLASS_OF', schema:'SUBCLASS_OF(class → class)', description:'A class can be related to a more general class.', supportIds:['k1','k2'], supportCount:2, accepted:true, origin:'starter_schema', acceptedAt:nowIso() }
    ],
    derived: [],
    relations: [],
    lastRunAt: null,
    interpretationHistory: []
  };
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return createInitialState();
    const parsed = JSON.parse(raw);
    if (parsed.schemaVersion !== 2 || !Array.isArray(parsed.claims) || !Array.isArray(parsed.patterns)) return createInitialState();
    parsed.derived = Array.isArray(parsed.derived) ? parsed.derived : [];
    parsed.relations = Array.isArray(parsed.relations) ? parsed.relations : [];
    parsed.interpretationHistory = Array.isArray(parsed.interpretationHistory) ? parsed.interpretationHistory : [];
    return parsed;
  } catch (error) {
    console.warn('Could not load saved workbench data; using demo data.', error);
    return createInitialState();
  }
}
let state = loadState();
let currentInterpretation = null;
let localRuntimeAvailable = false;
let ollamaAvailable = false;
let installedModels = [];
let toastTimer = null;
let latestBatchExport = null;
let batchRunning = false;

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    refreshMetrics();
  } catch (error) {
    showToast('Could not save to browser storage. Export your data for backup.', true);
    console.error(error);
  }
}
function showToast(message, isError = false) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.classList.toggle('error', isError);
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 3000);
}
function relationLabel(predicate) {
  const labels = { SUBCLASS_OF:'SUBCLASS_OF', INSTANCE_OF:'INSTANCE_OF', MEASURES:'MEASURES', NEEDS:'NEEDS', PART_OF:'PART_OF', CAUSES:'CAUSES', HAS_PROPERTY:'HAS_PROPERTY', DIFFER:'DIFFER', CHANGE:'CHANGE' };
  return labels[predicate] || String(predicate || 'RELATED_TO').toUpperCase();
}
function entityTypeFor(predicate, side) {
  const map = {
    SUBCLASS_OF: { subject:'class', object:'class' }, INSTANCE_OF: { subject:'individual', object:'class' },
    MEASURES: { subject:'instrument', object:'measurable_property' }, NEEDS:{subject:'agent_or_topic',object:'artifact_or_resource'},
    PART_OF:{subject:'entity',object:'entity'}, CAUSES:{subject:'event_or_cause',object:'event_or_effect'}
  };
  return map[predicate]?.[side] || 'unknown';
}
function allEntities() {
  const map = new Map();
  for (const claim of state.claims) {
    if (claim.subject?.text) map.set(norm(claim.subject.text), { text:claim.subject.text, type:claim.subject.type || 'unknown' });
    if (claim.object?.text) map.set(norm(claim.object.text), { text:claim.object.text, type:claim.object.type || 'unknown' });
  }
  return [...map.values()];
}
function refreshMetrics() {
  const ids = ['metric-claims','metric-concepts','metric-patterns','metric-derived'];
  if (!$('#metric-claims')) return;
  $( '#metric-claims').textContent = state.claims.length;
  $('#metric-concepts').textContent = allEntities().length;
  $('#metric-patterns').textContent = state.patterns.filter(p => p.accepted).length;
  $('#metric-derived').textContent = state.derived.length;
}
function navigate(viewName) {
  const allowed = ['overview','interpret','knowledge','reasoning','patterns','model'];
  if (!allowed.includes(viewName)) return;
  $$('.view').forEach(view => view.classList.toggle('active', view.id === `view-${viewName}`));
  $$('.nav-item').forEach(button => button.classList.toggle('active', button.dataset.view === viewName));
  const names = { overview:'Overview', interpret:'Interpret language', knowledge:'Knowledge base', reasoning:'Reasoning lab', patterns:'Pattern library', model:'Local model' };
  $('#page-name').textContent = names[viewName];
  if (viewName === 'knowledge') renderKnowledge();
  if (viewName === 'patterns') renderPatterns();
  if (viewName === 'reasoning') renderReasoning();
  window.scrollTo({ top:0, behavior:'smooth' });
}

// ---------------------- Interpretation: explicit local patterns ----------------------
function makeEvidence(sourceText) {
  return { sourceText, quote:sourceText, start:0, end:sourceText.length, verified:true };
}
function parseCondition(text, marker) {
  const phrase = cleanLabel(text);
  let match;
  if ((match = phrase.match(/^(.+?)\s+(?:are|is)\s+different$/i))) {
    return { marker:marker.toLowerCase(), proposition:{ subject:normalizeEntity(match[1]), predicate:'DIFFER', object:null }, scope:'main_relation', effect:marker.toLowerCase()==='unless'?'exception_to_assertion':'condition_for_assertion', consequence:marker.toLowerCase()==='unless'?'unspecified':'assertion_applies_when_condition_holds', evidenceText:phrase };
  }
  if ((match = phrase.match(/^(.+?)\s+differ$/i))) {
    return { marker:marker.toLowerCase(), proposition:{ subject:normalizeEntity(match[1]), predicate:'DIFFER', object:null }, scope:'main_relation', effect:marker.toLowerCase()==='unless'?'exception_to_assertion':'condition_for_assertion', consequence:marker.toLowerCase()==='unless'?'unspecified':'assertion_applies_when_condition_holds', evidenceText:phrase };
  }
  if ((match = phrase.match(/^(.+?)\s+(?:changes|change)$/i))) {
    return { marker:marker.toLowerCase(), proposition:{ subject:normalizeEntity(match[1]), predicate:'CHANGE', object:null }, scope:'main_relation', effect:marker.toLowerCase()==='unless'?'exception_to_assertion':'condition_for_assertion', consequence:marker.toLowerCase()==='unless'?'unspecified':'assertion_applies_when_condition_holds', evidenceText:phrase };
  }
  return null;
}
function detectTense(sentence) {
  if (/\b(did|was|were|had)\b/i.test(sentence)) return 'past';
  if (/\b(will|shall)\b/i.test(sentence)) return 'future';
  return 'present';
}
function detectModality(sentence) {
  if (/\b(might|may|could|perhaps|possibly)\b/i.test(sentence)) return 'possible';
  if (/\b(must|necessarily)\b/i.test(sentence)) return 'necessary';
  if (/\b(should|ought to)\b/i.test(sentence)) return 'obligatory';
  if (/\b(can|able to)\b/i.test(sentence)) return 'possible_or_ability';
  return 'asserted';
}
function localInterpretCore(sentence) {
  const original = sentence.trim();
  const text = cleanLabel(original);
  if (!text) return { ok:false, engine:'rule_fallback', intent:'unknown', interpretation:'Enter a sentence to analyze.', claims:[], unresolved:['No source text was provided.'], sourceText:original };
  const evidence = makeEvidence(original);
  let match;
  const common = { evidence, provenance:'local_rule', sourceKind:'interpreted_text', confidence:0.86, note:'Matched an explicit local starter pattern. This is a candidate interpretation, not proof of truth.' };

  // v0.4: quantifier negation has scope over the universal statement, not over each customer.
  match = text.match(/^not\s+every\s+(.+?)\s+needs?\s+(.+)$/i);
  if (match) {
    const claim = buildClaim(match[1], 'NEEDS', match[2], { ...common, polarity:'positive', tense:'present', modality:'asserted', subjectType:'agent_or_topic', objectType:'artifact_or_resource' });
    return { ok:true, engine:'rule_fallback', intent:'ASSERTION', interpretation:'The sentence denies that every customer (or member of the stated class) needs the object. It does not state that no member needs it.', claims:[claim], explanations:[], unresolved:[], warnings:['Negation scopes over the universal quantifier; do not reinterpret this as “no customer needs the tool.”'], sourceText:original };
  }

  // v0.4: simple conditional with an independently represented antecedent proposition.
  match = text.match(/^if\s+(.+?),\s*(.+)$/i);
  if (match) {
    const conditionText = cleanLabel(match[1]);
    const effectText = cleanLabel(match[2]);
    const conditionMatch = conditionText.match(/^(.+?)\s+(increase|increases|increased|change|changes|changed|differ|differs|differed)$/i);
    const effectMatch = effectText.match(/^(.+?)\s+(?:will\s+)?(stop\s+using|stops\s+using|stopped\s+using|need|needs|use|uses)\s+(.+)$/i);
    if (conditionMatch && effectMatch) {
      const conditionVerb = conditionMatch[2].toLowerCase();
      const conditionPredicate = conditionVerb.startsWith('increas') ? 'INCREASE' : (conditionVerb.startsWith('change') ? 'CHANGE' : 'DIFFER');
      const conditionTense = /(?:ed)$/.test(conditionVerb) ? 'past' : 'present';
      const effectVerb = effectMatch[2].toLowerCase();
      const effectPredicate = effectVerb.includes('stop') ? 'STOP_USING' : (effectVerb.startsWith('need') ? 'NEEDS' : 'USES');
      const effectTense = /\bwill\s+/i.test(effectText) ? 'future' : (/stopped|\bused\b/i.test(effectVerb) ? 'past' : 'present');
      const conditionEntity = normalizeEntity(conditionMatch[1]);
      const effectSubject = normalizeEntity(effectMatch[1]);
      const effectObject = cleanLabel(effectMatch[3]);
      const condition = {
        id:uid('cond'), marker:'if', scope:'claim', effect:'condition_for_assertion',
        proposition:{ subject:{text:conditionEntity,surfaceText:conditionMatch[1],type:'unknown',reference:detectReference(conditionMatch[1]),entityId:null}, predicate:conditionPredicate, object:null, polarity:'positive', tense:conditionTense, modality:'asserted' },
        consequence:'the effect proposition is presented as conditional on the antecedent; no occurrence is asserted',
        evidenceText:conditionText, evidence:buildSourceEvidence(original, original.toLowerCase().indexOf(conditionText.toLowerCase()), original.toLowerCase().indexOf(conditionText.toLowerCase())+conditionText.length)
      };
      const claim = buildClaim(effectSubject,effectPredicate,effectObject,{...common,polarity:'positive',tense:effectTense,modality:'asserted',conditions:[condition],subjectType:'agent_or_topic'});
      return {ok:true,engine:'rule_fallback',intent:'ASSERTION',interpretation:'A conditional relation: the effect proposition is not asserted unconditionally; it is linked to a separately represented IF antecedent.',claims:[claim],explanations:[],unresolved:[],warnings:['The IF antecedent and consequent have independent tense fields. The conditional sentence does not assert that the antecedent actually occurred.'],sourceText:original};
    }
    return {ok:true,engine:'rule_fallback',intent:'ASSERTION',interpretation:'A conditional marker was detected, but its propositions do not match a supported local frame.',claims:[],explanations:[],unresolved:[`Unsupported conditional construction: “${conditionText}” → “${effectText}”.`],warnings:['The local interpreter does not guess the meaning or scope of an unsupported conditional.'],sourceText:original};
  }

  // v0.4: keep both clauses in a contrastive pair; the pronoun in the second clause is resolved locally.
  match = text.match(/^(.+?)\s+needs?\s+(.+?),\s*but\s+(?:does\s+not\s+need|doesn't\s+need|do\s+not\s+need|don't\s+need)\s+(it|them|that|those)$/i);
  if (match) {
    const subject = cleanLabel(match[1]); const object = cleanLabel(match[2]);
    const first = buildClaim(subject,'NEEDS',object,{...common,polarity:'positive',tense:'present',subjectType:'agent_or_topic'});
    const second = buildClaim(subject,'NEEDS',object,{...common,polarity:'negative',tense:'present',subjectType:'agent_or_topic',objectReference:detectReference(object),note:'The pronoun in the second clause is resolved to the object of the first clause.'});
    return {ok:true,engine:'rule_fallback',intent:'ASSERTION',interpretation:'Two propositions are preserved: a positive NEEDS claim followed by a negative NEEDS claim. Neither is discarded.',claims:[first,second],explanations:[],unresolved:[],warnings:['The two same-scope propositions have opposite polarity and are marked as a contradiction candidate for review.'],sourceText:original};
  }

  // v0.4: retain the temporal change expressed by “needed … but no longer needs it”.
  match = text.match(/^(.+?)\s+needed\s+(.+?)\s+but\s+no\s+longer\s+needs?\s+(it|them|that|those)$/i);
  if (match) {
    const first = buildClaim(match[1],'NEEDS',match[2],{...common,polarity:'positive',tense:'past',subjectType:'agent_or_topic'});
    const second = buildClaim(match[1],'NEEDS',match[2],{...common,polarity:'negative',tense:'present',subjectType:'agent_or_topic',note:'The pronoun refers to the object introduced in the earlier clause.'});
    return {ok:true,engine:'rule_fallback',intent:'ASSERTION',interpretation:'The sentence describes a temporal change: NEEDS was positive in the past and is negative in the present.',claims:[first,second],explanations:[],unresolved:[],warnings:['The claims have different temporal frames and are therefore not marked as a direct contradiction.'],sourceText:original};
  }

  // v0.4: a small two-sentence discourse frame with explicit pronoun and frequency slots.
  const discourseMatch = original.match(/^((?:the|a|an)\s+[^.!?]+?)\s+(bought|purchased|acquired)\s+((?:a|an|the)\s+[^.!?]+?)[.!?]\s*(he|she|they)\s+(uses?|use|used)\s+(it|them|that|those)(?:\s+(every\s+day|daily|every\s+week|weekly|every\s+month|monthly))?[.!?]?$/i);
  if (discourseMatch) {
    const antecedentSubject = cleanLabel(discourseMatch[1]); const antecedentObject = cleanLabel(discourseMatch[3]);
    const subjectEntityId = `e_${normalizeEntity(antecedentSubject).toLowerCase().replace(/[^a-z0-9]+/g,'_')}`;
    const objectEntityId = `e_${normalizeEntity(antecedentObject).toLowerCase().replace(/[^a-z0-9]+/g,'_')}`;
    const first = buildClaim(antecedentSubject,'BOUGHT',antecedentObject,{...common,tense:'past',subjectType:'agent_or_topic',subjectEntityId,objectEntityId});
    const second = buildClaim(antecedentSubject,'USES',antecedentObject,{...common,tense:/used/i.test(discourseMatch[5])?'past':'present',subjectType:'agent_or_topic',subjectEntityId,objectEntityId,note:`Pronouns “${discourseMatch[4]}” and “${discourseMatch[6]}” were resolved to the earlier subject and object.`});
    // Keep clause-local evidence text so time/frequency normalization cannot
    // accidentally inspect only the first clause of a multi-sentence input.
    first.sourceClauseText=`${antecedentSubject} ${discourseMatch[2]} ${antecedentObject}`;
    second.sourceClauseText=`${discourseMatch[4]} ${discourseMatch[5]} ${discourseMatch[6]}${discourseMatch[7] ? ` ${discourseMatch[7]}` : ''}`;
    const frequency = discourseMatch[7] ? cleanLabel(discourseMatch[7]) : null;
    if (frequency) second.eventAttributes = [{type:'frequency',value:frequency,normalizedValue:/every\s+day|daily/i.test(frequency)?'P1D':(/every\s+week|weekly/i.test(frequency)?'P1W':'P1M'),surfaceText:frequency,scope:'event'}];
    return {ok:true,engine:'rule_fallback',intent:'ASSERTION',interpretation:'Two linked discourse propositions are represented. The later pronouns are resolved to the earlier subject and object; the frequency phrase is stored as an event attribute.',claims:[first,second],explanations:[],unresolved:[],warnings:['Coreference resolution here uses a narrow, source-grounded English pattern. Review entity links before acceptance.'],sourceText:original};
  }

  // v0.4: stop-using plus a coreferential failure clause; cause remains source-attributed.
  match = text.match(/^(.+?)\s+stopped\s+using\s+(.+?)\s+because\s+it\s+failed$/i);
  if (match) {
    const subject = cleanLabel(match[1]); const object = cleanLabel(match[2]);
    const effect = buildClaim(subject,'STOP_USING',object,{...common,tense:'past',subjectType:'agent_or_topic'});
    const cause = buildClaim(object,'FAILS',null,{...common,objectIsNull:true,tense:'past',subjectType:'artifact_or_resource',evidence:buildSourceEvidence(original,original.toLowerCase().indexOf('because')+8,original.length),ruleId:'R-COREFERENCE-CAUSE',provenance:'local_rule',note:'“It” is resolved to the tool introduced in the effect clause.'});
    const start = original.toLowerCase().indexOf('because');
    const link = {id:uid('x'),type:'CAUSE',causeClaimId:cause.id,effectClaimId:effect.id,attribution:'source_asserted',evidenceText:cleanLabel(original.slice(start+8)),evidence:buildSourceEvidence(original,start,original.length),note:'The source presents the failure as the reason for stopping use; objective causality is not independently verified.'};
    effect.causalLinks=[link];
    return {ok:true,engine:'rule_fallback',intent:'ASSERTION',interpretation:'The main event and its because-clause are separate propositions. The pronoun in the cause clause is linked to the tool.',claims:[effect,cause],explanations:[link],unresolved:[],warnings:['The causal link is source-asserted, not independently proven. The pronoun resolution is based on the explicit local pattern.'],sourceText:original};
  }

  // Needs + negation/modality + simple condition. The exception is represented separately.
  const needsMatch = text.match(/^(.+?)\s+(does\s+not\s+need|doesn't\s+need|do\s+not\s+need|don't\s+need|did\s+not\s+need|didn't\s+need|needs|need|may\s+need|might\s+need|must\s+need)\s+(.+)$/i);
  if (needsMatch) {
    let subject = cleanLabel(needsMatch[1]);
    let verb = needsMatch[2].toLowerCase();
    let tail = cleanLabel(needsMatch[3]);
    let condition = null;
    let parsedCause = null;
    let unsupportedCauseText = null;
    let causeClause = null;
    const conditionMatch = tail.match(/\s+(unless|if|when|because)\s+(.+)$/i);
    if (conditionMatch) {
      const marker = conditionMatch[1].toLowerCase();
      tail = cleanLabel(tail.slice(0, conditionMatch.index));
      if (marker === 'because') {
        causeClause = extractBecauseClause(original);
        parsedCause = parseBecauseProposition({ text:cleanLabel(conditionMatch[2]) });
        if (!parsedCause) unsupportedCauseText = cleanLabel(conditionMatch[2]);
      } else {
        condition = parseCondition(conditionMatch[2], marker);
        if (!condition) {
          return { ok:true, engine:'rule_fallback', intent:'ASSERTION', interpretation:'A NEEDS relationship was detected, but the condition could not be safely represented. No semantic claim was created.', claims:[], unresolved:[`Unsupported condition phrase: “${cleanLabel(conditionMatch[2])}”. The condition is preserved in the source text but its scope is not interpreted.`], sourceText:original, warnings:['The local pattern interpreter does not guess the meaning of unsupported condition phrases.'] };
        }
      }
    }
    const negative = /not|n't/.test(verb);
    const clauseTense = detectClaimTense(original, subject);
    const tense = verb.startsWith('did') ? 'past' : (['past','present','future'].includes(clauseTense) ? clauseTense : 'present');
    const modality = /^(may|might|must)/.test(verb) ? (verb.startsWith('must')?'necessary':'possible') : 'asserted';
    const claim = buildClaim(subject, 'NEEDS', tail, { ...common, polarity:negative?'negative':'positive', tense, modality, conditions:condition?[condition]:[], subjectType:'agent_or_topic', objectType:'artifact_or_resource' });
    const explanation = negative
      ? `The sentence proposes a negative NEEDS relation: ${subject} does not need ${tail}.`
      : `The sentence proposes a NEEDS relation: ${subject} ${verb} ${tail}.`;
    const conditionText = condition ? (condition.marker==='unless'
      ? `The negative assertion has an exception when “${condition.evidenceText}”. The sentence does not explicitly state what happens in that exception case.`
      : `The NEEDS assertion is conditioned on “${condition.evidenceText}”.`) : '';
    const claims = [claim];
    const explanations = [];
    const unresolved = [];
    const warnings = condition?.marker==='unless' ? ['An “unless” clause is preserved as an exception; the exception outcome is deliberately left unspecified.'] : [];
    if (parsedCause) {
      const causeEvidence = causeClause || { text:cleanLabel(conditionMatch[2]), start:original.indexOf(conditionMatch[2]), end:original.indexOf(conditionMatch[2])+conditionMatch[2].length, markerStart:original.toLowerCase().indexOf('because') };
      const causeIsUnderspecified = false;
      const causeCompleteness = { status:'complete', missingRoles:[], note:'' };
      const causeClaim = buildClaim(parsedCause.subject, parsedCause.predicate, parsedCause.object, {
        subjectType:'unknown', objectIsNull:true, completeness:causeCompleteness, polarity:'positive', tense:parsedCause.tense, modality:'asserted',
        evidence:buildSourceEvidence(original,causeEvidence.start,causeEvidence.end), provenance:'local_rule', sourceKind:'interpreted_text',
        ruleId:'R-BECAUSE-CLAUSE', confidence:0.86, note:causeCompleteness.note || 'Parsed from the explicit “because” clause.'
      });
      claims.push(causeClaim);

      const link = { id:uid('x'), type:'CAUSE', causeClaimId:causeClaim.id, effectClaimId:claim.id, attribution:'source_asserted', evidenceText:causeEvidence.text, evidence:buildSourceEvidence(original,causeEvidence.markerStart,causeEvidence.end), note:'The source sentence presents the cause claim as the reason for the effect claim; this relation is not independently verified as an objective cause.' };
      claim.causalLinks = [link];
      explanations.push(link);
      warnings.push('A source-explicit “because” clause was represented as a separate claim and a source-attributed causal link; this does not independently prove causation.');
    } else if (unsupportedCauseText) {
      unresolved.push(`The “because” clause “${unsupportedCauseText}” was preserved but its proposition could not be parsed safely.`);
      warnings.push('The causal clause was not converted into a claim because its proposition pattern is unsupported.');
    }
    return { ok:true, engine:'rule_fallback', intent:'ASSERTION', interpretation:[explanation,conditionText].filter(Boolean).join(' '), claims, explanations, unresolved, warnings, sourceText:original };
  }

  // Explicit DISLIKE is kept distinct from negated LIKE (e.g. “does not dislike”).
  match = text.match(/^(.+?)\s+(does\s+not\s+dislike|doesn't\s+dislike|do\s+not\s+dislike|don't\s+dislike|dislikes?)\s+(.+)$/i);
  if (match) {
    const negative=/not|n't/i.test(match[2]);
    const claim=buildClaim(match[1],'DISLIKE',match[3],{...common,polarity:negative?'negative':'positive',tense:detectClaimTense(original,match[1])==='unknown'?'present':detectClaimTense(original,match[1])});
    return {ok:true,engine:'rule_fallback',intent:'ASSERTION',interpretation:'The source expresses DISLIKE with its own polarity. A negative DISLIKE proposition is not equivalent to a positive LIKE proposition.',claims:[claim],explanations:[],unresolved:[],warnings:[],sourceText:original};
  }

  // A standalone difference statement is interpretable even when its
  // comparison reference is implicit. The comparisonFrame records that
  // limitation for downstream comparison tasks without rejecting the claim.
  match = text.match(/^(.+?)\s+(was|were|is|are)\s+different$/i);
  if (match) {
    const tense = /^(was|were)$/i.test(match[2]) ? 'past' : 'present';
    const claim = buildClaim(match[1], 'DIFFER', null, { ...common, objectIsNull:true, tense, modality:'asserted', subjectType:'unknown', completeness:{status:'complete',missingRoles:[],note:'The source expresses difference, while the comparison reference remains context-dependent.'} });
    return { ok:true, engine:'rule_fallback', intent:'ASSERTION', interpretation:`The source states that ${cleanLabel(match[1])} was/is different. The comparison reference is not specified.`, claims:[claim], explanations:[], unresolved:[], warnings:['The proposition is interpretable, but calculations or explicit pairwise comparison require a comparison reference or comparison set.'], sourceText:original };
  }

  // MEASURES relation.
  match = text.match(/^(.+?)\s+measures?\s+(.+)$/i);
  if (match) {
    const claim = buildClaim(match[1], 'MEASURES', match[2], { ...common, subjectType:'instrument', objectType:'measurable_property', tense:detectTense(text), modality:detectModality(text) });
    return { ok:true, engine:'rule_fallback', intent:'ASSERTION', interpretation:`The sentence proposes that ${cleanLabel(match[1])} measures ${cleanLabel(match[2])}.`, claims:[claim], unresolved:[], warnings:[], sourceText:original };
  }

  // Explicit subclass constructions.
  const subclassPatterns = [
    { re:/^(.+?)\s+is\s+(?:a\s+)?kind\s+of\s+(.+)$/i, reverse:false },
    { re:/^(.+?)\s+is\s+(?:a\s+)?type\s+of\s+(.+)$/i, reverse:false },
    { re:/^(.+?)\s+is\s+(?:a\s+)?subclass\s+of\s+(.+)$/i, reverse:false },
    { re:/^(.+?)\s+is\s+classified\s+as\s+(?:a\s+)?(.+)$/i, reverse:false },
    { re:/^(.+?)\s+belongs\s+to\s+(?:the\s+)?(.+?)\s+family$/i, reverse:false },
    { re:/^(.+?)\s+belongs\s+to\s+(?:the\s+)?(.+)$/i, reverse:false },
    { re:/^(.+?)\s+includes?\s+(.+)$/i, reverse:true }
  ];
  for (const item of subclassPatterns) {
    match = text.match(item.re);
    if (match) {
      const subject = item.reverse ? match[2] : match[1];
      const object = item.reverse ? match[1] : match[2];
      const claim = buildClaim(subject, 'SUBCLASS_OF', object, { ...common, subjectType:'class', objectType:'class' });
      return { ok:true, engine:'rule_fallback', intent:'ASSERTION', interpretation:`The sentence proposes that ${cleanLabel(subject)} is a subclass of ${cleanLabel(object)}.`, claims:[claim], unresolved:[], warnings:['Entity classes are provisional until supported by accepted knowledge or reviewed evidence.'], sourceText:original };
    }
  }

  // Explicit instance construction.
  match = text.match(/^(.+?)\s+is\s+(?:an?\s+)?instance\s+of\s+(.+)$/i);
  if (match) {
    const claim = buildClaim(match[1], 'INSTANCE_OF', match[2], { ...common, subjectType:'individual', objectType:'class' });
    return { ok:true, engine:'rule_fallback', intent:'ASSERTION', interpretation:`The sentence proposes that ${cleanLabel(match[1])} is an instance of ${cleanLabel(match[2])}.`, claims:[claim], unresolved:[], warnings:[], sourceText:original };
  }

  // A simple copular singular sentence is represented as instance membership, not subclass.
  match = text.match(/^(.+?)\s+is\s+(?:an?\s+)([a-z][\w -]+)$/i);
  if (match && !/^(kind|type|subclass|instance)\b/i.test(match[2])) {
    const claim = buildClaim(match[1], 'INSTANCE_OF', match[2], { ...common, subjectType:'individual', objectType:'class' });
    return { ok:true, engine:'rule_fallback', intent:'ASSERTION', interpretation:`The sentence is provisionally read as instance membership: ${cleanLabel(match[1])} is an instance of ${cleanLabel(match[2])}.`, claims:[claim], unresolved:[], warnings:['A simple “is a” sentence can be ambiguous between identity, class membership, and other meanings. Review the candidate before accepting it.'], sourceText:original };
  }

  return {
    ok:true, engine:'rule_fallback', intent:'UNRESOLVED', interpretation:'No supported local pattern matched this sentence. The original text is preserved, but no semantic claim was created.',
    claims:[], unresolved:['The local rule interpreter does not recognize this construction. Connect a local LLM for broader language interpretation, or add a fact manually to the knowledge base.'], warnings:[], sourceText:original
  };
}

// ---------------------- Local LLM adapter ----------------------
async function apiGet(path) {
  const response = await fetch(path, { method:'GET', cache:'no-store' });
  if (!response.ok) throw new Error(`Local workbench service returned HTTP ${response.status}.`);
  return response.json();
}
async function checkRuntime() {
  const status = $('#runtime-status');
  try {
    const result = await apiGet('/api/health');
    localRuntimeAvailable = !!result.ok;
    status.classList.toggle('online', localRuntimeAvailable);
    status.classList.toggle('offline', !localRuntimeAvailable);
    status.innerHTML = `<i class="status-dot"></i><span>${localRuntimeAvailable?'Local bridge ready':'Static mode · no model bridge'}</span>`;
  } catch {
    localRuntimeAvailable = false;
    status.classList.add('offline');
    status.innerHTML = '<i class="status-dot"></i><span>Offline fallback mode</span>';
  }
  updateEngineLabel();
}
function updateEngineLabel() {
  const useModel = ollamaAvailable && $('#model-select')?.value;
  $('#engine-indicator').classList.toggle('online', !!useModel);
  $('#engine-label').textContent = useModel ? `Local LLM · ${$('#model-select').value}` : 'Rule interpreter · offline';
}
function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
function normalizeModelPredicate(rawPredicate, rawPolarity) {
  let predicate = String(rawPredicate || '').trim().toUpperCase().replace(/[^A-Z0-9_]/g,'_').slice(0,48);
  let polarity = ['negative','positive'].includes(String(rawPolarity ?? '').toLowerCase()) ? String(rawPolarity).toLowerCase() : 'unknown';
  // Some models encode the negator inside the relation name (e.g. DOES_NOT_LIKE)
  // while also setting polarity=negative. Store negation only in the polarity field.
  const prefixed = predicate.match(/^(?:DOES_NOT|DO_NOT|DID_NOT|IS_NOT|ARE_NOT|WAS_NOT|WERE_NOT|NOT)_(.+)$/);
  let warning = null;
  if (prefixed && prefixed[1]) {
    predicate = prefixed[1];
    if (polarity === 'positive' || polarity === 'unknown') {
      warning = `The predicate name encoded negation; “${rawPredicate}” was normalized to ${predicate} with negative polarity.`;
    } else {
      warning = `The predicate name encoded negation as well as the polarity field; “${rawPredicate}” was normalized to ${predicate} with one negative-polarity marker.`;
    }
    polarity = 'negative';
  }
  return { predicate:predicate || 'RELATED_TO', polarity, warning };
}
function sourceHasExplicitNegatedLike(sourceText, subjectText) {
  const clause = sourceClauseForSubject(sourceText, subjectText);
  return /\b(?:does|do|did)\s+not\s+like\b|\b(?:doesn't|don't|didn't)\s+like\b/i.test(clause);
}
function reconcilePredicateWithSource(predicate, polarity, sourceText, subjectText) {
  // Anchor this correction in the source wording: "does not like" is not "does not dislike".
  if (sourceHasExplicitNegatedLike(sourceText, subjectText) && ['LIKE','DISLIKES'].includes(predicate)) {
    const changed = predicate !== 'LIKE' || polarity !== 'negative';
    return { predicate:'LIKE', polarity:'negative', warning:changed ? `The source explicitly says “does not like”; the model proposal ${predicate}/${polarity} was reconciled to LIKE with negative polarity.` : null };
  }
  return { predicate, polarity, warning:null };
}
function sourceClauseForSubject(sourceText, subjectText) {
  const normalized = normalizeEntity(subjectText);
  if (!normalized) return String(sourceText || '');
  const phrase = escapeRegExp(normalized).replace(/\s+/g, '\\s+');
  const subjectMatch = new RegExp(`\\b${phrase}\\b`, 'i').exec(String(sourceText || ''));
  if (!subjectMatch) return String(sourceText || '');
  const start = subjectMatch.index;
  const rest = String(sourceText || '').slice(start);
  const boundary = /\b(?:because|although|unless|if|when|while|whereas|but|or|and)\b|[;.!?]/i.exec(rest.slice(subjectMatch[0].length));
  const end = boundary ? start + subjectMatch[0].length + boundary.index : String(sourceText || '').length;
  return String(sourceText || '').slice(start, end).trim();
}
function detectClaimTense(sourceText, subjectText) {
  return detectExplicitSourceTense(sourceClauseForSubject(sourceText, subjectText));
}
function recoverObjectFromSource(sourceText, subjectText, predicate) {
  const verbForms = {
    NEEDS:['does not need',"doesn't need",'do not need',"don't need",'did not need',"didn't need",'needs','need','needed'],
    LIKE:['does not like',"doesn't like",'do not like',"don't like",'did not like',"didn't like",'likes','like','liked'],
    MEASURES:['does not measure',"doesn't measure",'do not measure',"don't measure",'did not measure',"didn't measure",'measures','measure','measured'],
    CAUSES:['does not cause',"doesn't cause",'do not cause',"don't cause",'causes','cause','caused'],
    HAS_PROPERTY:['does not have',"doesn't have",'do not have',"don't have",'has','have','had'],
    DISLIKE:['does not dislike',"doesn't dislike",'do not dislike',"don't dislike",'dislikes','dislike','disliked']
  }[predicate];
  if (!verbForms) return null;
  const normalized = normalizeEntity(subjectText);
  if (!normalized) return null;
  const subjectPattern = escapeRegExp(normalized).replace(/\s+/g, '\\s+');
  const subjectMatch = new RegExp(`\\b${subjectPattern}\\b`, 'i').exec(String(sourceText || ''));
  if (!subjectMatch) return null;
  const rest = String(sourceText || '').slice(subjectMatch.index + subjectMatch[0].length);
  const verbsPattern = verbForms.slice().sort((a,b)=>b.length-a.length).map(escapeRegExp).join('|');
  const match = new RegExp(`^\\s+(?:${verbsPattern})\\s+(.+?)(?=\\s+(?:because|if|unless|when|although|while|whereas)\\b|[,;.!?]|$)`, 'i').exec(rest);
  if (!match) return null;
  const recovered = cleanLabel(match[1]);
  return recovered || null;
}
function extractBecauseClause(sourceText) {
  const source = String(sourceText || '');
  const match = /\bbecause\s+(.+?)(?=[.!?]|$)/i.exec(source);
  if (!match) return null;
  const text = cleanLabel(match[1]);
  if (!text) return null;
  const phraseOffset = match[0].toLowerCase().indexOf(match[1].toLowerCase());
  const start = match.index + phraseOffset;
  return { text, start, end:start + match[1].length, markerStart:match.index };
}
function parseBecauseProposition(clause) {
  if (!clause) return null;
  let match;
  if ((match = clause.text.match(/^(.+?)\s+(was|were|is|are)\s+different$/i))) {
    return { subject:cleanLabel(match[1]), predicate:'DIFFER', object:null, tense:/^(was|were)$/i.test(match[2])?'past':'present' };
  }
  if ((match = clause.text.match(/^(.+?)\s+differed$/i))) {
    return { subject:cleanLabel(match[1]), predicate:'DIFFER', object:null, tense:'past' };
  }
  if ((match = clause.text.match(/^(.+?)\s+differs?$/i))) {
    return { subject:cleanLabel(match[1]), predicate:'DIFFER', object:null, tense:'present' };
  }
  if ((match = clause.text.match(/^(.+?)\s+(was|were|is|are)\s+changing$/i))) {
    return { subject:cleanLabel(match[1]), predicate:'CHANGE', object:null, tense:/^(was|were)$/i.test(match[2])?'past':'present' };
  }
  if ((match = clause.text.match(/^(.+?)\s+changed$/i))) {
    return { subject:cleanLabel(match[1]), predicate:'CHANGE', object:null, tense:'past' };
  }
  if ((match = clause.text.match(/^(.+?)\s+changes?$/i))) {
    return { subject:cleanLabel(match[1]), predicate:'CHANGE', object:null, tense:'present' };
  }
  return null;
}
function buildSourceEvidence(sourceText, start, end) {
  const source = String(sourceText || '');
  const safeStart = Math.max(0, Math.min(source.length, Number(start) || 0));
  const safeEnd = Math.max(safeStart, Math.min(source.length, Number(end) || safeStart));
  const quote = source.slice(safeStart, safeEnd);
  return { sourceText:source, quote, start:safeStart, end:safeEnd, verified:!!quote && source.slice(safeStart, safeEnd) === quote, modelQuote:null, modelQuoteVerified:null };
}

// ---------------------- USG Semantic Representation v0.4 ----------------------
const SEMANTIC_SCHEMA_VERSION = '0.5.1';
function valueText(value) {
  if (typeof value === 'string') return cleanLabel(value);
  if (value && typeof value === 'object' && !Array.isArray(value)) return cleanLabel(value.text ?? value.label ?? value.name ?? '');
  return '';
}
function semanticEntity(value, fallbackType='unknown', knownEntities=null) {
  const surface = (value && typeof value==='object' && !Array.isArray(value)) ? cleanLabel(value.surfaceText || value.text || value.label || value.name || '') : valueText(value);
  if (!surface) return null;
  const normalized = (value && typeof value==='object' && !Array.isArray(value) && cleanLabel(value.canonicalText || value.text)) ? normalizeEntity(value.canonicalText || value.text) : normalizeEntity(surface);
  const known = knownEntities?.get(norm(normalized));
  return {
    text:known?.text || normalized,
    canonicalText:known?.text || normalized,
    surfaceText:surface,
    type:(value && typeof value==='object' && typeof value.type==='string') ? value.type.slice(0,64) : fallbackType,
    reference:(value && typeof value==='object' && ['definite','indefinite','unmarked','unknown','resolved_pronoun'].includes(value.reference)) ? value.reference : detectReference(surface),
    entityId:(value && typeof value==='object' && value.entityId) || known?.id || null
  };
}
function semanticProposition(raw, fallback={}) {
  if (!raw || typeof raw!=='object' || Array.isArray(raw)) return null;
  const subjectRaw = raw.subject ?? raw.agent ?? fallback.subject;
  const objectRaw = raw.object ?? raw.patient ?? fallback.object;
  const subject = semanticEntity(subjectRaw);
  if (!subject) return null;
  const predicateRaw = raw.predicate ?? raw.relation ?? fallback.predicate;
  if (typeof predicateRaw !== 'string' || !predicateRaw.trim()) return null;
  const predicate = String(predicateRaw).toUpperCase().replace(/[^A-Z0-9_]/g,'_').slice(0,48);
  const object = objectRaw == null || valueText(objectRaw)==='' ? null : semanticEntity(objectRaw);
  const tense=['past','present','future','unknown'].includes(String(raw.tense||'').toLowerCase()) ? String(raw.tense).toLowerCase() : 'unknown';
  const modality=['asserted','possible','necessary','obligatory','possible_or_ability','expected','unknown'].includes(String(raw.modality||'').toLowerCase()) ? String(raw.modality).toLowerCase() : 'asserted';
  const sourceTime=raw.time && typeof raw.time==='object' ? raw.time : {grammaticalTense:tense,aspect:'unknown',referenceTime:'unspecified'};
  const modalScope=sanitizeModalScope(raw.modalScope) || {operator:modality.toUpperCase(),force:modality,scope:'proposition',surfaceText:null};
  return {
    subject, predicate, object,
    polarity:['positive','negative','unknown'].includes(String(raw.polarity||'').toLowerCase()) ? String(raw.polarity).toLowerCase() : 'positive',
    tense, modality, time:sourceTime, modalScope
  };
}
function parseFrequencyPhrase(sourceText) {
  const source=String(sourceText||'');
  const patterns=[
    [/\b(every\s+day|daily)\b/i,'P1D'],[/\b(every\s+week|weekly)\b/i,'P1W'],[/\b(every\s+month|monthly)\b/i,'P1M'],[/\b(every\s+year|yearly|annually)\b/i,'P1Y']
  ];
  for (const [pattern,normalizedValue] of patterns) { const match=pattern.exec(source); if(match)return {type:'frequency',value:cleanLabel(match[1]),normalizedValue,surfaceText:match[1],scope:'event'}; }
  return null;
}
function sourceModalFrame(sourceText, subjectText) {
  const clause=sourceClauseForSubject(sourceText,subjectText);
  const cues=[
    [/\bis\s+expected\s+to\b|\bare\s+expected\s+to\b|\bwas\s+expected\s+to\b|\bwere\s+expected\s+to\b/i,'EXPECTED','expected','epistemic_expectation'],
    [/\bmight\b/i,'MIGHT','possible','epistemic_possibility'],[/\bmay\b/i,'MAY','possible','epistemic_possibility'],[/\bcould\b/i,'COULD','possible_or_ability','ambiguous_possibility_or_ability'],
    [/\bmust\b/i,'MUST','necessary','necessity_or_obligation_ambiguous'],[/\bshould\b|\ ought\ to\b/i,'SHOULD','obligatory','deontic'],[/\bcan\b|\bable\s+to\b/i,'CAN','possible_or_ability','ability_or_permission']
  ];
  for (const [pattern,operator,legacy,force] of cues) { const m=pattern.exec(clause); if(m)return {operator,force,scope:'proposition',surfaceText:m[0],legacyModality:legacy}; }
  return {operator:'ASSERTED',force:'assertion',scope:'proposition',surfaceText:null,legacyModality:'asserted'};
}
function sourceQuantifierFrame(sourceText) {
  const source=String(sourceText||'');
  let match=source.match(/\bnot\s+every\s+([a-z][a-z\s-]*?)\s+(?:needs?|likes?|uses?|has|have|is|are|measures?)\b/i);
  if (match) {
    const category=normalizeEntity(match[1]);
    return {operator:'NOT',quantifier:'FORALL',variable:'x',restrictor:{predicate:'INSTANCE_OF',entity:{text:category,type:'class',reference:'unmarked'}},scope:'claim',surfaceText:`not every ${category}`,logicalForm:'NOT(FORALL x: category(x) -> proposition(x))',interpretation:'The universal statement is negated. This does not mean that no member satisfies the predicate.'};
  }
  match=source.match(/\bno\s+(?!longer\b)([a-z][a-z\s-]*?)\s+(?:needs?|likes?|uses?|has|have|is|are|measures?)\b/i);
  if (match) {
    const category=normalizeEntity(match[1]);
    return {operator:'NO',quantifier:'FORALL',variable:'x',restrictor:{predicate:'INSTANCE_OF',entity:{text:category,type:'class',reference:'unmarked'}},scope:'claim',surfaceText:`no ${category}`,logicalForm:'FORALL x: category(x) -> NOT(proposition(x))',interpretation:'The negative predicate applies to every member of the stated class.'};
  }
  return null;
}
function sanitizeModalScope(raw) {
  if(!raw || typeof raw!=='object' || Array.isArray(raw)) return null;
  const operator=String(raw.operator||'').toUpperCase().replace(/[^A-Z0-9_]/g,'_').slice(0,40);
  if(!operator) return null;
  return {operator,force:String(raw.force||'unknown').slice(0,80),scope:String(raw.scope||'proposition').slice(0,80),surfaceText:typeof raw.surfaceText==='string'?raw.surfaceText.slice(0,120):null};
}
function sanitizeQuantifierScope(raw) {
  if(!raw || typeof raw!=='object' || Array.isArray(raw)) return null;
  const operatorValue=String(raw.operator||'').toUpperCase();
  const quantifierValue=String(raw.quantifier||'').toUpperCase();
  const meaningfulText = value => !!cleanLabel(value) && !/^(?:unknown|none|null|\.{2,}|exact source phrase|source phrase)$/i.test(cleanLabel(value));
  const hasMeaning = (!!operatorValue && !['UNKNOWN','NONE','NULL'].includes(operatorValue)) ||
    (!!quantifierValue && quantifierValue!=='UNKNOWN') || meaningfulText(raw.surfaceText) ||
    meaningfulText(raw.logicalForm) || !!(raw.restrictor && typeof raw.restrictor==='object' && meaningfulText(raw.restrictor.entity?.text || raw.restrictor.entity?.canonicalText || raw.restrictor.text || raw.restrictor.entityText || ''));
  if(!hasMeaning) return null;
  const restrictorCandidate=raw.restrictor && typeof raw.restrictor==='object' && !Array.isArray(raw.restrictor) ? raw.restrictor : null;
  const restrictorRaw=restrictorCandidate && cleanLabel(restrictorCandidate.entity?.text || restrictorCandidate.entity?.canonicalText || restrictorCandidate.text || restrictorCandidate.entityText || '') ? restrictorCandidate : null;
  const entity=restrictorRaw?.entity==null?null:semanticEntity(restrictorRaw.entity,'class');
  return {
    operator:String(raw.operator||'UNKNOWN').toUpperCase().replace(/[^A-Z0-9_]/g,'_').slice(0,32),
    quantifier:String(raw.quantifier||'UNKNOWN').toUpperCase().replace(/[^A-Z0-9_]/g,'_').slice(0,32),
    variable:String(raw.variable||'x').slice(0,16),
    restrictor:restrictorRaw?{predicate:String(restrictorRaw.predicate||'INSTANCE_OF').toUpperCase().replace(/[^A-Z0-9_]/g,'_').slice(0,48),entity}:null,
    scope:String(raw.scope||'claim').slice(0,80),
    logicalForm:String(raw.logicalForm||'').slice(0,400),
    surfaceText:typeof raw.surfaceText==='string'?raw.surfaceText.slice(0,160):null,
    interpretation:typeof raw.interpretation==='string'?raw.interpretation.slice(0,400):null
  };
}
function sanitizeEventAttributes(raw, sourceText='') {
  if(!Array.isArray(raw)) return [];
  const allowedTypes=new Set(['frequency','duration','manner','temporal_reference','intensity','quantity','location','instrument']);
  const source=String(sourceText||'');
  return raw.filter(a=>a && typeof a==='object' && !Array.isArray(a)).map(a=>({
    type:String(a.type||'').toLowerCase().replace(/[^a-z0-9_]/g,'_').slice(0,40),
    value:String(a.value??a.surfaceText??'').trim().slice(0,160),
    normalizedValue:typeof a.normalizedValue==='string' && !/^(?:\.{2,}|normalizedValue|\.\.\.)$/i.test(a.normalizedValue)?a.normalizedValue.slice(0,80):null,
    surfaceText:typeof a.surfaceText==='string'?a.surfaceText.trim().slice(0,160):String(a.value??'').trim().slice(0,160),
    scope:String(a.scope||'event').slice(0,40)
  })).filter(a=>{
    const placeholder=/^(?:\.{2,}|exact source phrase|source phrase|value|frequency\|duration\|manner\|\.\.\.|frequency_duration_manner_*)$/i.test(a.value) || /^(?:\.{2,}|exact source phrase|source phrase)$/i.test(a.surfaceText);
    const grounded=!!a.surfaceText && source.includes(a.surfaceText);
    return allowedTypes.has(a.type) && !!a.value && !placeholder && (!source || grounded);
  });
}
function sanitizeComparisonFrame(raw) {
  if(!raw || typeof raw!=='object' || Array.isArray(raw)) return null;
  return {reference:raw.reference==null?null:String(raw.reference).slice(0,160),comparisonSet:raw.comparisonSet==null?null:String(raw.comparisonSet).slice(0,240),status:['specified','context_dependent','unresolved'].includes(raw.status)?raw.status:'context_dependent',requiredFor:Array.isArray(raw.requiredFor)?raw.requiredFor.map(x=>String(x).slice(0,80)):[],note:typeof raw.note==='string'?raw.note.slice(0,400):''};
}
function clauseTense(sourceText, clauseText, fallback='unknown') {
  const t=detectExplicitSourceTense(clauseText || sourceText);
  return t==='conflict'?'unknown':(t==='unknown'?fallback:t);
}
function resolveSimpleDiscourse(sourceText, claims) {
  const src=String(sourceText||'');
  const purchase=src.match(/^((?:the|a|an)\s+[^.!?]+?)\s+(?:bought|purchased|acquired)\s+((?:a|an|the)\s+[^.!?]+?)[.!?]/i);
  const needContrast=cleanLabel(src).match(/^(.+?)\s+needs?\s+(.+?),\s*but\s+(?:does\s+not\s+need|doesn't\s+need|do\s+not\s+need|don't\s+need)\s+(it|them|that|those)$/i);
  const becauseFailure=src.match(/^(.+?)\s+stopped\s+using\s+(.+?)\s+because\s+it\s+failed/i);
  const frame=purchase ? {subjectSurface:purchase[1],objectSurface:purchase[2],kind:'purchase'} : (needContrast ? {subjectSurface:needContrast[1],objectSurface:needContrast[2],kind:'need_contrast'} : (becauseFailure ? {subjectSurface:becauseFailure[1],objectSurface:becauseFailure[2],kind:'because_failure'} : null));
  const entityMap=new Map();
  const mentions=[];
  let subjectEntry=null, objectEntry=null;
  const register=(surface,role)=>{
    const canonical=normalizeEntity(surface);
    const key=norm(canonical);
    const id=`e_${canonical.toLowerCase().replace(/[^a-z0-9]+/g,'_')}`;
    const entry={id,text:canonical,type:role==='subject'?'agent_or_topic':'artifact_or_resource'};
    entityMap.set(key,entry);
    mentions.push({entityId:id,surfaceText:surface,canonicalText:canonical,mentionType:'noun_phrase',antecedentId:null});
    return entry;
  };
  if(frame) {
    subjectEntry=register(frame.subjectSurface,'subject');
    objectEntry=register(frame.objectSurface,'object');
    if(frame.kind==='purchase') {
      const subjectPronoun=src.match(/\b(he|she|they)\b/i);
      if(subjectPronoun) mentions.push({entityId:subjectEntry.id,surfaceText:subjectPronoun[1],canonicalText:subjectEntry.text,mentionType:'pronoun',antecedentId:subjectEntry.id});
    }
    const objectPronoun=src.match(/\b(it|them|that|those)\b/i);
    if(objectPronoun) mentions.push({entityId:objectEntry.id,surfaceText:objectPronoun[1],canonicalText:objectEntry.text,mentionType:'pronoun',antecedentId:objectEntry.id});
    for(const claim of claims) {
      if(claim.subject?.reference==='resolved_pronoun' && claim.subject.surfaceText) {
        const pronounTarget=norm(claim.subject.text)===norm(objectEntry.text)?objectEntry:subjectEntry;
        if(pronounTarget) mentions.push({entityId:pronounTarget.id,surfaceText:claim.subject.surfaceText,canonicalText:pronounTarget.text,mentionType:'pronoun',antecedentId:pronounTarget.id});
      }
      if(claim.object?.reference==='resolved_pronoun' && claim.object.surfaceText) {
        mentions.push({entityId:objectEntry.id,surfaceText:claim.object.surfaceText,canonicalText:objectEntry.text,mentionType:'pronoun',antecedentId:objectEntry.id});
      }
      if(claim.subject?.text && /^(he|she|they|him|her|them|it|that|those)$/i.test(claim.subject.text)) {
        const pronounTarget=/^(it|them|that|those)$/i.test(claim.subject.text)?objectEntry:subjectEntry;
        claim.subject={...claim.subject,text:pronounTarget.text,canonicalText:pronounTarget.text,entityId:pronounTarget.id,surfaceText:claim.subject.surfaceText||claim.subject.text,reference:'resolved_pronoun'};
        mentions.push({entityId:pronounTarget.id,surfaceText:claim.subject.surfaceText,canonicalText:pronounTarget.text,mentionType:'pronoun',antecedentId:pronounTarget.id});
      }
      if(claim.object?.text && /^(it|them|that|those)(?:\s+.*)?$/i.test(claim.object.text)) {
        const frequency=parseFrequencyPhrase(claim.object.text) || parseFrequencyPhrase(src);
        claim.object={...claim.object,text:objectEntry.text,canonicalText:objectEntry.text,entityId:objectEntry.id,surfaceText:claim.object.surfaceText||claim.object.text,reference:'resolved_pronoun'};
        if(frequency) {
          claim.eventAttributes=Array.isArray(claim.eventAttributes)?claim.eventAttributes:[];
          if(!claim.eventAttributes.some(x=>x.type==='frequency')) claim.eventAttributes.push(frequency);
        }
        mentions.push({entityId:objectEntry.id,surfaceText:claim.object.surfaceText,canonicalText:objectEntry.text,mentionType:'pronoun',antecedentId:objectEntry.id});
      }
    }
  }
  // Resolve an explicit pronoun in a nested condition proposition only when this narrow frame has an antecedent.
  if(frame) for(const claim of claims) for(const condition of claim.conditions||[]) {
    const p=condition.proposition;
    if(!p) continue;
    if(p.subject?.text && /^(it|them|that|those)$/i.test(p.subject.text)) {
      p.subject={...p.subject,text:objectEntry.text,canonicalText:objectEntry.text,entityId:objectEntry.id,surfaceText:p.subject.surfaceText||p.subject.text,reference:'resolved_pronoun'};
    }
    if(p.object?.text && /^(it|them|that|those)$/i.test(p.object.text)) {
      p.object={...p.object,text:objectEntry.text,canonicalText:objectEntry.text,entityId:objectEntry.id,surfaceText:p.object.surfaceText||p.object.text,reference:'resolved_pronoun'};
    }
  }
  // Include nested condition propositions in the same entity registry.
  for (const claim of claims) for (const condition of claim.conditions || []) {
    const p=condition.proposition;
    if(!p) continue;
    for(const entity of [p.subject,p.object]) if(entity?.text) {
      const key=norm(entity.text); if(!entityMap.has(key)) entityMap.set(key,{id:entity.entityId||`e_${key.replace(/[^a-z0-9]+/g,'_')}`,text:entity.text,type:entity.type||'unknown'});
      const entry=entityMap.get(key); entity.entityId=entity.entityId||entry.id; entity.canonicalText=entity.canonicalText||entity.text;
    }
  }
  // Always add referents found in normalized claims to the entity registry.
  for (const claim of claims) for (const [role,entity] of [['subject',claim.subject],['object',claim.object]]) {
    if (!entity?.text) continue;
    const key=norm(entity.text);
    if (!entityMap.has(key)) {
      const id=entity.entityId || `e_${key.replace(/[^a-z0-9]+/g,'_')}`;
      entityMap.set(key,{id,text:entity.text,type:entity.type||'unknown'});
    }
    const entry=entityMap.get(key);
    entity.entityId=entity.entityId||entry.id;
    entity.canonicalText=entity.canonicalText||entity.text;
    entity.surfaceText=entity.surfaceText||entity.text;
    if (!mentions.some(m=>m.entityId===entry.id && m.surfaceText===entity.surfaceText)) mentions.push({entityId:entry.id,surfaceText:entity.surfaceText,canonicalText:entry.text,mentionType:'noun_phrase',antecedentId:null});
  }
  return {entities:[...entityMap.values()].map(e=>({id:e.id,canonicalText:e.text,type:e.type})),mentions};
}
function conditionTenseFromEvidence(evidenceText, marker, fallback='unknown') {
  const text=String(evidenceText||'').trim();
  if(!text) return fallback;
  if(/\b(will|shall)\b/i.test(text)) return 'future';
  if(/\b(did|was|were|had)\b/i.test(text) || /\b[a-z]+ed\b/i.test(text)) return 'past';
  if(['if','when','unless'].includes(String(marker||'').toLowerCase())) return 'present';
  return fallback;
}
function normalizeConditionV04(condition, sourceText, parentClaim = null) {
  if (!condition || typeof condition!=='object' || Array.isArray(condition)) return null;
  const rawProp=condition.proposition && typeof condition.proposition==='object' ? condition.proposition : condition;
  const proposition=semanticProposition(rawProp);
  const evidenceText=cleanLabel(condition.evidenceText || condition.evidence_text || '');
  const evidenceIndex=evidenceText?String(sourceText||'').indexOf(evidenceText):-1;
  const evidence=evidenceIndex>=0?buildSourceEvidence(sourceText,evidenceIndex,evidenceIndex+evidenceText.length):null;
  if(proposition && evidenceText && evidenceIndex>=0) {
    const sourceTense=conditionTenseFromEvidence(evidenceText,condition.marker,proposition.tense);
    if(sourceTense!=='unknown') {
      proposition.tense=sourceTense;
      proposition.time={...(proposition.time||{}),grammaticalTense:sourceTense,referenceTime:proposition.time?.referenceTime||sourceTense,sourceTense,clauseEvidence:evidenceText};
    }
    const modal=sourceModalFrame(evidenceText,proposition.subject.text);
    if(modal.surfaceText) {
      proposition.modality=modal.legacyModality;
      proposition.modalScope={operator:modal.operator,force:modal.force,scope:modal.scope,surfaceText:modal.surfaceText};
    } else if(proposition.modalScope) proposition.modalScope=sanitizeModalScope(proposition.modalScope)||proposition.modalScope;
  }
  const marker=String(condition.marker||'if').toLowerCase().slice(0,32);
  const markerStatus=marker==='unless'?'exception_relation_asserted':(marker==='when'?'when_clause_not_asserted':'conditional_not_asserted');
  const markerEffect=marker==='unless'?'exception_to_assertion':(marker==='when'?'temporal_condition_for_assertion':'condition_for_assertion');
  const parentClaimId=typeof parentClaim==='string' ? parentClaim : (parentClaim && parentClaim.id ? parentClaim.id : null);
  const parentSubject=parentClaim?.subject?.surfaceText || parentClaim?.subject?.text || 'unknown subject';
  const parentObject=parentClaim?.object?.surfaceText || parentClaim?.object?.text || null;
  const parentArguments=parentObject ? `${parentSubject}, ${parentObject}` : parentSubject;
  const parentSummary=parentClaim?.predicate ? `${parentClaim.polarity==='negative'?'NOT ':''}${String(parentClaim.predicate).toUpperCase()}(${parentArguments})` : null;
  const suppliedConsequence=String(condition.consequence||'').trim();
  const consequence=suppliedConsequence && suppliedConsequence.toLowerCase()!=='unspecified' ? suppliedConsequence : (parentSummary || 'unspecified');
  const consequenceInterpretation=String(condition.consequenceInterpretation||'').trim() || (marker==='unless' && parentSummary
    ? `The parent claim ${parentSummary} is the EXCEPTION consequent; it is not an unconditional assertion.`
    : (parentSummary ? `The parent claim ${parentSummary} is linked to this ${marker.toUpperCase()} clause; the subordinate clause is not an independent asserted fact.` : ''));
  return {
    id:condition.id||uid('cond'),marker,
    scope:String(condition.scope||'claim').slice(0,80),
    // The source marker determines the canonical effect. The original model
    // proposal remains available in the generation audit if its metadata differed.
    effect:markerEffect,
    proposition,
    consequence:consequence.slice(0,240),
    consequenceInterpretation:consequenceInterpretation.slice(0,600)||null,
    // The condition is scoped to this parent claim; do not trust a model-proposed
    // dangling consequent identifier over the adapter's actual parent claim.
    consequentClaimId:parentClaimId||condition.consequentClaimId||null,
    evidenceText:evidenceText||null,evidence,
    logicalStatus:proposition?markerStatus:'unresolved_proposition'
  };
}
function addClaimRelations(claims) {
  const relations=[];
  const stable = value => JSON.stringify(value ?? null);
  const timeSignature = claim => {
    const t=claim.time||{};
    return stable({
      tense:claim.tense||'unknown',
      grammaticalTense:t.grammaticalTense||claim.tense||'unknown',
      referenceTime:t.referenceTime||claim.tense||'unspecified',
      temporalAdverbials:(Array.isArray(t.temporalAdverbials)?t.temporalAdverbials:[]).map(norm).sort()
    });
  };
  const modalSignature = claim => {
    const m=claim.modalScope||{};
    return stable({modality:claim.modality||'unknown',operator:m.operator||null,force:m.force||null,scope:m.scope||null});
  };
  const quantifierSignature = claim => {
    const q=claim.quantifierScope;
    if(!q)return 'null';
    return stable({operator:q.operator||null,quantifier:q.quantifier||null,scope:q.scope||null,logicalForm:q.logicalForm||null,restrictor:q.restrictor?.entity?.text||q.restrictor?.text||null});
  };
  const eventSignature = claim => stable((claim.eventAttributes||[]).map(a=>({type:a.type||null,value:a.normalizedValue||a.value||null,scope:a.scope||null})).sort((a,b)=>stable(a).localeCompare(stable(b))));
  const conditionSignature = claim => (claim.conditions||[]).map(c=>{
    const p=c.proposition||{};
    return stable({marker:c.marker||null,scope:c.scope||null,effect:c.effect||null,subject:norm(p.subject?.text||p.subject||''),predicate:p.predicate||'',object:norm(p.object?.text||p.object||''),polarity:p.polarity||'positive',tense:p.tense||'unknown',modality:p.modality||'unknown'});
  }).sort().join('|');
  for(let i=0;i<claims.length;i++) for(let j=i+1;j<claims.length;j++) {
    const a=claims[i],b=claims[j];
    const sameCore=norm(a.subject?.text)===norm(b.subject?.text) && a.predicate===b.predicate && norm(a.object?.text||'')===norm(b.object?.text||'');
    const sameContext=timeSignature(a)===timeSignature(b) && modalSignature(a)===modalSignature(b) && quantifierSignature(a)===quantifierSignature(b) && eventSignature(a)===eventSignature(b);
    const sameSemanticConditions=conditionSignature(a)===conditionSignature(b);
    if(sameCore && sameContext && sameSemanticConditions && ['positive','negative'].includes(a.polarity) && ['positive','negative'].includes(b.polarity) && a.polarity!==b.polarity) {
      relations.push({id:uid('rel'),type:'CONTRADICTS',fromClaimId:a.id,toClaimId:b.id,scope:'same_proposition_same_time_same_modality_same_conditions',status:'candidate',note:'Opposite polarity is attached to otherwise matching proposition frames, including time, modality, quantifier scope, event attributes, and conditions. This is a contradiction candidate, not a resolution.'});
    }
  }
  return relations;
}
function claimFromSourceComposition(parsed, sourceText) {
  const subject=parsed.subject||{}; const object=parsed.object||null;
  const built=buildClaim(subject.text||'',parsed.predicate,object?.text||null,{
    id:parsed.id, objectIsNull:!object, subjectType:subject.type||'unknown', objectType:object?.type||'unknown',
    subjectReference:subject.reference||'unmarked', objectReference:object?.reference||'unknown',
    subjectEntityId:subject.entityId||null, objectEntityId:object?.entityId||null,
    polarity:parsed.polarity||'unknown', tense:parsed.tense||'unknown', modality:parsed.modality||'asserted',
    modalScope:parsed.modalScope||null, time:parsed.time||null, quantifierScope:parsed.quantifierScope||null,
    eventAttributes:Array.isArray(parsed.eventAttributes)?parsed.eventAttributes:[],
    conditions:Array.isArray(parsed.conditions)?parsed.conditions:[],
    comparisonFrame:parsed.comparisonFrame||null, evidence:parsed.evidence||makeEvidence(sourceText),
    provenance:'source_composition_rule', sourceKind:'interpreted_text', ruleId:parsed.ruleId||'SRC-CLAUSE-COMPOSITION',
    confidence:1, note:parsed.note||'Parsed by the reusable source-grounded clause grammar.'
  });
  built.subject=semanticEntity(subject,'unknown');
  built.object=object?semanticEntity(object,'unknown'):null;
  built.sourceClauseText=parsed.sourceClauseText||parsed.evidence?.quote||sourceText;
  built.compositionRole=parsed.id;
  return built;
}
function enrichV04Record(record) {
  if (!record || typeof record!=='object') return record;
  const source=String(record.sourceText||'');
  let claims=Array.isArray(record.claims)?record.claims:[];
  const sourceComposer=globalThis.USGSemanticComposer;
  if(sourceComposer && typeof sourceComposer.composeSourceText==='function') {
    const composed=sourceComposer.composeSourceText(source);
    if(composed?.complete && Array.isArray(composed.claims) && composed.claims.length) {
      const proposed=claims.map(c=>({subject:c.subject?.text||c.subject||null,predicate:c.predicate||null,object:c.object?.text||c.object||null,polarity:c.polarity||null,tense:c.tense||null,modality:c.modality||null}));
      const proposalWarnings=[...(record.warnings||[])].slice(0,20);
      record.modelProposalSummary={claimCount:proposed.length,claims:proposed,unresolved:[...(record.unresolved||[])],warnings:proposalWarnings};
      claims=composed.claims.map(c=>claimFromSourceComposition(c,source));
      record.claims=claims;
      record.explanations=composed.explanations||[];
      record.semanticComposition=composed.semanticComposition||null;
      record.unresolved=composed.unresolved||[];
      record.compositionAudit={parser:composed.parser,parserVersion:composed.parserVersion,applied:true,compositionType:composed.compositionType,clauseCount:composed.clauseCount,modelProposalRetained:true,selection:'source_grounded_compositional_parse'};
      record.warnings=['A source-grounded compositional parse supplied the canonical clause structure. The original LLM proposal and its warnings are retained in modelProposalSummary for comparison.'];
    }
  }
  for(const claim of claims) {
    if(!claim.subject || typeof claim.subject!=='object') continue;
    claim.subject=semanticEntity(claim.subject,claim.subject.type||'unknown');
    claim.object=claim.object==null?null:semanticEntity(claim.object,claim.object.type||'unknown');
    const clauseText=claim.sourceClauseText || sourceClauseForSubject(source,claim.subject?.surfaceText||claim.subject?.text||'');
    const sourceTense=claim.provenance==='source_composition_rule' ? (claim.tense||'unknown') : detectClaimTense(clauseText,claim.subject?.surfaceText||claim.subject?.text||'');
    const detectedAspect=/\b(has|have|had)\s+\w+ed\b/i.test(clauseText)?'perfect':(/\b(am|is|are|was|were)\s+\w+ing\b/i.test(clauseText)?'progressive':'simple');
    const proposedTime=claim.time && typeof claim.time==='object' && !Array.isArray(claim.time)?claim.time:{};
    const allowedAspects=['simple','progressive','perfect','habitual','unknown'];
    const timeAdverbials=Array.isArray(proposedTime.temporalAdverbials)?proposedTime.temporalAdverbials.filter(x=>typeof x==='string'):[];
    claim.time={...proposedTime,grammaticalTense:claim.tense||'unknown',aspect:allowedAspects.includes(proposedTime.aspect)?proposedTime.aspect:detectedAspect,referenceTime:typeof proposedTime.referenceTime==='string'?proposedTime.referenceTime.slice(0,80):(claim.tense==='past'?'past':(claim.tense==='future'?'future':(claim.tense==='present'?'present':'unspecified'))),sourceTense:sourceTense==='conflict'?'unknown':sourceTense,clauseEvidence:clauseText||claim.evidence?.quote||null,temporalAdverbials:[...new Set([...timeAdverbials,...(claim.eventAttributes||[]).filter(a=>['duration','frequency','temporal_reference'].includes(a.type)).map(a=>a.surfaceText||a.value).filter(Boolean)])]};
    const modal=sourceModalFrame(clauseText,claim.subject.text);
    const proposedModalScope=sanitizeModalScope(claim.modalScope);
    claim.modalScope=modal.surfaceText?{operator:modal.operator,force:modal.force,scope:modal.scope,surfaceText:modal.surfaceText}:(proposedModalScope||{operator:modal.operator,force:modal.force,scope:modal.scope,surfaceText:modal.surfaceText});
    if(modal.legacyModality!=='asserted' && modal.legacyModality!=='unknown') claim.modality=modal.legacyModality;
    if(claim.predicate==='DIFFER' && !claim.object) claim.comparisonFrame=claim.comparisonFrame || {reference:null,comparisonSet:null,status:'context_dependent',requiredFor:['explicit_pairwise_comparison','rank_or_difference_calculation'],note:'The sentence expresses difference, but does not name the comparison reference or set. This does not make the sentence globally uninterpretable.'};
    claim.conditions=(Array.isArray(claim.conditions)?claim.conditions:[]).map(c=>normalizeConditionV04(c,source,claim)).filter(Boolean);
    for(const condition of claim.conditions) if(!condition.proposition) { (record.unresolved ||= []).push(`A ${condition.marker} condition was detected, but its internal proposition was not structurally valid; it was not treated as an asserted fact.`); (record.warnings ||= []).push('An incomplete condition proposition was preserved as unresolved instead of converting an object or malformed value into entity text.'); }
    claim.eventAttributes=Array.isArray(claim.eventAttributes)?claim.eventAttributes:[];
    const freq=parseFrequencyPhrase(clauseText);
    if(freq && /\b(?:USE|USES|USED|STOP_USING)\b/.test(claim.predicate) && !claim.eventAttributes.some(x=>x.type==='frequency')) claim.eventAttributes.push(freq);
    let quantifier=sourceQuantifierFrame(clauseText);
    // The compatibility claim subject may omit a leading scope marker; retain
    // overt sentence-initial quantifiers from the full source as a fallback.
    if(!quantifier && /^(?:not\s+every|no)\b/i.test(source)) quantifier=sourceQuantifierFrame(source);
    if(quantifier) {
      claim.quantifierScope=quantifier;
      if (claim.polarity === 'negative') { claim.polarity='positive'; (record.warnings ||= []).push('Quantifier-scope normalization moved negation from claim polarity into quantifierScope.'); }
      const qSubject=clauseText.match(/\bnot\s+every\s+([a-z][a-z\s-]*?)\s+(?:needs?|likes?|uses?|has|have|is|are|measures?)\b/i);
      const noSubject=clauseText.match(/\bno\s+(?!longer\b)([a-z][a-z\s-]*?)\s+(?:needs?|likes?|uses?|has|have|is|are|measures?)\b/i);
      const qMatch=qSubject||noSubject;
      if(qMatch) {
        const category=normalizeEntity(qMatch[1]);
        claim.subject={...claim.subject,text:category,canonicalText:category,surfaceText:qSubject?`not every ${category}`:`no ${category}`,type:'class',reference:'unmarked'};
      }
    } else if(claim.quantifierScope) {
      claim.quantifierScope=sanitizeQuantifierScope(claim.quantifierScope);
    }
    claim.eventAttributes=sanitizeEventAttributes(claim.eventAttributes,clauseText);
    if(claim.predicate==='DIFFER' && !claim.object) claim.comparisonFrame=sanitizeComparisonFrame(claim.comparisonFrame)||claim.comparisonFrame;
    if(!claim.completeness || typeof claim.completeness!=='object') claim.completeness={status:'complete',missingRoles:[],note:''};
    if(!Array.isArray(claim.completeness.missingRoles))claim.completeness.missingRoles=[];
    if(!['complete','underspecified','unresolved','not_applicable'].includes(claim.completeness.status))claim.completeness.status=claim.completeness.missingRoles.length?'underspecified':'complete';
    claim.semanticStatus=claim.completeness.status;
  }
  const discourse=resolveSimpleDiscourse(source,claims);
  const claimRelations=addClaimRelations(claims);
  const unresolved=Array.isArray(record.unresolved)?record.unresolved:[];
  const enriched={...record,schema:'USG-SEMANTIC-RECORD',schemaVersion:SEMANTIC_SCHEMA_VERSION,entities:discourse.entities,mentions:discourse.mentions,claimRelations,validation:{status:(unresolved.length || claims.some(c=>c.completeness?.status!=='complete'))?'partial':(claims.length?'candidate':'unresolved'),claimCount:claims.length,unresolvedCount:unresolved.length,underspecifiedCount:claims.filter(c=>c.completeness?.status!=='complete').length,allClaimsRequireReview:true},representationProfile:'USG-SR/0.5.1'};
  const semanticCore=globalThis.USGSemanticCore;
  if (semanticCore && typeof semanticCore.buildSemanticModel==='function') {
    const built=semanticCore.buildSemanticModel(enriched);
    enriched.semanticModel=built.model;
    enriched.semanticValidation=built.validation;
    const canonicalUnresolved = [...(built.validation.unresolved || []), ...(built.validation.errors || [])];
    if (canonicalUnresolved.length) {
      enriched.unresolved=[...new Set([...(enriched.unresolved||[]),...canonicalUnresolved])];
      enriched.validation.status='partial';
      enriched.validation.unresolvedCount=enriched.unresolved.length;
    }
    if (built.validation.status==='invalid') {
      enriched.warnings=[...(enriched.warnings||[]),'Canonical semantic-model validation failed; review this record before acceptance.',...built.validation.errors.map(e=>`Semantic-model error: ${e}`)];
    } else if (built.validation.warnings.length) {
      enriched.warnings=[...(enriched.warnings||[]),...built.validation.warnings.map(w=>`Semantic-model note: ${w}`)];
    }
  } else {
    enriched.semanticValidation={status:'unavailable',valid:false,errors:['semantic-core.js was not loaded'],warnings:[],requiresHumanReview:true,objectiveTruthEstablished:false};
    enriched.warnings=[...(enriched.warnings||[]),'Canonical semantic core was not loaded; the compatibility claim view is available but the v0.5 semantic model is missing.'];
  }
  return enriched;
}

function safeModelInterpretation(data, sourceText, correctionAudit=null) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('The local model did not return a JSON object.');
  const warnings = ['LLM-generated interpretation: inspect it before acceptance. Confidence is model-reported and is not calibrated.'];
  if (correctionAudit) {
    if (correctionAudit.status === 'repaired') warnings.push(`USG detected and repaired generation defects in ${correctionAudit.repairRounds || 0} correction round(s). Review the audit before acceptance.`);
    if (correctionAudit.status === 'needs_review') warnings.push('USG attempted targeted correction, but one or more semantic defects remain flagged. Review the generation audit before acceptance.');
    if (correctionAudit.status === 'review_unavailable') warnings.push('Deterministic checks ran, but the model-based semantic review was unavailable. Structural validation is not proof of semantic correctness.');
    for (const item of [...(correctionAudit.finalDiagnostics || []), ...(correctionAudit.reviewerIssues || [])]) {
      if (item && (item.severity === 'error' || item.severity === 'critical' || item.severity === 'warning') && item.problem) warnings.push(`Generation audit [${item.code || item.severity}]: ${item.problem}`);
    }
  }
  const rawClaims = Array.isArray(data.claims) ? data.claims : [];
  const claims = [];
  const unresolved = Array.isArray(data.unresolved) ? data.unresolved.map(x => String(x)) : [];
  for (const item of rawClaims) {
    if (!item || typeof item !== 'object' || Array.isArray(item)) continue;
    const subjectValue = item.subject;
    const objectValue = item.object;
    const subjectText = typeof subjectValue === 'string' ? subjectValue : (subjectValue && typeof subjectValue === 'object' && typeof subjectValue.text === 'string' ? subjectValue.text : '');
    let objectText = typeof objectValue === 'string' ? objectValue : (objectValue && typeof objectValue === 'object' && typeof objectValue.text === 'string' ? objectValue.text : '');
    if (!cleanLabel(subjectText) || typeof item.predicate !== 'string' || !cleanLabel(item.predicate)) continue;

    const normalizedPredicate = normalizeModelPredicate(item.predicate, item.polarity);
    const sourceAlignedPredicate = reconcilePredicateWithSource(normalizedPredicate.predicate, normalizedPredicate.polarity, sourceText, subjectText);
    const predicate = sourceAlignedPredicate.predicate;
    let polarity = sourceAlignedPredicate.polarity;
    if (normalizedPredicate.warning) warnings.push(normalizedPredicate.warning);
    if (sourceAlignedPredicate.warning) warnings.push(sourceAlignedPredicate.warning);
    if (polarity === 'unknown') warnings.push(`Claim “${cleanLabel(subjectText)} ${predicate}” has missing or invalid polarity; it was retained as unknown.`);
    if (!cleanLabel(objectText)) {
      const recoveredObject = recoverObjectFromSource(sourceText, subjectText, predicate);
      if (recoveredObject) {
        objectText = recoveredObject;
        warnings.push(`The model omitted the object for “${cleanLabel(subjectText)} ${predicate}”; “${recoveredObject}” was recovered from an explicit source-text pattern.`);
      } else if (['NEEDS','LIKE','MEASURES','CAUSES','HAS_PROPERTY'].includes(predicate)) {
        warnings.push(`The object for “${cleanLabel(subjectText)} ${predicate}” is missing and could not be recovered confidently from the source.`);
      }
    }

    const allowedTenses = ['past','present','future','unknown'];
    let tense = String(item.tense ?? '').toLowerCase();
    if (!allowedTenses.includes(tense)) tense = 'unknown';
    const sourceTense = detectClaimTense(sourceText, subjectText);
    if (sourceTense === 'conflict') {
      warnings.push(`The source contains conflicting tense markers inside the clause for “${cleanLabel(subjectText)} ${predicate}”; tense was set to unknown rather than guessing.`);
      tense = 'unknown';
    } else if (sourceTense !== 'unknown' && tense !== sourceTense) {
      warnings.push(`Tense correction for “${cleanLabel(subjectText)} ${predicate}”: model proposed ${tense}, but the source clause has a clear ${sourceTense} marker. Stored tense was set to ${sourceTense}.`);
      tense = sourceTense;
    }

    const allowedModalities = ['asserted','possible','necessary','obligatory','possible_or_ability','expected','unknown'];
    let modality = String(item.modality ?? '').toLowerCase();
    if (!allowedModalities.includes(modality)) modality = 'unknown';

    const conditions = Array.isArray(item.conditions) ? item.conditions.filter(c => c && typeof c === 'object' && !Array.isArray(c)).map(c => ({
      marker:String(c.marker || 'if').toLowerCase().slice(0,32),
      proposition:{ subject:c.subject ?? c.proposition?.subject ?? '', predicate:String(c.predicate || c.proposition?.predicate || 'RELATED_TO').toUpperCase().replace(/[^A-Z0-9_]/g,'_').slice(0,48), object:(c.object ?? c.proposition?.object) != null ? (c.object ?? c.proposition?.object) : null, polarity:c.polarity ?? c.proposition?.polarity, tense:c.tense ?? c.proposition?.tense, modality:c.modality ?? c.proposition?.modality, time:c.time ?? c.proposition?.time, modalScope:c.modalScope ?? c.proposition?.modalScope },
      scope:String(c.scope || 'main_relation').slice(0,80), effect:String(c.effect || (String(c.marker||'if').toLowerCase()==='unless'?'exception_to_assertion':(String(c.marker||'if').toLowerCase()==='when'?'temporal_condition_for_assertion':'condition_for_assertion'))).slice(0,80), consequence:String(c.consequence || 'unspecified').slice(0,240), consequenceInterpretation:String(c.consequenceInterpretation || '').slice(0,600), consequentClaimId:c.consequentClaimId || null, logicalStatus:c.logicalStatus || null, evidenceText:cleanLabel(c.evidence_text || c.evidenceText || '')
    })) : [];
    if (Array.isArray(item.conditions) && conditions.length !== item.conditions.length) warnings.push(`One or more malformed conditions on “${cleanLabel(subjectText)} ${predicate}” were ignored.`);

    const modelModalScope=sanitizeModalScope(item.modalScope);
    const modelTime=item.time && typeof item.time==='object' && !Array.isArray(item.time)?{...item.time}:null;
    const modelQuantifierScope=sanitizeQuantifierScope(item.quantifierScope);
    const modelEventAttributes=sanitizeEventAttributes(item.eventAttributes,sourceText);
    const modelComparisonFrame=sanitizeComparisonFrame(item.comparisonFrame);
    const evidenceText = typeof item.evidence_text === 'string' ? item.evidence_text : '';
    const evidenceIndex = evidenceText ? String(sourceText || '').indexOf(evidenceText) : -1;
    const modelEvidenceVerified = evidenceIndex >= 0;
    const storedEvidenceQuote = modelEvidenceVerified ? evidenceText : String(sourceText || '');
    const storedEvidenceStart = modelEvidenceVerified ? evidenceIndex : 0;
    const storedEvidenceEnd = storedEvidenceStart + storedEvidenceQuote.length;
    const sourceSpanVerified = !!storedEvidenceQuote && String(sourceText || '').slice(storedEvidenceStart, storedEvidenceEnd) === storedEvidenceQuote;
    if (!modelEvidenceVerified) {
      warnings.push(`The model-provided evidence quote for “${cleanLabel(subjectText)} ${predicate}” was missing or not an exact source substring; the full source was retained as a verified source span. The model quote itself remains unverified.`);
    }
    const score = item.confidence == null || item.confidence === '' ? NaN : Number(item.confidence);
    const noteText = String(item.notes || '').slice(0,600);
    const strengtheningPattern = /\b(incapable|unable to|cannot|can't|impossible|never)\b/i;
    if (polarity === 'negative' && strengtheningPattern.test(`${noteText} ${String(data.interpretation || '')}`) && !strengtheningPattern.test(sourceText)) {
      warnings.push(`The model may have strengthened the negative claim “${cleanLabel(subjectText)} ${predicate}” into an inability or impossibility statement not explicitly present in the source. Review its explanation.`);
    }
    const subjectType = subjectValue && typeof subjectValue === 'object' && !Array.isArray(subjectValue) && typeof subjectValue.type === 'string' ? subjectValue.type.slice(0,64) : 'unknown';
    const objectType = objectValue && typeof objectValue === 'object' && !Array.isArray(objectValue) && typeof objectValue.type === 'string' ? objectValue.type.slice(0,64) : 'unknown';
    const requiredObjectPredicates = new Set(['SUBCLASS_OF','INSTANCE_OF','MEASURES','NEEDS','LIKE','CAUSES','PART_OF','HAS_PROPERTY']);
    const missingRoles = !cleanLabel(objectText) && requiredObjectPredicates.has(predicate) ? ['object'] : [];
    const completeness = missingRoles.length ? {
      status:'underspecified', missingRoles,
      note:`The ${predicate} claim has no object, and an explicit object could not be recovered from the source.`
    } : { status:'complete', missingRoles:[], note:'' };
    if (missingRoles.length) unresolved.push(`The ${predicate} claim for “${cleanLabel(subjectText)}” is underspecified: its object is missing and could not be recovered from the source.`);

    claims.push(buildClaim(subjectText, predicate, objectText || null, {
      objectIsNull:!cleanLabel(objectText), subjectType, objectType, completeness,
      subjectReference:detectReference(subjectText), objectReference:objectText ? detectReference(objectText) : 'unknown',
      polarity, tense, modality, conditions, modalScope:modelModalScope, time:modelTime, quantifierScope:modelQuantifierScope, eventAttributes:modelEventAttributes, comparisonFrame:modelComparisonFrame,
      evidence:{sourceText,quote:storedEvidenceQuote,start:storedEvidenceStart,end:storedEvidenceEnd,verified:sourceSpanVerified,modelQuote:evidenceText || null,modelQuoteVerified:evidenceText ? modelEvidenceVerified : null},
      provenance:'local_llm_proposal', sourceKind:'interpreted_text', confidence:Number.isFinite(score)?Math.max(0,Math.min(1,score)):0.5,
      note:noteText
    }));
  }
  const explanations = [];
  const becauseClause = extractBecauseClause(sourceText);
  if (becauseClause && !globalThis.USGSemanticComposer?.composeSourceText?.(sourceText)?.complete) {
    const parsedCause = parseBecauseProposition(becauseClause);
    const mainClauseText = String(sourceText || '').slice(0, becauseClause.markerStart);
    const effectClaim = claims.find(c => {
      const subject = normalizeEntity(c.subject?.text || '');
      if (!subject) return false;
      const subjectPattern = escapeRegExp(subject).replace(/\s+/g, '\\s+');
      return new RegExp(`\\b${subjectPattern}\\b`, 'i').test(mainClauseText);
    }) || claims[0] || null;
    if (parsedCause && effectClaim) {
      const causeIsUnderspecified = false;
      const causeCompleteness = { status:'complete', missingRoles:[], note:'' };
      let causeClaim = claims.find(c => norm(c.subject.text) === norm(parsedCause.subject) && c.predicate === parsedCause.predicate);
      if (!causeClaim) {
        causeClaim = buildClaim(parsedCause.subject, parsedCause.predicate, parsedCause.object, {
          subjectType:'unknown', objectIsNull:true, subjectReference:detectReference(parsedCause.subject), completeness:causeCompleteness,
          polarity:'positive', tense:parsedCause.tense, modality:'asserted', conditions:[], causalLinks:[],
          evidence:buildSourceEvidence(sourceText, becauseClause.start, becauseClause.end),
          provenance:'local_rule', sourceKind:'interpreted_text', ruleId:'R-BECAUSE-CLAUSE', confidence:0.86,
          note:causeCompleteness.note || 'Parsed from the explicit “because” clause.'
        });
        claims.push(causeClaim);
      }
      const link = {
        id:uid('x'), type:'CAUSE', causeClaimId:causeClaim.id, effectClaimId:effectClaim.id,
        attribution:'source_asserted', evidenceText:becauseClause.text,
        evidence:buildSourceEvidence(sourceText, becauseClause.markerStart, becauseClause.end),
        note:'The source sentence presents the cause claim as the reason for the effect claim; this relation is not independently verified as an objective cause.'
      };
      effectClaim.causalLinks = [...(effectClaim.causalLinks || []), link];
      explanations.push(link);
      warnings.push('A source-explicit “because” clause was represented as a separate claim and a source-attributed causal link. The link records what the sentence asserts, not independently proven causation.');
    } else if (!parsedCause) {
      unresolved.push(`The “because” clause “${becauseClause.text}” was preserved but its proposition could not be parsed safely.`);
      warnings.push('A causal marker was detected, but the causal clause was not converted into a claim because its proposition pattern is unsupported.');
    } else {
      unresolved.push(`The “because” clause “${becauseClause.text}” was parsed, but no effect claim was available to link it to.`);
    }
  }
  if (rawClaims.length && !claims.length) unresolved.push('The model returned claims, but none passed basic structural validation.');
  if (!claims.length && !unresolved.length) unresolved.push('The model returned no usable semantic claims.');
  return enrichV04Record({
    ok:true, engine:'local_llm', intent:String(data.intent || 'ASSERTION').toUpperCase().slice(0,40),
    interpretation:String(data.interpretation || 'The local model proposed a structured interpretation.').slice(0,1500),
    claims, explanations, unresolved, warnings:[...new Set(warnings)], sourceText, modelGenerationAudit:correctionAudit, modelProposalRaw:data
  });
}
function localInterpret(sentence) { return enrichV04Record(localInterpretCore(sentence)); }
function detectExplicitSourceTense(sentence) {
  const text = String(sentence || '');
  const cues = new Set();
  if (/\b(will|shall)\b/i.test(text)) cues.add('future');
  if (/\b(did|was|were|had)\b/i.test(text)) cues.add('past');
  if (/\b(does|doesn't|does\s+not|do|don't|do\s+not|is|are|am|has|have)\b/i.test(text)) cues.add('present');
  if (cues.size > 1) return 'conflict';
  return cues.size === 1 ? [...cues][0] : 'unknown';
}
function generationFailureAudit(error) {
  if (error && error.correctionAudit && typeof error.correctionAudit === 'object') return error.correctionAudit;
  const category = error?.failureCategory || 'model_request_error';
  const diagnostic = error?.diagnostic || null;
  const attempts = Array.isArray(error?.generationAttempts) ? error.generationAttempts : [];
  return {
    status: 'generation_request_failed', repairRounds: 0,
    reviewerMode: 'same_model_second_pass', reviewerStatus: 'not_run', reviewerAssessment: 'unknown',
    generation: attempts,
    generationArtifacts: [{
      phase: diagnostic?.phase || 'generation', status: 'request_failed',
      failureCategory: category, error: String(error?.message || error || 'Unknown model request failure'),
      diagnostic, partialModelResponse: error?.modelOutput ?? null
    }],
    failure: { category, message: String(error?.message || error || 'Unknown model request failure'), diagnostic },
    resourceNote: 'No semantic item-count limit was applied. The model request failed before a complete proposal was accepted.'
  };
}
function modelTransportError(cause, requestStartedAt = null, requestStartedMs = null) {
  const message = String(cause?.message || cause || 'The Workbench bridge could not be reached.');
  const lowered = message.toLowerCase();
  const category = cause?.name === 'AbortError' || /timed out|timeout|aborted/.test(lowered)
    ? 'timeout'
    : (/fetch failed|network|econnrefused|failed to fetch/.test(lowered) ? 'connection_or_transport_error' : 'model_request_error');
  const error = new Error(message);
  error.name = cause?.name || 'WorkbenchTransportError';
  error.failureCategory = category;
  error.diagnostic = {
    phase: 'workbench_bridge', category,
    originalErrorName: cause?.name || null, originalErrorMessage: message,
    errorCode: cause?.cause?.code || cause?.code || null,
    requestStartedAt, requestEndedAt: nowIso(),
    durationMs: requestStartedMs == null ? null : Date.now() - requestStartedMs,
    responseReceived: false
  };
  error.correctionAudit = generationFailureAudit(error);
  return error;
}
function modelHttpError(payload, status, responseBody = '') {
  const detail = payload && typeof payload === 'object' ? payload : {};
  const error = new Error(detail.error || `Local model error (${status}).`);
  error.name = 'WorkbenchModelRequestError';
  error.httpStatus = status;
  error.failureCategory = detail.failureCategory || detail.diagnostic?.category || 'model_request_error';
  error.diagnostic = detail.diagnostic
    ? {...detail.diagnostic, bridgeHttpStatus:status, bridgeResponseBody:responseBody}
    : { phase:'workbench_bridge_response', category:error.failureCategory, bridgeHttpStatus:status, responseBody, responseReceived:true };
  error.modelOutput = detail.modelOutput ?? null;
  error.generationAttempts = detail.generationAttempts ?? null;
  error.correctionAudit = detail.correctionAudit || null;
  error.correctionAudit = generationFailureAudit(error);
  return error;
}
async function requestModelInterpretation(sourceText) {
  let response;
  const requestStartedAt=nowIso();
  const requestStartedMs=Date.now();
  try {
    response = await fetch('/api/interpret', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({ ollamaUrl:$('#ollama-url').value.trim(), model:$('#model-select').value, text:sourceText, knowledge:state.claims.map(c => ({subject:c.subject.text,predicate:c.predicate,object:c.object?.text || null,polarity:c.polarity})) })
    });
  } catch (cause) {
    throw modelTransportError(cause,requestStartedAt,requestStartedMs);
  }
  let responseBody = '';
  try { responseBody = await response.text(); }
  catch (cause) { throw modelTransportError(cause,requestStartedAt,requestStartedMs); }
  let payload;
  try { payload = responseBody ? JSON.parse(responseBody) : {}; }
  catch (cause) {
    const error = new Error(`The Workbench returned invalid JSON: ${cause.message}`);
    error.failureCategory = 'response_parse_error';
    error.diagnostic = { phase:'workbench_bridge_response', category:error.failureCategory, bridgeHttpStatus:response.status, responseBody, requestStartedAt, requestEndedAt:nowIso(), durationMs:Date.now()-requestStartedMs, responseReceived:true };
    error.correctionAudit = generationFailureAudit(error);
    throw error;
  }
  if (!response.ok) throw modelHttpError(payload, response.status, responseBody);
  return payload;
}
async function analyzeSentence() {
  const sourceText = $('#source-text').value.trim();
  if (!sourceText) { showToast('Enter a sentence first.', true); $('#source-text').focus(); return; }
  const button = $('#analyze-button');
  button.disabled = true; button.innerHTML = 'Analyzing… <span>◌</span>';
  let result;
  try {
    if (localRuntimeAvailable && ollamaAvailable && $('#model-select').value) {
      const payload = await requestModelInterpretation(sourceText);
      result = safeModelInterpretation(payload.result, sourceText, payload.correctionAudit || null);
    } else {
      result = localInterpret(sourceText);
    }
  } catch (error) {
    showToast(`Local model failed: ${error.message}. Using the explicit rule fallback.`, true);
    result = localInterpret(sourceText);
    result.modelGenerationAudit = generationFailureAudit(error);
    result.modelFailureDiagnostic = error.diagnostic || null;
    result.warnings = [...(result.warnings || []), `The local model request failed (${error.failureCategory || 'model_request_error'}); this result came from the local rule fallback. The failure audit is retained.`];
  } finally {
    button.disabled = false; button.innerHTML = 'Analyze sentence <span>→</span>';
  }
  currentInterpretation = result;
  state.interpretationHistory.unshift({ id:uid('i'), sourceText, engine:result.engine, at:nowIso(), claimCount:result.claims.length, unresolvedCount:result.unresolved.length });
  state.interpretationHistory = state.interpretationHistory.slice(0,50);
  saveState();
  renderInterpretation(result);
}
async function interpretForBatch(sourceText) {
  if (localRuntimeAvailable && ollamaAvailable && $('#model-select').value) {
    const payload = await requestModelInterpretation(sourceText);
    return {record:safeModelInterpretation(payload.result, sourceText, payload.correctionAudit || null),rawModelResponse:payload.result,modelGenerationAudit:payload.correctionAudit || null};
  }
  return {record:localInterpret(sourceText),rawModelResponse:null};
}
function parseBatchLines(text) {
  return String(text||'').split(/\r?\n/).map(line=>line.trim()).filter(Boolean);
}
function batchSentences() {
  return parseBatchLines($('#batch-input').value);
}
function batchStatusForRecord(record) {
  if (!record || !Array.isArray(record.claims) || !record.claims.length) return 'unresolved';
  const hasIncompleteClaim = record.claims.some(claim => claim.completeness && claim.completeness.status !== 'complete');
  if (record.semanticValidation?.valid === false || record.semanticValidation?.status === 'partial' || (record.semanticModel?.unresolvedItems || []).length || (record.unresolved || []).length || hasIncompleteClaim) return 'partial';
  return 'completed';
}
function createBatchExport(items, model, startedAt, ollamaUrl=null) {
  return {
    schema:'USG-BATCH-TEST-EXPORT',schemaVersion:'1.3',semanticSchemaVersion:'0.5.1',application:'USG Semantic Workbench',workbenchVersion:'0.5.4',
    batchId:uid('batch'),startedAt,completedAt:nowIso(),execution:'sequential',
    model:model||'rule_fallback',ollamaUrl:model?(ollamaUrl||null):null,
    note:'Batch results are candidate interpretations only. No records were accepted into the knowledge base. A partial result contains at least one valid claim but also unresolved or underspecified semantic content.',
    summary:{total:items.length,completed:items.filter(x=>x.status==='completed').length,partial:items.filter(x=>x.status==='partial').length,unresolved:items.filter(x=>x.status==='unresolved').length,fallbackAfterError:items.filter(x=>x.status==='fallback_after_error').length},
    results:items
  };
}
function updateBatchCount() {
  const count = batchSentences().length;
  $('#batch-count').textContent = `${count} test sentence${count===1?'':'s'} · maximum 100`;
}
function renderBatchResults(items) {
  const host = $('#batch-results');
  host.hidden = false;
  host.innerHTML = items.map((item,index)=>{
    const record=item.record;
    const status=item.status==='fallback_after_error'?'FALLBACK':(item.status==='partial'?'PARTIAL':(item.error?'ERROR':(record.claims.length?'CLAIMS':'UNRESOLVED')));
    const cls=item.status==='fallback_after_error'||item.status==='partial'?'warning':(item.error?'error':(record.claims.length?'success':'warning'));
    const incomplete=(record.claims||[]).filter(c=>c.completeness && c.completeness.status!=='complete').length;
    const details=item.error?item.error:`${record.engine} · ${record.claims.length} claim${record.claims.length===1?'':'s'} · ${(record.unresolved||[]).length} unresolved · ${incomplete} underspecified · ${(record.warnings||[]).length} warnings`;
    return `<article class="batch-result-item"><div class="batch-result-top"><span class="batch-index">${String(index+1).padStart(2,'0')}</span><span class="batch-result-text">${escapeHtml(item.sourceText)}</span><span class="batch-status ${cls}">${status}</span></div><small>${escapeHtml(details)}</small></article>`;
  }).join('');
}
async function runBatchTests() {
  if (batchRunning) return;
  const sentences=batchSentences();
  if (!sentences.length) { showToast('Enter at least one test sentence.',true); return; }
  if (sentences.length>100) { showToast('Please limit a batch to 100 sentences.',true); return; }
  if (!localRuntimeAvailable || !ollamaAvailable || !$('#model-select').value) {
    showToast('Ollama is not connected. This batch will use the local rule interpreter.',true);
  }
  batchRunning=true;
  const runButton=$('#batch-run-button');
  runButton.disabled=true; runButton.textContent='Running batch…';
  $('#batch-clear-button').disabled=true;
  $('#batch-export-button').disabled=true;
  $('#batch-progress').hidden=false;
  $('#batch-results').hidden=true;
  $('#batch-progress-bar').style.width='0%';
  const startedAt=nowIso();
  const model=(localRuntimeAvailable && ollamaAvailable)?$('#model-select').value:null;
  const items=[];
  try {
    for (let i=0;i<sentences.length;i++) {
      const sourceText=sentences[i];
      $('#batch-progress-label').textContent=`Analyzing: ${sourceText.slice(0,72)}${sourceText.length>72?'…':''}`;
      $('#batch-progress-count').textContent=`${i} / ${sentences.length}`;
      try {
        const analyzed=await interpretForBatch(sourceText);
        const record=analyzed.record;
        items.push({index:i+1,sourceText,status:batchStatusForRecord(record),engine:record.engine,rawModelResponse:analyzed.rawModelResponse,modelGenerationAudit:analyzed.modelGenerationAudit || null,record:toExportableInterpretation(record)});
      } catch(error) {
        const fallback=localInterpret(sourceText);
        const failureAudit=generationFailureAudit(error);
        fallback.modelGenerationAudit=failureAudit;
        fallback.modelFailureDiagnostic=error.diagnostic||null;
        fallback.warnings=[...(fallback.warnings||[]),`Batch LLM request failed (${error.failureCategory||'model_request_error'}): ${error.message}. This item uses the local rule fallback; the generation failure audit is retained.`];
        items.push({
          index:i+1,sourceText,status:'fallback_after_error',engine:fallback.engine,
          rawModelResponse:error.modelOutput??null,modelGenerationAudit:failureAudit,
          failureCategory:error.failureCategory||'model_request_error',diagnostic:error.diagnostic||null,
          error:error.message,record:toExportableInterpretation(fallback)
        });
      }
      $('#batch-progress-count').textContent=`${i+1} / ${sentences.length}`;
      $('#batch-progress-bar').style.width=`${Math.round(((i+1)/sentences.length)*100)}%`;
      renderBatchResults(items);
    }
    latestBatchExport=createBatchExport(items,model,startedAt,model?$('#ollama-url').value.trim():null);
    $('#batch-progress-label').textContent='Batch complete';
    $('#batch-export-button').disabled=false;
    $('#batch-export-note').textContent=`Completed ${items.length} tests. Export the JSON and share it here for review.`;
    showToast(`Batch complete: ${items.length} test${items.length===1?'':'s'} processed.`);
  } finally {
    batchRunning=false;
    runButton.disabled=false; runButton.innerHTML='Run batch tests <span>→</span>';
    $('#batch-clear-button').disabled=false;
  }
}
function exportBatchJson() {
  if (!latestBatchExport) return;
  const stamp=new Date().toISOString().replace(/[:.]/g,'-');
  downloadJson(`usg-batch-results-${stamp}.json`,latestBatchExport);
  showToast('Batch JSON exported.');
}

function renderInterpretation(result) {
  $('#interpret-results').hidden = false;
  $('#interpret-empty').hidden = true;
  $('#result-title').textContent = result.claims.length ? 'Candidate semantic interpretation' : 'No semantic claim created';
  $('#result-subtitle').textContent = result.engine === 'local_llm' ? 'Proposed by your local language model. Verify before accepting.' : 'Produced by the explicit local rule interpreter.';
  const badge = $('#result-status');
  badge.textContent = result.claims.length ? (result.engine==='local_llm'?'LLM PROPOSAL':'RULE PROPOSAL') : 'UNRESOLVED';
  badge.className = `result-badge ${result.claims.length?'':'unresolved'}`;
  renderMeaning(result);
  renderStructure(result);
  renderEvidence(result);
  $('#raw-json').textContent = JSON.stringify(toExportableInterpretation(result), null, 2);
  setResultTab('meaning');
  $('#accept-button').disabled = !result.claims.length;
  $('#accept-button').style.opacity = result.claims.length ? '1' : '.45';
}
function toExportableInterpretation(result) {
  const enriched = result?.schemaVersion === SEMANTIC_SCHEMA_VERSION ? result : enrichV04Record(result);
  return { schema:'USG-SEMANTIC-RECORD', schemaVersion:SEMANTIC_SCHEMA_VERSION, representationProfile:'USG-SR/0.5.1', analyzedAt:nowIso(), ...enriched };
}
function renderMeaning(result) {
  const host = $('#result-tab-meaning');
  let html = `<div class="interpretation-overview"><small>INTERPRETATION</small><p>${escapeHtml(result.interpretation)}</p></div>`;
  const audit=result.modelGenerationAudit;
  if(audit) {
    const trace=(audit.generation||[]).map(x=>`${escapeHtml(x.phase||'model')} · ${escapeHtml(x.eval_count??'token count unavailable')} tokens · budget ${escapeHtml(x.requested_num_predict??'adaptive')} · ${escapeHtml(x.tokens_per_second??'n/a')} tok/s`).join('<br>');
    const findings=[...(audit.finalDiagnostics||[]),...(audit.reviewerIssues||[])].filter(x=>x&&x.problem).map(x=>`<li><b>${escapeHtml(x.code||x.severity||'finding')}</b>: ${escapeHtml(x.problem)}</li>`).join('');
    const failedArtifacts=(audit.generationArtifacts||[]).filter(x=>x&&x.status==='request_failed');
    const failureLines=failedArtifacts.map(x=>`<li><b>${escapeHtml(x.failureCategory||'request_failed')}</b>: ${escapeHtml(x.error||'Request failed.')}</li>`).join('');
    const failureDetails=audit.failure?`<p class="claim-explain">Failure category: ${escapeHtml(audit.failure.category||'unknown')} · ${escapeHtml(audit.failure.message||'')}</p>`:'';
    const fullAudit=(audit.generationArtifacts||[]).length?`<details><summary>Raw generation/review/repair artifacts (${(audit.generationArtifacts||[]).length})</summary><pre>${escapeHtml(JSON.stringify(audit.generationArtifacts,null,2))}</pre></details>`:'';
    html += `<div class="condition-box"><b>MODEL GENERATION · DIAGNOSIS · REPAIR</b><p>Status: ${escapeHtml(audit.status||'unknown')} · repair rounds: ${escapeHtml(audit.repairRounds??0)} · second-pass review (same model): ${escapeHtml(audit.reviewerStatus||'not run')} (${escapeHtml(audit.reviewerAssessment||'unknown')})</p>${trace?`<p class="claim-explain">${trace}</p>`:''}${failureDetails}${failureLines?`<b>Failed model stages</b><ul>${failureLines}</ul>`:''}${findings?`<ul>${findings}</ul>`:''}${fullAudit}<p class="claim-explain">The reviewer is a second pass by the same model, not an independent evaluator. This audit reports detected defects; it is not proof of semantic correctness.</p></div>`;
  }
  (result.explanations || []).forEach(link => {
    const cause = result.claims.find(c => c.id === link.causeClaimId);
    const effect = result.claims.find(c => c.id === link.effectClaimId);
    if (!cause || !effect) return;
    html += `<div class="condition-box"><b>SOURCE-ASSERTED CAUSAL EXPLANATION</b><p>${escapeHtml(cause.subject.text)} ${escapeHtml(cause.predicate)} → ${escapeHtml(effect.subject.text)} ${escapeHtml(effect.predicate)}. Evidence: “${escapeHtml(link.evidenceText || '')}”.</p><p>${escapeHtml(link.note || '')}</p></div>`;
  });
  if (result.claims.length) {
    result.claims.forEach((claim, i) => {
      const object = claim.object?.text || '∅';
      const conditions = claim.conditions?.length ? claim.conditions.map(c => { const p=c.proposition||{}; const ps=typeof p.subject==='object'?(p.subject?.text||'condition'):(p.subject||'condition'); const po=typeof p.object==='object'?(p.object?.text||''):(p.object||''); return `<div class="condition-box"><b>${escapeHtml((c.marker||'condition').toUpperCase())} · ${escapeHtml(c.effect||'condition')}</b><p>${escapeHtml(ps)} ${escapeHtml(p.predicate||'')} ${escapeHtml(po)} — ${escapeHtml(c.consequence||'unspecified')}. Tense: ${escapeHtml(p.tense||'unknown')}. ${c.evidenceText?`Evidence: “${escapeHtml(c.evidenceText)}”`:''}</p></div>`; }).join('') : '';
      const completenessNote = claim.completeness?.status && claim.completeness.status!=='complete' ? `<div class="unresolved-box"><span class="unresolved-symbol">!</span><div><b>Underspecified claim</b><p>${escapeHtml(claim.completeness.note || `Missing roles: ${(claim.completeness.missingRoles||[]).join(', ')}`)}</p></div></div>` : '';
      const comparisonNote=claim.comparisonFrame?`<div class="condition-box"><b>COMPARISON FRAME</b><p>${escapeHtml(claim.comparisonFrame.note)} Context required for: ${escapeHtml((claim.comparisonFrame.requiredFor||[]).join(', '))}</p></div>`:'';
      const quantifierNote=claim.quantifierScope?`<div class="condition-box"><b>QUANTIFIER SCOPE</b><p>${escapeHtml(claim.quantifierScope.logicalForm)} · ${escapeHtml(claim.quantifierScope.interpretation)}</p></div>`:'';
      const modalNote=claim.modalScope?`<p class="claim-explain">Modal operator: ${escapeHtml(claim.modalScope.operator)} · force: ${escapeHtml(claim.modalScope.force)} · scope: ${escapeHtml(claim.modalScope.scope)}</p>`:'';
      const timeNote=claim.time?`<p class="claim-explain">Time frame: ${escapeHtml(claim.time.grammaticalTense)} · aspect: ${escapeHtml(claim.time.aspect)} · reference: ${escapeHtml(claim.time.referenceTime)}</p>`:'';
      const eventNote=(claim.eventAttributes||[]).map(a=>`<p class="claim-explain">Event attribute: ${escapeHtml(a.type)} = ${escapeHtml(a.value)}${a.normalizedValue?` (${escapeHtml(a.normalizedValue)})`:''}</p>`).join('');
      html += `<article class="claim-card"><div class="claim-card-head"><b>Candidate claim ${i+1}</b><div class="claim-tags"><span class="mini-tag ${claim.polarity==='negative'?'negative':'positive'}">${escapeHtml(claim.polarity.toUpperCase())}</span><span class="mini-tag">${escapeHtml(claim.tense.toUpperCase())}</span><span class="mini-tag">${escapeHtml(claim.modality.toUpperCase())}</span></div></div><div class="triple-line"><span class="triple-entity">${escapeHtml(claim.subject.text)}</span><span class="triple-predicate">${escapeHtml(claim.predicate)}</span><span class="triple-entity">${escapeHtml(object)}</span></div><p class="claim-explain">Subject type: ${escapeHtml(claim.subject.type)} · Subject reference: ${escapeHtml(claim.subject.reference||'unknown')} · Object type: ${escapeHtml(claim.object?.type||'none')} · Object reference: ${escapeHtml(claim.object?.reference||'unknown')} · ${escapeHtml(claim.provenance==='local_llm_proposal'?'Local LLM proposal':'Local pattern match')} · ${Math.round((claim.confidence||0)*100)}% reported confidence</p>${timeNote}${modalNote}${eventNote}${quantifierNote}${comparisonNote}${completenessNote}${conditions}</article>`;
    });
  } else if (!(result.unresolved || []).length) {
    html += '<div class="unresolved-box"><span class="unresolved-symbol">?</span><div><b>Unresolved</b><p>No supported semantic claim was produced.</p></div></div>';
  }
  (result.unresolved || []).forEach(item => html += `<div class="unresolved-box"><span class="unresolved-symbol">?</span><div><b>Unresolved</b><p>${escapeHtml(item)}</p></div></div>`);
  (result.warnings||[]).forEach(w => html += `<p class="claim-explain" style="margin:9px 2px">ⓘ ${escapeHtml(w)}</p>`);
  host.innerHTML = html;
}
function renderStructure(result) {
  const host = $('#result-tab-structure');
  if (!result.claims.length && !result.semanticModel?.expressions?.length) { const unresolved=(result.semanticModel?.unresolvedItems||[]).map(item=>`<li><b>${escapeHtml(item.status)}</b> · ${escapeHtml(item.reason)} ${item.surfaceText?`<blockquote>${escapeHtml(item.surfaceText)}</blockquote>`:''}</li>`).join(''); host.innerHTML = `<div class="empty-state">No semantic propositions were created. USG did not invent a claim where the source could not be represented safely.</div>${unresolved?`<div class="unresolved-box"><b>Unresolved semantic items</b><ul>${unresolved}</ul></div>`:''}`; return; }
  let rows = '';
  result.claims.forEach((claim, index) => {
    rows += `<tr><td>c${index+1}</td><td><b>${escapeHtml(claim.subject.text)}</b></td><td>${escapeHtml(claim.subject.type)} · ${escapeHtml(claim.subject.reference||'unknown')}</td><td>SUBJECT · ${escapeHtml(claim.tense || 'unknown')} TENSE</td></tr>`;
    if (claim.object) rows += `<tr><td>c${index+1}o</td><td><b>${escapeHtml(claim.object.text)}</b></td><td>${escapeHtml(claim.object.type)} · ${escapeHtml(claim.object.reference||'unknown')}</td><td>OBJECT</td></tr>`;
    (claim.completeness?.missingRoles || []).forEach((role, roleIndex) => rows += `<tr><td>c${index+1}m${roleIndex+1}</td><td><b>Not specified</b></td><td>unknown</td><td>MISSING ROLE (${escapeHtml(role)})</td></tr>`);
    (claim.conditions || []).forEach((condition, conditionIndex) => {
      const conditionSubject = (typeof condition.proposition?.subject==='object' ? condition.proposition.subject?.text : condition.proposition?.subject) || condition.evidenceText || 'condition';
      rows += `<tr><td>c${index+1}cond${conditionIndex+1}</td><td><b>${escapeHtml(conditionSubject)}</b></td><td>unknown</td><td>CONDITION (${escapeHtml(condition.marker || 'if')})</td></tr>`;
    });
  });
  (result.explanations || []).forEach((link, index) => {
    const causeIndex = result.claims.findIndex(c => c.id === link.causeClaimId);
    const effectIndex = result.claims.findIndex(c => c.id === link.effectClaimId);
    if (causeIndex >= 0 && effectIndex >= 0) rows += `<tr><td>x${index+1}</td><td>c${causeIndex+1} → c${effectIndex+1}</td><td>${escapeHtml(link.type)}</td><td>EXPLANATION (${escapeHtml(link.attribution || 'source_asserted')})</td></tr>`;
  });
  (result.mentions || []).forEach((mention,index) => { rows += `<tr><td>m${index+1}</td><td><b>${escapeHtml(mention.surfaceText||'')}</b></td><td>${escapeHtml(mention.canonicalText||'')} · ${escapeHtml(mention.entityId||'')}</td><td>${escapeHtml(mention.mentionType||'MENTION')}</td></tr>`; });
  (result.claimRelations || []).forEach((relation,index) => { const from=result.claims.findIndex(c=>c.id===relation.fromClaimId),to=result.claims.findIndex(c=>c.id===relation.toClaimId); rows += `<tr><td>r${index+1}</td><td>c${from+1} ↔ c${to+1}</td><td>${escapeHtml(relation.status||'candidate')}</td><td>${escapeHtml(relation.type)}</td></tr>`; });
  const model=result.semanticModel;
  const expressionLabel=expression=>{
    if(expression.type==='PREDICATION') return `${expression.predicate}(${(expression.arguments||[]).map(a=>a.variableId ? `${a.variableId}∈${model.entities.find(e=>e.id===a.bindingEntityId)?.canonicalText||a.bindingEntityId}` : (a.entityId ? (model.entities.find(e=>e.id===a.entityId)?.canonicalText||a.entityId) : '∅')).join(', ')})`;
    if(expression.type==='OPERATOR') return `${expression.operator} → ${expression.scope?.targetId||'missing scope'}`;
    if(expression.type==='CONNECTIVE') return `${expression.connective} → ${(expression.operandIds||[expression.antecedentId,expression.consequentId]).filter(Boolean).join(' + ')}`;
    return expression.type;
  };
  const graphRows=model?.expressions?.map(e=>`<tr><td>${escapeHtml(e.id)}</td><td><b>${escapeHtml(e.type)}</b></td><td>${escapeHtml(expressionLabel(e))}</td><td>${escapeHtml(e.operatorType||e.marker||'—')}</td></tr>`).join('')||'';
  const unresolvedRows=(model?.unresolvedItems||[]).map(item=>`<li><b>${escapeHtml(item.status)}</b> · ${escapeHtml(item.reason)} ${item.surfaceText?`<blockquote>${escapeHtml(item.surfaceText)}</blockquote>`:''}</li>`).join('');
  const unresolvedPanel=unresolvedRows?`<div class="unresolved-box"><b>Unresolved / unsupported semantic content</b><ul>${unresolvedRows}</ul></div>`:'';
  const graphPanel=model?`<div class="claim-card" style="margin-top:14px"><div class="panel-kicker">CANONICAL SEMANTIC EXPRESSION GRAPH · ${escapeHtml(model.profile)}</div><p class="claim-explain">${model.entities.length} entities · ${model.mentions.length} mentions · ${model.expressions.length} expressions · ${model.relations.length} relations · ${model.unresolvedItems?.length||0} unresolved items · validation: ${escapeHtml(result.semanticValidation?.status||'unknown')}</p><table class="structure-table"><thead><tr><th>Expression ID</th><th>Node</th><th>Meaning / target</th><th>Operator</th></tr></thead><tbody>${graphRows}</tbody></table><p class="claim-explain">Root expressions: ${escapeHtml((model.rootExpressionIds||[]).join(', ')||'none')}. This graph is the canonical compositional view; the claims array remains a compatibility projection.</p>${unresolvedPanel}</div>`:'<div class="unresolved-box"><p>Canonical semantic graph unavailable. Check that semantic-core.js loaded successfully.</p></div>';
  host.innerHTML = `<table class="structure-table"><thead><tr><th>ID</th><th>Surface form</th><th>Semantic class</th><th>Role</th></tr></thead><tbody>${rows}</tbody></table><div class="claim-card" style="margin-top:14px"><div class="panel-kicker">COMPATIBILITY PROPOSITION VIEW</div>${result.claims.map(c=>`<p class="claim-explain" style="margin-top:8px"><b>${escapeHtml(c.predicate)}</b> · polarity=${escapeHtml(c.polarity)} · tense=${escapeHtml(c.tense)} · modality=${escapeHtml(c.modality)} · quantifier=${escapeHtml(c.quantifierScope?.operator||'none')} · conditions=${c.conditions.length} · causal links=${(c.causalLinks||[]).length}</p>`).join('')}</div>${graphPanel}`;
}
function renderEvidence(result) {
  const host = $('#result-tab-evidence');
  host.innerHTML = `<div class="evidence-card"><small>ORIGINAL SOURCE TEXT</small><blockquote>${escapeHtml(result.sourceText)}</blockquote><p>Source preserved as entered by the user.</p></div>`;
  result.claims.forEach((claim, i) => {
    const ev = claim.evidence || {};
    const quoteStatus = ev.verified ? 'Stored evidence span is an exact substring of the original source.' : 'Stored evidence span could not be verified as an exact source substring.';
    const modelQuoteStatus = ev.modelQuoteVerified === false ? ' The model-provided quote was not exact; the full source was retained as the verified span.' : (ev.modelQuoteVerified === true ? ' The model-provided quote was found verbatim in the source.' : ' No separate verified model quote was recorded.');
    host.innerHTML += `<div class="evidence-card"><small>CLAIM ${i+1} · ${escapeHtml(claim.provenance)}</small><blockquote>${escapeHtml(ev.quote || result.sourceText)}</blockquote><p>${quoteStatus}${modelQuoteStatus} · Rule: ${escapeHtml(claim.ruleId || (claim.provenance==='local_llm_proposal'?'LLM_STRUCTURED_PROPOSAL':'LOCAL_STARTER_PATTERN'))}</p></div>`;
  });
  (result.explanations || []).forEach(link => {
    host.innerHTML += `<div class="evidence-card"><small>CAUSAL LINK · ${escapeHtml(link.attribution || 'source_asserted')}</small><blockquote>${escapeHtml(link.evidence?.quote || link.evidenceText || '')}</blockquote><p>${escapeHtml(link.note || 'Source-attributed explanatory relation; not independently verified.')}</p></div>`;
  });
  if (result.engine==='local_llm') host.innerHTML += '<div class="evidence-card"><small>MODEL PROVENANCE</small><p>Generated by a locally installed Ollama model. This records where the proposal came from; it does not independently verify correctness.</p></div>';
}
function setResultTab(name) {
  $$('.result-tab').forEach(b=>b.classList.toggle('active',b.dataset.resultTab===name));
  ['meaning','structure','evidence','raw'].forEach(tab => $(`#result-tab-${tab}`).hidden = tab!==name);
}
function acceptInterpretation() {
  if (!currentInterpretation?.claims?.length) return;
  if (currentInterpretation.semanticValidation && (currentInterpretation.semanticValidation.valid !== true || currentInterpretation.semanticValidation.status === 'partial' || (currentInterpretation.semanticModel?.unresolvedItems || []).length > 0)) {
    showToast('The semantic foundation contains unresolved or invalid structure. Resolve it before accepting this interpretation.', true);
    return;
  }
  let added = 0;
  const acceptedIdMap = new Map();
  for (const proposed of currentInterpretation.claims) {
    const duplicate = state.claims.find(c => norm(c.subject.text)===norm(proposed.subject.text) && c.predicate===proposed.predicate && norm(c.object?.text||'')===norm(proposed.object?.text||'') && c.polarity===proposed.polarity && JSON.stringify(c.conditions||[])===JSON.stringify(proposed.conditions||[]));
    if (duplicate) {
      acceptedIdMap.set(proposed.id, duplicate.id);
      continue;
    }
    const accepted = { ...proposed, id:uid('k'), causalLinks:[], provenance:proposed.provenance==='local_llm_proposal'?'accepted_local_llm_proposal':'accepted_local_rule_proposal', sourceKind:'accepted_interpretation', createdAt:nowIso() };
    state.claims.push(accepted);
    acceptedIdMap.set(proposed.id, accepted.id);
    added++;
  }
  // Rebind proposal-local causal references to the IDs actually stored in the KB.
  for (const proposed of currentInterpretation.claims) {
    if (!(proposed.causalLinks || []).length) continue;
    const acceptedId = acceptedIdMap.get(proposed.id);
    const stored = state.claims.find(c => c.id === acceptedId);
    if (!stored) continue;
    const remapped = proposed.causalLinks.map(link => ({
      ...link,
      causeClaimId:acceptedIdMap.get(link.causeClaimId) || link.causeClaimId,
      effectClaimId:acceptedIdMap.get(link.effectClaimId) || link.effectClaimId
    }));
    stored.causalLinks = [...(stored.causalLinks || []), ...remapped.filter(link => !(stored.causalLinks || []).some(existing => existing.type===link.type && existing.causeClaimId===link.causeClaimId && existing.effectClaimId===link.effectClaimId))];
  }
  // Persist analysis-level claim relations with knowledge-base IDs, separately from propositions.
  state.relations = Array.isArray(state.relations) ? state.relations : [];
  for (const relation of currentInterpretation.claimRelations || []) {
    const fromClaimId=acceptedIdMap.get(relation.fromClaimId), toClaimId=acceptedIdMap.get(relation.toClaimId);
    if (!fromClaimId || !toClaimId) continue;
    if (!state.relations.some(existing=>existing.type===relation.type && existing.fromClaimId===fromClaimId && existing.toClaimId===toClaimId)) {
      state.relations.push({...relation,id:uid('rel'),fromClaimId,toClaimId,status:'accepted_candidate_requires_review',acceptedAt:nowIso()});
    }
  }
  saveState();
  if (added) showToast(`${added} semantic claim${added===1?'':'s'} added to the knowledge base.`);
  else showToast('These claims already exist in the knowledge base.');
  renderInterpretation(currentInterpretation);
  $('#accept-button').textContent = 'Accepted ✓';
  $('#accept-button').disabled = true;
}

// ---------------------- Knowledge base ----------------------
function claimSentence(claim) {
  const s = claim.subject?.text || '?'; const o = claim.object?.text || '∅'; const predicate = claim.predicate || 'RELATED_TO';
  if (predicate === 'DIFFER' && !claim.object) {
    const plural = /(?:s|prices|values|numbers)$/i.test(s);
    const auxiliary = claim.tense === 'past' ? (plural ? 'were' : 'was') : (plural ? 'are' : 'is');
    return `${s} ${auxiliary} ${claim.polarity === 'negative' ? 'not ' : ''}different`;
  }
  if (predicate === 'CHANGE' && !claim.object) {
    return `${s} ${claim.polarity === 'negative' ? 'did not change' : claim.tense === 'past' ? 'changed' : 'changes'}`;
  }
  const positive = { SUBCLASS_OF:'is a subclass of', INSTANCE_OF:'is an instance of', MEASURES:'measures', NEEDS:'needs', LIKE:'likes', PART_OF:'is part of', CAUSES:'causes', HAS_PROPERTY:'has property', DIFFER:'differs from', CHANGE:'changes' };
  const negative = { SUBCLASS_OF:'is not a subclass of', INSTANCE_OF:'is not an instance of', MEASURES:'does not measure', NEEDS:'does not need', LIKE:'does not like', PART_OF:'is not part of', CAUSES:'does not cause', HAS_PROPERTY:'does not have property', DIFFER:'does not differ from', CHANGE:'does not change' };
  const verb = (claim.polarity === 'negative' ? negative[predicate] : positive[predicate]) || `${claim.polarity === 'negative' ? 'does not ' : ''}${predicate.toLowerCase().replaceAll('_',' ')}`;
  return `${s} ${verb} ${o}`;
}
function provenanceLabel(value) {
  return ({demo_seed:'Starter example',user_entry:'User entry',accepted_local_rule_proposal:'Accepted · local rule',accepted_local_llm_proposal:'Accepted · local LLM',accepted_interpretation:'Accepted interpretation'})[value] || value || 'Unknown source';
}
function renderKnowledge() {
  const query = norm($('#knowledge-search')?.value || '');
  const rows = state.claims.filter(c => !query || [c.subject?.text,c.predicate,c.object?.text,c.evidence?.sourceText,c.evidence?.quote].some(v=>norm(v||'').includes(query)));
  $('#knowledge-summary').innerHTML = `<span class="summary-chip">${state.claims.length} explicit claims</span><span class="summary-chip">${allEntities().length} concepts</span><span class="summary-chip">${state.claims.filter(c=>c.conditions?.length).length} conditional records</span>`;
  $('#knowledge-list').innerHTML = rows.map(claim => `<article class="knowledge-card"><span class="knowledge-id">${escapeHtml(claim.id.slice(0,7))}</span><div class="knowledge-main"><b>${escapeHtml(claimSentence(claim))}</b><small>${escapeHtml(claim.evidence?.sourceText || claim.note || 'No source text supplied.')}${claim.conditions?.length?' · contains condition':''}${claim.causalLinks?.length?' · has causal explanation':''}</small></div><span class="knowledge-relation">${escapeHtml(relationLabel(claim.predicate))}</span><span class="knowledge-origin">${escapeHtml(provenanceLabel(claim.provenance))}</span><button class="knowledge-delete" data-delete-claim="${escapeHtml(claim.id)}" title="Delete claim" aria-label="Delete claim">×</button></article>`).join('');
  $('#knowledge-empty').hidden = rows.length !== 0;
}
function addManualFact(event) {
  event.preventDefault();
  const subject = cleanLabel($('#fact-subject').value);
  const predicate = $('#fact-predicate').value;
  const object = cleanLabel($('#fact-object').value);
  const evidenceText = cleanLabel($('#fact-evidence').value);
  if (!subject || !object) { showToast('Enter both a subject and an object.', true); return; }
  const claim = buildClaim(subject,predicate,object,{subjectType:entityTypeFor(predicate,'subject'),objectType:entityTypeFor(predicate,'object'),provenance:'user_entry',sourceKind:'user_observation',evidence:makeEvidence(evidenceText || `User-entered fact: ${subject} ${predicate} ${object}.`),confidence:1,note:'Manually entered by the user.'});
  state.claims.push(claim); state.derived=[]; saveState(); $('#add-claim-dialog').close(); $('#add-claim-form').reset(); renderKnowledge(); showToast('Fact added to the knowledge base.');
}

// ---------------------- Symbolic reasoning engine ----------------------
function tupleKey(claim) { return [norm(claim.subject?.text),claim.predicate,norm(claim.object?.text||''),claim.polarity||'positive'].join('|'); }
function runReasoning() {
  const explicit = state.claims.filter(c => c.polarity==='positive' && c.modality==='asserted' && !c.quantifierScope && (!c.conditions || c.conditions.length===0) && (!c.tense || c.tense==='present') && (!c.time || c.time.referenceTime==='present'));
  let working = explicit.map(c=>({...c, premiseIds:[c.id]}));
  const derived = [];
  let changed = true; let safety = 0;
  const has = (predicate, subject, object) => working.find(c=>c.predicate===predicate && norm(c.subject.text)===norm(subject) && norm(c.object?.text||'')===norm(object) && c.polarity==='positive');
  while (changed && safety < 20) {
    changed = false; safety++;
    const subclasses = working.filter(c=>c.predicate==='SUBCLASS_OF');
    const instances = working.filter(c=>c.predicate==='INSTANCE_OF');
    for (const first of subclasses) {
      for (const second of subclasses) {
        if (norm(first.object?.text||'')!==norm(second.subject.text)) continue;
        if (norm(first.subject.text)===norm(second.object?.text||'')) continue;
        if (has('SUBCLASS_OF',first.subject.text,second.object?.text)) continue;
        const item = buildClaim(first.subject.text,'SUBCLASS_OF',second.object.text,{id:uid('d'),subjectType:'class',objectType:'class',provenance:'inference_engine',sourceKind:'derived',ruleId:'R-IS-A-TRANSITIVE',confidence:0.99,note:'Derived by subclass transitivity.'});
        item.premiseIds=[first.id,second.id]; item.premiseDescriptions=[claimSentence(first),claimSentence(second)];
        working.push(item); derived.push(item); changed=true;
      }
    }
    for (const instance of instances) {
      for (const sub of subclasses) {
        if (norm(instance.object?.text||'')!==norm(sub.subject.text)) continue;
        if (has('INSTANCE_OF',instance.subject.text,sub.object?.text)) continue;
        const item = buildClaim(instance.subject.text,'INSTANCE_OF',sub.object.text,{id:uid('d'),subjectType:'individual',objectType:'class',provenance:'inference_engine',sourceKind:'derived',ruleId:'R-INSTANCE-INHERITANCE',confidence:0.99,note:'Derived by instance inheritance.'});
        item.premiseIds=[instance.id,sub.id]; item.premiseDescriptions=[claimSentence(instance),claimSentence(sub)];
        working.push(item); derived.push(item); changed=true;
      }
    }
  }
  // Remove any duplicate derived tuples defensively.
  const unique = new Map(); for (const item of derived) if (!explicit.some(e=>tupleKey(e)===tupleKey(item))) unique.set(tupleKey(item),item);
  state.derived = [...unique.values()]; state.lastRunAt = nowIso(); saveState(); renderReasoning();
  showToast(`Reasoning completed: ${state.derived.length} new claim${state.derived.length===1?'':'s'} derived.`);
}
function renderReasoning() {
  const stats = $('#reasoning-stats');
  if (!state.lastRunAt) stats.innerHTML = '<div><small>LAST RUN</small><b>Not run yet</b></div><div><small>NEW DERIVATIONS</small><b>—</b></div><div><small>RULES ACTIVE</small><b>2</b></div>';
  else stats.innerHTML = `<div><small>LAST RUN</small><b>${new Date(state.lastRunAt).toLocaleString()}</b></div><div><small>NEW DERIVATIONS</small><b>${state.derived.length}</b></div><div><small>RULES ACTIVE</small><b>2</b></div>`;
  if (!state.derived.length) {
    $('#derived-list').innerHTML = `<div class="empty-state">${state.lastRunAt?'No new claims could be derived from the current knowledge base.':'Run reasoning to see which conclusions follow from the current knowledge base.'}</div>`;
    return;
  }
  $('#derived-list').innerHTML = state.derived.map((claim,index)=>`<article class="derived-card"><div><div class="claim-formula">${escapeHtml(claimSentence(claim))}</div><div class="claim-meta"><span>INFERRED</span><span>${escapeHtml(claim.ruleId)}</span><span>${Math.round(claim.confidence*100)}% engine confidence</span></div></div><div class="premises">Premises<br><b>${escapeHtml((claim.premiseIds||[]).join(' + '))}</b></div></article>`).join('');
}

// ---------------------- Pattern discovery ----------------------
function schemaFor(predicate) {
  const known = {
    MEASURES:'MEASURES(instrument → measurable_property)', SUBCLASS_OF:'SUBCLASS_OF(class → class)', INSTANCE_OF:'INSTANCE_OF(individual → class)',
    NEEDS:'NEEDS(agent_or_topic → required_object)', PART_OF:'PART_OF(component → whole)', CAUSES:'CAUSES(cause → effect)', HAS_PROPERTY:'HAS_PROPERTY(entity → property)'
  };
  return known[predicate] || `${predicate}(subject → object)`;
}
function renderPatterns() {
  const accepted = state.patterns.filter(p=>p.accepted);
  $('#accepted-count').textContent = `${accepted.length} accepted`;
  $('#accepted-patterns').innerHTML = accepted.map(p=>`<article class="pattern-card"><div class="pattern-status"><span>ACCEPTED SCHEMA</span><span>${p.supportCount} supporting observation${p.supportCount===1?'':'s'}</span></div><div class="pattern-formula">${escapeHtml(p.schema)}</div><div class="pattern-description">${escapeHtml(p.description || 'A reusable relation schema retained after review.')}</div><div class="pattern-support">${p.origin==='starter_schema'?'Starter schema from v0.1 demo knowledge.':`Reviewed ${new Date(p.acceptedAt || nowIso()).toLocaleDateString()}.`}</div></article>`).join('') || '<div class="empty-state">No accepted schemas yet.</div>';
  const acceptedPredicates = new Set(accepted.map(p=>p.predicate));
  const groups = new Map();
  for (const claim of state.claims) {
    const key = claim.predicate;
    if (!groups.has(key)) groups.set(key,[]);
    groups.get(key).push(claim);
  }
  const candidates = [...groups.entries()].filter(([predicate,claims])=>!acceptedPredicates.has(predicate) && new Set(claims.map(c=>`${norm(c.subject.text)}|${norm(c.object?.text||'')}`)).size>=2).map(([predicate,claims])=>({predicate,claims}));
  $('#candidate-count').textContent = `${candidates.length} candidate${candidates.length===1?'':'s'}`;
  $('#candidate-patterns').innerHTML = candidates.map(item=>`<article class="candidate-card"><span class="candidate-symbol">◇</span><div class="candidate-details"><b>${escapeHtml(schemaFor(item.predicate))}</b><small>${item.claims.length} observations across distinct entity pairs · predicate repetition detected</small></div><button class="secondary-button" data-accept-pattern="${escapeHtml(item.predicate)}">Review & accept</button></article>`).join('') || '<div class="empty-state">No new candidate patterns found. Add observations with a repeated relation, then run discovery.</div>';
}
function discoverPatterns() {
  renderPatterns();
  showToast('Pattern scan complete. Only repeated predicates with distinct entity pairs are proposed.');
}
function acceptPattern(predicate) {
  const claims = state.claims.filter(c=>c.predicate===predicate);
  if (claims.length<2) return;
  state.patterns.push({id:uid('p'),predicate,schema:schemaFor(predicate),description:`A candidate schema based on repeated ${predicate} observations. Review for exceptions before treating it as broadly applicable.`,supportIds:claims.map(c=>c.id),supportCount:claims.length,accepted:true,origin:'user_reviewed',acceptedAt:nowIso()});
  saveState(); renderPatterns(); showToast(`Accepted schema: ${predicate}.`);
}

// ---------------------- Model settings and API connection ----------------------
function getModelSettings() {
  try { return JSON.parse(localStorage.getItem('usg_model_settings_v02') || '{}'); } catch { return {}; }
}
function saveModelSettings() {
  const settings = { ollamaUrl:$('#ollama-url').value.trim().replace(/\/$/,''), model:$('#model-select').value };
  localStorage.setItem('usg_model_settings_v02',JSON.stringify(settings));
  showToast('Local model settings saved.');
}
async function checkModelConnection() {
  const message = $('#model-message');
  const button = $('#check-model-button');
  button.disabled = true; button.textContent = 'Checking…';
  ollamaAvailable = false; installedModels = [];
  try {
    if (!localRuntimeAvailable) throw new Error('The local bridge is not available. Launch with launch_windows.bat using Node.js; a plain static server does not include the model adapter.');
    const base = $('#ollama-url').value.trim().replace(/\/$/,'');
    const params = new URLSearchParams({ base });
    const response = await apiGet(`/api/models?${params.toString()}`);
    installedModels = Array.isArray(response.models) ? response.models : [];
    if (!installedModels.length) throw new Error('Ollama responded, but no installed models were found. Pull a model first, for example: ollama pull qwen2.5:3b');
    ollamaAvailable = true;
    const select = $('#model-select');
    const previous = select.value || getModelSettings().model || '';
    select.innerHTML = installedModels.map(m=>`<option value="${escapeHtml(m)}">${escapeHtml(m)}</option>`).join('');
    if (installedModels.includes(previous)) select.value = previous;
    $('#model-state-title').textContent = 'Ollama is connected';
    $('#model-state-copy').textContent = `${installedModels.length} locally installed model${installedModels.length===1?'':'s'} detected. Choose one to interpret language.`;
    message.textContent = `Connected. Models: ${installedModels.join(', ')}`;
    message.style.color = '#16845a';
    saveModelSettings(); updateEngineLabel();
  } catch (error) {
    $('#model-state-title').textContent = 'Local model not connected';
    $('#model-state-copy').textContent = 'The explicit local rule interpreter remains available.';
    message.textContent = error.message;
    message.style.color = '#a66d20';
    updateEngineLabel();
    showToast('Could not connect to a local model.', true);
  } finally {
    button.disabled = false; button.textContent = 'Check connection';
  }
}

// ---------------------- Import / export ----------------------
function downloadJson(filename, data) {
  const blob = new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href=url; a.download=filename; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
}
function exportWorkspace() {
  downloadJson(`usg-workbench-backup-${new Date().toISOString().slice(0,10)}.json`,{application:'USG Semantic Workbench',version:'0.5.4',semanticSchemaVersion:'0.5.1',exportedAt:nowIso(),state});
  showToast('Workspace backup exported.');
}
async function copyText(text) {
  try { await navigator.clipboard.writeText(text); showToast('Copied to clipboard.'); }
  catch {
    const el=document.createElement('textarea');el.value=text;document.body.appendChild(el);el.select();
    try { document.execCommand('copy'); showToast('Copied to clipboard.'); } catch { showToast('Clipboard access is unavailable in this browser.',true); }
    el.remove();
  }
}
function importWorkspace(file) {
  const reader=new FileReader();
  reader.onload=()=>{
    try {
      const parsed=JSON.parse(reader.result);
      const imported=parsed.state || parsed;
      if (imported.schemaVersion!==2 || !Array.isArray(imported.claims) || !Array.isArray(imported.patterns)) throw new Error('This file is not a valid USG Workbench backup.');
      if (!confirm(`Import ${imported.claims.length} claims and ${imported.patterns.length} schemas? This replaces the data currently saved in this browser.`)) return;
      state={...imported,derived:Array.isArray(imported.derived)?imported.derived:[],relations:Array.isArray(imported.relations)?imported.relations:[],interpretationHistory:Array.isArray(imported.interpretationHistory)?imported.interpretationHistory:[]};
      saveState();renderKnowledge();renderPatterns();renderReasoning();showToast('Workspace imported.');
    } catch(error) { showToast(error.message || 'Could not import this file.',true); }
  };
  reader.readAsText(file);
}

// ---------------------- Event wiring / initialization ----------------------
$$('.nav-item').forEach(button=>button.addEventListener('click',()=>navigate(button.dataset.view)));
$$('[data-go]').forEach(button=>button.addEventListener('click',()=>navigate(button.dataset.go)));
$('#source-text').addEventListener('input',()=>$('#char-count').textContent=`${$('#source-text').value.length} characters`);
$('#source-text').addEventListener('keydown',event=>{if(event.ctrlKey&&event.key==='Enter')analyzeSentence();});
$$('.example-chip').forEach(button=>button.addEventListener('click',()=>{ $('#source-text').value=button.dataset.example; $('#char-count').textContent=`${button.dataset.example.length} characters`; $('#source-text').focus(); }));
$('#analyze-button').addEventListener('click',analyzeSentence);
$('#batch-input').addEventListener('input',updateBatchCount);
$('#batch-run-button').addEventListener('click',runBatchTests);
$('#batch-clear-button').addEventListener('click',()=>{if(batchRunning)return;$('#batch-input').value='';latestBatchExport=null;$('#batch-results').hidden=true;$('#batch-progress').hidden=true;$('#batch-export-button').disabled=true;$('#batch-export-note').textContent='The JSON export includes each original sentence, engine, normalized semantic record, warnings, and errors.';updateBatchCount();});
$('#batch-export-button').addEventListener('click',exportBatchJson);
$$('.result-tab').forEach(button=>button.addEventListener('click',()=>setResultTab(button.dataset.resultTab)));
$('#accept-button').addEventListener('click',acceptInterpretation);
$('#reject-button').addEventListener('click',()=>{currentInterpretation=null;$('#interpret-results').hidden=true;$('#interpret-empty').hidden=false;showToast('Candidate interpretation discarded.');});
$('#copy-json-button').addEventListener('click',()=>{if(currentInterpretation)copyText(JSON.stringify(toExportableInterpretation(currentInterpretation),null,2));});
$('#knowledge-search').addEventListener('input',renderKnowledge);
$('#add-claim-button').addEventListener('click',()=>$('#add-claim-dialog').showModal());
$('#add-claim-form').addEventListener('submit',addManualFact);
$('#knowledge-list').addEventListener('click',event=>{const button=event.target.closest('[data-delete-claim]');if(!button)return;const id=button.dataset.deleteClaim;if(!confirm('Delete this explicit claim from the knowledge base?'))return;state.claims=state.claims.filter(c=>c.id!==id);state.derived=[];saveState();renderKnowledge();showToast('Claim deleted.');});
$('#run-reasoning-button').addEventListener('click',runReasoning);
$('#discover-patterns-button').addEventListener('click',discoverPatterns);
$('#candidate-patterns').addEventListener('click',event=>{const button=event.target.closest('[data-accept-pattern]');if(button)acceptPattern(button.dataset.acceptPattern);});
$('#check-model-button').addEventListener('click',checkModelConnection);
$('#save-model-button').addEventListener('click',saveModelSettings);
$('#model-select').addEventListener('change',()=>{updateEngineLabel();saveModelSettings();});
$('#export-button').addEventListener('click',exportWorkspace);
$('#knowledge-export-button').addEventListener('click',exportWorkspace);
$('#reset-demo-button').addEventListener('click',()=>{if(!confirm('Restore the starter demo knowledge and remove all locally added claims and patterns? Export a backup first if you want to keep your work.'))return;state=createInitialState();saveState();renderKnowledge();renderPatterns();renderReasoning();showToast('Starter demo workspace restored.');});
$('#import-button').addEventListener('click',()=>$('#import-file').click());
$('#import-file').addEventListener('change',event=>{const file=event.target.files?.[0];if(file)importWorkspace(file);event.target.value='';});

(function init(){
  const settings=getModelSettings();
  if(settings.ollamaUrl)$('#ollama-url').value=settings.ollamaUrl;
  renderKnowledge();renderPatterns();renderReasoning();refreshMetrics();checkRuntime();updateBatchCount();
  // Probe a saved local model configuration once the local API bridge has been detected.
  setTimeout(()=>{if(localRuntimeAvailable && settings.model)checkModelConnection();},700);
})();
