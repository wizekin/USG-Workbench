'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const appPath = path.join(__dirname, '..', 'app.js');
const source = fs.readFileSync(appPath, 'utf8');
const semanticCore = require(path.join(__dirname, '..', 'semantic-core.js'));
const eventSection = source.indexOf('// ---------------------- Event wiring / initialization ----------------------');
if (eventSection < 0) throw new Error('Could not locate the end of the app logic.');
const executable = source.slice(0, eventSection) + `\nrenderReasoning = () => {};\nrenderInterpretation = () => {};\nshowToast = () => {};\nglobalThis.__test = { localInterpret, safeModelInterpretation, runReasoning, claimSentence, renderMeaning, renderStructure, renderEvidence, toExportableInterpretation, parseBatchLines, batchStatusForRecord, createBatchExport, acceptInterpretation, addClaimRelations, enrichV04Record, sourceQuantifierFrame, buildClaim, setState:(value)=>{state=value;}, setCurrentInterpretation:(value)=>{currentInterpretation=value;}, getState:()=>state };`;
const store = new Map();
const uiNodes = new Map();
const sandbox = {
  console,
  Date,
  Math,
  JSON,
  Map,
  Set,
  URL,
  URLSearchParams,
  localStorage: { getItem:key=>store.has(key)?store.get(key):null, setItem:(key,value)=>store.set(key,value) },
  document: { querySelector:(selector)=>{ if (['#metric-claims','#metric-concepts','#metric-patterns','#metric-derived','#accept-button','#result-tab-meaning','#result-tab-structure','#result-tab-evidence'].includes(selector)) { if (!uiNodes.has(selector)) uiNodes.set(selector,{textContent:'',innerHTML:'',hidden:false,disabled:false,style:{opacity:''}}); return uiNodes.get(selector); } return null; }, querySelectorAll:()=>[] },
  window: { scrollTo:()=>{} },
  setTimeout,
  clearTimeout,
  confirm:()=>true,
  USGSemanticCore:semanticCore
};
vm.createContext(sandbox);
vm.runInContext(executable, sandbox, { filename:'app.js' });
const { localInterpret, safeModelInterpretation, runReasoning, claimSentence, getState } = sandbox.__test;
function assert(condition, message) { if (!condition) throw new Error(`FAIL: ${message}`); console.log(`PASS: ${message}`); }

let result = localInterpret('A sparrow is a kind of bird.');
assert(result.claims.length===1 && result.claims[0].predicate==='SUBCLASS_OF', 'subclass pattern creates one SUBCLASS_OF claim');
assert(result.claims[0].subject.text==='sparrow' && result.claims[0].object.text==='bird', 'leading articles are removed from concept labels');

result = localInterpret('A thermometer measures temperature.');
assert(result.claims.length===1 && result.claims[0].predicate==='MEASURES', 'measurement relation is extracted');
assert(result.claims[0].subject.text==='thermometer' && result.claims[0].object.text==='temperature', 'measurement entities are normalized');

result = localInterpret('The customer does not need a tool unless prices differ.');
assert(result.claims.length===1 && result.claims[0].predicate==='NEEDS', 'negative NEEDS proposition is extracted');
assert(result.claims[0].polarity==='negative', 'negation is preserved');
assert(result.claims[0].tense==='present', 'does-not-need is represented in present tense');
assert(result.claims[0].conditions.length===1 && result.claims[0].conditions[0].marker==='unless', 'unless clause is represented separately');
assert(/^NOT NEEDS\(/.test(result.claims[0].conditions[0].consequence) && result.claims[0].conditions[0].consequentClaimId===result.claims[0].id, 'unless consequence is explicitly linked to the source-grounded negative parent claim rather than left unspecified');
assert(result.claims[0].object.text==='tool', 'the condition is not merged into the object phrase');

// LLM adapter regression tests: malformed optional fields must not crash normalization.
const llmNullObject = safeModelInterpretation({
  intent:'ASSERTION', interpretation:'A subject is related to something unspecified.',
  claims:[{subject:{text:'The customer',type:'person'},predicate:'HAS_PROPERTY',object:null,polarity:'positive',tense:'present',modality:'asserted',conditions:[null,{marker:'if',proposition:{subject:'prices',predicate:'DIFFER',object:null}}],confidence:0.7}]
}, 'The customer is waiting.');
assert(llmNullObject.claims.length===1 && llmNullObject.claims[0].object===null, 'LLM null object is retained without crashing');
assert(llmNullObject.claims[0].subject.reference==='definite', 'definite reference is preserved independently of the normalized entity label');
assert(llmNullObject.claims[0].conditions.length===1, 'malformed null condition is ignored while valid condition survives');

const llmNegativeLike = safeModelInterpretation({
  claims:[{subject:{text:'The customer',type:'person'},predicate:'LIKE',object:{text:'the tool',type:'artifact'},polarity:'negative',tense:'present',modality:'asserted',evidence_text:'does not like the tool'}]
}, 'The customer does not like the tool.');
assert(llmNegativeLike.claims[0].predicate==='LIKE' && llmNegativeLike.claims[0].polarity==='negative', 'negative LIKE remains LIKE with negative polarity');
assert(llmNegativeLike.claims[0].object.text==='tool' && llmNegativeLike.claims[0].object.reference==='definite', 'definite object reference survives article normalization');
assert(llmNegativeLike.claims[0].tense==='present', 'present simple is retained for a negative LIKE sentence');

const llmBadTense = safeModelInterpretation({
  claims:[{subject:'The thermometer',predicate:'MEASURES',object:'temperature',polarity:'negative',tense:'past',modality:'asserted'}]
}, 'The thermometer does not measure temperature.');
assert(llmBadTense.claims[0].tense==='present', 'clear present-tense source marker corrects an inconsistent model tense');
assert(llmBadTense.warnings.some(w=>w.includes('Tense correction')), 'tense correction is disclosed in validation warnings');
assert(llmBadTense.claims[0].predicate==='MEASURES' && llmBadTense.claims[0].polarity==='negative', 'negative MEASURES does not imply inability or change the predicate');
const llmOverstated = safeModelInterpretation({
  interpretation:'The thermometer is incapable of measuring temperature.',
  claims:[{subject:'The thermometer',predicate:'MEASURES',object:'temperature',polarity:'negative',tense:'present',modality:'asserted',notes:'The device is incapable of measuring it.'}]
}, 'The thermometer does not measure temperature.');
assert(llmOverstated.warnings.some(w=>w.includes('strengthened the negative claim')), 'unsupported inability wording is flagged instead of silently accepted as a consequence of negation');
const llmMixedTense = safeModelInterpretation({
  claims:[{subject:'The customer',predicate:'NEEDS',object:'the tool',polarity:'negative',tense:'past',modality:'asserted'}]
}, 'The customer does not need the tool because prices were different.');
assert(llmMixedTense.claims[0].tense==='present', 'main-clause tense is detected separately from a past-tense because clause');
assert(llmMixedTense.claims.some(c=>c.subject.text==='prices' && c.predicate==='DIFFER' && c.tense==='past'), 'because clause receives its own past-tense cause proposition');
assert(llmMixedTense.explanations.length===1 && llmMixedTense.explanations[0].type==='CAUSE', 'because clause is linked to the effect through an explicit causal explanation');
assert(llmMixedTense.explanations[0].attribution==='source_asserted', 'causal relation is attributed to the source rather than treated as independently verified');



// Negation, reference, tense, and clause-level regression tests.
const qwenNeedNullObject = safeModelInterpretation({
  intent:'ASSERTION', interpretation:'The customer does not need the tool.',
  claims:[{id:'q1',subject:{text:'The customer',type:'unknown'},predicate:'NEEDS',object:null,polarity:'negative',tense:'present',modality:'asserted',conditions:[],confidence:1,notes:'Direct negative assertion.'}]
}, 'The customer does not need the tool.');
assert(qwenNeedNullObject.claims[0].object?.text==='tool', 'missing NEEDS object is recovered from the explicit source phrase');
assert(qwenNeedNullObject.claims[0].object.reference==='definite', 'recovered object retains the source definite article');
assert(qwenNeedNullObject.claims[0].polarity==='negative' && qwenNeedNullObject.claims[0].predicate==='NEEDS', 'negative NEEDS retains its base predicate and polarity');

const qwenNegatedPredicate = safeModelInterpretation({
  intent:'ASSERTION', interpretation:'The customer does not like the tool.',
  claims:[{id:'q2',subject:{text:'The customer',type:'unknown'},predicate:'DOES_NOT_LIKE',object:{text:'the tool',type:'unknown'},polarity:'negative',tense:'present',modality:'asserted',conditions:[],confidence:1,notes:'The source states dislike.'}]
}, 'The customer does not like the tool.');
assert(qwenNegatedPredicate.claims[0].predicate==='LIKE' && qwenNegatedPredicate.claims[0].polarity==='negative', 'DOES_NOT_LIKE is normalized to LIKE with negative polarity');
assert(qwenNegatedPredicate.claims[0].object.reference==='definite', 'negated LIKE preserves the definite object reference');
assert(qwenNegatedPredicate.warnings.some(w=>w.includes('predicate name encoded negation')), 'predicate negation normalization is disclosed to the user');

const qwenNegativeMeasures = safeModelInterpretation({
  intent:'ASSERTION', interpretation:'The thermometer does not measure temperature.',
  claims:[{id:'q3',subject:{text:'The thermometer',type:'unknown'},predicate:'MEASURES',object:{text:'temperature',type:'unknown'},polarity:'negative',tense:'present',modality:'asserted',conditions:[],confidence:1}]
}, 'The thermometer does not measure temperature.');
assert(qwenNegativeMeasures.claims[0].predicate==='MEASURES' && qwenNegativeMeasures.claims[0].polarity==='negative', 'negative MEASURES remains a negative MEASURES proposition');
assert(qwenNegativeMeasures.claims[0].tense==='present', 'negative MEASURES is present tense');

const qwenBecause = safeModelInterpretation({
  intent:'ASSERTION', interpretation:'The customer does not need the tool because of different prices.',
  claims:[{id:'q4',subject:{text:'The customer',type:'unknown'},predicate:'NEEDS',object:null,polarity:'negative',tense:'unknown',modality:'asserted',conditions:[],confidence:0.95,notes:'The sentence directly states the reason.'}]
}, 'The customer does not need the tool because prices were different.');
const qwenBecauseEffect = qwenBecause.claims.find(c=>c.predicate==='NEEDS');
const qwenBecauseCause = qwenBecause.claims.find(c=>c.predicate==='DIFFER');
assert(qwenBecauseEffect?.object?.text==='tool', 'because sentence recovers the omitted main-clause object');
assert(qwenBecauseEffect?.tense==='present', 'because sentence retains present tense on the main claim');
assert(qwenBecauseCause?.subject.text==='prices' && qwenBecauseCause.tense==='past', 'because clause is a separate past-tense proposition');
assert(qwenBecause.explanations.length===1 && qwenBecause.explanations[0].causeClaimId===qwenBecauseCause.id && qwenBecause.explanations[0].effectClaimId===qwenBecauseEffect.id, 'causal link points to the correct separate cause and effect claims');
assert(qwenBecause.explanations[0].evidence.quote==='because prices were different', 'causal relation retains an exact source evidence span');
assert(qwenBecause.explanations[0].attribution==='source_asserted', 'causal relation is clearly marked as asserted by the source');
assert(qwenBecause.claims.length===2, 'cause and effect are represented as two propositions, not one merged claim');
assert(qwenBecauseCause.completeness.status==='complete' && qwenBecauseCause.comparisonFrame.status==='context_dependent', 'DIFFER can be interpreted as a sentence-level proposition while retaining its unstated comparison frame');
assert(!qwenBecause.unresolved.some(x=>x.includes('comparison reference')) && sandbox.__test.batchStatusForRecord(qwenBecause)==='completed', 'an unstated comparison target is task-specific context, not automatic global semantic incompleteness');
assert(claimSentence(qwenBecauseCause)==='prices were different', 'knowledge display renders the objectless past-tense cause claim naturally');
sandbox.__test.renderMeaning(qwenBecause);
sandbox.__test.renderStructure(qwenBecause);
sandbox.__test.renderEvidence(qwenBecause);
assert(uiNodes.get('#result-tab-meaning').innerHTML.includes('SOURCE-ASSERTED CAUSAL EXPLANATION'), 'Meaning view renders the explicit causal explanation');
assert(uiNodes.get('#result-tab-structure').innerHTML.includes('EXPLANATION (source_asserted)'), 'Structure view renders the causal link between claim IDs');
assert(uiNodes.get('#result-tab-evidence').innerHTML.includes('because prices were different'), 'Evidence view renders the causal source span');
assert(sandbox.__test.toExportableInterpretation(qwenBecause).schemaVersion==='0.5.1', 'JSON export identifies the v0.5 semantic representation schema');

// Regression fixture: this is the exact raw Qwen batch export supplied by the user.
const qwenBatchFixture = JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures','qwen_batch_v0_3_2.json'),'utf8'));
assert(qwenBatchFixture.workbenchVersion==='0.3.2' && qwenBatchFixture.results.length===4, 'actual v0.3.2 Qwen export fixture loads with all four original test cases');
const actualNeed = qwenBatchFixture.results[0];
const actualNeedNormalized = safeModelInterpretation(actualNeed.rawModelResponse, actualNeed.sourceText);
assert(actualNeedNormalized.claims[0].object?.text==='tool', 'actual Qwen null-object response is repaired from its source text');
assert(actualNeedNormalized.claims[0].evidence.verified===true && actualNeedNormalized.claims[0].evidence.modelQuoteVerified===false, 'invalid model quote is distinguished from the exact full-source evidence fallback');
assert(actualNeedNormalized.claims[0].evidence.start===0 && actualNeedNormalized.claims[0].evidence.end===actualNeed.sourceText.length && actualNeedNormalized.claims[0].evidence.quote===actualNeed.sourceText, 'fallback evidence offsets exactly cover the original source');
const actualNotLike = qwenBatchFixture.results[1];
const actualNotLikeNormalized = safeModelInterpretation(actualNotLike.rawModelResponse, actualNotLike.sourceText);
assert(actualNotLike.rawModelResponse.claims[0].predicate.toLowerCase()==='dislikes', 'fixture retains the model’s original DISLIKES proposal for audit');
assert(actualNotLikeNormalized.claims[0].predicate==='LIKE' && actualNotLikeNormalized.claims[0].polarity==='negative', 'actual DISLIKES plus negative output is source-reconciled to LIKE plus negative polarity');
assert(actualNotLikeNormalized.warnings.some(w=>w.includes('reconciled to LIKE')), 'source-based negated-LIKE repair is disclosed in warnings');
const notDislikeControl = safeModelInterpretation({claims:[{subject:'The customer',predicate:'DISLIKES',object:'the tool',polarity:'negative',tense:'present',modality:'asserted'}]}, 'The customer does not dislike the tool.');
assert(notDislikeControl.claims[0].predicate==='DISLIKES' && notDislikeControl.claims[0].polarity==='negative', 'does not dislike is not incorrectly rewritten by the narrow does not like repair');
const actualBecause = qwenBatchFixture.results[3];
const actualBecauseNormalized = safeModelInterpretation(actualBecause.rawModelResponse, actualBecause.sourceText);
const actualBecauseCause = actualBecauseNormalized.claims.find(c=>c.predicate==='DIFFER');
assert(actualBecauseCause?.completeness.status==='complete' && actualBecauseCause.comparisonFrame.status==='context_dependent', 'actual because-clause cause claim preserves its context-dependent comparison frame');
assert(!actualBecauseNormalized.unresolved.some(x=>x.includes('comparison reference')), 'context-dependent comparison is not incorrectly promoted to a global unresolved error');
assert(sandbox.__test.batchStatusForRecord(actualBecauseNormalized)==='completed', 'a sentence-level complete DIFFER claim is not forced to PARTIAL solely because its comparison set is implicit');
const mixedBatch = sandbox.__test.createBatchExport([
  {status:'completed'}, {status:'partial'}, {status:'unresolved'}, {status:'fallback_after_error'}
], 'qwen2.5:1.5b', '2026-11-07T00:00:00.000Z', 'http://127.0.0.1:11434');
assert(mixedBatch.summary.total===4 && mixedBatch.summary.completed===1 && mixedBatch.summary.partial===1 && mixedBatch.summary.unresolved===1 && mixedBatch.summary.fallbackAfterError===1, 'batch summary separately counts completed, partial, unresolved, and fallback results');

const unsupportedBecause = safeModelInterpretation({
  claims:[{subject:'The customer',predicate:'NEEDS',object:null,polarity:'negative',tense:'present',modality:'asserted'}]
}, 'The customer does not need the tool because the meeting was postponed.');
assert(unsupportedBecause.explanations.length===0 && unsupportedBecause.unresolved.some(x=>x.includes('because')), 'unsupported because clause is preserved as unresolved, not guessed');
sandbox.__test.renderMeaning(unsupportedBecause);
assert(uiNodes.get('#result-tab-meaning').innerHTML.includes('Unresolved') && uiNodes.get('#result-tab-meaning').innerHTML.includes('meeting was postponed'), 'unresolved causal subclause is visible alongside a valid main claim');

const llmMalformed = safeModelInterpretation({claims:[null,{}, {subject:null,predicate:'LIKES',object:null}]}, 'Unclear.');
assert(llmMalformed.claims.length===0 && llmMalformed.unresolved.length>0, 'malformed model claims are rejected with an explicit unresolved note');

result = localInterpret('A robin belongs to the bird family.');
assert(result.claims.length===1 && result.claims[0].subject.text==='robin' && result.claims[0].object.text==='bird', 'family-membership wording is normalized to subclass relation');

result = localInterpret('Although the instrument is accurate, the reading may be misleading.');
assert(result.claims.length===0 && result.unresolved.length>0, 'unsupported complex sentence remains unresolved without fabricated claims');


const fallbackBecause = localInterpret('The customer does not need the tool because prices were different.');
assert(fallbackBecause.claims.length===2, 'offline NEEDS parser separates the effect and because-clause claims');
assert(fallbackBecause.claims[0].object.text==='tool' && fallbackBecause.claims[0].tense==='present', 'offline NEEDS parser retains the main object and present tense');
assert(fallbackBecause.claims[1].subject.text==='prices' && fallbackBecause.claims[1].tense==='past', 'offline because-clause claim retains past tense');
assert(fallbackBecause.explanations.length===1 && fallbackBecause.explanations[0].type==='CAUSE', 'offline parser also produces an explicit causal link');
assert(fallbackBecause.claims[1].completeness.status==='complete' && fallbackBecause.claims[1].comparisonFrame.status==='context_dependent' && fallbackBecause.unresolved.length===0, 'offline because parser stores a task-specific comparison frame without global incompleteness');
assert(sandbox.__test.batchStatusForRecord(fallbackBecause)==='completed', 'offline cause record is complete at sentence level while comparison tasks remain context-dependent');

// Confirm the source-linked cause/effect IDs survive acceptance into persistent knowledge.
sandbox.__test.setCurrentInterpretation(qwenBecause);
sandbox.__test.acceptInterpretation();
let acceptedState = sandbox.__test.getState();
const acceptedEffect = acceptedState.claims.find(c=>c.predicate==='NEEDS' && c.polarity==='negative' && c.evidence?.sourceText==='The customer does not need the tool because prices were different.');
const acceptedLink = acceptedEffect?.causalLinks?.[0];
const acceptedCause = acceptedState.claims.find(c=>c.id===acceptedLink?.causeClaimId);
assert(!!acceptedEffect && !!acceptedCause, 'accepted knowledge stores both the effect and cause propositions');
assert(acceptedLink.effectClaimId===acceptedEffect.id && acceptedCause.predicate==='DIFFER', 'accepted causal link is remapped to persistent knowledge-base claim IDs');

assert(acceptedEffect.provenance==='accepted_local_llm_proposal', 'accepted LLM proposal remains visibly distinguished by provenance');
const contradictionProposal=localInterpret('The customer needs the tool, but does not need it.');
sandbox.__test.setCurrentInterpretation(contradictionProposal);
sandbox.__test.acceptInterpretation();
acceptedState=sandbox.__test.getState();
assert(acceptedState.relations.some(r=>r.type==='CONTRADICTS' && r.status==='accepted_candidate_requires_review'), 'accepted proposition pairs persist their contradiction candidate with remapped knowledge-base IDs');


runReasoning();
let state = getState();
assert(state.derived.length===3, 'starter knowledge derives exactly three claims');
assert(state.derived.some(c=>c.ruleId==='R-IS-A-TRANSITIVE' && c.subject.text==='Sparrow' && c.object.text==='Animal'), 'subclass transitivity derives Sparrow → Animal');
assert(state.derived.some(c=>c.ruleId==='R-INSTANCE-INHERITANCE' && c.subject.text==='Tweety' && c.object.text==='Bird'), 'instance inheritance derives Tweety → Bird');
assert(state.derived.some(c=>c.ruleId==='R-INSTANCE-INHERITANCE' && c.subject.text==='Tweety' && c.object.text==='Animal'), 'inference chain derives Tweety → Animal');
runReasoning();
state = getState();

assert(state.derived.length===3, 'rerunning reasoning does not duplicate derived claims');
const originalReasoningState=sandbox.__test.getState();
const possibleFact=sandbox.__test.buildClaim('ConditionalBird','SUBCLASS_OF','Bird',{modality:'possible',tense:'present'});
const assertedFact=sandbox.__test.buildClaim('Bird','SUBCLASS_OF','Animal',{modality:'asserted',tense:'present'});
const quantifiedFact=sandbox.__test.buildClaim('EverySparrow','INSTANCE_OF','Bird',{modality:'asserted',tense:'present',quantifierScope:{operator:'NOT',quantifier:'FORALL'}});
sandbox.__test.setState({schemaVersion:2,claims:[possibleFact,assertedFact,quantifiedFact],patterns:[],derived:[],relations:[],interpretationHistory:[],lastRunAt:null});
sandbox.__test.runReasoning();
assert(sandbox.__test.getState().derived.length===0, 'v0.4 simple inference excludes modal and quantified claims');
const futureReferenceInstance=sandbox.__test.buildClaim('FutureTweety','INSTANCE_OF','Bird',{modality:'asserted',tense:'present',time:{grammaticalTense:'present',referenceTime:'future'}});
sandbox.__test.setState({schemaVersion:2,claims:[assertedFact,futureReferenceInstance],patterns:[],derived:[],relations:[],interpretationHistory:[],lastRunAt:null});
sandbox.__test.runReasoning();
assert(sandbox.__test.getState().derived.length===0, 'v0.4 simple inference excludes a present-grammatical claim with future temporal reference');
sandbox.__test.setState(originalReasoningState);


const batchLines = sandbox.__test.parseBatchLines('First sentence.\n\n Second sentence. \r\nThird sentence.');
assert(batchLines.length===3 && batchLines[1]==='Second sentence.', 'batch parser trims lines and ignores blanks');
const batchFile = sandbox.__test.createBatchExport([{status:'completed'},{status:'unresolved'},{status:'fallback_after_error'}], 'qwen2.5:1.5b', '2026-11-07T00:00:00.000Z', 'http://127.0.0.1:11434');
assert(batchFile.schema==='USG-BATCH-TEST-EXPORT' && batchFile.workbenchVersion==='0.5.4' && batchFile.schemaVersion==='1.3' && batchFile.semanticSchemaVersion==='0.5.1', 'batch export identifies its dedicated schema and workbench version');
assert(batchFile.summary.total===3 && batchFile.summary.completed===1 && batchFile.summary.partial===0 && batchFile.summary.unresolved===1 && batchFile.summary.fallbackAfterError===1, 'batch export summary counts each result state');


// ---------------------- USG Semantic Representation Specification v0.4 ----------------------
const conditionalV04=localInterpret('If prices increase, the customer will stop using the tool.');
assert(conditionalV04.claims.length===1 && conditionalV04.claims[0].predicate==='STOP_USING', 'v0.4 extracts the consequent as its own proposition');
assert(conditionalV04.claims[0].tense==='future', 'v0.4 preserves future tense on the consequent');
assert(conditionalV04.claims[0].conditions[0].proposition.predicate==='INCREASE' && conditionalV04.claims[0].conditions[0].proposition.tense==='present', 'v0.4 stores the IF antecedent as a nested proposition with independent present tense');
assert(conditionalV04.claims[0].conditions[0].logicalStatus==='conditional_not_asserted', 'v0.4 does not treat a conditional antecedent as an asserted observation');
assert(conditionalV04.claims[0].conditions[0].proposition.subject.entityId, 'v0.4 registers entities appearing inside nested conditions');
assert(conditionalV04.semanticModel?.profile==='USG-SR/0.5.1' && conditionalV04.semanticValidation?.valid===true, 'v0.5 builds a canonical expression graph alongside the v0.4 compatibility claim view');
assert(conditionalV04.semanticModel.expressions.some(e=>e.type==='CONNECTIVE'&&e.connective==='CONDITIONAL'), 'v0.5 exposes the IF construction as a canonical scoped connective');
assert(sandbox.__test.batchStatusForRecord(conditionalV04)==='completed', 'a structurally valid, resolved conditional is eligible for completed batch status');

const opposingV04=localInterpret('The customer needs the tool, but does not need it.');
assert(opposingV04.claims.length===2 && opposingV04.claims[0].polarity==='positive' && opposingV04.claims[1].polarity==='negative', 'v0.4 preserves both opposing clauses as separate propositions');
assert(opposingV04.claimRelations.length===1 && opposingV04.claimRelations[0].type==='CONTRADICTS', 'v0.4 creates a contradiction candidate only for matching proposition frames');
const modalFrameA=sandbox.__test.buildClaim('customer','NEEDS','tool',{polarity:'positive',modality:'possible',modalScope:{operator:'MIGHT',force:'possible',scope:'proposition'},tense:'present',time:{grammaticalTense:'present',referenceTime:'present',temporalAdverbials:[]}});
const modalFrameB=sandbox.__test.buildClaim('customer','NEEDS','tool',{polarity:'negative',modality:'possible',modalScope:{operator:'MAY',force:'possible',scope:'proposition'},tense:'present',time:{grammaticalTense:'present',referenceTime:'present',temporalAdverbials:[]}});
assert(sandbox.__test.addClaimRelations([modalFrameA,modalFrameB]).length===0, 'v0.4 does not equate distinct modal operators merely because their broad modality labels match');
const frequencyFrameA=sandbox.__test.buildClaim('customer','USES','tool',{polarity:'positive',tense:'present',eventAttributes:[{type:'frequency',value:'every day',normalizedValue:'P1D',scope:'event'}],time:{grammaticalTense:'present',referenceTime:'present',temporalAdverbials:['every day']}});
const frequencyFrameB=sandbox.__test.buildClaim('customer','USES','tool',{polarity:'negative',tense:'present',eventAttributes:[{type:'frequency',value:'every week',normalizedValue:'P1W',scope:'event'}],time:{grammaticalTense:'present',referenceTime:'present',temporalAdverbials:['every week']}});
assert(sandbox.__test.addClaimRelations([frequencyFrameA,frequencyFrameB]).length===0, 'v0.4 does not flag different event-frequency frames as direct contradictions');

const modalV04=localInterpret('The customer might need the tool.');
assert(modalV04.claims[0].modality==='possible' && modalV04.claims[0].modalScope.operator==='MIGHT', 'v0.4 preserves “might” as an explicit modal operator and possibility force');

const temporalV04=localInterpret('The customer needed the tool but no longer needs it.');
assert(temporalV04.claims.length===2 && temporalV04.claims[0].tense==='past' && temporalV04.claims[1].tense==='present', 'v0.4 preserves the past-to-present temporal change');
assert(temporalV04.claimRelations.length===0, 'v0.4 does not mark opposite claims at different times as a contradiction');
assert(temporalV04.claims.every(c=>c.quantifierScope===null), 'v0.4 does not confuse “no longer” with the quantifier “no”');

const modelNeedCorefV04=safeModelInterpretation({claims:[
  {subject:'The customer',predicate:'NEEDS',object:'the tool',polarity:'positive',tense:'present',modality:'asserted'},
  {subject:'The customer',predicate:'NEEDS',object:'it',polarity:'negative',tense:'present',modality:'asserted'}
]},'The customer needs the tool, but does not need it.');
assert(modelNeedCorefV04.claims[1].object.text==='tool' && modelNeedCorefV04.mentions.some(m=>m.surfaceText==='it' && m.canonicalText==='tool'), 'v0.4 resolves the Gemma-style “it” object in paired NEEDS claims and retains its mention');
const modelCauseCorefV04=safeModelInterpretation({claims:[
  {subject:'The customer',predicate:'STOP_USING',object:'the tool',polarity:'positive',tense:'past',modality:'asserted'},
  {subject:'it',predicate:'FAILS',object:null,polarity:'positive',tense:'past',modality:'asserted'}
]},'The customer stopped using the tool because it failed.');
assert(modelCauseCorefV04.claims[1].subject.text==='tool' && modelCauseCorefV04.mentions.some(m=>m.surfaceText==='it' && m.canonicalText==='tool'), 'v0.4 resolves a model-proposed “it” cause subject to the explicit tool antecedent');
const modelDiscourseCorefV04=safeModelInterpretation({claims:[
  {subject:'The customer',predicate:'BOUGHT',object:'a tool',polarity:'positive',tense:'past',modality:'asserted'},
  {subject:'He',predicate:'USES',object:'it every day',polarity:'positive',tense:'present',modality:'asserted'}
]},'The customer bought a tool. He uses it every day.');
assert(modelDiscourseCorefV04.claims[1].subject.text==='customer' && modelDiscourseCorefV04.claims[1].object.text==='tool' && modelDiscourseCorefV04.claims[1].eventAttributes.some(a=>a.normalizedValue==='P1D'), 'v0.4 repairs model-style pronoun and frequency argument conflation in the supported purchase/use discourse');

const discourseV04=localInterpret('The customer bought a tool. He uses it every day.');
assert(discourseV04.claims.length===2 && discourseV04.claims[1].subject.text==='customer' && discourseV04.claims[1].object.text==='tool', 'v0.4 resolves “He” and “it” to the earlier customer and tool entities');
assert(discourseV04.mentions.some(m=>m.surfaceText==='He' && m.canonicalText==='customer') && discourseV04.mentions.some(m=>m.surfaceText==='it' && m.canonicalText==='tool'), 'v0.4 preserves pronoun surface mentions and antecedent identity');
assert(discourseV04.claims[1].eventAttributes.some(a=>a.type==='frequency' && a.normalizedValue==='P1D'), 'v0.4 represents “every day” as a structured event frequency');

const quantifierV04=localInterpret('Not every customer needs the tool.');
assert(quantifierV04.claims[0].quantifierScope.operator==='NOT' && quantifierV04.claims[0].quantifierScope.quantifier==='FORALL', 'v0.4 represents “not every” as negation over a universal quantifier');
assert(quantifierV04.claims[0].polarity==='positive' && quantifierV04.claims[0].subject.text==='customer', 'v0.4 keeps predicate polarity separate from quantifier-scope negation');
assert(!quantifierV04.claims[0].quantifierScope.logicalForm.includes('FORALL x: category(x) -> NOT'), 'v0.4 does not collapse “not every” into “no customer” semantics');

const noQuantifierV04=localInterpret('No customer needs the tool.');
assert(noQuantifierV04.claims[0].quantifierScope.operator==='NO' && noQuantifierV04.claims[0].quantifierScope.logicalForm.includes('FORALL'), 'v0.4 represents “no customer” as universal negative quantification, distinct from “not every”');

const causalCorefV04=localInterpret('The customer stopped using the tool because it failed.');
assert(causalCorefV04.claims.length===2 && causalCorefV04.claims[1].subject.text==='tool' && causalCorefV04.claims[1].predicate==='FAILS', 'v0.4 resolves “it” in the cause clause to the tool entity');
assert(causalCorefV04.explanations[0].attribution==='source_asserted', 'v0.4 retains source attribution rather than asserting objective causation');
assert(causalCorefV04.mentions.some(m=>m.surfaceText==='it' && m.canonicalText==='tool'), 'v0.4 records the causal-clause pronoun mention');


const comparisonV04=localInterpret('Prices were different.');
assert(comparisonV04.claims.length===1 && comparisonV04.claims[0].completeness.status==='complete' && comparisonV04.claims[0].comparisonFrame.status==='context_dependent', 'v0.4 separates sentence-level interpretability from comparison-task completeness');

const dislikeV04=localInterpret('The customer does not dislike the tool.');
assert(dislikeV04.claims[0].predicate==='DISLIKE' && dislikeV04.claims[0].polarity==='negative', 'v0.4 preserves “does not dislike” without converting it into positive LIKE');

const structuredModelV04=safeModelInterpretation({claims:[{subject:'The customer',predicate:'USES',object:'the tool',polarity:'positive',tense:'present',modality:'possible',modalScope:{operator:'MAY',force:'epistemic_possibility',scope:'proposition',surfaceText:'may'},time:{grammaticalTense:'present',aspect:'habitual',referenceTime:'present'},eventAttributes:[{type:'frequency',value:'every day',normalizedValue:'P1D',surfaceText:'every day',scope:'event'}]}]},'The customer might use the tool every day.');
assert(structuredModelV04.claims[0].modalScope.operator==='MIGHT' && structuredModelV04.claims[0].time.aspect==='habitual' && structuredModelV04.claims[0].eventAttributes.some(a=>a.normalizedValue==='P1D'), 'v0.4 source-corrects the model modal operator while preserving time aspect and event attributes');

const quantifierModelV04=safeModelInterpretation({claims:[{subject:'every customer',predicate:'NEEDS',object:'the tool',polarity:'negative',tense:'present',modality:'asserted'}]},'Not every customer needs the tool.');
assert(quantifierModelV04.claims[0].quantifierScope.operator==='NOT' && quantifierModelV04.claims[0].polarity==='positive', 'v0.4 repairs model polarity duplication when source negation scopes over “every”');

const nestedConditionV04=safeModelInterpretation({claims:[{subject:'The customer',predicate:'STOP_USING',object:'the tool',polarity:'positive',tense:'future',modality:'asserted',conditions:[{marker:'if',proposition:{subject:{text:'prices',type:'unknown'},predicate:'INCREASE',object:null,polarity:'positive',tense:'future',modality:'asserted'},scope:'claim',effect:'condition_for_assertion',evidence_text:'prices increase'}]}]},'If prices increase, the customer will stop using the tool.');
assert(nestedConditionV04.claims[0].conditions[0].proposition.subject.text==='prices' && nestedConditionV04.claims[0].conditions[0].proposition.tense==='present' && nestedConditionV04.claims[0].conditions[0].proposition.time.grammaticalTense==='present', 'v0.4 source-corrects a model future-tense error on a present-simple IF antecedent');
const nestedModalConditionV04=safeModelInterpretation({claims:[{subject:'The customer',predicate:'STOP_USING',object:'the tool',polarity:'positive',tense:'future',modality:'asserted',conditions:[{marker:'if',proposition:{subject:{text:'prices',type:'unknown'},predicate:'INCREASE',object:null,polarity:'positive',tense:'future',modality:'asserted',modalScope:{operator:'MAY',force:'epistemic_possibility',scope:'proposition',surfaceText:'may'},time:{grammaticalTense:'future',aspect:'simple',referenceTime:'future'}},scope:'claim',effect:'condition_for_assertion',evidence_text:'prices might increase'}]}]},'If prices might increase, the customer will stop using the tool.');
assert(nestedModalConditionV04.claims[0].conditions[0].proposition.modality==='possible' && nestedModalConditionV04.claims[0].conditions[0].proposition.modalScope.operator==='MIGHT' && nestedModalConditionV04.claims[0].conditions[0].proposition.tense==='present' && nestedModalConditionV04.claims[0].conditions[0].proposition.time.referenceTime==='future', 'v0.4 source-corrects nested modal operator and grammatical tense while preserving its future reference time');
const malformedConditionV04=safeModelInterpretation({claims:[{subject:'The customer',predicate:'NEEDS',object:'the tool',polarity:'positive',tense:'present',modality:'asserted',conditions:[{marker:'if',proposition:'[object Object]'}]}]},'The customer needs the tool if prices increase.');
assert(malformedConditionV04.claims[0].conditions[0].proposition===null && malformedConditionV04.unresolved.some(x=>x.includes('internal proposition')), 'v0.4 preserves a serialized malformed condition as unresolved instead of storing “[object Object]”');

const v04Export=sandbox.__test.toExportableInterpretation(conditionalV04);
assert(v04Export.schemaVersion==='0.5.1' && v04Export.representationProfile==='USG-SR/0.5.1' && v04Export.validation.allClaimsRequireReview===true, 'v0.5 export declares its representation profile and mandatory human-review boundary');
const partialCandidate=safeModelInterpretation({claims:[{subject:'The customer',predicate:'NEEDS',object:null,polarity:'positive',tense:'present',modality:'asserted'}]},'The customer needs.');
assert(partialCandidate.semanticValidation?.status==='partial' && partialCandidate.semanticModel?.unresolvedItems?.length>0, 'missing required argument is surfaced in the canonical graph as a partial interpretation');
assert(sandbox.__test.batchStatusForRecord(partialCandidate)==='partial', 'batch status does not call a partially represented proposition completed');
const claimsBeforeBlockedAccept=sandbox.__test.getState().claims.length;
sandbox.__test.setCurrentInterpretation(partialCandidate);
sandbox.__test.acceptInterpretation();
assert(sandbox.__test.getState().claims.length===claimsBeforeBlockedAccept, 'knowledge acceptance is blocked while the canonical semantic graph contains unresolved items');
const semanticSchemaV05=JSON.parse(fs.readFileSync(path.join(__dirname,'..','schemas','usg-semantic-record-v0.5.schema.json'),'utf8'));
assert(semanticSchemaV05.properties.schemaVersion.const==='0.5.1' && semanticSchemaV05.properties.semanticModel.$ref==='#/$defs/semanticModel' && semanticSchemaV05.$defs.semanticModel.required.includes('expressions'), 'v0.5 ships a machine-readable JSON Schema for the canonical compositional semantic model');
assert(semanticSchemaV05.$defs.semanticModel.required.includes('unresolvedItems') && semanticSchemaV05.$defs.operatorExpression.properties.operatorType.enum.includes('UNRESOLVED_SCOPE'), 'v0.5 schema requires structured unresolved content and defines an explicit unresolved-scope operator');

console.log('\nAll smoke tests passed.');
