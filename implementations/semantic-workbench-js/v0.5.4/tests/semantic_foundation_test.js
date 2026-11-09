'use strict';
const assert = require('node:assert/strict');
const core = require('../semantic-core.js');
const passed = [];
function check(condition, label) { assert.ok(condition, label); passed.push(label); }
function ev(source, quote = source, start = source.indexOf(quote)) { return { sourceText:source, quote, start:Math.max(0,start), end:Math.max(0,start)+quote.length, verified:source.slice(Math.max(0,start),Math.max(0,start)+quote.length)===quote }; }
function claim(source, opts = {}) {
  const subject=opts.subject||{text:'customer',surfaceText:'The customer',entityId:'e_customer',type:'agent_or_topic'};
  const object=Object.prototype.hasOwnProperty.call(opts,'object')?opts.object:{text:'tool',surfaceText:'the tool',entityId:'e_tool',type:'artifact_or_resource'};
  return {id:opts.id||'c1',subject,predicate:opts.predicate||'NEEDS',object,polarity:opts.polarity||'positive',tense:opts.tense||'present',modality:opts.modality||'asserted',modalScope:opts.modalScope||{operator:'ASSERTED',force:'assertion',scope:'proposition'},time:opts.time||{grammaticalTense:opts.tense||'present',aspect:'simple',referenceTime:'present',sourceTense:opts.tense||'present',temporalAdverbials:[]},quantifierScope:opts.quantifierScope||null,conditions:opts.conditions||[],eventAttributes:opts.eventAttributes||[],completeness:opts.completeness||{status:'complete',missingRoles:[],note:''},evidence:opts.evidence||ev(source),provenance:'test_fixture',sourceKind:'interpreted_text',ruleId:null,confidence:0.8};
}
function build(source, claims, extra={}) { return core.buildSemanticModel({sourceText:source,claims,entities:extra.entities||[],mentions:extra.mentions||[],explanations:extra.explanations||[],claimRelations:extra.claimRelations||[],unresolved:extra.unresolved||[]}); }
function find(model, predicate) { return model.expressions.find(predicate); }

const simpleSource='The customer needs the tool.';
let result=build(simpleSource,[claim(simpleSource)]);
check(result.validation.valid && result.model.profile==='USG-SR/0.5.1','basic proposition builds a valid canonical semantic model');
check(result.model.rootExpressionIds.length===1 && find(result.model,e=>e.type==='PREDICATION'&&e.predicate==='NEEDS'),'a basic claim is represented as an explicit PREDICATION root');
check(result.model.acceptanceBoundary.requiresHumanReview===true && result.model.acceptanceBoundary.objectiveTruthEstablished===false,'semantic model preserves human-review and non-truth-establishment boundary');

const negativeSource='The customer does not like the tool.';
result=build(negativeSource,[claim(negativeSource,{predicate:'LIKE',polarity:'negative'})]);
const negativeAtom=find(result.model,e=>e.type==='PREDICATION');
const negativeNode=find(result.model,e=>e.type==='OPERATOR'&&e.operatorType==='NEGATION');
check(negativeAtom.predicate==='LIKE' && negativeNode.operator==='NOT' && negativeNode.scope.targetId===negativeAtom.id,'negation is a scoped NOT operator; predicate identity remains LIKE');

const modalSource='The customer might not need the tool.';
result=build(modalSource,[claim(modalSource,{polarity:'negative',modality:'possible',modalScope:{operator:'MIGHT',force:'epistemic_possibility',scope:'proposition'}})]);
const modalNode=find(result.model,e=>e.type==='OPERATOR'&&e.operatorType==='MODAL');
const nestedNot=find(result.model,e=>e.type==='OPERATOR'&&e.operatorType==='NEGATION');
check(modalNode.operator==='MIGHT' && modalNode.scope.targetId===nestedNot.id && nestedNot.scope.targetId===find(result.model,e=>e.type==='PREDICATION').id,'modal and negative operators retain explicit nested scope: MIGHT(NOT(P))');

const notEverySource='Not every customer needs the tool.';
result=build(notEverySource,[claim(notEverySource,{subject:{text:'customer',surfaceText:'not every customer',entityId:'e_customer_class',type:'class'},quantifierScope:{operator:'NOT',quantifier:'FORALL',variable:'x',restrictor:{predicate:'INSTANCE_OF',entity:{text:'customer',type:'class'}},scope:'claim',surfaceText:'not every customer'}})]);
const notEveryRoot=result.model.expressions.find(e=>e.id===result.model.rootExpressionIds[0]);
check(notEveryRoot.type==='OPERATOR'&&notEveryRoot.operatorType==='NEGATION'&&result.model.expressions.some(e=>e.type==='OPERATOR'&&e.operatorType==='QUANTIFIER'&&e.operator==='FORALL'),'not every is represented as NOT(FORALL(...P...))');
const notEveryQuantifier=result.model.expressions.find(e=>e.type==='OPERATOR'&&e.operatorType==='QUANTIFIER');
const notEveryAtom=find(result.model,e=>e.type==='PREDICATION');
check(notEveryQuantifier.variableBinding?.variable==='x'&&notEveryAtom.arguments.find(a=>a.role==='subject').variableId==='x','quantifier variable is explicitly bound to the predicate argument and restrictor entity');
const noSource='No customer needs the tool.';
result=build(noSource,[claim(noSource,{subject:{text:'customer',surfaceText:'no customer',entityId:'e_customer_class',type:'class'},quantifierScope:{operator:'NO',quantifier:'FORALL',variable:'x',restrictor:{predicate:'INSTANCE_OF',entity:{text:'customer',type:'class'}},scope:'claim',surfaceText:'no customer'}})]);
check(result.model.expressions.some(e=>e.type==='OPERATOR'&&e.operatorType==='QUANTIFIER'&&e.operator==='FORALL'&&result.model.expressions.find(n=>n.id===e.scope.targetId)?.operatorType==='NEGATION'),'no customer is represented as FORALL(... NOT(P) ...)');
const noQuantifier=result.model.expressions.find(e=>e.type==='OPERATOR'&&e.operatorType==='QUANTIFIER');
check(noQuantifier.variableBinding?.restrictorEntityId&&find(result.model,e=>e.type==='PREDICATION').arguments.find(a=>a.role==='subject').bindingEntityId===noQuantifier.variableBinding.restrictorEntityId,'NO quantifier binds its variable to the restricted class in the scoped proposition');

const conditionalSource='If prices increase, the customer will stop using the tool.';
const cond= {id:'cond1',marker:'if',scope:'claim',effect:'condition_for_assertion',proposition:{subject:{text:'prices',surfaceText:'prices',entityId:'e_prices',type:'unknown'},predicate:'INCREASE',object:null,polarity:'positive',tense:'present',modality:'asserted',time:{grammaticalTense:'present',aspect:'simple',referenceTime:'future',sourceTense:'present',temporalAdverbials:[]}},logicalStatus:'conditional_not_asserted',evidenceText:'prices increase',evidence:ev(conditionalSource,'prices increase')};
result=build(conditionalSource,[claim(conditionalSource,{predicate:'STOP_USING',tense:'future',conditions:[cond]})]);
const conditional=find(result.model,e=>e.type==='CONNECTIVE'&&e.connective==='CONDITIONAL');
check(!!conditional&&conditional.logicalStatus==='conditional_not_asserted','conditional is an explicit connective and its antecedent is not asserted as an observation');
check(!result.model.rootExpressionIds.includes(conditional.antecedentId),'conditional antecedent is nested, not independently promoted to a top-level asserted root');
check(result.validation.valid,'nested conditional graph passes reference validation');

const causeSource='The customer stopped using the tool because it failed.';
const causeClaims=[claim(causeSource,{id:'effect',predicate:'STOP_USING',tense:'past',evidence:ev(causeSource,'The customer stopped using the tool')}),claim(causeSource,{id:'cause',subject:{text:'tool',surfaceText:'it',entityId:'e_tool',type:'artifact_or_resource'},predicate:'FAILS',object:null,tense:'past',evidence:ev(causeSource,'it failed')})];
result=build(causeSource,causeClaims,{explanations:[{id:'causeLink',type:'CAUSE',causeClaimId:'cause',effectClaimId:'effect',attribution:'source_asserted',evidence:ev(causeSource,'because it failed'),note:'The source presents the cause.'}]});
const causeRelation=result.model.relations.find(r=>r.type==='CAUSE');
check(causeRelation?.attribution.kind==='source_asserted'&&causeRelation.verification==='not_independently_verified','causal link preserves source attribution and does not claim objective verification');

const temporalSource='The customer needed the tool but no longer needs it.';
result=build(temporalSource,[claim(temporalSource,{id:'past',tense:'past',polarity:'positive',evidence:ev(temporalSource,'needed the tool')}),claim(temporalSource,{id:'present',tense:'present',polarity:'negative',evidence:ev(temporalSource,'no longer needs it')})]);
check(result.model.expressions.filter(e=>e.type==='PREDICATION').map(e=>e.grammaticalTense).includes('past')&&result.model.expressions.filter(e=>e.type==='PREDICATION').map(e=>e.grammaticalTense).includes('present'),'separate propositions retain their own grammatical tense');

const discourseSource='The customer bought a tool. He uses it every day.';
result=build(discourseSource,[claim(discourseSource,{id:'buy',predicate:'BOUGHT',tense:'past',eventAttributes:[],evidence:ev(discourseSource,'The customer bought a tool')}),claim(discourseSource,{id:'use',subject:{text:'customer',surfaceText:'He',entityId:'e_customer',type:'agent_or_topic'},predicate:'USES',object:{text:'tool',surfaceText:'it',entityId:'e_tool',type:'artifact_or_resource'},eventAttributes:[{type:'frequency',value:'every day',normalizedValue:'P1D',scope:'event'}],evidence:ev(discourseSource,'He uses it every day')})],{mentions:[{entityId:'e_customer',surfaceText:'He',canonicalText:'customer',mentionType:'pronoun',antecedentId:'e_customer'},{entityId:'e_tool',surfaceText:'it',canonicalText:'tool',mentionType:'pronoun',antecedentId:'e_tool'}]});
check(result.model.mentions.some(m=>m.surfaceText==='He'&&m.entityId==='e_customer'&&m.antecedentEntityId==='e_customer')&&result.model.mentions.some(m=>m.surfaceText==='it'&&m.entityId==='e_tool'),'coreference mentions preserve surface form and resolved entity/antecedent identity');
const useAtom=find(result.model,e=>e.type==='PREDICATION'&&e.predicate==='USES');
check(useAtom.eventFrame.attributes.some(a=>a.type==='frequency'&&a.normalizedValue==='P1D'),'frequency is attached to the event proposition, not appended to the object entity');

const badSource='A thermometer measures temperature.';
result=build(badSource,[claim(badSource,{evidence:{sourceText:badSource,quote:'temperature is measured',start:0,end:25,verified:true}})]);
check(result.validation.warnings.some(w=>w.includes('not an exact source substring')),'evidence mismatch is reported as alignment warning, not semantic proof');

const invalid=JSON.parse(JSON.stringify(result.model));
invalid.rootExpressionIds=['missing-expression'];
check(core.validateSemanticModel(invalid).valid===false,'validator rejects dangling root references');
const cyclic=JSON.parse(JSON.stringify(result.model));
const atom=cyclic.expressions.find(e=>e.type==='PREDICATION');
cyclic.expressions.push({id:'op_cycle',type:'OPERATOR',operatorType:'NEGATION',operator:'NOT',scope:{targetId:'op_cycle',scopeKind:'whole_expression'},evidenceRefs:[]});
cyclic.rootExpressionIds=['op_cycle'];
check(core.validateSemanticModel(cyclic).errors.some(e=>e.includes('cycle')),'validator detects expression-scope cycles');


// Additional v0.5 foundation safeguards: unresolved meanings must remain explicit.
const unresolvedPronounSource='It needs the tool.';
result=build(unresolvedPronounSource,[claim(unresolvedPronounSource,{subject:{text:'it',surfaceText:'It'},object:{text:'tool',surfaceText:'the tool'}})]);
const unresolvedPronounAtom=find(result.model,e=>e.type==='PREDICATION');
check(result.validation.valid&&result.validation.status==='partial','unresolved pronoun remains a valid-but-partial semantic graph');
check(!result.model.entities.some(e=>e.canonicalText.toLowerCase()==='it')&&result.model.mentions.some(m=>m.surfaceText==='It'&&m.entityId===null&&m.resolutionStatus==='unresolved'),'unresolved pronoun is preserved as a mention rather than invented as a concept/entity');
check(unresolvedPronounAtom.arguments.find(a=>a.role==='subject').entityId===null,'unresolved pronoun argument retains a null entity link');

const incompleteNeedSource='The customer needs.';
result=build(incompleteNeedSource,[claim(incompleteNeedSource,{object:null})]);
const incompleteNeed=find(result.model,e=>e.type==='PREDICATION');
check(incompleteNeed.completeness.status==='underspecified'&&incompleteNeed.argumentRequirements.missingRoles.includes('object'),'known transitive NEEDS frame is marked underspecified when its object is absent');
check(result.model.unresolvedItems.some(x=>x.reason.includes('object')),'missing required argument is preserved as a structured unresolved item');

const noPredicateSource='The customer.';
result=build(noPredicateSource,[{id:'no-predicate',subject:{text:'customer'},predicate:null,object:null,evidence:ev(noPredicateSource)}]);
check(!result.model.expressions.some(e=>e.type==='PREDICATION')&&result.model.unresolvedItems.some(x=>x.reason.includes('no explicit predicate')),'missing predicate is not replaced with a fabricated RELATED_TO relation');

const unsupportedConditionSource='Although prices increased, the customer stopped using the tool.';
const unsupportedCondition={id:'although1',marker:'although',proposition:{subject:{text:'prices'},predicate:'INCREASE',object:null,polarity:'positive',tense:'past',modality:'asserted'},evidenceText:'prices increased',evidence:ev(unsupportedConditionSource,'prices increased')};
result=build(unsupportedConditionSource,[claim(unsupportedConditionSource,{predicate:'STOP_USING',tense:'past',conditions:[unsupportedCondition]})]);
check(!result.model.expressions.some(e=>e.type==='CONNECTIVE'&&e.connective==='CONDITIONAL')&&result.model.unresolvedItems.some(x=>x.status==='unsupported'&&x.scope==='subordinate_clause'),'unsupported subordinate marker is retained as unresolved instead of being mislabeled CONDITIONAL');

const whenSource='When prices increase, the customer stops using the tool.';
const whenCondition={id:'when1',marker:'when',proposition:{subject:{text:'prices'},predicate:'INCREASE',object:null,polarity:'positive',tense:'present',modality:'asserted'},evidenceText:'prices increase',evidence:ev(whenSource,'prices increase')};
result=build(whenSource,[claim(whenSource,{predicate:'STOP_USING',conditions:[whenCondition]})]);
const whenNode=find(result.model,e=>e.type==='CONNECTIVE'&&e.connective==='WHEN');
check(!!whenNode&&whenNode.logicalStatus==='when_clause_not_asserted','when-clause is represented distinctly from a general IF conditional');
check(find(result.model,e=>e.type==='PREDICATION'&&e.predicate==='INCREASE').attribution.status==='embedded_condition_not_asserted','WHEN antecedent is not promoted to a standalone asserted fact');

const unsupportedQuantifierSource='Most customers need the tool.';
result=build(unsupportedQuantifierSource,[claim(unsupportedQuantifierSource,{subject:{text:'customer',surfaceText:'most customers',entityId:'e_customer_class',type:'class'},quantifierScope:{operator:'MOST',quantifier:'MOST',variable:'x',restrictor:{predicate:'INSTANCE_OF',entity:{text:'customer',type:'class'}},surfaceText:'most customers'}})]);
const unsupportedQuantifierRoot=result.model.expressions.find(e=>e.id===result.model.rootExpressionIds[0]);
check(unsupportedQuantifierRoot.type==='OPERATOR'&&unsupportedQuantifierRoot.operatorType==='UNRESOLVED_SCOPE','unsupported quantifier scope visibly wraps the proposition instead of leaving it as an unconditional assertion');
check(result.validation.status==='partial'&&result.model.unresolvedItems.some(x=>x.scope==='quantifier'),'unsupported quantifier is machine-readable and blocks completion status');

const expectedModalSource='The customer is expected to need the tool.';
result=build(expectedModalSource,[claim(expectedModalSource,{modality:'expected',modalScope:{operator:'EXPECTED',force:'epistemic_expectation',scope:'proposition',surfaceText:'is expected'}})]);
check(find(result.model,e=>e.type==='OPERATOR'&&e.operatorType==='MODAL')?.operator==='EXPECTED','epistemic expectation is represented by EXPECTED rather than being collapsed into deontic MUST');

const duplicateMentionSource='The customer saw the tool. The customer used the tool.';
result=build(duplicateMentionSource,[claim(duplicateMentionSource,{id:'seen',predicate:'SAW'}),claim(duplicateMentionSource,{id:'used',predicate:'USED'})]);
check(result.model.mentions.filter(m=>m.surfaceText==='The customer').length===2,'repeated noun mentions are preserved as separate occurrences');

const reusedEntityIdSource='The customer needs the tool.';
result=build(reusedEntityIdSource,[claim(reusedEntityIdSource,{subject:{text:'customer',entityId:'reused'},object:{text:'tool',entityId:'reused'}})]);
check(new Set(result.model.entities.map(e=>e.id)).size===2&&result.validation.warnings.some(w=>w.includes('reused for a different canonical label')),'a reused source entity ID cannot silently merge different canonical concepts');

// Scope/validation edge cases and disjunction handling.
const orSource='The customer needs the tool or wants a refund.';
result=build(orSource,[claim(orSource,{id:'needs',predicate:'NEEDS',evidence:ev(orSource,'The customer needs the tool')}),claim(orSource,{id:'refund',predicate:'WANTS',object:{text:'refund',surfaceText:'a refund',entityId:'e_refund'},evidence:ev(orSource,'wants a refund')})]);
const orNode=find(result.model,e=>e.type==='CONNECTIVE'&&e.connective==='OR');
check(!!orNode&&orNode.disjunctionSemantics==='inclusive_or_unspecified'&&orNode.operandIds.length===2,'OR coordination is represented without silently assuming exclusive disjunction');
check(result.validation.valid,'two-claim OR graph passes canonical reference validation');

const partialValidation=JSON.parse(JSON.stringify(result.model));
partialValidation.unresolvedItems.push({id:'unres_test',surfaceText:'some phrase',reason:'Not yet represented',status:'unsupported',evidenceRef:null,scope:'clause'});
check(core.validateSemanticModel(partialValidation).valid===true&&core.validateSemanticModel(partialValidation).status==='partial','standalone validator distinguishes structurally valid but semantically partial graphs');

const badMention=JSON.parse(JSON.stringify(result.model));
badMention.mentions.push({id:'mention_bad_span',entityId:null,surfaceText:'customer',mentionType:'noun_phrase',resolutionStatus:'unresolved',antecedentEntityId:null,sourceSpan:{start:0,end:8}});
check(core.validateSemanticModel(badMention).errors.some(e=>e.includes('source span does not match')),'validator rejects mention offsets that do not match source text');

const duplicateRoots=JSON.parse(JSON.stringify(result.model));
duplicateRoots.rootExpressionIds=[duplicateRoots.rootExpressionIds[0],duplicateRoots.rootExpressionIds[0]];
check(core.validateSemanticModel(duplicateRoots).errors.some(e=>e.includes('duplicate identifiers')),'validator rejects duplicate root expression identifiers');

const notDislikeSource='The customer does not dislike the tool.';
result=build(notDislikeSource,[claim(notDislikeSource,{predicate:'DISLIKE',polarity:'negative',evidence:ev(notDislikeSource)})]);
check(find(result.model,e=>e.type==='PREDICATION')?.predicate==='DISLIKE'&&find(result.model,e=>e.type==='OPERATOR'&&e.operatorType==='NEGATION')?.scope.targetId===find(result.model,e=>e.type==='PREDICATION').id,'does not dislike is preserved as NOT(DISLIKE), not silently translated to LIKE');


const noClaimsSource='It is unclear whether the customer needs the tool.';
result=build(noClaimsSource,[],{unresolved:['The sentence could not be interpreted safely.']});
check(result.model.unresolvedItems.some(item=>item.reason.includes('could not be interpreted safely'))&&result.validation.status==='partial','legacy unresolved messages are promoted into structured canonical unresolved items');




const defensiveSource='The customer uses the tool every day.';
result=build(defensiveSource,[claim(defensiveSource,{predicate:'USES',completeness:{status:'complete',missingRoles:'invalid-shape',note:''},eventAttributes:[null,{type:'frequency',value:'every day',surfaceText:'every day',normalizedValue:'P1D'}]})]);
check(result.validation.valid&&find(result.model,e=>e.type==='PREDICATION').eventFrame.attributes.some(a=>a.type==='frequency'),'semantic core preserves source-grounded event attributes while normalizing malformed optional completeness');
const placeholderAttr=build(defensiveSource,[claim(defensiveSource,{predicate:'USES',eventAttributes:[{type:'frequency',value:'...',surfaceText:'exact source phrase'}]})]);
check(!find(placeholderAttr.model,e=>e.type==='PREDICATION').eventFrame.attributes.length,'semantic core discards placeholder or source-unaligned event attributes');
const emptyQuantifier=build(simpleSource,[claim(simpleSource,{quantifierScope:{operator:'UNKNOWN',quantifier:'UNKNOWN',variable:'x',restrictor:null,logicalForm:'',surfaceText:null},eventAttributes:[{type:'frequency',value:'...',surfaceText:'exact source phrase'}]})]);
check(!emptyQuantifier.model.expressions.some(e=>e.type==='OPERATOR'&&e.operatorType==='UNRESOLVED_SCOPE')&&emptyQuantifier.validation.status!=='partial','empty quantifier metadata does not manufacture unresolved scope');


const disconnectedCycle=JSON.parse(JSON.stringify(result.model));
const disconnectedAtom=disconnectedCycle.expressions.find(e=>e.type==='PREDICATION');
const disconnectedId='op_disconnected_cycle';
disconnectedCycle.expressions.push({id:disconnectedId,type:'OPERATOR',operatorType:'NEGATION',operator:'NOT',scope:{targetId:disconnectedId,scopeKind:'whole_expression'},evidenceRefs:[]});
check(core.validateSemanticModel(disconnectedCycle).errors.some(e=>e.includes('not reachable from any declared root'))&&core.validateSemanticModel(disconnectedCycle).errors.some(e=>e.includes('cycle')),'validator detects orphaned expressions and cycles even when they are disconnected from declared roots');
console.log(`\nSemantic foundation tests: ${passed.length} passed, 0 failed.`);
