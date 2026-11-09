'use strict';

const composer = require('../semantic-composer.js');
const core = require('../semantic-core.js');
let passed = 0;
function check(value, message) {
  if (!value) throw new Error(`FAIL: ${message}`);
  passed += 1;
  console.log(`PASS: ${message}`);
}
function compose(source) {
  const parsed = composer.composeSourceText(source);
  check(!!parsed && parsed.complete === true, `source composer safely parsed: ${source}`);
  const claims = parsed.claims.map(claim => ({
    ...claim,
    evidence: claim.evidence || { sourceText: source, quote: source, start: 0, end: source.length, verified: true },
    completeness: { status: 'complete', missingRoles: [], note: '' },
    provenance: 'source_composition_rule',
    sourceKind: 'interpreted_text'
  }));
  const built = core.buildSemanticModel({
    sourceText: source,
    claims,
    explanations: parsed.explanations,
    semanticComposition: parsed.semanticComposition
  });
  check(built.validation.valid, `canonical semantic graph validates: ${source}`);
  check(built.validation.status === 'valid', `no unresolved semantic structure for supported case: ${source}`);
  return { parsed, model: built.model, validation: built.validation };
}
function find(model, fn) { return model.expressions.find(fn); }
function root(model) { return model.expressions.find(e => e.id === model.rootExpressionIds[0]); }

const c1 = compose('The customer does not dislike the tool.');
const notDislike = root(c1.model);
check(notDislike?.type === 'OPERATOR' && notDislike.operatorType === 'NEGATION', 'NOT scopes over DISLIKE');
check(find(c1.model, e => e.type === 'PREDICATION' && e.predicate === 'DISLIKE')?.arguments.find(a => a.role === 'object')?.entityId, 'NOT DISLIKE retains the explicit TOOL argument');

const c2 = compose('The customer might not need the tool.');
const might = root(c2.model);
const not = c2.model.expressions.find(e => e.id === might?.scope?.targetId);
check(might?.operator === 'MIGHT' && not?.operator === 'NOT', 'MIGHT takes scope over NOT, which takes scope over NEEDS');

const c3 = compose('The customer needs the tool, but does not need it.');
check(c3.parsed.claims.length === 2, 'BUT preserves two independent clause propositions');
check(c3.parsed.claims[1].object?.text === 'tool' && c3.parsed.claims[1].polarity === 'negative', 'omitted subject and pronoun object are resolved from discourse context');
check(root(c3.model)?.connective === 'CONTRAST', 'BUT becomes a top-level CONTRAST connective');

const c4 = compose('If prices increase, the customer will stop using the tool.');
const ifNode = root(c4.model);
check(ifNode?.connective === 'CONDITIONAL', 'IF forms a directed conditional connective');
check(c4.parsed.claims[0].conditions[0].proposition.tense === 'present' && c4.parsed.claims[0].tense === 'future', 'IF antecedent and consequent retain independent tense');
check(find(c4.model, e => e.type === 'PREDICATION' && e.predicate === 'INCREASE')?.attribution.status === 'embedded_condition_not_asserted', 'IF antecedent is not promoted to an asserted fact');

const c5 = compose('Unless prices increase, the customer does not need the tool.');
check(root(c5.model)?.connective === 'EXCEPTION', 'UNLESS is represented as EXCEPTION, not ordinary IF');
check(c5.parsed.claims[0].polarity === 'negative' && c5.parsed.claims[0].conditions[0].marker === 'unless', 'UNLESS preserves both the negative consequent and exception marker');
check(c5.parsed.claims[0].conditions[0].effect === 'exception_to_assertion' && c5.parsed.claims[0].conditions[0].logicalStatus === 'exception_relation_asserted', 'UNLESS compatibility metadata retains exception-specific effect and status');
check(c5.parsed.claims[0].conditions[0].consequence !== 'unspecified' && c5.parsed.claims[0].conditions[0].consequentClaimId === c5.parsed.claims[0].id, 'UNLESS metadata explicitly links its consequent to the parent negative claim');
check(root(c5.model).conditionMetadata?.effect === 'exception_to_assertion' && root(c5.model).conditionMetadata?.consequentClaimId === c5.parsed.claims[0].id, 'canonical EXCEPTION connective agrees with claim-level condition metadata');
const unlessAntecedent=c5.model.expressions.find(e=>e.id===root(c5.model).antecedentId);
check(unlessAntecedent?.type==='OPERATOR' && unlessAntecedent.operator==='NOT' && root(c5.model).antecedentInterpretation.includes('if_not_P'), 'UNLESS explicitly scopes NOT over its exception condition (IF NOT P, Q)');
const inconsistentUnless = structuredClone(c5.model);
inconsistentUnless.expressions.find(e=>e.connective==='EXCEPTION').conditionMetadata.effect='condition_for_assertion';
const inconsistentUnlessValidation = core.validateSemanticModel(inconsistentUnless);
check(!inconsistentUnlessValidation.valid && inconsistentUnlessValidation.errors.some(e=>e.includes('conflicts with condition effect')), 'semantic validator detects disagreement between EXCEPTION graph and compatibility metadata');

const c6 = compose('When prices increase, the customer stops using the tool.');
check(root(c6.model)?.connective === 'WHEN' && root(c6.model).logicalStatus === 'when_clause_not_asserted', 'WHEN is distinct from an IF conditional');
check(c6.parsed.claims[0].conditions[0].effect === 'temporal_condition_for_assertion' && root(c6.model).conditionMetadata.effect === 'temporal_condition_for_assertion', 'WHEN retains temporal effect metadata across the claim and canonical graph');
const inconsistentWhen=structuredClone(c6.model);
inconsistentWhen.expressions.find(e=>e.connective==='WHEN').conditionMetadata.effect='condition_for_assertion';
const inconsistentWhenValidation=core.validateSemanticModel(inconsistentWhen);
check(!inconsistentWhenValidation.valid && inconsistentWhenValidation.errors.some(e=>e.includes('non-temporal condition effect')), 'semantic validator rejects WHEN metadata that collapses temporal meaning into a generic conditional');

const c7 = compose('Although prices increased, the customer stopped using the tool.');
check(c7.parsed.claims.length === 2 && root(c7.model)?.connective === 'CONCESSIVE', 'ALTHOUGH relates two separate propositions through CONCESSIVE');
check(root(c7.model).evidenceRefs.length === 2 && root(c7.model).evidenceRefs.every(ref=>c7.model.evidence.some(e=>e.id===ref)), 'CONCESSIVE connective retains valid evidence references for both clauses');

const c8 = compose('The customer stopped using the tool because it failed.');
check(c8.parsed.claims[1].subject.text === 'tool' && c8.parsed.claims[1].predicate === 'FAIL', 'BECAUSE clause resolves IT to the tool and creates a separate cause proposition');
check(c8.model.relations.some(r => r.type === 'CAUSE' && r.attribution.kind === 'source_asserted' && r.verification === 'not_independently_verified'), 'CAUSE retains source attribution and is not marked independently verified');

const c9 = compose('The customer bought a tool. He uses it every day.');
check(c9.parsed.claims.length === 2 && c9.parsed.claims[1].subject.text === 'customer' && c9.parsed.claims[1].object.text === 'tool', 'cross-sentence HE and IT resolve to prior discourse entities');
check(c9.parsed.claims[1].eventAttributes.some(a => a.type === 'frequency' && a.normalizedValue === 'P1D'), 'EVERY DAY is attached to the USES event, not the object');
check(c9.model.mentions.some(m => m.surfaceText === 'He' && m.mentionType === 'pronoun' && m.resolutionStatus === 'resolved') && c9.model.mentions.some(m => m.surfaceText === 'it' && m.mentionType === 'pronoun' && m.resolutionStatus === 'resolved'), 'canonical graph preserves both resolved pronoun surface mentions');

const c10 = compose('The customer needs the tool or wants a refund.');
check(c10.parsed.claims.length === 2 && root(c10.model)?.connective === 'OR', 'OR keeps two propositions and creates an explicit disjunction');
check(root(c10.model).disjunctionSemantics === 'inclusive_or_unspecified', 'OR remains inclusive/unspecified instead of assuming exclusive alternatives');
const c10and = compose('The customer buys the tool and uses it every day.');
check(c10and.parsed.claims.length===2 && root(c10and.model)?.connective==='AND', 'AND retains both propositions within a conjunction');

const c11 = compose('Not every customer needs the tool.');
const c11root = root(c11.model);
const c11target = c11.model.expressions.find(e => e.id === c11root.scope.targetId);
check(c11root.operatorType === 'NEGATION' && c11target.operator === 'FORALL', 'NOT EVERY is represented as NOT over FORALL');

const c12 = compose('No customer needs the tool.');
const c12root = root(c12.model);
const c12target = c12.model.expressions.find(e => e.id === c12root.scope.targetId);
check(c12root.operator === 'FORALL' && c12target.operator === 'NOT', 'NO CUSTOMER is represented as FORALL over NOT');

const c13 = compose('The customer is expected to need the tool.');
check(root(c13.model)?.operator === 'EXPECTED' && root(c13.model).force === 'epistemic_expectation', 'EXPECTED is not flattened into deontic MUST');

const c14 = compose('Prices were different.');
check(c14.parsed.claims[0].predicate === 'DIFFER' && c14.parsed.claims[0].completeness?.status !== 'underspecified', 'Prices were different remains a complete assertion without a comparison target');

// Generalization checks: same clause-composition rules with unseen predicate vocabulary,
// and subordinate clauses in either surface order.
const g1 = compose('If demand decreases, the company reduces production.');
check(root(g1.model)?.connective === 'CONDITIONAL' && g1.parsed.claims[0].predicate === 'REDUCE', 'conditional composition generalizes to unseen predicate vocabulary');
const g2 = compose('The customer will stop using the tool if prices increase.');
check(root(g2.model)?.connective === 'CONDITIONAL', 'trailing IF clauses compose like leading IF clauses');
const g3 = compose('The customer stopped using the tool although prices increased.');
check(root(g3.model)?.connective === 'CONCESSIVE', 'trailing ALTHOUGH clauses compose as concessive relations');
const g3b = compose('The customer stops using the tool unless prices increase.');
check(root(g3b.model)?.connective === 'EXCEPTION', 'trailing UNLESS clauses compose as exception relations');
const g3c = compose('The customer stops using the tool when prices increase.');
check(root(g3c.model)?.connective === 'WHEN', 'trailing WHEN clauses compose as temporal relations');
const g4 = compose('Because it failed, the customer stopped using the tool.');
check(g4.model.relations.some(r => r.type === 'CAUSE') && g4.parsed.claims[0].subject.text === 'tool', 'leading BECAUSE clauses preserve cause/effect relation and resolve pronouns');
const g5 = compose('Although inventory fell, the business increased output.');
check(g5.parsed.claims[0].predicate === 'DECREASE' && g5.parsed.claims[1].predicate === 'INCREASE', 'concessive composition generalizes to additional verb frames');

// Unsupported or incomplete source patterns must not be labelled as fully parsed.
check(composer.composeSourceText('The customer needs.') === null, 'a transitive clause with a missing object is not declared a complete source parse');
check(composer.composeSourceText('If prices increase, the customer stops.') === null, 'an incomplete conditional consequent is not silently accepted');

// Defensive regression: empty quantifier metadata and template placeholders must disappear.
const malformed = core.buildSemanticModel({
  sourceText: 'The customer uses the tool every day.',
  claims: [{
    id: 'malformed', subject: { text: 'customer' }, predicate: 'USES', object: { text: 'tool' },
    polarity: 'positive', tense: 'present', modality: 'asserted',
    quantifierScope: { operator: null, quantifier: null, variable: null, restrictor: {}, surfaceText: '...', logicalForm: '...' },
    eventAttributes: [
      { type: 'frequency', value: '...', normalizedValue: '...', surfaceText: '...', scope: 'event' },
      { type: 'frequency', value: 'every day', normalizedValue: '...', surfaceText: 'every day', scope: 'event' }
    ],
    evidence: { sourceText: 'The customer uses the tool every day.', quote: 'The customer uses the tool every day.', start: 0, end: 37 }
  }]
});
check(!malformed.model.expressions.some(e => e.operatorType === 'UNRESOLVED_SCOPE'), 'empty model quantifier placeholders do not create UNRESOLVED_SCOPE');
const uses = find(malformed.model, e => e.type === 'PREDICATION' && e.predicate === 'USES');
check(uses.eventFrame.attributes.length === 1 && uses.eventFrame.attributes[0].value === 'every day' && uses.eventFrame.attributes[0].normalizedValue === null, 'placeholder event attributes are discarded while source-grounded attributes survive');

console.log(`\nSemantic composition tests: ${passed} passed, 0 failed.`);
