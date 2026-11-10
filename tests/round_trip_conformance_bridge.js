'use strict';

const fs = require('node:fs');
const adapter = require('../interoperability/workbench_adapter');

function makeModel({ warnings = false, opaque = false } = {}) {
  const text = '😀 Alice needs the tool unless Bob agrees; when Carol arrives, Alice helps it.';
  const span = (needle, occurrence = 0) => {
    let from = 0, at = -1;
    for (let i = 0; i <= occurrence; i++) {
      at = text.indexOf(needle, from);
      if (at < 0) throw new Error('Fixture span not found: ' + needle);
      from = at + needle.length;
    }
    return { start: at, end: at + needle.length };
  };
  const evidence = (id, quote) => ({ id, sourceText: text, quote, ...span(quote),
    exactSourceMatch: true, modelQuote: null, modelQuoteVerified: null,
    verificationMeaning: 'source_alignment_only_not_semantic_entailment' });
  const predication = (id, predicate, subject, object, quote, tense = 'present', aspect = 'simple') => ({
    id, type: 'PREDICATION', predicate,
    arguments: [
      { role: 'subject', entityId: subject, mentionId: subject + '-mention' },
      ...(object ? [{ role: 'object', entityId: object, mentionId: object + '-mention' }] : [])
    ],
    argumentRequirements: { requiredRoles: object ? ['subject', 'object'] : ['subject'], missingRoles: [] },
    grammaticalTense: tense, aspect,
    temporalFrame: { referenceTime: tense, temporalAdverbials: ['today'], sourceTense: tense },
    eventFrame: { id: id + '-frame', kind: 'event', predicate,
      participants: [
        { role: 'subject', entityId: subject },
        ...(object ? [{ role: 'object', entityId: object }] : [])
      ],
      attributes: [{ key: 'manner', value: 'carefully' }] },
    attribution: { kind: 'source_voice', status: 'source_asserted',
      truthStatus: 'not_independently_established' },
    provenance: { method: 'source_composition_rule', ruleId: 'SRC-CLAUSE-VERB-FRAME',
      sourceKind: 'interpreted_text' },
    completeness: { status: 'complete', missingRoles: [] },
    evidenceRefs: [quote + '-evidence'], sourceClaimId: 'claim-' + id
  });
  const entities = [
    ['alice', 'Alice', 'person'], ['tool', 'the tool', 'artifact'],
    ['bob', 'Bob', 'person'], ['carol', 'Carol', 'person'],
    ['person-class', 'person', 'class']
  ].map(([id, canonicalText, type]) => ({
    id, canonicalText, type, aliases: [canonicalText], identityStatus: 'provisional'
  }));
  const mentions = [
    ['alice', 'Alice', 'noun_phrase', 'linked'],
    ['tool', 'the tool', 'noun_phrase', 'linked'],
    ['bob', 'Bob', 'noun_phrase', 'linked'],
    ['carol', 'Carol', 'noun_phrase', 'linked']
  ].map(([id, surfaceText, mentionType, resolutionStatus]) => ({
    id: id + '-mention', entityId: id, surfaceText, mentionType, resolutionStatus,
    sourceSpan: span(surfaceText)
  }));
  mentions.push({
    id: 'it-mention', entityId: null, surfaceText: 'it', mentionType: 'pronoun',
    resolutionStatus: 'unresolved', antecedentEntityId: null,
    sourceSpan: span('it')
  });

  const evidenceRecords = [
    evidence('needs-evidence', 'needs'), evidence('agrees-evidence', 'agrees'),
    evidence('arrives-evidence', 'arrives'), evidence('helps-evidence', 'helps')
  ];
  const expressions = [
    predication('needs', 'NEEDS', 'alice', 'tool', 'needs', 'present', 'simple'),
    { id: 'not-needs', type: 'OPERATOR', operatorType: 'NEGATION', operator: 'NOT',
      scope: { targetId: 'needs', scopeKind: 'whole_expression' }, evidenceRefs: ['needs-evidence'] },
    { id: 'might-not-needs', type: 'OPERATOR', operatorType: 'MODAL', operator: 'MIGHT',
      force: 'epistemic_possibility',
      scope: { targetId: 'not-needs', scopeKind: 'whole_expression' }, evidenceRefs: ['needs-evidence'] },
    predication('agrees', 'AGREES', 'bob', 'alice', 'agrees', 'past', 'perfect'),
    predication('arrives', 'ARRIVES', 'carol', null, 'arrives', 'future', 'progressive'),
    predication('helps', 'HELPS', 'alice', null, 'helps', 'present', 'habitual'),
    { id: 'forall-root', type: 'OPERATOR', operatorType: 'QUANTIFIER', operator: 'FORALL',
      variable: 'x', restrictor: { entityId: 'person-class', predicate: 'INSTANCE_OF' },
      variableBinding: { variable: 'x', role: 'subject', restrictorEntityId: 'person-class' },
      scope: { targetId: 'needs', scopeKind: 'quantifier_body' }, evidenceRefs: ['needs-evidence'] },
    { id: 'not-forall-root', type: 'OPERATOR', operatorType: 'NEGATION', operator: 'NOT',
      scope: { targetId: 'forall-root', scopeKind: 'whole_expression' }, evidenceRefs: ['needs-evidence'] },
    { id: 'exists-root', type: 'OPERATOR', operatorType: 'QUANTIFIER', operator: 'EXISTS',
      variable: 'x', restrictor: { entityId: 'person-class', predicate: 'INSTANCE_OF' },
      variableBinding: { variable: 'x', role: 'subject', restrictorEntityId: 'person-class' },
      scope: { targetId: 'needs', scopeKind: 'quantifier_body' }, evidenceRefs: ['needs-evidence'] },
    { id: 'no-root', type: 'OPERATOR', operatorType: 'NEGATION', operator: 'NOT',
      scope: { targetId: 'exists-root', scopeKind: 'whole_expression' }, evidenceRefs: ['needs-evidence'] },
    { id: 'if-root', type: 'CONNECTIVE', connective: 'CONDITIONAL',
      antecedentId: 'not-needs', consequentId: 'agrees',
      logicalStatus: 'conditional_not_asserted', marker: 'if',
      conditionMetadata: { effect: 'condition_for_assertion', logicalStatus: 'conditional_not_asserted' },
      evidenceRefs: ['needs-evidence'], attribution: { kind: 'source_voice', status: 'conditional_relation_asserted' } },
    { id: 'unless-root', type: 'CONNECTIVE', connective: 'EXCEPTION',
      antecedentId: 'not-needs', consequentId: 'helps',
      logicalStatus: 'exception_relation_asserted', marker: 'unless',
      antecedentInterpretation: 'negated_exception_condition_equivalent_to_if_not_P_then_Q',
      conditionMetadata: { effect: 'exception_to_assertion', logicalStatus: 'exception_relation_asserted' },
      evidenceRefs: ['needs-evidence'], attribution: { kind: 'source_voice', status: 'exception_relation_asserted' } },
    { id: 'when-root', type: 'CONNECTIVE', connective: 'WHEN',
      antecedentId: 'arrives', consequentId: 'helps',
      logicalStatus: 'when_clause_not_asserted', marker: 'when',
      evidenceRefs: ['arrives-evidence', 'helps-evidence'] },
    { id: 'concessive-root', type: 'CONNECTIVE', connective: 'CONCESSIVE',
      antecedentId: 'agrees', consequentId: 'helps',
      logicalStatus: 'concessive_relation_asserted', marker: 'although',
      evidenceRefs: ['agrees-evidence', 'helps-evidence'] }
  ];
  const needs = expressions.find(x => x.id === 'needs');
  needs.arguments[0].variableId = 'x';
  needs.arguments[0].bindingEntityId = 'person-class';
  needs.eventFrame.participants[0].variableId = 'x';
  needs.eventFrame.participants[0].bindingEntityId = 'person-class';
  const helps = expressions.find(x => x.id === 'helps');
  helps.arguments.push({ role: 'object', entityId: null, mentionId: 'it-mention' });
  helps.argumentRequirements.missingRoles = ['object'];
  helps.eventFrame.participants.push({ role: 'object', entityId: null });
  helps.completeness = { status: 'unresolved', missingRoles: ['object'] };
  if (opaque) {
    expressions.push({ id: 'opaque-root', type: 'OPERATOR', operatorType: 'POLARITY',
      operator: 'UNKNOWN', scope: { targetId: 'needs', scopeKind: 'whole_expression' },
      evidenceRefs: [] });
  }
  const model = {
    profile: 'USG-SR/0.5.1', version: '0.5.1', canonical: true,
    source: { text, language: 'en', sourceId: 'step4d-fixture' },
    entities, mentions, evidence: evidenceRecords,
    expressions, relations: [{
      id: 'candidate-cause', type: 'CAUSE',
      sourceExpressionId: 'not-needs', targetExpressionId: 'helps',
      verification: 'candidate_not_proof', status: 'candidate',
      note: 'Candidate causal relation; not a proof.',
      attribution: { kind: 'source_asserted', holder: null },
      evidenceRefs: ['needs-evidence', 'helps-evidence']
    }],
    rootExpressionIds: ['might-not-needs', 'not-forall-root', 'no-root',
      'if-root', 'unless-root', 'when-root', 'concessive-root', ...(opaque ? ['opaque-root'] : [])],
    unresolvedItems: [{
      id: 'unresolved-it', status: 'unresolved', reason: 'Pronoun antecedent not established.',
      surfaceText: 'it', scope: 'needs', evidenceRef: 'needs-evidence'
    }],
    acceptanceBoundary: { requiresHumanReview: true, acceptedIntoKnowledgeBase: false,
      objectiveTruthEstablished: false },
    buildNotes: warnings ? ['An unsupported event attribute was discarded upstream.'] : []
  };
  return model;
}

async function toContract() {
  const model = makeModel();
  const result = await adapter.workbenchToContract(model);
  return { model, document: result.document, report: result.report };
}

async function fromContract(document) {
  return adapter.contractToWorkbench(document);
}

async function largeRoundTrip(size = 512) {
  const text = 'large semantic graph fixture';
  const entities = [];
  const expressions = [];
  const roots = [];
  for (let i = 0; i < size; i++) {
    const subject = 'subject-' + i, object = 'object-' + i, id = 'predicate-' + i;
    entities.push({ id: subject, canonicalText: subject, type: 'entity', aliases: [], identityStatus: 'provisional' });
    entities.push({ id: object, canonicalText: object, type: 'entity', aliases: [], identityStatus: 'provisional' });
    expressions.push({
      id, type: 'PREDICATION', predicate: 'RELATED_TO',
      arguments: [{ role: 'subject', entityId: subject, mentionId: null },
        { role: 'object', entityId: object, mentionId: null }],
      argumentRequirements: { requiredRoles: ['subject', 'object'], missingRoles: [] },
      grammaticalTense: 'unknown', aspect: 'unknown',
      temporalFrame: { referenceTime: 'unspecified', temporalAdverbials: [] },
      eventFrame: { id: id + '-frame', kind: 'relation', predicate: 'RELATED_TO',
        participants: [{ role: 'subject', entityId: subject }, { role: 'object', entityId: object }], attributes: [] },
      attribution: { kind: 'source_voice', status: 'source_asserted' },
      provenance: { method: 'conformance-fixture', ruleId: 'STEP4D-LARGE', sourceKind: 'interpreted_text' },
      completeness: { status: 'complete', missingRoles: [] }, evidenceRefs: []
    });
    roots.push(id);
  }
  const model = { profile: 'USG-SR/0.5.1', version: '0.5.1', canonical: true,
    source: { text, language: 'en', sourceId: 'large-fixture' },
    entities, mentions: [], evidence: [], expressions, relations: [],
    rootExpressionIds: roots, unresolvedItems: [], buildNotes: [] };
  const first = await adapter.workbenchToContract(model);
  const second = await adapter.contractToWorkbench(first.document);
  return { inputCount: expressions.length, canonicalCount: first.document.expressions.length,
    outputCount: second.model.expressions.length, rootCount: second.model.rootExpressionIds.length,
    sourceStatus: first.report.status, reconstructionStatus: second.report.status,
    validation: second.validation };
}

async function main() {
  const mode = process.argv[2];
  if (mode === 'to-contract') {
    process.stdout.write(JSON.stringify(await toContract()));
  } else if (mode === 'from-contract') {
    const chunks = [];
    for await (const chunk of process.stdin) chunks.push(chunk);
    process.stdout.write(JSON.stringify(await fromContract(JSON.parse(Buffer.concat(chunks).toString('utf8')))));
  } else if (mode === 'large') {
    process.stdout.write(JSON.stringify(await largeRoundTrip(Number(process.argv[3] || 512))));
  } else if (mode === 'warning') {
    const model = makeModel({ warnings: true, opaque: true });
    const first = await adapter.workbenchToContract(model);
    const second = await adapter.contractToWorkbench(first.document);
    process.stdout.write(JSON.stringify({ sourceReport: first.report, resultReport: second.report }));
  } else {
    throw new Error('Unknown mode: ' + mode);
  }
}

if (require.main === module) main().catch(error => {
  process.stderr.write(error.stack || String(error));
  process.exitCode = 1;
});

module.exports = { makeModel, toContract, fromContract, largeRoundTrip };
