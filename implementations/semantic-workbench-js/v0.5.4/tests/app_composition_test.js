'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const appPath = path.join(__dirname, '..', 'app.js');
const source = fs.readFileSync(appPath, 'utf8');
const eventSection = source.indexOf('// ---------------------- Event wiring / initialization ----------------------');
if (eventSection < 0) throw new Error('Could not locate the end of app logic.');
const semanticCore = require('../semantic-core.js');
const semanticComposer = require('../semantic-composer.js');
const store = new Map();
const sandbox = {
  console, Date, Math, JSON, Map, Set, URL, URLSearchParams,
  localStorage: { getItem:k=>store.has(k)?store.get(k):null, setItem:(k,v)=>store.set(k,v) },
  document: { querySelector:()=>null, querySelectorAll:()=>[] },
  window: { scrollTo:()=>{} }, setTimeout, clearTimeout, confirm:()=>true,
  USGSemanticCore:semanticCore,
  USGSemanticComposer:semanticComposer
};
vm.createContext(sandbox);
vm.runInContext(source.slice(0,eventSection) + `\nglobalThis.__test = { safeModelInterpretation, localInterpret, modelHttpError, modelTransportError, generationFailureAudit };`, sandbox, {filename:'app.js'});
const { safeModelInterpretation, modelHttpError, modelTransportError, generationFailureAudit } = sandbox.__test;
let passed=0;
function check(value,message){if(!value)throw new Error(`FAIL: ${message}`);passed++;console.log(`PASS: ${message}`);}
const failureHttpPayload={
  error:'prediction aborted, token repeat limit reached',
  failureCategory:'repetition_abort',
  diagnostic:{category:'repetition_abort',httpStatus:500,responseBody:'prediction aborted, token repeat limit reached',responseReceived:true},
  correctionAudit:{status:'generation_request_failed',failure:{category:'repetition_abort',message:'prediction aborted, token repeat limit reached'},generationArtifacts:[{phase:'generation',status:'request_failed',failureCategory:'repetition_abort',diagnostic:{httpStatus:500,responseBody:'prediction aborted, token repeat limit reached'}}]}
};
const preservedHttpError=modelHttpError(failureHttpPayload,502,JSON.stringify(failureHttpPayload));
check(preservedHttpError.failureCategory==='repetition_abort' && preservedHttpError.correctionAudit.generationArtifacts[0].diagnostic.responseBody.includes('repeat limit reached'),'browser adapter preserves the server repetition-abort audit and Ollama error body');
const transportError=modelTransportError(Object.assign(new Error('fetch failed'),{cause:{code:'ECONNREFUSED'}}));
const transportAudit=generationFailureAudit(transportError);
check(transportError.failureCategory==='connection_or_transport_error' && transportAudit.generationArtifacts[0].diagnostic.responseReceived===false,'browser adapter creates a typed transport audit when the Workbench bridge cannot be reached');

const inputs=[
'The customer does not dislike the tool.',
'The customer might not need the tool.',
'The customer needs the tool, but does not need it.',
'If prices increase, the customer will stop using the tool.',
'Unless prices increase, the customer does not need the tool.',
'When prices increase, the customer stops using the tool.',
'Although prices increased, the customer stopped using the tool.',
'The customer stopped using the tool because it failed.',
'The customer bought a tool. He uses it every day.',
'The customer needs the tool or wants a refund.',
'Not every customer needs the tool.',
'No customer needs the tool.',
'The customer is expected to need the tool.',
'Prices were different.'
];
for (const sentence of inputs) {
  // Deliberately bad model output tests that the source-grounded composer is
  // selected for covered inputs, while the original proposal remains auditable.
  const record=safeModelInterpretation({
    intent:'ASSERTION',
    interpretation:'deliberately noisy model proposal',
    claims:[{
      subject:'customer', predicate:'NEEDS', object:null, polarity:'negative', tense:'past', modality:'asserted',
      quantifierScope:{operator:null,quantifier:null,variable:null,restrictor:{},surfaceText:null,logicalForm:null},
      eventAttributes:[{type:'frequency_duration_manner____',value:'...',normalizedValue:'...',surfaceText:'...',scope:'claim'}]
    }]
  },sentence);
  check(record.compositionAudit?.applied===true,`app pipeline uses source composition for: ${sentence}`);
  check(record.semanticModel?.profile==='USG-SR/0.5.1' && record.semanticValidation?.valid===true,`app pipeline returns valid v0.5.1 canonical graph: ${sentence}`);
  check(record.modelProposalSummary?.claimCount===1,`original LLM proposal is retained for audit: ${sentence}`);
  check(!record.semanticModel.expressions.some(e=>e.operatorType==='UNRESOLVED_SCOPE'),`empty model quantifier metadata cannot contaminate: ${sentence}`);
  if (sentence === 'The customer needs the tool, but does not need it.') {
    const compatibilityContradictions=(record.claimRelations||[]).filter(r=>r.type==='CONTRADICTS');
    const graphContradictions=(record.semanticModel.relations||[]).filter(r=>r.type==='CONTRADICTS');
    check(compatibilityContradictions.length===1 && graphContradictions.length===1,'the case-3 CONTRADICTS candidate is present in both compatibility and canonical graph relations');
  }
}

const unhandled=safeModelInterpretation({
  intent:'ASSERTION',
  claims:[{subject:'The customer',predicate:'WAITING',object:null,polarity:'positive',tense:'present',modality:'asserted',
    quantifierScope:{operator:null,quantifier:null,variable:null,restrictor:{},surfaceText:'...',logicalForm:'...'},
    eventAttributes:[{type:'frequency_duration_manner____',value:'...',normalizedValue:'...',surfaceText:'...',scope:'claim'}]}]
},'The customer is waiting patiently.');
check(unhandled.compositionAudit?.applied!==true,'unsupported clause is not replaced by a speculative source parse');
check(unhandled.claims[0].quantifierScope===null && !unhandled.semanticModel.expressions.some(e=>e.operatorType==='UNRESOLVED_SCOPE'),'empty quantifier placeholders are removed in the ordinary model-adapter path');
check(unhandled.claims[0].eventAttributes.length===0,'placeholder event attributes are removed in the ordinary model-adapter path');
check(unhandled.modelProposalSummary===undefined,'uncomposable model proposal remains the regular candidate instead of being hidden');

const longSource='The customer is waiting patiently.';
const manyConditions=Array.from({length:7},(_,i)=>({marker:'if',proposition:{subject:{text:`condition ${i+1}`,type:'unknown'},predicate:'OCCURS',object:null,polarity:'positive',tense:'present',modality:'asserted'},scope:'claim',effect:'condition_for_assertion',consequence:'unspecified',evidence_text:'patiently'}));
const manyAttributes=Array.from({length:14},(_,i)=>({type:'manner',value:`patiently ${i+1}`,normalizedValue:null,surfaceText:'patiently',scope:'event'}));
const manyClaims=Array.from({length:15},(_,i)=>({subject:{text:'customer',type:'person'},predicate:`WAITING_${i+1}`,object:null,polarity:'positive',tense:'present',modality:'asserted',evidence_text:longSource,confidence:0.7,notes:'',conditions:i===0?manyConditions:[],eventAttributes:i===0?manyAttributes:[]}));
const highComplexity=safeModelInterpretation({intent:'ASSERTION',interpretation:'A high-item-count proposal used to test preservation.',claims:manyClaims,entities:[],mentions:[],claimRelations:[],unresolved:Array.from({length:12},(_,i)=>`Unresolved detail ${i+1}.`)},longSource);
check(highComplexity.claims.length===15,'model adapter preserves all 15 returned claims rather than silently truncating at 12');
check(highComplexity.unresolved.filter(x=>/^Unresolved detail/.test(x)).length===12,'model adapter preserves all unresolved items rather than truncating at 8');
check(highComplexity.claims[0].conditions.length===7,'model adapter preserves more than five source condition candidates');
check(highComplexity.claims[0].eventAttributes.length===14,'model adapter preserves more than twelve event attributes');
const nestedRawProposal={intent:'ASSERTION',interpretation:'Nested test',claims:[{subject:{text:'customer',type:'person'},predicate:'NEEDS',object:{text:'tool',type:'artifact'},polarity:'positive',tense:'present',modality:'asserted',evidence_text:longSource,conditions:[{marker:'if',proposition:{subject:{text:'prices',type:'unknown'},predicate:'INCREASE',object:null,polarity:'positive',tense:'present',modality:'asserted',conditions:[{marker:'when',proposition:{subject:{text:'demand',type:'unknown'},predicate:'FALL',object:null,polarity:'positive',tense:'present',modality:'asserted'}}]}}]}],entities:[],mentions:[],claimRelations:[],unresolved:[]};
const nestedRetained=safeModelInterpretation(nestedRawProposal,longSource);
check(nestedRetained.modelProposalRaw.claims[0].conditions[0].proposition.conditions[0].marker==='when','full nested semantic structure is retained in the raw proposal rather than rejected or silently flattened');

const adapterConditionSource='The customer waits patiently unless prices increase.';
const adapterCondition=safeModelInterpretation({
  intent:'ASSERTION',interpretation:'The customer waits unless prices increase.',
  claims:[{subject:{text:'customer',type:'person'},predicate:'WAIT',object:null,polarity:'positive',tense:'present',modality:'asserted',
    evidence_text:adapterConditionSource,
    conditions:[{marker:'unless',effect:'condition_for_assertion',logicalStatus:'conditional_not_asserted',consequence:'unspecified',consequentClaimId:'model_supplied_dangling_claim',
      evidence_text:'prices increase',
      proposition:{subject:{text:'prices',type:'unknown'},predicate:'INCREASE',object:null,polarity:'positive',tense:'present',modality:'asserted'}}]}],
  entities:[],mentions:[],claimRelations:[],unresolved:[]
},adapterConditionSource);
check(adapterCondition.compositionAudit?.applied!==true,'unsupported WAIT pattern remains on the model-adapter path for condition-normalization coverage');
check(adapterCondition.claims[0].conditions[0].effect==='exception_to_assertion' && adapterCondition.claims[0].conditions[0].logicalStatus==='exception_relation_asserted','model-adapter normalization corrects model-proposed UNLESS effect and status from the source marker');
check(adapterCondition.claims[0].conditions[0].consequence==='WAIT(customer)' && adapterCondition.claims[0].conditions[0].consequentClaimId===adapterCondition.claims[0].id,'model-adapter derives the UNLESS consequence from the parent claim and replaces a dangling model consequent ID');
check(adapterCondition.semanticModel.expressions.some(e=>e.type==='CONNECTIVE' && e.connective==='EXCEPTION'),'model-adapter condition metadata produces a canonical EXCEPTION connective');

console.log(`\nApp composition integration tests: ${passed} passed, 0 failed.`);
