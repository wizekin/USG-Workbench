'use strict';

// USG generation diagnosis and repair utilities.
// Deliberately contains no maximum counts for claims, entities, mentions,
// relations, conditions, event attributes, or unresolved semantic content.

function text(value) {
  return typeof value === 'string' ? value.trim() : '';
}
function norm(value) {
  return text(value).toLowerCase().replace(/\s+/g, ' ').replace(/[“”]/g, '"').replace(/[’]/g, "'");
}
function entityText(value) {
  if (typeof value === 'string') return text(value);
  if (value && typeof value === 'object' && !Array.isArray(value)) return text(value.text || value.canonicalText || value.surfaceText);
  return '';
}
function issue(code, severity, location, problem, correction) {
  return { code, severity, location, problem, recommendedCorrection: correction };
}
function claimSignature(claim) {
  const subject = entityText(claim.subject);
  const object = entityText(claim.object);
  const conditions = Array.isArray(claim.conditions) ? claim.conditions.map(c => {
    const p = c && c.proposition || c || {};
    return [norm(c && c.marker), norm(entityText(p.subject)), norm(p.predicate), norm(entityText(p.object)), norm(p.polarity)].join('|');
  }).sort().join('||') : '';
  const scope = [claim.modalScope, claim.time, claim.quantifierScope, claim.comparisonFrame, claim.eventAttributes].map(value => {
    try { return JSON.stringify(value ?? null); } catch { return String(value); }
  }).join('|');
  return [norm(subject), norm(claim.predicate), norm(object), norm(claim.polarity), norm(claim.tense), norm(claim.modality), conditions, scope].join('|');
}

function diagnoseProposal(proposal, sourceText) {
  const issues = [];
  const source = String(sourceText || '');
  if (!proposal || typeof proposal !== 'object' || Array.isArray(proposal)) {
    return [issue('INVALID_ROOT', 'error', '$', 'The proposal is not a JSON object.', 'Return one complete JSON object matching the USG proposal contract.')];
  }
  const requiredArrays = ['claims', 'entities', 'mentions', 'claimRelations', 'unresolved'];
  for (const key of requiredArrays) {
    if (!Array.isArray(proposal[key])) issues.push(issue('MISSING_ARRAY', 'error', key, `The required ${key} field is missing or is not an array.`, `Return ${key} as an array. Do not omit any supported semantic items.`));
  }
  if (typeof proposal.intent !== 'string' || !proposal.intent.trim()) {
    issues.push(issue('MISSING_INTENT', 'error', 'intent', 'The proposal has no intent label.', 'Identify the source utterance intent without changing its meaning.'));
  }
  if (typeof proposal.interpretation !== 'string' || !proposal.interpretation.trim()) {
    issues.push(issue('MISSING_INTERPRETATION', 'warning', 'interpretation', 'The proposal has no plain-language interpretation.', 'Add a concise account of what the source states while preserving ambiguity.'));
  }

  const claims = Array.isArray(proposal.claims) ? proposal.claims : [];
  const seenClaims = new Map();
  claims.forEach((claim, index) => {
    const location = `claims[${index}]`;
    if (!claim || typeof claim !== 'object' || Array.isArray(claim)) {
      issues.push(issue('INVALID_CLAIM', 'error', location, 'A claim is not an object.', 'Replace it with a structured claim grounded in the source, or remove it if unsupported.'));
      return;
    }
    const subject = entityText(claim.subject);
    const predicate = text(claim.predicate);
    if (!subject) issues.push(issue('MISSING_SUBJECT', 'error', `${location}.subject`, 'The claim has no usable subject.', 'Identify the subject expressed or clearly referenced by the source.'));
    if (!predicate) issues.push(issue('MISSING_PREDICATE', 'error', `${location}.predicate`, 'The claim has no predicate.', 'Represent the relation or event actually expressed by the source.'));
    if (!['positive', 'negative', 'unknown'].includes(norm(claim.polarity))) {
      issues.push(issue('INVALID_POLARITY', 'error', `${location}.polarity`, 'The claim polarity is missing or invalid.', 'Represent polarity separately from predicate identity.'));
    }
    if (claim.evidence_text != null) {
      const quote = String(claim.evidence_text);
      if (!quote || !source.includes(quote)) {
        issues.push(issue('EVIDENCE_NOT_GROUNDED', 'error', `${location}.evidence_text`, 'The evidence quote is not an exact substring of the source.', 'Replace it with the exact source words that support this claim. Do not paraphrase evidence.'));
      }
    } else {
      issues.push(issue('MISSING_EVIDENCE', 'error', `${location}.evidence_text`, 'The claim has no source evidence quote.', 'Add an exact contiguous quote from the source that supports this claim.'));
    }
    if (Array.isArray(claim.conditions)) {
      claim.conditions.forEach((condition, conditionIndex) => {
        const cLoc = `${location}.conditions[${conditionIndex}]`;
        const proposition = condition && condition.proposition || condition;
        if (!condition || typeof condition !== 'object' || !proposition || typeof proposition !== 'object') {
          issues.push(issue('INVALID_CONDITION', 'error', cLoc, 'A condition is not represented as a structured proposition.', 'Represent the condition as a distinct proposition with its own subject, predicate, polarity, tense, and modality.'));
          return;
        }
        if (!entityText(proposition.subject) || !text(proposition.predicate)) {
          issues.push(issue('INCOMPLETE_CONDITION', 'error', cLoc, 'The condition proposition is missing its subject or predicate.', 'Repair the condition from the source, or mark only the genuinely indeterminate part unresolved.'));
        }
        const marker = norm(condition.marker);
        const expectedEffect = marker === 'unless' ? 'exception_to_assertion' :
          (marker === 'when' ? 'temporal_condition_for_assertion' : (marker === 'if' ? 'condition_for_assertion' : null));
        if (expectedEffect && condition.effect && norm(condition.effect) !== expectedEffect) {
          issues.push(issue('CONDITION_EFFECT_MISMATCH', 'error', `${cLoc}.effect`,
            `The ${marker.toUpperCase()} marker is paired with effect “${condition.effect}”, but USG's condition contract expects “${expectedEffect}”.`,
            `Set effect to “${expectedEffect}” while preserving the nested proposition and the parent claim as the scoped consequent.`));
        }
        const expectedStatus = marker === 'unless' ? 'exception_relation_asserted' :
          (marker === 'when' ? 'when_clause_not_asserted' : (marker === 'if' ? 'conditional_not_asserted' : null));
        if (expectedStatus && condition.logicalStatus && norm(condition.logicalStatus) !== expectedStatus) {
          issues.push(issue('CONDITION_LOGICAL_STATUS_MISMATCH', 'error', `${cLoc}.logicalStatus`,
            `The ${marker.toUpperCase()} marker has logicalStatus “${condition.logicalStatus}”, which conflicts with “${expectedStatus}”.`,
            `Preserve the marker-specific logical status: ${expectedStatus}.`));
        }
        const conditionEvidence = text(condition.evidence_text || condition.evidenceText);
        if (conditionEvidence && !source.includes(conditionEvidence)) {
          issues.push(issue('CONDITION_EVIDENCE_NOT_GROUNDED', 'error', `${cLoc}.evidence_text`,
            'The condition evidence is not an exact substring of the source.',
            'Use the exact subordinate-clause words from the source, without paraphrase.'));
        }
      });
    } else if (claim.conditions != null) {
      issues.push(issue('INVALID_CONDITIONS', 'error', `${location}.conditions`, 'Conditions must be represented as an array.', 'Return all source-expressed conditions as an array.'));
    }
    if (claim.eventAttributes != null && !Array.isArray(claim.eventAttributes)) {
      issues.push(issue('INVALID_EVENT_ATTRIBUTES', 'error', `${location}.eventAttributes`, 'Event attributes must be an array when present.', 'Return all source-expressed event attributes as an array.'));
    }
    const signature = claimSignature(claim);
    if (signature.replace(/\|/g, '').trim()) {
      const key = `${signature}|evidence:${norm(claim.evidence_text)}`;
      const evidence = text(claim.evidence_text);
      const evidenceOccurrences = evidence ? source.split(evidence).length - 1 : 0;
      if (seenClaims.has(key) && evidenceOccurrences <= 1) {
        issues.push(issue('DUPLICATE_CLAIM', 'error', location, `This claim duplicates claims[${seenClaims.get(key)}] with the same semantic content and a source phrase that occurs only once.`, 'Remove the genuine duplicate while preserving every distinct proposition, semantic scope, and repeated source occurrence.'));
      } else if (!seenClaims.has(key)) seenClaims.set(key, index);
    }
  });

  // A relation is meaningful only if both endpoints identify actual proposal claims.
  // Some model formats omit claim IDs; in that case leave endpoint resolution to
  // the adapter rather than rejecting an otherwise source-grounded relation.
  const claimIds = new Set(claims.map(c => text(c && c.id)).filter(Boolean));
  (Array.isArray(proposal.claimRelations) ? proposal.claimRelations : []).forEach((relation, index) => {
    const location = `claimRelations[${index}]`;
    if (!relation || typeof relation !== 'object' || Array.isArray(relation)) {
      issues.push(issue('INVALID_CLAIM_RELATION', 'error', location, 'A claim relation is not an object.', 'Return a structured relation with type and claim endpoints.'));
      return;
    }
    if (!text(relation.type) || !text(relation.fromClaimId) || !text(relation.toClaimId)) {
      issues.push(issue('INCOMPLETE_CLAIM_RELATION', 'error', location, 'A claim relation is missing its type or one of its endpoints.', 'Supply a relation type and both source/target claim identifiers.'));
      return;
    }
    if (claimIds.size && (!claimIds.has(String(relation.fromClaimId)) || !claimIds.has(String(relation.toClaimId)))) {
      issues.push(issue('DANGLING_CLAIM_RELATION', 'error', location, 'The relation references a claim identifier not present in the proposal.', 'Correct the relation endpoints or add the missing source-grounded claim.'));
    }
  });

  if (claims.length === 0 && norm(proposal.intent) === 'assertion' && (!Array.isArray(proposal.unresolved) || proposal.unresolved.length === 0)) {
    issues.push(issue('ASSERTION_WITHOUT_CLAIM_OR_UNRESOLVED', 'error', 'claims', 'The proposal labels the source as an assertion but contains neither a claim nor an explanation of what cannot be represented.', 'Represent the source assertion, or explain specifically why its meaning cannot safely be represented.'));
  }

  const entities = Array.isArray(proposal.entities) ? proposal.entities : [];
  const entityIds = new Set();
  const entityKeys = new Map();
  entities.forEach((entity, index) => {
    const location = `entities[${index}]`;
    if (!entity || typeof entity !== 'object' || Array.isArray(entity)) {
      issues.push(issue('INVALID_ENTITY', 'error', location, 'An entity entry is not an object.', 'Return a structured entity with an identifier, canonical text, and type.'));
      return;
    }
    const id = text(entity.id);
    const canonical = norm(entity.canonicalText);
    if (!id || !canonical) issues.push(issue('INCOMPLETE_ENTITY', 'error', location, 'An entity is missing its identifier or canonical text.', 'Provide a stable identifier and canonical text for this entity.'));
    if (id && entityIds.has(id)) issues.push(issue('DUPLICATE_ENTITY_ID', 'error', `${location}.id`, `Entity identifier ${id} is used more than once.`, 'Give each distinct entity record a unique identifier and update its mentions consistently.'));
    if (id) entityIds.add(id);
    const key = `${canonical}|${norm(entity.type)}`;
    if (canonical && entityKeys.has(key)) issues.push(issue('POSSIBLE_DUPLICATE_ENTITY', 'warning', location, `This entity has the same canonical text and type as entities[${entityKeys.get(key)}]; the referents may or may not be identical.`, 'Check whether these records denote the same referent before merging them; identical labels alone do not prove identity.'));
    else if (canonical) entityKeys.set(key, index);
  });

  const mentions = Array.isArray(proposal.mentions) ? proposal.mentions : [];
  mentions.forEach((mention, index) => {
    const location = `mentions[${index}]`;
    if (!mention || typeof mention !== 'object' || Array.isArray(mention)) {
      issues.push(issue('INVALID_MENTION', 'error', location, 'A mention entry is not an object.', 'Return a structured mention linked to an entity identity.'));
      return;
    }
    if (mention.entityId && entityIds.size && !entityIds.has(String(mention.entityId))) {
      issues.push(issue('DANGLING_MENTION_ENTITY', 'error', `${location}.entityId`, `Mention references unknown entity ${mention.entityId}.`, 'Link the mention to a declared entity or add the missing entity.'));
    }
    if (mention.antecedentId && entityIds.size && !entityIds.has(String(mention.antecedentId))) {
      issues.push(issue('DANGLING_ANTECEDENT', 'error', `${location}.antecedentId`, `Mention references unknown antecedent ${mention.antecedentId}.`, 'Use a declared antecedent entity identity, or set antecedentId to null when the reference is unresolved.'));
    }
  });

  return issues;
}

function normalizeReviewerReport(report) {
  if (!report || typeof report !== 'object' || Array.isArray(report)) {
    return { status: 'unavailable', overallAssessment: 'unknown', issues: [], error: 'Reviewer did not return a JSON object.' };
  }
  const sourceIssues = Array.isArray(report.issues) ? report.issues : [];
  const issues = sourceIssues.filter(x => x && typeof x === 'object' && !Array.isArray(x)).map((x, index) => ({
    code: text(x.code) || `MODEL_REVIEW_${index + 1}`,
    severity: ['error', 'critical', 'warning', 'info'].includes(norm(x.severity)) ? norm(x.severity) : 'warning',
    location: text(x.location) || 'semantic_review',
    problem: text(x.problem || x.description || x.issue),
    recommendedCorrection: text(x.recommendedCorrection || x.correction || x.recommendation)
  })).filter(x => x.problem);
  const overallAssessment = norm(report.overallAssessment || report.status || 'unknown').toUpperCase().replace(/\s+/g, '_');
  const missingContent = Array.isArray(report.missingContent) ? report.missingContent.map(text).filter(Boolean) : [];
  if (overallAssessment === 'NEEDS_REPAIR') {
    for (const missing of missingContent) {
      if (!issues.some(x => norm(x.problem) === norm(missing))) {
        issues.push({code:'MODEL_REVIEW_MISSING_CONTENT',severity:'error',location:'semantic_coverage',problem:missing,recommendedCorrection:'Restore this source-grounded semantic content in the complete proposal.'});
      }
    }
  }
  return { status: 'completed', overallAssessment, issues, missingContent };
}

function shouldRepair(diagnostics, reviewer) {
  if ((diagnostics || []).some(x => x.severity === 'error')) return true;
  return !!reviewer && reviewer.status === 'completed' && (
    reviewer.issues.some(x => x.severity === 'error' || x.severity === 'critical') ||
    (reviewer.overallAssessment === 'NEEDS_REPAIR' && reviewer.issues.length > 0)
  );
}

function buildReviewMessages(sourceText, proposal, diagnostics) {
  const system = `You are the second-pass semantic auditor for USG. You are the same selected language model operating in a distinct review role; do not claim to be an independent model. You do not rewrite the proposal. Compare the original source with the complete proposal and identify only material semantic defects.

Check: omitted source propositions or subordinate clauses; invented or unsupported propositions; incorrect subject/predicate/object roles; polarity and negation scope; tense and modality; quantifier scope; condition and causal scope; coreference; entity/mention identity; duplicated claims or entities; source evidence accuracy; contradictions introduced by the proposal; and unnecessary unresolved items.

Do not demand a fixed number of claims, entities, conditions, relations, event attributes, or unresolved items. Semantic complexity is determined by the source. Do not call a valid long or complex proposal incomplete merely because it has many items. Do not recommend deleting valid distinct content. Distinguish genuine ambiguity from an error. A source quote can establish alignment but not truth. Return ONLY JSON with this shape:
{"overallAssessment":"SOUND|NEEDS_REPAIR|UNCERTAIN","issues":[{"code":"...","severity":"error|critical|warning|info","location":"...","problem":"...","recommendedCorrection":"..."}],"missingContent":["..."]}
Use an empty issues array when you find no material defect. Only use error/critical for defects that are clearly supported by the source.`;
  const user = `ORIGINAL SOURCE:\n${sourceText}\n\nCURRENT PROPOSAL:\n${JSON.stringify(proposal)}\n\nDETERMINISTIC DIAGNOSTICS:\n${JSON.stringify(diagnostics || [])}\n\nAudit the meaning carefully. Do not invent requirements or impose item-count limits.`;
  return [{ role: 'system', content: system }, { role: 'user', content: user }];
}

function buildRepairMessages(sourceText, candidate, diagnostics, reviewer) {
  const system = `You are the semantic correction component of USG. Repair the supplied proposal using the ORIGINAL SOURCE as the sole authority for what the source asserts.

Return one complete JSON object with the same USG proposal keys: intent, interpretation, claims, entities, mentions, claimRelations, unresolved. Preserve every correct part of the candidate. Fix only diagnosed defects and any additional clear errors you discover while re-reading the source. Remove genuine duplicates, not distinct propositions. Restore omitted propositions, subordinate clauses, scope, arguments, polarity, tense, modality, quantification, event attributes, and coreference when explicitly supported. Correct evidence_text to exact contiguous source words. Never invent missing facts. Preserve unresolved ambiguity explicitly. Preserve nested conditions, scope, and all other compositional structure; do not flatten or discard nested meaning merely because the compatibility view is simpler. If a projection cannot represent a structure, retain it in the proposal and mark the projection limitation explicitly.

There are NO fixed maximum counts for semantic items. Do not truncate, summarize away, or cap claims, entities, mentions, relations, conditions, event attributes, or unresolved items. Output the complete corrected representation, not a patch or explanation. Output valid JSON only, with no markdown fences or commentary.`;
  const user = `ORIGINAL SOURCE (authoritative):\n${sourceText}\n\nCANDIDATE TO CORRECT:\n${JSON.stringify(candidate)}\n\nDETERMINISTIC DIAGNOSTICS:\n${JSON.stringify(diagnostics || [])}\n\nINDEPENDENT REVIEW FINDINGS:\n${JSON.stringify(reviewer || { status: 'not_run', issues: [] })}\n\nCorrect the proposal now. Preserve legitimate semantic complexity and all distinct source-grounded content.`;
  return [{ role: 'system', content: system }, { role: 'user', content: user }];
}

function parseModelJson(content) {
  let raw = String(content || '').trim();
  raw = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim();
  return JSON.parse(raw);
}

module.exports = {
  diagnoseProposal,
  normalizeReviewerReport,
  shouldRepair,
  buildReviewMessages,
  buildRepairMessages,
  parseModelJson
};
