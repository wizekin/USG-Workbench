/*
 * USG Source-grounded Semantic Composer v0.2
 * A small compositional grammar: clauses are parsed independently, then
 * linked by connective/operator structure. It is deliberately conservative.
 * Dependency-free; browser global + CommonJS export.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.USGSemanticComposer = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const VERSION = '0.2.0';
  // Predicate vocabulary is separate from composition rules: new predicates
  // inherit the same scope/connective behavior without sentence-specific rules.
  const VERBS = [
    { predicate:'STOP_USING', forms:['stopped using','stops using','stop using'], past:['stopped using'], objectRequired:true },
    { predicate:'BOUGHT', forms:['purchased','bought','acquired','buy','buys','purchase','purchases','acquire','acquires'], past:['purchased','bought','acquired'], objectRequired:true },
    { predicate:'NEEDS', forms:['needed','needs','need'], past:['needed'], objectRequired:true },
    { predicate:'DISLIKE', forms:['disliked','dislikes','dislike'], past:['disliked'], objectRequired:true },
    { predicate:'LIKE', forms:['liked','likes','like'], past:['liked'], objectRequired:true },
    { predicate:'INCREASE', forms:['increased','increases','increase','rose','rises','rise'], past:['increased','rose'], objectRequired:false },
    { predicate:'DECREASE', forms:['decreased','decreases','decrease','fell','falls','fall'], past:['decreased','fell'], objectRequired:false },
    { predicate:'REDUCE', forms:['reduced','reduces','reduce'], past:['reduced'], objectRequired:true },
    { predicate:'FAIL', forms:['failed','fails','fail'], past:['failed'], objectRequired:false },
    { predicate:'USES', forms:['used','uses','use'], past:['used'], objectRequired:true },
    { predicate:'WANTS', forms:['wanted','wants','want'], past:['wanted'], objectRequired:true },
    { predicate:'SELLS', forms:['sold','sells','sell'], past:['sold'], objectRequired:true },
    { predicate:'PRODUCES', forms:['produced','produces','produce'], past:['produced'], objectRequired:true },
    { predicate:'RECEIVES', forms:['received','receives','receive'], past:['received'], objectRequired:true },
    { predicate:'BREAKS', forms:['broke','breaks','break'], past:['broke'], objectRequired:true },
    { predicate:'STARTS', forms:['started','starts','start'], past:['started'], objectRequired:true },
    { predicate:'CLOSES', forms:['closed','closes','close'], past:['closed'], objectRequired:true },
    { predicate:'MEASURES', forms:['measured','measures','measure'], past:['measured'], objectRequired:true }
  ].map(v => ({...v, forms:[...new Set(v.forms)].sort((a,b)=>b.length-a.length)}));
  const MODALS = {
    might:['MIGHT','possible','epistemic_possibility'],
    may:['MAY','possible','epistemic_possibility'],
    could:['COULD','possible_or_ability','ambiguous_possibility_or_ability'],
    can:['CAN','possible_or_ability','ability_or_permission'],
    must:['MUST','necessary','necessity_or_obligation_ambiguous'],
    should:['SHOULD','obligatory','deontic'],
    will:['WILL','asserted','temporal_future'],
    would:['WOULD','possible','conditional_or_hypothetical']
  };
  const PRONOUNS = new Set(['he','she','they','him','her','them','it','this','that','these','those']);

  function clean(s) { return String(s || '').trim().replace(/\s+/g,' ').replace(/[.!?]+$/,'').trim(); }
  function norm(s) { return clean(s).toLowerCase().replace(/^(?:the|a|an)\s+/,''); }
  function escape(s) { return String(s).replace(/[.*+?^${}()|[\]\\]/g,'\\$&'); }
  function entityId(s) { return `e_${norm(s).replace(/[^a-z0-9]+/g,'_').replace(/^_|_$/g,'') || 'entity'}`; }
  function evidence(source, phrase, from=0) {
    const p=String(phrase||''); const start=source.indexOf(p,Math.max(0,from));
    return start<0 ? null : {sourceText:source,quote:p,start,end:start+p.length,verified:true};
  }
  function sourceFrame(phrase) {
    const original=clean(phrase);
    if(!original) return null;

    // A clausal expectation operator takes scope over an infinitival predication.
    let m=original.match(/^(.+?)\s+(is|are|was|were)\s+expected\s+to\s+(.+)$/i);
    if(m) {
      const subject=clean(m[1]);
      const inner=parseClause(`${subject} ${m[3]}`);
      if(!inner) return null;
      const tense=/^(was|were)$/i.test(m[2])?'past':'present';
      inner.tense='unknown';
      inner.time={grammaticalTense:'unknown',aspect:'simple',referenceTime:'unspecified',sourceTense:tense,clauseEvidence:original,temporalAdverbials:[]};
      inner.modality='expected';
      inner.modalScope={operator:'EXPECTED',force:'epistemic_expectation',scope:'proposition',surfaceText:`${m[2]} expected`};
      inner.sourceClauseText=original;
      return inner;
    }

    m=original.match(/^(.+?)\s+(was|were|is|are)\s+different$/i);
    if(m) return {
      subject:entity(m[1]), predicate:'DIFFER', object:null, polarity:'positive',
      tense:/^(was|were)$/i.test(m[2])?'past':'present', modality:'asserted',
      modalScope:{operator:'ASSERTED',force:'assertion',scope:'proposition',surfaceText:null},
      time:{grammaticalTense:/^(was|were)$/i.test(m[2])?'past':'present',aspect:'simple',referenceTime:/^(was|were)$/i.test(m[2])?'past':'present',sourceTense:/^(was|were)$/i.test(m[2])?'past':'present',clauseEvidence:original,temporalAdverbials:[]},
      eventAttributes:[], conditions:[], sourceClauseText:original, ruleId:'SRC-COPULAR-DIFFERENT'
    };

    const forms=VERBS.flatMap(v=>v.forms.map(f=>({form:f,verb:v}))).sort((a,b)=>b.form.length-a.form.length);
    const formRe=forms.map(x=>escape(x.form)).join('|');
    const re=new RegExp(`^(.+?)\\s+(?:(might|may|could|can|must|should|will|would)\\s+)?(?:(does\\s+not|do\\s+not|did\\s+not|doesn't|don't|didn't|not)\\s+)?(${formRe})(?:\\s+(.+))?$`,'i');
    m=original.match(re);
    if(!m) return null;
    const subjectSurface=clean(m[1]);
    const modalWord=(m[2]||'').toLowerCase();
    const negator=(m[3]||'').toLowerCase();
    const verbForm=(m[4]||'').toLowerCase();
    const spec=forms.find(x=>x.form===verbForm)?.verb;
    if(!spec) return null;
    let tail=clean(m[5]||'');
    let frequency=null;
    const freqMatch=tail.match(/\b(every\s+day|daily|every\s+week|weekly|every\s+month|monthly|every\s+year|yearly|annually)$/i);
    if(freqMatch) {
      const value=freqMatch[1];
      const normalizedValue=/day|daily/i.test(value)?'P1D':(/week|weekly/i.test(value)?'P1W':(/month|monthly/i.test(value)?'P1M':'P1Y'));
      frequency={type:'frequency',value,normalizedValue,surfaceText:value,scope:'event'};
      tail=clean(tail.slice(0,freqMatch.index));
    }
    if(spec.objectRequired && !tail) return null;
    const subjectPronoun=subjectSurface.toLowerCase();
    const objectSurface=tail || null;
    const past=spec.past.includes(verbForm) || /^(did\s+not|didn't)$/i.test(negator);
    const tense=modalWord==='will'?'future':(modalWord && modalWord!=='would' && modalWord!=='could' ? 'unknown' : (past?'past':'present'));
    const modal=modalWord ? MODALS[modalWord] : null;
    const out={
      subject:entity(subjectSurface), predicate:spec.predicate,
      object:objectSurface?entity(objectSurface):null,
      polarity:negator?'negative':'positive', tense,
      modality:modal?modal[1]:'asserted',
      modalScope:modal?{operator:modal[0],force:modal[2],scope:'proposition',surfaceText:modalWord}:{operator:'ASSERTED',force:'assertion',scope:'proposition',surfaceText:null},
      time:{grammaticalTense:tense,aspect:'simple',referenceTime:tense==='unknown'?'unspecified':tense,sourceTense:tense,clauseEvidence:original,temporalAdverbials:frequency?[frequency.value]:[]},
      eventAttributes:frequency && ['USES','STOP_USING'].includes(spec.predicate)?[frequency]:[], conditions:[],
      sourceClauseText:original, ruleId:'SRC-CLAUSE-VERB-FRAME'
    };
    if(PRONOUNS.has(subjectPronoun)) out.subject={...out.subject,text:subjectPronoun,surfaceText:subjectSurface,reference:'unresolved_pronoun'};
    return out;
  }
  function entity(surface) {
    const s=clean(surface);
    return {text:norm(s),canonicalText:norm(s),surfaceText:s,type:'unknown',reference:/^the\s+/i.test(s)?'definite':(/^(?:a|an)\s+/i.test(s)?'indefinite':'unmarked'),entityId:entityId(s)};
  }
  function resolveFrame(frame, context) {
    if(!frame) return null;
    if(frame.subject && PRONOUNS.has(frame.subject.text.toLowerCase())) {
      const pronoun=frame.subject.surfaceText || frame.subject.text;
      const ref=/^(it|them|this|that|these|those)$/i.test(pronoun) ? context.object : context.subject;
      if(!ref) return null;
      frame.subject={...ref,surfaceText:pronoun,reference:'resolved_pronoun',entityId:ref.entityId||entityId(ref.text)};
    }
    if(frame.object && PRONOUNS.has(frame.object.text.toLowerCase())) {
      const pronoun=frame.object.surfaceText || frame.object.text;
      if(!context.object) return null;
      frame.object={...context.object,surfaceText:pronoun,reference:'resolved_pronoun',entityId:context.object.entityId||entityId(context.object.text)};
    }
    return frame;
  }
  function parseClause(text, context={}) {
    const originalPhrase=clean(text);
    let phrase=originalPhrase;
    if(!phrase) return null;
    let quantifier=null;
    const q=phrase.match(/^(not\s+every|no)\s+(.+)$/i);
    if(q) {
      const category=q[2].match(/^(.+?)\s+(?=(?:does\s+not|do\s+not|did\s+not|needs?|needed|dislikes?|disliked|likes?|liked|uses?|used|wants?|wanted|measures?|is|are|has|have)\b)/i);
      if(category) {
        const label=category[1];
        phrase=`${label} ${q[2].slice(category[0].length)}`;
        quantifier={
          operator:q[1].toLowerCase()==='no'?'NO':'NOT', quantifier:'FORALL', variable:'x',
          restrictor:{predicate:'INSTANCE_OF',entity:{text:norm(label),type:'class',reference:'unmarked'}},
          scope:'claim',surfaceText:`${q[1]} ${label}`, 
          logicalForm:q[1].toLowerCase()==='no'?'FORALL x: category(x) -> NOT(proposition(x))':'NOT(FORALL x: category(x) -> proposition(x))',
          interpretation:q[1].toLowerCase()==='no'?'The predicate is negated for every member of the stated class.':'The universal statement is negated; this does not mean that no member satisfies the predicate.'
        };
      }
    }

    const startsWithPredicateOrAuxiliary=/^(?:(?:might|may|could|can|must|should|will|would)\s+)?(?:(?:does|do|did)\s+not|doesn't|don't|didn't|not)\s+/i.test(phrase)
      || VERBS.some(v=>v.forms.some(form=>new RegExp(`^${escape(form)}\\b`,'i').test(phrase)));
    let frame=null;
    if(context.subject && startsWithPredicateOrAuxiliary) frame=sourceFrame(`${context.subject.surfaceText||context.subject.text} ${phrase}`);
    if(!frame) frame=sourceFrame(phrase);
    if(!frame && context.subject) frame=sourceFrame(`${context.subject.surfaceText||context.subject.text} ${phrase}`);
    if(!frame) return null;
    frame=resolveFrame(frame,context);
    if(!frame) return null;
    if(quantifier) {
      frame.sourceClauseText=originalPhrase;
      frame.time.clauseEvidence=originalPhrase;
      frame.quantifierScope=quantifier;
      frame.subject={...entity(quantifier.restrictor.entity.text),type:'class',surfaceText:`${q[1]} ${q[2].match(/^(.+?)\s+(?=(?:does\s+not|do\s+not|did\s+not|needs?|needed|dislikes?|disliked|likes?|liked|uses?|used|wants?|wanted|measures?|is|are|has|have)\b)/i)?.[1] || quantifier.restrictor.entity.text}`,entityId:entityId(quantifier.restrictor.entity.text)};
      frame.polarity='positive';
    } else frame.quantifierScope=null;
    if(frame.predicate==='DIFFER') frame.comparisonFrame={reference:null,comparisonSet:null,status:'context_dependent',requiredFor:['explicit_pairwise_comparison','rank_or_difference_calculation'],note:'The proposition is complete; the comparison reference is not supplied.'};
    return frame;
  }
  function propositionSummary(frame) {
    if (!frame) return 'unspecified proposition';
    const subject = frame.subject?.surfaceText || frame.subject?.text || 'unknown subject';
    const object = frame.object?.surfaceText || frame.object?.text;
    const args = object ? `${subject}, ${object}` : subject;
    return `${frame.polarity === 'negative' ? 'NOT ' : ''}${frame.predicate}(${args})`;
  }
  function asCondition(frame, marker, source, phrase, consequentFrame) {
    const ev=evidence(source,phrase);
    const consequenceSummary = propositionSummary(consequentFrame);
    return {
      id:`src_condition_${marker}_${entityId(phrase)}`, marker,
      scope:'claim', effect:marker==='unless'?'exception_to_assertion':(marker==='when'?'temporal_condition_for_assertion':'condition_for_assertion'),
      proposition:{subject:frame.subject,predicate:frame.predicate,object:frame.object,polarity:frame.polarity,tense:frame.tense,modality:frame.modality,modalScope:frame.modalScope,time:frame.time},
      // The consequent is the parent claim. Naming it here prevents the old
      // ambiguous "unspecified" metadata from obscuring an explicit graph link.
      consequence: consequenceSummary,
      consequenceInterpretation: marker==='unless'
        ? `The parent claim ${consequenceSummary} is the EXCEPTION consequent; do not promote it to an unconditional assertion or infer its opposite when P holds.`
        : `The parent claim ${consequenceSummary} is linked to this ${marker.toUpperCase()} clause; the clause is not an independent asserted fact.`,
      consequentClaimId:claimId(0),
      evidenceText:phrase, evidence:ev,
      logicalStatus:marker==='unless'?'exception_relation_asserted':(marker==='when'?'when_clause_not_asserted':'conditional_not_asserted')
    };
  }
  function claimId(i) { return `src_claim_${i+1}`; }
  function addContext(frame, context) {
    if(frame.subject && !/^((he|she|they|him|her|them|it|this|that|these|those))$/i.test(frame.subject.surfaceText||'')) context.subject=frame.subject;
    if(frame.object && !/^((it|them|this|that|these|those))$/i.test(frame.object.surfaceText||'')) context.object=frame.object;
  }
  function applySpan(frame, source, from=0) {
    const phrase=frame.sourceClauseText || '';
    frame.evidence=evidence(source,phrase,from) || evidence(source,phrase,0);
    return frame;
  }
  function composeSourceText(sourceText) {
    const source=String(sourceText||'').trim();
    if(!source) return null;
    const context={subject:null,object:null};
    let frames=[]; let composition=null; let explanations=[]; let unresolved=[];
    const leadingSub=source.match(/^(if|unless|when|although)\s+(.+?),\s*(.+)$/i);
    const trailingSub=leadingSub?null:source.match(/^(.+?)\s+(if|unless|when|although)\s+(.+)$/i);
    const sub=leadingSub||trailingSub;
    if(sub) {
      const leading=!!leadingSub;
      const marker=(leading?sub[1]:sub[2]).toLowerCase();
      const antecedentText=clean(leading?sub[2]:sub[3]);
      const consequentText=clean(leading?sub[3]:sub[1]);
      const consequent=parseClause(consequentText,context);
      if(!consequent) return null;
      addContext(consequent,context);
      const antecedent=parseClause(antecedentText,context);
      if(!antecedent) return null;
      resolveFrame(antecedent,context);
      applySpan(antecedent,source); applySpan(consequent,source);
      if(marker==='although') {
        frames=[antecedent,consequent];
        composition={type:'CONCESSIVE',marker,antecedentClaimId:claimId(0),consequentClaimId:claimId(1),clauseOrder:leading?'subordinate_first':'matrix_first'};
      } else {
        consequent.conditions=[asCondition(antecedent,marker,source,antecedentText,consequent)];
        frames=[consequent];
        composition={type:marker==='if'?'CONDITIONAL':(marker==='unless'?'EXCEPTION':'WHEN'),marker,antecedentClaimId:null,consequentClaimId:claimId(0),antecedentRepresentation:'embedded_condition',clauseOrder:leading?'subordinate_first':'matrix_first'};
      }
    } else {
      const leadingBecause=source.match(/^because\s+(.+?),\s*(.+)$/i);
      const trailingBecause=leadingBecause?null:source.match(/^(.+?)\s+because\s+(.+)$/i);
      const because=leadingBecause||trailingBecause;
      if(because) {
        const causeText=clean(leadingBecause?because[1]:because[2]);
        const effectText=clean(leadingBecause?because[2]:because[1]);
        const effect=parseClause(effectText,context);
        if(!effect) return null;
        addContext(effect,context);
        const cause=parseClause(causeText,context);
        if(!cause) return null;
        resolveFrame(cause,context);
        applySpan(effect,source); applySpan(cause,source);
        frames=leadingBecause?[cause,effect]:[effect,cause];
        const causeIndex=leadingBecause?0:1, effectIndex=leadingBecause?1:0;
        explanations=[{id:'src_cause_1',type:'CAUSE',causeClaimId:claimId(causeIndex),effectClaimId:claimId(effectIndex),attribution:'source_asserted',evidenceText:`because ${causeText}`,evidence:evidence(source,`because ${causeText}`),note:'The source attributes the effect to this cause; the causal relationship is not independently verified.'}];
        composition={type:'CAUSE',marker:'because',causeClaimId:claimId(causeIndex),effectClaimId:claimId(effectIndex)};
      } else {
        const connector=source.match(/^(.+?)(?:,\s*|\s+)(but|or|and)\s+(.+)$/i);
        if(connector) {
          const leftText=clean(connector[1]); const marker=connector[2].toLowerCase(); const rightText=clean(connector[3]);
          const left=parseClause(leftText,context);
          if(!left) return null;
          addContext(left,context);
          const right=parseClause(rightText,context);
          if(!right) return null;
          applySpan(left,source); applySpan(right,source);
          frames=[left,right];
          composition={type:marker==='but'?'CONTRAST':marker.toUpperCase(),marker,leftClaimId:claimId(0),rightClaimId:claimId(1)};
        } else {
          const sentences=source.split(/(?<=[.!?])\s+/).map(clean).filter(Boolean);
          if(sentences.length>1) {
            for(const sentence of sentences) {
              const frame=parseClause(sentence,context);
              if(!frame) return null;
              applySpan(frame,source);
              frames.push(frame); addContext(frame,context);
            }
          } else {
            const frame=parseClause(source,context);
            if(!frame) return null;
            applySpan(frame,source); frames=[frame];
          }
        }
      }
    }

    const claims=frames.map((frame,i)=>({...frame,id:claimId(i),provenance:'source_composition_rule',sourceKind:'interpreted_text',confidence:0.86,ruleId:frame.ruleId||'SRC-CLAUSE-COMPOSITION',note:'Parsed by the reusable source-grounded clause grammar. This heuristic confidence is not calibrated and is not proof of semantic correctness or truth.'}));
    if(!claims.length) return null;
    return {
      parser:'USG-SRC', parserVersion:VERSION, complete:true,
      claims, explanations, semanticComposition:composition, unresolved,
      clauseCount:claims.length, compositionType:composition?.type || (claims.length>1?'DISCOURSE':'ATOMIC')
    };
  }

  return { VERSION, composeSourceText, parseClause };
});
