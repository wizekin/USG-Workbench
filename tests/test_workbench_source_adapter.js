'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const adapter = require('../interoperability/workbench_adapter');
const semanticCore = require('../implementations/semantic-workbench-js/v0.5.4/semantic-core.js');

function fixture() {
  const sourceText = '😀 Alice needs it.';
  const aliceStart = sourceText.indexOf('Alice');
  const itStart = sourceText.indexOf('it');
  const needsStart = sourceText.indexOf('needs');
  return {
    profile: 'USG-SR/0.5.1',
    version: '0.5.1',
    canonical: true,
    source: { text: sourceText, language: 'en', sourceId: 'fixture-source' },
    entities: [
      { id: 'entity-alice', canonicalText: 'Alice', type: 'unknown', aliases: ['Alice'], identityStatus: 'provisional' },
      { id: 'entity-tool', canonicalText: 'the tool', type: 'unknown', aliases: ['tool'], identityStatus: 'provisional' }
    ],
    mentions: [
      { id: 'mention-alice', entityId: 'entity-alice', surfaceText: 'Alice', mentionType: 'noun_phrase',
        resolutionStatus: 'linked', sourceSpan: { start: aliceStart, end: aliceStart + 5 } },
      { id: 'mention-it', entityId: null, surfaceText: 'it', mentionType: 'pronoun',
        resolutionStatus: 'unresolved', antecedentEntityId: null, sourceSpan: { start: itStart, end: itStart + 2 } }
    ],
    evidence: [
      { id: 'evidence-needs', sourceText, quote: 'needs', start: needsStart, end: needsStart + 5,
        exactSourceMatch: true, modelQuote: null, modelQuoteVerified: null,
        verificationMeaning: 'source_alignment_only_not_semantic_entailment' }
    ],
    expressions: [
      { id: 'pred-needs', type: 'PREDICATION', predicate: 'NEEDS',
        arguments: [
          { role: 'subject', entityId: 'entity-alice', mentionId: 'mention-alice' },
          { role: 'object', entityId: null, mentionId: 'mention-it' }
        ],
        argumentRequirements: { requiredRoles: ['subject', 'object'], missingRoles: ['object'] },
        grammaticalTense: 'present', aspect: 'simple',
        temporalFrame: { referenceTime: 'present', temporalAdverbials: [], sourceTense: 'present', clauseEvidence: 'needs' },
        eventFrame: { id: 'frame-needs', kind: 'state', predicate: 'NEEDS',
          participants: [{ role: 'subject', entityId: 'entity-alice' }, { role: 'object', entityId: null }],
          attributes: [] },
        attribution: { kind: 'source_voice', status: 'source_asserted', truthStatus: 'not_independently_established' },
        provenance: { method: 'source_composition_rule', ruleId: 'SRC-CLAUSE-VERB-FRAME', sourceKind: 'interpreted_text' },
        completeness: { status: 'unresolved', missingRoles: ['object'], note: 'Object reference unresolved.' },
        evidenceRefs: ['evidence-needs'], sourceClaimId: 'src_claim_1' },
      { id: 'neg-needs', type: 'OPERATOR', operatorType: 'NEGATION', operator: 'NOT',
        scope: { targetId: 'pred-needs', scopeKind: 'whole_expression' }, evidenceRefs: ['evidence-needs'] },
      { id: 'modal-needs', type: 'OPERATOR', operatorType: 'MODAL', operator: 'MIGHT',
        force: 'epistemic_possibility',
        scope: { targetId: 'neg-needs', scopeKind: 'whole_expression' }, evidenceRefs: ['evidence-needs'] },
      { id: 'unless-root', type: 'CONNECTIVE', connective: 'EXCEPTION',
        antecedentId: 'neg-needs', consequentId: 'modal-needs',
        logicalStatus: 'exception_relation_asserted', marker: 'unless',
        antecedentInterpretation: 'negated_exception_condition_equivalent_to_if_not_P_then_Q',
        conditionMetadata: { effect: 'exception_to_assertion', logicalStatus: 'exception_relation_asserted' },
        evidenceRefs: ['evidence-needs'],
        attribution: { kind: 'source_voice', status: 'exception_relation_asserted', truthStatus: 'not_independently_established' } }
    ],
    relations: [],
    rootExpressionIds: ['unless-root'],
    unresolvedItems: [
      { id: 'unresolved-it', status: 'unresolved', reason: 'Pronoun antecedent not established.',
        surfaceText: 'it', scope: 'pred-needs', evidenceRef: 'evidence-needs' }
    ],
    acceptanceBoundary: { requiresHumanReview: true, acceptedIntoKnowledgeBase: false, objectiveTruthEstablished: false },
    buildNotes: []
  };
}


test('converts an actual semantic-core build result without requiring manual review', async () => {
  const sourceText = 'Alice needs the tool.';
  const built = semanticCore.buildSemanticModel({
    sourceText,
    sourceId: 'actual-core-fixture',
    claims: [{
      id: 'claim-actual-1',
      subject: { canonicalText: 'Alice', surfaceText: 'Alice', type: 'person', entityId: 'alice' },
      predicate: 'NEEDS',
      object: { canonicalText: 'the tool', surfaceText: 'the tool', type: 'artifact', entityId: 'tool' },
      polarity: 'positive',
      tense: 'present',
      modality: 'asserted',
      time: { referenceTime: 'present', temporalAdverbials: [], aspect: 'simple' },
      evidence: { start: 0, end: sourceText.length, quote: sourceText }
    }]
  });
  assert.equal(built.validation.valid, true);
  const { document, report } = await adapter.workbenchToContract(built.model);
  const predicate = document.expressions.find(x => x.op === 'PREDICATE_APP');
  assert.ok(predicate);
  assert.equal(predicate.params.predicate, 'NEEDS');
  assert.deepEqual(predicate.params.roles, ['SUBJECT', 'OBJECT']);
  assert.equal(report.status, 'LOSSLESS');
  assert.equal(document.sources[0].text, sourceText);
});

test('maps a Workbench graph into USG-SEM without flattening operators or EXCEPTION direction', async () => {
  const model = fixture();
  const { document, report } = await adapter.workbenchToContract(model);
  const byNative = new Map(document.expressions.filter(x => x.nativeId).map(x => [x.nativeId, x]));
  assert.equal(document.profileId, 'USG-SEM/1.0');
  assert.equal(report.status, 'LOSSLESS');
  assert.equal(byNative.get('pred-needs').op, 'PREDICATE_APP');
  assert.equal(byNative.get('pred-needs').sort, 'SIT');
  assert.deepEqual(byNative.get('pred-needs').params.roles, ['SUBJECT', 'OBJECT']);
  const holds = document.expressions.find(x => x.op === 'HOLDS' &&
    x.operandRefs[0] === byNative.get('pred-needs').id);
  assert.ok(holds, 'a proposition-valued operator must receive an explicit HOLDS wrapper');
  assert.equal(holds.sort, 'PROP');
  assert.deepEqual(byNative.get('neg-needs').operandRefs, [holds.id]);
  assert.equal(byNative.get('neg-needs').op, 'NOT');
  assert.equal(byNative.get('modal-needs').op, 'MODAL');
  assert.equal(byNative.get('modal-needs').params.force, 'POSSIBILITY');
  assert.equal(byNative.get('modal-needs').params.flavor, 'EPISTEMIC');
  assert.equal(byNative.get('modal-needs').params.nativeForce, 'epistemic_possibility');
  assert.equal(byNative.get('unless-root').op, 'CONNECTIVE');
  assert.deepEqual(byNative.get('unless-root').operandRefs,
    [byNative.get('neg-needs').id, byNative.get('modal-needs').id]);
  assert.deepEqual(byNative.get('unless-root').params.operandRoles, ['antecedent', 'consequent']);
  assert.equal(byNative.get('unless-root').params.marker, 'unless');
  assert.equal(document.rootExpressionRefs[0], byNative.get('unless-root').id);
  assert.equal(document.mentions.find(x => x.nativeId === 'mention-it').resolutionStatus, 'UNRESOLVED');
  assert.equal(document.unresolvedItems[0].status, 'UNRESOLVED');
  assert.equal(document.assertions.length, 0, 'the adapter must not invent source assertion records');
  assert.equal(document.contexts.length, 0, 'the adapter must not invent context records');
  assert.equal(document.acceptanceBoundary, undefined, 'legacy human-review workflow is not canonical semantics');
  assert.equal(document.extensions[adapter.NAMESPACE].nativeModel.acceptanceBoundary.requiresHumanReview, true);
});

test('converts UTF-16 source offsets to Unicode code-point offsets', async () => {
  const { document } = await adapter.workbenchToContract(fixture());
  const alice = document.mentions.find(x => x.nativeId === 'mention-alice');
  const it = document.mentions.find(x => x.nativeId === 'mention-it');
  assert.deepEqual([alice.sourceSpan.start, alice.sourceSpan.end], [2, 7]);
  assert.deepEqual([it.sourceSpan.start, it.sourceSpan.end], [14, 16]);
  const evidence = document.evidence[0];
  assert.deepEqual([evidence.span.start, evidence.span.end], [8, 13]);
  assert.equal(evidence.quote, 'needs');
});

test('refuses a Workbench span that splits a surrogate pair', async () => {
  const model = fixture();
  model.mentions[0].sourceSpan = { start: 1, end: 6 };
  await assert.rejects(() => adapter.workbenchToContract(model), /splits a UTF-16 surrogate pair/);
});

test('reports builder warnings and opaque operator meanings as PARTIAL', async () => {
  const model = fixture();
  model.buildNotes = ['An unsupported event attribute was discarded upstream.'];
  model.expressions[1] = { id: 'unknown-polarity', type: 'OPERATOR', operatorType: 'POLARITY',
    operator: 'UNKNOWN', scope: { targetId: 'pred-needs', scopeKind: 'whole_expression' }, evidenceRefs: [] };
  model.expressions[2].scope.targetId = 'unknown-polarity';
  model.expressions[3].antecedentId = 'unknown-polarity';
  const { document, report } = await adapter.workbenchToContract(model);
  const opaque = document.expressions.find(x => x.nativeId === 'unknown-polarity');
  assert.equal(opaque.op, 'OPAQUE');
  assert.equal(opaque.interpretationStatus, 'UNRESOLVED');
  assert.equal(report.status, 'PARTIAL');
  assert.ok(report.unmappedRefs.includes(opaque.id));
  assert.ok(report.unmappedRefs.some(x => x.startsWith('wb:warning:')));
});


test('preserves relation metadata and reports non-exact verification states as PARTIAL', async () => {
  const model = fixture();
  model.relations = [{
    id: 'relation-candidate',
    type: 'CAUSE',
    sourceExpressionId: 'neg-needs',
    targetExpressionId: 'modal-needs',
    verification: 'candidate_not_proof',
    status: 'candidate',
    note: 'Candidate relation; not a proof.',
    attribution: { kind: 'source_asserted', holder: null },
    evidenceRefs: ['evidence-needs']
  }];
  const { document, report } = await adapter.workbenchToContract(model);
  assert.equal(report.status, 'PARTIAL');
  assert.equal(document.expressionRelations[0].verificationStatus, 'UNKNOWN');
  assert.equal(document.expressionRelations[0].nativeVerification, 'candidate_not_proof');
  assert.equal(document.expressionRelations[0].nativeStatus, 'candidate');
  assert.equal(document.expressionRelations[0].note, 'Candidate relation; not a proof.');
});

test('native snapshot verification detects canonical document edits', async () => {
  const { document } = await adapter.workbenchToContract(fixture());
  const valid = await adapter.verifyNativeSnapshot(document);
  assert.equal(valid.valid, true);
  document.expressions.find(x => x.nativeId === 'unless-root').params.marker = 'if';
  const stale = await adapter.verifyNativeSnapshot(document);
  assert.equal(stale.nativeValid, true);
  assert.equal(stale.projectionValid, false);
  assert.equal(stale.valid, false);
});

test('rejects dangling native expression references instead of dropping them', async () => {
  const model = fixture();
  model.expressions[1].scope.targetId = 'missing-expression';
  await assert.rejects(() => adapter.workbenchToContract(model), /missing Workbench expression/);
});
