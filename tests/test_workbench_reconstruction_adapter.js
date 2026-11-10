'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const adapter = require('../interoperability/workbench_adapter');
const sourceAdapter = require('../interoperability/workbench_adapter');

function sourceModel() {
  const sourceText = '😀 Alice needs the tool.';
  const start = sourceText.indexOf('needs');
  return {
    profile: 'USG-SR/0.5.1', version: '0.5.1', canonical: true,
    source: { text: sourceText, language: 'en', sourceId: 'reconstruction-fixture' },
    entities: [
      { id: 'alice', canonicalText: 'Alice', type: 'person', aliases: ['Alice'], identityStatus: 'provisional' },
      { id: 'tool', canonicalText: 'the tool', type: 'artifact', aliases: ['tool'], identityStatus: 'provisional' }
    ],
    mentions: [
      { id: 'alice-mention', entityId: 'alice', surfaceText: 'Alice', mentionType: 'noun_phrase',
        resolutionStatus: 'linked', sourceSpan: { start: sourceText.indexOf('Alice'), end: sourceText.indexOf('Alice') + 5 } },
      { id: 'tool-mention', entityId: 'tool', surfaceText: 'the tool', mentionType: 'noun_phrase',
        resolutionStatus: 'linked', sourceSpan: { start: sourceText.indexOf('the tool'), end: sourceText.indexOf('the tool') + 8 } }
    ],
    evidence: [{ id: 'needs-evidence', sourceText, quote: 'needs', start, end: start + 5,
      exactSourceMatch: true, modelQuote: null, modelQuoteVerified: null,
      verificationMeaning: 'source_alignment_only_not_semantic_entailment' }],
    expressions: [
      { id: 'needs', type: 'PREDICATION', predicate: 'NEEDS',
        arguments: [
          { role: 'subject', entityId: 'alice', mentionId: 'alice-mention' },
          { role: 'object', entityId: 'tool', mentionId: 'tool-mention' }
        ],
        argumentRequirements: { requiredRoles: ['subject', 'object'], missingRoles: [] },
        grammaticalTense: 'present', aspect: 'simple',
        temporalFrame: { referenceTime: 'present', temporalAdverbials: [], sourceTense: 'present' },
        eventFrame: { id: 'needs-frame', kind: 'state', predicate: 'NEEDS',
          participants: [{ role: 'subject', entityId: 'alice' }, { role: 'object', entityId: 'tool' }], attributes: [] },
        attribution: { kind: 'source_voice', status: 'source_asserted', truthStatus: 'not_independently_established' },
        provenance: { method: 'test', ruleId: 'TEST-NEEDS', sourceKind: 'interpreted_text' },
        completeness: { status: 'complete', missingRoles: [] }, evidenceRefs: ['needs-evidence'], sourceClaimId: 'claim-needs' },
      { id: 'not-needs', type: 'OPERATOR', operatorType: 'NEGATION', operator: 'NOT',
        scope: { targetId: 'needs', scopeKind: 'whole_expression' }, evidenceRefs: ['needs-evidence'] },
      { id: 'might-not-needs', type: 'OPERATOR', operatorType: 'MODAL', operator: 'MIGHT',
        force: 'epistemic_possibility', scope: { targetId: 'not-needs', scopeKind: 'whole_expression' },
        evidenceRefs: ['needs-evidence'] },
      { id: 'if-root', type: 'CONNECTIVE', connective: 'CONDITIONAL',
        antecedentId: 'not-needs', consequentId: 'might-not-needs',
        logicalStatus: 'conditional_not_asserted', marker: 'if',
        conditionMetadata: { effect: 'condition_for_assertion', logicalStatus: 'conditional_not_asserted' },
        evidenceRefs: ['needs-evidence'], attribution: { kind: 'source_voice', status: 'conditional_relation_asserted' } }
    ],
    relations: [], rootExpressionIds: ['if-root'], unresolvedItems: [],
    acceptanceBoundary: { requiresHumanReview: true, acceptedIntoKnowledgeBase: false, objectiveTruthEstablished: false },
    buildNotes: []
  };
}

test('reconstructs native predicate arguments, nested operator scope, and directed connective roles', async () => {
  const { document, report: sourceReport } = await sourceAdapter.workbenchToContract(sourceModel());
  assert.equal(sourceReport.status, 'LOSSLESS');
  const result = await adapter.contractToWorkbench(document);
  assert.equal(result.validation.valid, true, result.validation.errors.join('; '));
  assert.equal(result.report.status, 'PARTIAL', 'adapter-generated derivation metadata has no Workbench-native field');
  assert.ok(result.report.unmappedRefs.some(ref => ref.startsWith('wb:derivation:')));
  const byId = new Map(result.model.expressions.map(x => [x.id, x]));
  const root = byId.get('if-root');
  assert.equal(root.type, 'CONNECTIVE');
  assert.equal(root.antecedentId, 'not-needs');
  assert.equal(root.consequentId, 'might-not-needs');
  assert.equal(byId.get('not-needs').scope.targetId, 'needs');
  assert.equal(byId.get('might-not-needs').scope.targetId, 'not-needs');
  const predicate = byId.get('needs');
  assert.deepEqual(predicate.arguments.map(x => [x.role, x.entityId]), [
    ['subject', 'alice'], ['object', 'tool']
  ]);
  assert.deepEqual(result.model.rootExpressionIds, ['if-root']);
  assert.equal(result.model.acceptanceBoundary, undefined,
    'legacy human-review gate must not be emitted as a semantic requirement');
  assert.equal(result.report.archivalNativeFields.acceptanceBoundary.requiresHumanReview, true);
  assert.ok(result.report.diagnostics.some(x => x.includes('inert archival metadata')));
});

test('preserves quantifier binding and restrictor identity', async () => {
  const model = sourceModel();
  model.entities.push({ id: 'person-class', canonicalText: 'person', type: 'class',
    aliases: ['person'], identityStatus: 'provisional' });
  model.expressions[0].arguments[0].variableId = 'x';
  model.expressions[0].arguments[0].bindingEntityId = 'person-class';
  model.expressions[0].eventFrame.participants[0].variableId = 'x';
  model.expressions[0].eventFrame.participants[0].bindingEntityId = 'person-class';
  model.expressions = [model.expressions[0]];
  model.expressions.push({
    id: 'forall-root', type: 'OPERATOR', operatorType: 'QUANTIFIER', operator: 'FORALL',
    variable: 'x', restrictor: { entityId: 'person-class', predicate: 'INSTANCE_OF' },
    variableBinding: { variable: 'x', role: 'subject', restrictorEntityId: 'person-class' },
    scope: { targetId: 'needs', scopeKind: 'quantifier_body' }, evidenceRefs: ['needs-evidence']
  });
  model.rootExpressionIds = ['forall-root'];
  const { document } = await sourceAdapter.workbenchToContract(model);
  const result = await adapter.contractToWorkbench(document);
  assert.equal(result.validation.valid, true, result.validation.errors.join('; '));
  const quantifier = result.model.expressions.find(x => x.id === 'forall-root');
  const predication = result.model.expressions.find(x => x.id === 'needs');
  assert.equal(quantifier.operatorType, 'QUANTIFIER');
  assert.equal(quantifier.operator, 'FORALL');
  assert.equal(quantifier.restrictor.entityId, 'person-class');
  assert.equal(quantifier.variableBinding.restrictorEntityId, 'person-class');
  assert.equal(predication.arguments[0].variableId, 'x');
  assert.equal(predication.arguments[0].bindingEntityId, 'person-class');
});

test('preserves UNLESS as directed EXCEPTION with an explicit negated antecedent', async () => {
  const model = sourceModel();
  const root = model.expressions.find(x => x.id === 'if-root');
  root.connective = 'EXCEPTION';
  root.marker = 'unless';
  root.logicalStatus = 'exception_relation_asserted';
  root.antecedentInterpretation = 'negated_exception_condition_equivalent_to_if_not_P_then_Q';
  root.conditionMetadata = { effect: 'exception_to_assertion', logicalStatus: 'exception_relation_asserted' };
  const { document } = await sourceAdapter.workbenchToContract(model);
  const result = await adapter.contractToWorkbench(document);
  assert.equal(result.validation.valid, true, result.validation.errors.join('; '));
  const reconstructed = result.model.expressions.find(x => x.id === 'if-root');
  assert.equal(reconstructed.connective, 'EXCEPTION');
  assert.equal(reconstructed.marker, 'unless');
  assert.equal(result.model.expressions.find(x => x.id === reconstructed.antecedentId).operator, 'NOT');
  assert.equal(reconstructed.antecedentInterpretation, 'negated_exception_condition_equivalent_to_if_not_P_then_Q');
});

test('converts canonical code-point spans back to Workbench UTF-16 offsets', async () => {
  const { document } = await sourceAdapter.workbenchToContract(sourceModel());
  const result = await adapter.contractToWorkbench(document);
  const alice = result.model.mentions.find(x => x.id === 'alice-mention');
  const evidence = result.model.evidence.find(x => x.id === 'needs-evidence');
  assert.deepEqual(alice.sourceSpan, { start: 3, end: 8 });
  assert.equal(result.model.source.text.slice(evidence.start, evidence.end), evidence.quote);
  assert.equal(evidence.start, result.model.source.text.indexOf('needs'));
});

test('canonical edits win over stale native payload and force PARTIAL status', async () => {
  const { document } = await sourceAdapter.workbenchToContract(sourceModel());
  document.expressions.find(x => x.nativeId === 'needs').params.predicate = 'WANTS';
  const result = await adapter.contractToWorkbench(document);
  const predicate = result.model.expressions.find(x => x.id === 'needs');
  assert.equal(predicate.predicate, 'WANTS');
  assert.equal(result.report.snapshot.nativeValid, true);
  assert.equal(result.report.snapshot.projectionValid, false);
  assert.equal(result.report.restoredNativeSnapshot, false);
  assert.equal(result.report.status, 'PARTIAL');
  assert.equal(result.report.archivalNativeFields, null);
});

test('unsupported opaque constructors are reported, never coerced into a Workbench operator', async () => {
  const { document } = await sourceAdapter.workbenchToContract(sourceModel());
  document.expressions = [{
    id: 'opaque:custom', op: 'OPAQUE', sort: 'ANY', operandRefs: [],
    params: { nativeType: 'CUSTOM_SCOPE', preservationReason: 'No registered mapping.' },
    interpretationStatus: 'UNRESOLVED'
  }];
  document.rootExpressionRefs = ['opaque:custom'];
  const result = await adapter.contractToWorkbench(document);
  assert.equal(result.model.expressions.length, 0);
  assert.equal(result.model.rootExpressionIds.length, 0);
  assert.equal(result.report.status, 'PARTIAL');
  assert.ok(result.report.unmappedRefs.includes('opaque:custom'));
  assert.equal(result.validation.valid, true);
});

test('rejects invalid canonical profile and missing primary source', async () => {
  await assert.rejects(() => adapter.contractToWorkbench({ profileId: 'USG-SEM/0.9' }), /USG-SEM\/1.0/);
  await assert.rejects(() => adapter.contractToWorkbench({
    profileId: 'USG-SEM/1.0', sources: [], primarySourceRef: 'missing'
  }), /missing canonical record/);
});
