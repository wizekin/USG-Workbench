/*
 * USG Semantic Core v0.5.1
 * Canonical, compositional semantic expression graph.
 * Dependency-free; browser global + CommonJS export for tests.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.USGSemanticCore = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const VERSION = '0.5.1';
  const PROFILE = 'USG-SR/0.5.1';
  const VALID_TENSES = new Set(['past', 'present', 'future', 'unknown']);
  const VALID_POLARITIES = new Set(['positive', 'negative', 'unknown']);
  const VALID_MODALITIES = new Set(['asserted', 'possible', 'necessary', 'obligatory', 'possible_or_ability', 'expected', 'unknown']);
  const EVENT_PREDICATES = new Set(['BOUGHT','BUY','USES','USED','STOP_USING','FAIL','FAILS','INCREASE','DECREASE','CHANGE','MEASURES','ACQUIRED','PURCHASED','REDUCE','REDUCES','SELLS','SOLD','PRODUCES','PRODUCED','RECEIVES','RECEIVED','BREAKS','BROKE','STARTS','STARTED','CLOSES','CLOSED']);
  const STATE_PREDICATES = new Set(['NEEDS','NEED','LIKE','DISLIKE','WANTS','WANT','HAS_PROPERTY','EXISTS','KNOWS','BELIEVES']);
  const RELATION_PREDICATES = new Set(['SUBCLASS_OF','INSTANCE_OF','PART_OF','CAUSES','DIFFER','RELATED_TO']);
  const TRANSITIVE_PREDICATES = new Set(['NEEDS','NEED','LIKE','LIKED','DISLIKE','DISLIKED','WANTS','WANT','BUY','BUYS','BOUGHT','PURCHASE','PURCHASES','PURCHASED','ACQUIRE','ACQUIRES','ACQUIRED','USE','USES','USED','STOP_USING','MEASURE','MEASURES','REDUCE','REDUCES','SELL','SELLS','SOLD','PRODUCE','PRODUCES','PRODUCED','RECEIVE','RECEIVES','RECEIVED','BREAK','BREAKS','BROKE','START','STARTS','STARTED','CLOSE','CLOSES','CLOSED']);
  const PRONOUNS = new Set(['he','she','they','it','him','her','them','this','that','these','those','we','us','i','me','you']);
  const MODAL_OPERATORS = new Set(['MIGHT','MAY','COULD','CAN','MUST','SHOULD','WILL','WOULD','POSSIBLE','NECESSARY','OBLIGATORY','POSSIBLE_OR_ABILITY','EXPECTED','UNKNOWN']);
  const QUANTIFIERS = new Set(['FORALL','EXISTS','EXACTLY_ONE','AT_LEAST_ONE','AT_MOST_ONE']);

  function text(value) {
    if (typeof value === 'string') return value.trim().replace(/\s+/g, ' ');
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return String(value.canonicalText || value.text || value.label || value.name || '').trim().replace(/\s+/g, ' ');
    }
    return '';
  }
  function key(value) { return text(value).toLocaleLowerCase(); }
  function slug(value) { return key(value).normalize('NFKD').replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 36) || 'entity'; }
  function hash(value) {
    let h = 2166136261;
    for (const ch of String(value)) { h ^= ch.codePointAt(0); h = Math.imul(h, 16777619); }
    return (h >>> 0).toString(36);
  }
  function id(prefix, seed) { return `${prefix}_${slug(seed)}_${hash(seed)}`; }
  function safeArray(value) { return Array.isArray(value) ? value : []; }
  function cleanPredicate(value) { return String(value || 'RELATED_TO').toUpperCase().replace(/[^A-Z0-9_]/g, '_').slice(0, 64); }
  function clampSpan(evidence, source) {
    const start = Number.isInteger(evidence?.start) ? evidence.start : 0;
    const end = Number.isInteger(evidence?.end) ? evidence.end : start;
    const inRange = start >= 0 && end >= start && end <= source.length;
    const quote = typeof evidence?.quote === 'string' ? evidence.quote : '';
    const exact = inRange && quote.length > 0 && source.slice(start, end) === quote;
    return { start, end, quote, verified: exact };
  }

  function buildSemanticModel(record) {
    const sourceText = String(record?.sourceText || '');
    const claims = safeArray(record?.claims);
    const entities = new Map();
    const entitiesByCanonical = new Map();
    const mentions = [];
    const rawMentionPool = safeArray(record?.mentions).map((m, index) => ({ ...m, __poolIndex: index, __used: false }));
    const evidence = [];
    const expressions = [];
    const relations = [];
    const claimMap = new Map();
    const warnings = [];
    const unresolved = [];
    const unresolvedItems = [];
    const expressionIds = new Set();
    function addUnresolved(surfaceText, reason, status = 'unresolved', scope = null, rawEvidence = null) {
      const evidenceRef = rawEvidence ? addEvidence(rawEvidence) : null;
      const item = { id: id('unres', `${surfaceText}|${reason}|${unresolvedItems.length}`), surfaceText: String(surfaceText || ''), reason: String(reason || 'Insufficient information.'), status, evidenceRef, scope };
      unresolvedItems.push(item);
      unresolved.push(`${item.reason}${item.surfaceText ? ` Source text: “${item.surfaceText}”.` : ''}`);
      return item;
    }

    function addEntity(raw, fallbackType = 'unknown') {
      const canonicalText = text(raw);
      if (!canonicalText) return null;
      const suppliedId = raw && typeof raw === 'object' && typeof raw.entityId === 'string' && raw.entityId.trim() ? raw.entityId.trim() : null;
      // An unresolved pronoun is a mention, not a newly invented discourse entity.
      if (PRONOUNS.has(canonicalText.toLocaleLowerCase()) && !suppliedId) return null;
      const k = key(canonicalText);
      let entry = suppliedId ? entities.get(suppliedId) : entitiesByCanonical.get(k);
      if (entry && key(entry.canonicalText) !== k && suppliedId) {
        warnings.push(`Entity identifier ${suppliedId} was reused for a different canonical label; USG created a separate provisional entity instead of merging them.`);
        entry = null;
      }
      if (!entry) {
        let entityId = suppliedId || id('ent', k);
        if (entities.has(entityId) && key(entities.get(entityId).canonicalText) !== k) entityId = id('ent', `${suppliedId}|${k}`);
        entry = { id: entityId, canonicalText, type: (raw && typeof raw === 'object' && raw.type) || fallbackType || 'unknown', aliases: [], identityStatus: 'provisional' };
        entities.set(entityId, entry);
        if (!entitiesByCanonical.has(k)) entitiesByCanonical.set(k, entry);
      }
      const surfaceText = raw && typeof raw === 'object' ? text(raw.surfaceText || raw.text || raw.label || raw.name) : canonicalText;
      if (surfaceText && !entry.aliases.includes(surfaceText)) entry.aliases.push(surfaceText);
      if (entry.type === 'unknown' && fallbackType !== 'unknown') entry.type = fallbackType;
      return entry;
    }
    function addMention(raw, entity, fallbackType = 'noun_phrase', preferredRaw = null) {
      const surfaceText = raw && typeof raw === 'object' ? text(raw.surfaceText || raw.text || raw.canonicalText) : text(raw);
      if (!surfaceText) return null;
      const rawMention = preferredRaw || rawMentionPool.find(m => !m.__used && m.surfaceText === surfaceText && (!entity || !m.entityId || m.entityId === entity.id)) || null;
      if (rawMention) rawMention.__used = true;
      const start = rawMention?.start ?? rawMention?.sourceSpan?.start;
      const end = rawMention?.end ?? rawMention?.sourceSpan?.end;
      if (Number.isInteger(start) && Number.isInteger(end)) {
        const existing = mentions.find(m => m.surfaceText === surfaceText && m.entityId === (entity?.id || null) && m.sourceSpan?.start === start && m.sourceSpan?.end === end);
        if (existing) return existing.id;
      }
      const mentionId = rawMention?.id || id('men', `${surfaceText}|${entity?.id || 'unresolved'}|${mentions.length}`);
      const resolved = !!entity;
      const antecedentEntityId = rawMention?.antecedentEntityId || rawMention?.antecedentId || (rawMention?.reference === 'resolved_pronoun' ? entity?.id || null : null);
      const isPronounSurface = PRONOUNS.has(surfaceText.toLocaleLowerCase());
      const mentionType = rawMention?.mentionType || (isPronounSurface ? 'pronoun' : fallbackType);
      mentions.push({
        id: mentionId,
        entityId: entity?.id || null,
        surfaceText,
        mentionType,
        resolutionStatus: antecedentEntityId || mentionType === 'pronoun' ? (resolved ? 'resolved' : 'unresolved') : (resolved ? 'linked' : 'unresolved'),
        antecedentEntityId,
        sourceSpan: Number.isInteger(start) && Number.isInteger(end) ? { start, end } : null
      });
      return mentionId;
    }
    function addEvidence(raw, fallbackQuote = '') {
      if (!raw || typeof raw !== 'object') return null;
      const span = clampSpan(raw, sourceText);
      const quote = span.quote || fallbackQuote;
      const found = evidence.find(e => e.start === span.start && e.end === span.end && e.quote === quote);
      if (found) return found.id;
      const evidenceId = id('ev', `${span.start}|${span.end}|${quote}`);
      evidence.push({ id: evidenceId, sourceText, quote, start: span.start, end: span.end, exactSourceMatch: span.verified, modelQuote: typeof raw.modelQuote === 'string' ? raw.modelQuote : null, modelQuoteVerified: typeof raw.modelQuoteVerified === 'boolean' ? raw.modelQuoteVerified : null, verificationMeaning: 'source_alignment_only_not_semantic_entailment' });
      if (!span.verified && quote) warnings.push(`Evidence span ${evidenceId} is not an exact source substring.`);
      return evidenceId;
    }
    function addExpression(node) {
      if (expressionIds.has(node.id)) throw new Error(`Duplicate semantic expression id: ${node.id}`);
      expressionIds.add(node.id); expressions.push(node); return node.id;
    }
    function addOperator(operatorType, operator, targetId, options = {}) {
      const operatorId = id('op', `${operatorType}|${operator}|${targetId}|${expressions.length}`);
      return addExpression({
        id: operatorId, type: 'OPERATOR', operatorType, operator,
        force: options.force || null,
        variable: options.variable || null,
        restrictor: options.restrictor || null,
        variableBinding: options.variableBinding || null,
        scope: { targetId, scopeKind: options.scopeKind || 'whole_expression' },
        surfaceText: options.surfaceText || null,
        evidenceRefs: options.evidenceRefs || []
      });
    }
    function addProposition(raw, claim, label = 'claim') {
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
      const suppliedArguments = safeArray(raw.arguments);
      const subjectArgument = suppliedArguments.find(a=>a?.role==='subject');
      const objectArgument = suppliedArguments.find(a=>a?.role==='object');
      const subjectRaw = raw.subject ?? raw.agent ?? subjectArgument?.entity ?? subjectArgument?.value ?? null;
      const objectRaw = raw.object ?? raw.patient ?? objectArgument?.entity ?? objectArgument?.value ?? null;
      const subjectSurface = text(subjectRaw);
      const predicateSurface = String(raw.predicate || '').trim();
      if (!subjectSurface) { addUnresolved('', `Claim ${claim?.id || label} has no recoverable subject.`, 'unresolved', label, raw.evidence || claim?.evidence); return null; }
      if (!predicateSurface) { addUnresolved(subjectSurface, `Claim ${claim?.id || label} has no explicit predicate; USG did not invent a generic relation.`, 'unresolved', label, raw.evidence || claim?.evidence); return null; }
      const subjectEntity = addEntity(subjectRaw, subjectRaw?.type || 'unknown');
      const objectEntity = objectRaw == null || !text(objectRaw) ? null : addEntity(objectRaw, objectRaw?.type || 'unknown');
      const predicateId = cleanPredicate(predicateSurface);
      const propositionId = id('prop', `${claim?.id || label}|${predicateId}|${subjectEntity ? subjectEntity.id : `unresolved_${slug(subjectSurface)}`}|${objectEntity?.id || 'null'}|${expressions.length}`);
      const ev = addEvidence(raw.evidence || claim?.evidence, raw.evidence?.quote || claim?.evidence?.quote || '');
      const subjectMentionSurface = subjectRaw && typeof subjectRaw === 'object' ? String(subjectRaw.surfaceText || subjectRaw.text || subjectSurface) : subjectSurface;
      const objectMentionSurface = objectRaw && typeof objectRaw === 'object' ? String(objectRaw.surfaceText || objectRaw.text || text(objectRaw)) : text(objectRaw);
      const subjectMentionId = addMention(subjectRaw, subjectEntity, PRONOUNS.has(subjectMentionSurface.toLocaleLowerCase()) ? 'pronoun' : 'noun_phrase');
      const objectMentionId = objectRaw != null && text(objectRaw) ? addMention(objectRaw, objectEntity, PRONOUNS.has(objectMentionSurface.toLocaleLowerCase()) ? 'pronoun' : 'noun_phrase') : null;
      if (!subjectEntity && subjectMentionId) addUnresolved(subjectSurface, 'A pronoun subject has no resolved antecedent entity.', 'unresolved', label, raw.evidence || claim?.evidence);
      if (objectRaw != null && text(objectRaw) && !objectEntity && objectMentionId) addUnresolved(text(objectRaw), 'A pronoun object has no resolved antecedent entity.', 'unresolved', label, raw.evidence || claim?.evidence);
      const args = [
        { role: 'subject', entityId: subjectEntity?.id || null, mentionId: subjectMentionId },
        { role: 'object', entityId: objectEntity?.id || null, mentionId: objectMentionId }
      ];
      for (const rawArg of suppliedArguments) {
        if (!rawArg || !['instrument','recipient','location','time','other'].includes(rawArg.role)) continue;
        const rawValue = rawArg.entity ?? rawArg.value;
        const ent = addEntity(rawValue, 'unknown');
        args.push({ role: rawArg.role, entityId: ent?.id || null, mentionId: ent ? addMention(rawValue, ent) : null });
      }
      const tense = VALID_TENSES.has(raw.tense) ? raw.tense : 'unknown';
      const time = raw.time && typeof raw.time === 'object' && !Array.isArray(raw.time) ? raw.time : {};
      const temporalFrame = {
        referenceTime: typeof time.referenceTime === 'string' ? time.referenceTime : 'unspecified',
        temporalAdverbials: safeArray(time.temporalAdverbials).filter(x => typeof x === 'string'),
        sourceTense: typeof time.sourceTense === 'string' ? time.sourceTense : tense,
        clauseEvidence: typeof time.clauseEvidence === 'string' ? time.clauseEvidence : null
      };
      const allowedAttributeTypes = new Set(['frequency','duration','manner','temporal_reference','intensity','quantity','location','instrument']);
      const attributes = safeArray(raw.eventAttributes || claim?.eventAttributes)
        .filter(a => a && typeof a === 'object' && !Array.isArray(a))
        .map(a => ({ type: String(a.type || '').toLowerCase(), value: String(a.value || a.surfaceText || '').trim(), surfaceText: String(a.surfaceText || a.value || '').trim(), normalizedValue: typeof a.normalizedValue === 'string' && !/^(?:\.{2,}|normalizedvalue|exact source phrase)$/i.test(a.normalizedValue.trim()) ? a.normalizedValue : null, scope: a.scope || 'event' }))
        .filter(a => {
          const placeholder = !a.value || /^(?:\.{2,}|exact source phrase|source phrase|value|normalizedvalue|frequency\|duration|frequency_duration_manner_*)$/i.test(a.value) || /^(?:\.{2,}|exact source phrase|source phrase)$/i.test(a.surfaceText);
          const sourceGrounded = !!a.surfaceText && sourceText.includes(a.surfaceText);
          if (!allowedAttributeTypes.has(a.type) || placeholder || !sourceGrounded) {
            warnings.push(`An unsupported, placeholder, or source-unaligned event attribute (${a.type || 'unknown'}) was discarded.`);
            return false;
          }
          return true;
        }).map(a => ({ type:a.type, value:a.value, normalizedValue:a.normalizedValue, scope:a.scope }));
      const frameKind = EVENT_PREDICATES.has(predicateId) ? 'event' : (STATE_PREDICATES.has(predicateId) ? 'state' : (RELATION_PREDICATES.has(predicateId) ? 'relation' : 'unknown'));
      const requiredRoles = ['subject', ...(TRANSITIVE_PREDICATES.has(predicateId) ? ['object'] : [])];
      const presentRoles = args.filter(a => a.entityId).map(a => a.role);
      const missingRoles = requiredRoles.filter(role => !presentRoles.includes(role));
      const sourceCompleteness = claim?.completeness && typeof claim.completeness === 'object' && !Array.isArray(claim.completeness) ? claim.completeness : { status: 'complete', missingRoles: [], note: '' };
      const sourceMissingRoles = Array.isArray(sourceCompleteness.missingRoles) ? sourceCompleteness.missingRoles.filter(role => typeof role === 'string') : [];
      const completeness = { ...sourceCompleteness, missingRoles: [...new Set([...sourceMissingRoles, ...missingRoles])] };
      if (missingRoles.length) { completeness.status = 'underspecified'; completeness.note = completeness.note || `Required argument(s) missing: ${missingRoles.join(', ')}.`; addUnresolved('', `Proposition ${predicateId} is missing required argument(s): ${missingRoles.join(', ')}.`, 'unresolved', label, raw.evidence || claim?.evidence); }
      if (!subjectEntity) completeness.status = 'unresolved';
      const nestedCondition = label === 'condition';
      const proposition = {
        id: propositionId,
        type: 'PREDICATION',
        predicate: predicateId,
        arguments: args,
        argumentRequirements: { requiredRoles, missingRoles },
        grammaticalTense: tense,
        aspect: ['simple','progressive','perfect','habitual','unknown'].includes(time.aspect) ? time.aspect : 'unknown',
        temporalFrame,
        eventFrame: { id: id('evt', propositionId), kind: frameKind, predicate: predicateId, participants: args.map(a=>({role:a.role,entityId:a.entityId})), attributes },
        attribution: {
          kind: 'source_voice',
          status: nestedCondition ? 'embedded_condition_not_asserted' : (raw.modality && raw.modality !== 'asserted' ? 'source_modalized' : 'source_asserted'),
          embedding: nestedCondition ? 'conditional_or_temporal_antecedent' : null,
          truthStatus: 'not_independently_established'
        },
        provenance: {
          method: claim?.provenance || 'unknown',
          ruleId: claim?.ruleId || null,
          sourceKind: claim?.sourceKind || 'interpreted_text'
        },
        completeness,
        evidenceRefs: ev ? [ev] : [],
        sourceClaimId: claim?.id || null
      };
      addExpression(proposition);
      return { propositionId, subjectEntity, objectEntity };
    }
    function addNegation(targetId, claim) {
      const ev = addEvidence(claim?.evidence);
      return addOperator('NEGATION', 'NOT', targetId, { surfaceText: claim?.evidence?.quote || null, evidenceRefs: ev ? [ev] : [] });
    }
    function addUnknownPolarity(targetId, claim) {
      const ev = addEvidence(claim?.evidence);
      return addOperator('POLARITY', 'UNKNOWN', targetId, { surfaceText: null, evidenceRefs: ev ? [ev] : [] });
    }
    function addModal(targetId, claim) {
      const modal = claim?.modalScope || {};
      const modality = claim?.modality || 'unknown';
      let operator = String(modal.operator || ({ possible:'POSSIBLE', necessary:'NECESSARY', obligatory:'OBLIGATORY', possible_or_ability:'POSSIBLE_OR_ABILITY', expected:'EXPECTED', asserted:'ASSERTED' }[modality] || 'UNKNOWN')).toUpperCase();
      if (operator === 'ASSERTED' && modality === 'unknown') operator = 'UNKNOWN';
      if (operator === 'ASSERTED' && modality === 'asserted') return targetId;
      if (!MODAL_OPERATORS.has(operator)) { warnings.push(`Unsupported modal operator ${operator} was preserved as UNKNOWN rather than interpreted as a new logical operator.`); operator = 'UNKNOWN'; }
      const ev = addEvidence(claim?.evidence);
      return addOperator('MODAL', operator, targetId, { force: modal.force || modality, surfaceText: modal.surfaceText || null, evidenceRefs: ev ? [ev] : [] });
    }
    function bindQuantifierVariable(expressionId, variable, restrictorEntity, role = 'subject') {
      const seen = new Set();
      let cursor = expressionId;
      while (cursor && !seen.has(cursor)) {
        seen.add(cursor);
        const node = expressions.find(e => e.id === cursor);
        if (!node) return false;
        if (node.type === 'PREDICATION') {
          const argument = node.arguments.find(a => a.role === role);
          if (!argument) return false;
          argument.variableId = variable;
          argument.bindingEntityId = restrictorEntity.id;
          if (node.eventFrame) {
            const participant = node.eventFrame.participants.find(a => a.role === role);
            if (participant) { participant.variableId = variable; participant.bindingEntityId = restrictorEntity.id; }
          }
          return true;
        }
        if (node.type === 'OPERATOR') cursor = node.scope?.targetId;
        else if (node.type === 'CONNECTIVE') cursor = node.consequentId || safeArray(node.operandIds)[0];
        else return false;
      }
      return false;
    }
    function wrapClaim(claim, propositionId) {
      let rootId = propositionId;
      const rawQ = claim.quantifierScope;
      const q = rawQ && typeof rawQ === 'object' && !Array.isArray(rawQ) && (
        (rawQ.quantifier && String(rawQ.quantifier).toUpperCase() !== 'UNKNOWN') ||
        (rawQ.operator && !['UNKNOWN','NONE','NULL'].includes(String(rawQ.operator).toUpperCase())) ||
        !!rawQ.surfaceText && !/^(?:\.{2,}|exact source phrase|unknown)$/i.test(String(rawQ.surfaceText).trim()) ||
        !!rawQ.logicalForm && !/^(?:\.{2,}|unknown)$/i.test(String(rawQ.logicalForm).trim()) ||
        !!(rawQ.restrictor && typeof rawQ.restrictor==='object' && (text(rawQ.restrictor.entity) || text(rawQ.restrictor.text) || text(rawQ.restrictor.entityText)))
      ) ? rawQ : null;
      if (q && q.quantifier && q.quantifier !== 'UNKNOWN') {
        const quantifier = String(q.quantifier).toUpperCase();
        const qOperator = String(q.operator || 'NONE').toUpperCase();
        const restrictorEntity = addEntity(q.restrictor?.entity || q.restrictor?.text || q.restrictor?.entityText || '', 'class');
        const variable = q.variable || 'x';
        if (!QUANTIFIERS.has(quantifier) || !restrictorEntity || !['NO','NOT','NONE'].includes(qOperator)) {
          addUnresolved(q.surfaceText || '', `Quantifier scope on claim ${claim.id || ''} is incomplete or uses an unsupported quantifier/operator; it was not flattened into an ordinary proposition.`, 'unsupported', 'quantifier', claim.evidence);
          rootId = addOperator('UNRESOLVED_SCOPE', 'QUANTIFIER', rootId, { surfaceText: q.surfaceText || null, scopeKind: 'unknown' });
        } else if (qOperator === 'NO') {
          bindQuantifierVariable(rootId, variable, restrictorEntity, q.boundRole || 'subject');
          const negativeBody = addNegation(rootId, claim);
          rootId = addOperator('QUANTIFIER', 'FORALL', negativeBody, { variable, restrictor: { entityId: restrictorEntity.id, predicate: q.restrictor?.predicate || 'INSTANCE_OF' }, variableBinding: { variable, role: q.boundRole || 'subject', restrictorEntityId: restrictorEntity.id }, surfaceText: q.surfaceText || 'no' });
        } else {
          bindQuantifierVariable(rootId, variable, restrictorEntity, q.boundRole || 'subject');
          rootId = addOperator('QUANTIFIER', quantifier, rootId, { variable, restrictor: { entityId: restrictorEntity.id, predicate: q.restrictor?.predicate || 'INSTANCE_OF' }, variableBinding: { variable, role: q.boundRole || 'subject', restrictorEntityId: restrictorEntity.id }, surfaceText: q.surfaceText || null });
          if (qOperator === 'NOT') rootId = addOperator('NEGATION', 'NOT', rootId, { surfaceText: q.surfaceText || 'not' });
        }
      } else if (q) {
        addUnresolved(q.surfaceText || '', `Quantifier scope on claim ${claim.id || ''} uses an unsupported or unknown quantifier; it was not flattened into an ordinary proposition.`, 'unsupported', 'quantifier', claim.evidence);
        rootId = addOperator('UNRESOLVED_SCOPE', 'QUANTIFIER', rootId, { surfaceText: q.surfaceText || null, scopeKind: 'unknown' });
      } else if (claim.polarity === 'negative') {
        rootId = addNegation(rootId, claim);
      } else if (claim.polarity === 'unknown') {
        rootId = addUnknownPolarity(rootId, claim);
      }
      rootId = addModal(rootId, claim);
      const conditions = safeArray(claim.conditions);
      for (const condition of conditions) {
        const marker = String(condition.marker || '').toLowerCase();
        const supportedMarkers = new Set(['if','unless','when']);
        if (!supportedMarkers.has(marker)) {
          addUnresolved(condition.evidenceText || marker, `The clause marker “${marker || 'unknown'}” is not yet covered by the semantic foundation; its meaning was preserved as unresolved instead of being mislabeled as a conditional.`, 'unsupported', 'subordinate_clause', condition.evidence);
          continue;
        }
        const nested = addProposition(condition.proposition, null, 'condition');
        if (!nested) {
          addUnresolved(condition.evidenceText || marker, `Condition ${condition.id || marker} has no valid nested proposition.`, 'unresolved', 'subordinate_clause', condition.evidence);
          continue;
        }
        let antecedentRoot = wrapNestedProposition(condition.proposition, nested.propositionId, condition.evidence);
        // In standard compositional semantics, “unless P, Q” is represented as
        // the exception relation equivalent to “if NOT P, Q”. Keep the original
        // EXCEPTION marker while making the negated condition explicit.
        if (marker === 'unless') antecedentRoot = addOperator('NEGATION', 'NOT', antecedentRoot, { surfaceText: null, evidenceRefs: condition.evidence ? [addEvidence(condition.evidence)].filter(Boolean) : [] });
        const connectiveId = id('conn', `${marker}|${antecedentRoot}|${rootId}`);
        const type = marker === 'unless' ? 'EXCEPTION' : (marker === 'when' ? 'WHEN' : 'CONDITIONAL');
        const logicalStatus = marker === 'unless' ? 'exception_relation_asserted' : (marker === 'when' ? 'when_clause_not_asserted' : 'conditional_not_asserted');
        rootId = addExpression({
          id: connectiveId, type: 'CONNECTIVE', connective: type,
          antecedentId: antecedentRoot, consequentId: rootId,
          logicalStatus, marker, antecedentInterpretation: marker === 'unless' ? 'negated_exception_condition_equivalent_to_if_not_P_then_Q' : null,
          conditionMetadata: {
            effect: condition.effect || (marker === 'unless' ? 'exception_to_assertion' : (marker === 'when' ? 'temporal_condition_for_assertion' : 'condition_for_assertion')),
            logicalStatus: condition.logicalStatus || logicalStatus,
            consequence: condition.consequence || null,
            consequenceInterpretation: condition.consequenceInterpretation || null,
            consequentClaimId: condition.consequentClaimId || claim.id || null
          },
          evidenceRefs: (() => { const ref = addEvidence(condition.evidence); return ref ? [ref] : []; })(),
          attribution: { kind: 'source_voice', status: marker === 'when' ? 'temporal_condition_asserted' : (marker === 'unless' ? 'exception_relation_asserted' : 'conditional_relation_asserted'), truthStatus: 'not_independently_established' }
        });
      }
      return rootId;
    }
    function wrapNestedProposition(raw, propositionId, evidenceRaw = null) {
      let rootId = propositionId;
      if (raw.polarity === 'negative') rootId = addOperator('NEGATION', 'NOT', rootId, { surfaceText: evidenceRaw?.quote || null, evidenceRefs: evidenceRaw ? [addEvidence(evidenceRaw)].filter(Boolean) : [] });
      else if (raw.polarity === 'unknown') rootId = addOperator('POLARITY', 'UNKNOWN', rootId, { evidenceRefs: evidenceRaw ? [addEvidence(evidenceRaw)].filter(Boolean) : [] });
      const ms = raw.modalScope || {};
      const mod = raw.modality || 'asserted';
      if (mod !== 'asserted' || (ms.operator && ms.operator !== 'ASSERTED')) {
        let modalOperator = (ms.operator === 'ASSERTED' && mod === 'unknown') ? 'UNKNOWN' : String(ms.operator || mod.toUpperCase());
        modalOperator = modalOperator.toUpperCase();
        if (!MODAL_OPERATORS.has(modalOperator)) { warnings.push(`Unsupported nested modal operator ${modalOperator} was preserved as UNKNOWN.`); modalOperator = 'UNKNOWN'; }
        rootId = addOperator('MODAL', modalOperator, rootId, { force: ms.force || mod, surfaceText: ms.surfaceText || null });
      }
      return rootId;
    }

    // Carry legacy/top-level unresolved content into the canonical model so that
    // the semantic graph does not appear complete merely because no claim node
    // was created for an unsupported part of the source.
    for (const rawUnresolved of safeArray(record?.unresolved)) {
      const message = typeof rawUnresolved === 'string' ? rawUnresolved : text(rawUnresolved?.reason || rawUnresolved?.text);
      if (message) addUnresolved('', message, 'unresolved', 'record');
    }

    // Build entities and atomic propositions first, then apply semantic operators.
    for (const claim of claims) {
      const normalizedClaim = {
        subject: claim.subject, predicate: claim.predicate, object: claim.object,
        polarity: claim.polarity, tense: claim.tense, modality: claim.modality,
        modalScope: claim.modalScope, time: claim.time, quantifierScope: claim.quantifierScope,
        eventAttributes: claim.eventAttributes, evidence: claim.evidence
      };
      const built = addProposition(normalizedClaim, claim);
      if (!built) {
        addUnresolved(text(claim.subject), `Claim ${claim.id || ''} could not be represented as a proposition because its subject or predicate was missing or invalid.`, 'unresolved', 'claim', claim.evidence);
        continue;
      }
      const rootId = wrapClaim(claim, built.propositionId);
      claimMap.set(claim.id, { propositionId: built.propositionId, rootId });
    }

    // Source-level causal and claim relations are links between expression roots,
    // not unqualified facts about objective causation or logical proof.
    for (const explanation of safeArray(record?.explanations)) {
      const cause = claimMap.get(explanation.causeClaimId);
      const effect = claimMap.get(explanation.effectClaimId);
      if (!cause || !effect) { addUnresolved('', `Causal explanation ${explanation.id || ''} references a missing claim.`, 'unresolved', 'causal_relation', explanation.evidence); continue; }
      const ev = addEvidence(explanation.evidence);
      relations.push({
        id: explanation.id || id('rel', `${cause.rootId}|${effect.rootId}|CAUSE`),
        type: 'CAUSE', sourceExpressionId: cause.rootId, targetExpressionId: effect.rootId,
        attribution: { kind: 'source_asserted', holder: null },
        verification: 'not_independently_verified', evidenceRefs: ev ? [ev] : [], note: explanation.note || ''
      });
    }
    for (const relation of safeArray(record?.claimRelations)) {
      const from = claimMap.get(relation.fromClaimId);
      const to = claimMap.get(relation.toClaimId);
      if (!from || !to) { addUnresolved('', `Claim relation ${relation.id || ''} references a missing claim.`, 'unresolved', 'claim_relation'); continue; }
      relations.push({ id: relation.id || id('rel', `${from.rootId}|${to.rootId}|${relation.type}`), type: relation.type, sourceExpressionId: from.rootId, targetExpressionId: to.rootId, attribution: { kind: 'system_candidate', holder: null }, verification: 'candidate_not_proof', status: relation.status || 'candidate', note: relation.note || '' });
    }

    // A source-grounded composition pass may specify directed clause relations
    // (notably concessive although-clauses) without relying on global keyword scans.
    let explicitCompositionRootId = null;
    const semanticComposition = record?.semanticComposition && typeof record.semanticComposition === 'object' ? record.semanticComposition : null;
    if (semanticComposition?.type === 'CONCESSIVE') {
      const antecedent = claimMap.get(semanticComposition.antecedentClaimId);
      const consequent = claimMap.get(semanticComposition.consequentClaimId);
      if (antecedent && consequent) {
        const antecedentClaim = claims.find(claim => claim.id === semanticComposition.antecedentClaimId);
        const consequentClaim = claims.find(claim => claim.id === semanticComposition.consequentClaimId);
        const concessiveEvidenceRefs = [...new Set([
          addEvidence(antecedentClaim?.evidence),
          addEvidence(consequentClaim?.evidence)
        ].filter(Boolean))];
        explicitCompositionRootId = addExpression({
          id:id('conn', `concessive|${antecedent.rootId}|${consequent.rootId}`),
          type:'CONNECTIVE', connective:'CONCESSIVE',
          antecedentId:antecedent.rootId, consequentId:consequent.rootId,
          logicalStatus:'concessive_relation_asserted', marker:semanticComposition.marker || 'although',
          evidenceRefs:concessiveEvidenceRefs,
          attribution:{kind:'source_voice',status:'concessive_relation_asserted',truthStatus:'not_independently_established'}
        });
      } else {
        addUnresolved('', 'A concessive composition references a missing antecedent or consequent claim.', 'unresolved', 'composition');
      }
    }

    // Represent explicit coordination across multiple claims without flattening them.
    const sourceLower = sourceText.toLocaleLowerCase();
    const topRoots = [...new Set([...claimMap.values()].map(x => x.rootId))];
    if (!explicitCompositionRootId && topRoots.length > 1 && /\bbut\b/i.test(sourceText)) {
      const connectId = id('conn', `contrast|${topRoots.join('|')}`);
      addExpression({ id: connectId, type: 'CONNECTIVE', connective: 'CONTRAST', operandIds: topRoots, marker: 'but', attribution: { kind: 'source_voice', status: 'coordination_asserted' } });
    } else if (!explicitCompositionRootId && topRoots.length > 1 && /\bor\b/i.test(sourceText)) {
      const connectId = id('conn', `or|${topRoots.join('|')}`);
      addExpression({ id: connectId, type: 'CONNECTIVE', connective: 'OR', operandIds: topRoots, marker: 'or', disjunctionSemantics: 'inclusive_or_unspecified', attribution: { kind: 'source_voice', status: 'coordination_asserted' } });
    } else if (!explicitCompositionRootId && topRoots.length > 1 && /\band\b/i.test(sourceText)) {
      const connectId = id('conn', `and|${topRoots.join('|')}`);
      addExpression({ id: connectId, type: 'CONNECTIVE', connective: 'AND', operandIds: topRoots, marker: 'and', attribution: { kind: 'source_voice', status: 'coordination_asserted' } });
    }

    // Carry existing discourse mentions into the canonical registry, but never
    // manufacture an antecedent when the existing resolver did not supply one.
    for (const mention of rawMentionPool) {
      if (mention.__used) continue;
      const entity = [...entities.values()].find(e => e.id === mention.entityId) || [...entities.values()].find(e => key(e.canonicalText) === key(mention.canonicalText));
      const mid = addMention({ surfaceText: mention.surfaceText }, entity || null, mention.mentionType || 'noun_phrase', mention);
      const target = mentions.find(m => m.id === mid);
      if (target && (mention.antecedentId || mention.antecedentEntityId)) { target.resolutionStatus = entity ? 'resolved' : 'unresolved'; target.antecedentEntityId = mention.antecedentEntityId || mention.antecedentId; }
    }

    const rootExpressionIds = [];
    for (const value of claimMap.values()) if (!rootExpressionIds.includes(value.rootId)) rootExpressionIds.push(value.rootId);
    // If a complete connective groups all independent claim roots, make it the top root.
    const coordinator = expressions.findLast ? expressions.findLast(e => e.type === 'CONNECTIVE' && ['CONTRAST','AND','OR'].includes(e.connective) && e.operandIds?.length === rootExpressionIds.length) : [...expressions].reverse().find(e => e.type === 'CONNECTIVE' && ['CONTRAST','AND','OR'].includes(e.connective) && e.operandIds?.length === rootExpressionIds.length);
    if (explicitCompositionRootId) rootExpressionIds.splice(0, rootExpressionIds.length, explicitCompositionRootId);
    else if (coordinator) { rootExpressionIds.splice(0, rootExpressionIds.length, coordinator.id); }

    const model = {
      profile: PROFILE,
      version: VERSION,
      canonical: true,
      compatibilityView: 'record.claims',
      source: { text: sourceText, language: 'en', sourceId: record?.sourceId || null },
      entities: [...entities.values()].map(e => ({ ...e, aliases: [...new Set(e.aliases)] })),
      mentions,
      evidence,
      expressions,
      relations,
      rootExpressionIds,
      unresolvedItems,
      acceptanceBoundary: { requiresHumanReview: true, acceptedIntoKnowledgeBase: false, objectiveTruthEstablished: false },
      buildNotes: warnings
    };
    const validation = validateSemanticModel(model);
    validation.warningCount += warnings.length;
    validation.warnings.push(...warnings);
    validation.unresolved = unresolved;
    validation.status = validation.errors.length ? 'invalid' : (unresolved.length ? 'partial' : (warnings.length ? 'valid_with_warnings' : 'valid'));
    return { model, validation };
  }

  function validateSemanticModel(model) {
    const errors = [];
    const warnings = [];
    if (!model || typeof model !== 'object') return { valid: false, status: 'invalid', errors: ['Semantic model is not an object.'], warnings: [], expressionCount: 0, entityCount: 0, relationCount: 0, requiresHumanReview: true, objectiveTruthEstablished: false };
    if (model.profile !== PROFILE) errors.push(`Unexpected semantic profile: ${model.profile}`);
    if (model.version !== VERSION) errors.push(`Unexpected semantic model version: ${model.version}`);
    if (!model.source || typeof model.source !== 'object' || typeof model.source.text !== 'string' || typeof model.source.language !== 'string') errors.push('Semantic model source must contain text and language.');
    const entities = safeArray(model.entities);
    const expressions = safeArray(model.expressions);
    const evidence = safeArray(model.evidence);
    const mentions = safeArray(model.mentions);
    const relations = safeArray(model.relations);
    const entityIds = new Set();
    const expressionMap = new Map();
    const evidenceIds = new Set();
    const mentionIds = new Set();
    for (const entity of entities) {
      if (!entity.id || entityIds.has(entity.id)) errors.push(`Missing or duplicate entity id: ${entity.id || '(empty)'}`);
      entityIds.add(entity.id);
      if (!text(entity.canonicalText)) errors.push(`Entity ${entity.id} has no canonical text.`);
    }
    for (const ev of evidence) {
      if (!ev.id || evidenceIds.has(ev.id)) errors.push(`Missing or duplicate evidence id: ${ev.id || '(empty)'}`);
      evidenceIds.add(ev.id);
      if (!Number.isInteger(ev.start) || !Number.isInteger(ev.end) || ev.start < 0 || ev.end < ev.start || ev.end > String(model.source?.text || '').length) errors.push(`Evidence ${ev.id} has an invalid source span.`);
      else if (String(model.source?.text || '').slice(ev.start, ev.end) !== ev.quote) errors.push(`Evidence ${ev.id} quote does not match its source span.`);
    }
    for (const mention of mentions) {
      if (!mention.id || mentionIds.has(mention.id)) errors.push(`Missing or duplicate mention id: ${mention.id || '(empty)'}`);
      mentionIds.add(mention.id);
      if (mention.entityId && !entityIds.has(mention.entityId)) errors.push(`Mention ${mention.id} references missing entity ${mention.entityId}.`);
      if (mention.antecedentEntityId && !entityIds.has(mention.antecedentEntityId)) errors.push(`Mention ${mention.id} references missing antecedent entity ${mention.antecedentEntityId}.`);
      if (!mention.entityId && mention.resolutionStatus !== 'unresolved') warnings.push(`Mention ${mention.id} has no entity link and should remain unresolved.`);
      if (mention.sourceSpan) {
        const start = mention.sourceSpan.start, end = mention.sourceSpan.end;
        if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end < start || end > String(model.source?.text || '').length) errors.push(`Mention ${mention.id} has an invalid source span.`);
        else if (String(model.source?.text || '').slice(start, end) !== mention.surfaceText) errors.push(`Mention ${mention.id} source span does not match its surface text.`);
      }
    }
    const unresolvedIds = new Set();
    for (const item of safeArray(model.unresolvedItems)) {
      if (!item.id || unresolvedIds.has(item.id)) errors.push(`Missing or duplicate unresolved-item id: ${item.id || '(empty)'}`);
      unresolvedIds.add(item.id);
      if (!['unresolved','unsupported','ambiguous'].includes(item.status)) errors.push(`Unresolved item ${item.id} has invalid status ${item.status}.`);
      if (item.evidenceRef && !evidenceIds.has(item.evidenceRef)) errors.push(`Unresolved item ${item.id} references missing evidence ${item.evidenceRef}.`);
    }
    const expressionTypes = new Set(['PREDICATION','OPERATOR','CONNECTIVE']);
    const operatorTypes = new Set(['NEGATION','MODAL','QUANTIFIER','POLARITY','UNRESOLVED_SCOPE']);
    const modalOperators = new Set(['MIGHT','MAY','COULD','CAN','MUST','SHOULD','WILL','WOULD','POSSIBLE','NECESSARY','OBLIGATORY','POSSIBLE_OR_ABILITY','EXPECTED','UNKNOWN']);
    const quantifiers = new Set(['FORALL','EXISTS','EXACTLY_ONE','AT_LEAST_ONE','AT_MOST_ONE']);
    const connectives = new Set(['CONDITIONAL','EXCEPTION','WHEN','AND','OR','CONTRAST','CONCESSIVE']);
    for (const expression of expressions) {
      if (!expression.id || expressionMap.has(expression.id)) errors.push(`Missing or duplicate expression id: ${expression.id || '(empty)'}`);
      expressionMap.set(expression.id, expression);
      if (!expressionTypes.has(expression.type)) errors.push(`Expression ${expression.id} has unsupported type ${expression.type}.`);
      for (const ref of safeArray(expression.evidenceRefs)) if (!evidenceIds.has(ref)) errors.push(`Expression ${expression.id} references missing evidence ${ref}.`);
      if (expression.type === 'PREDICATION') {
        if (!expression.predicate) errors.push(`Predication ${expression.id} has no predicate.`);
        const args = safeArray(expression.arguments);
        const hasLinkedSubject = args.some(arg=>arg.role==='subject' && arg.entityId);
        const hasUnresolvedSubjectMention = args.some(arg=>arg.role==='subject' && !arg.entityId && arg.mentionId && mentions.some(m=>m.id===arg.mentionId && m.resolutionStatus==='unresolved'));
        if (!hasLinkedSubject && !hasUnresolvedSubjectMention) errors.push(`Predication ${expression.id} must have a linked subject or an explicit unresolved subject mention.`);
        if (args.filter(arg=>arg.role==='subject').length !== 1) errors.push(`Predication ${expression.id} must have exactly one subject argument.`);
        if (new Set(args.map(arg=>arg.role)).size !== args.length) errors.push(`Predication ${expression.id} contains duplicate argument roles.`);
        for (const arg of args) {
          if (!['subject','object','agent','patient','instrument','recipient','location','time','other'].includes(arg.role)) warnings.push(`Predication ${expression.id} uses nonstandard argument role ${arg.role}.`);
          if (arg.variableId && !arg.bindingEntityId) errors.push(`Predication ${expression.id} argument ${arg.role} has a variable without a binding entity.`);
          if (arg.bindingEntityId && !entityIds.has(arg.bindingEntityId)) errors.push(`Predication ${expression.id} argument ${arg.role} binds to a missing entity ${arg.bindingEntityId}.`);
          if (arg.entityId && !entityIds.has(arg.entityId)) errors.push(`Predication ${expression.id} argument ${arg.role} references missing entity ${arg.entityId}.`);
          if (!arg.entityId && arg.role === 'subject' && !hasUnresolvedSubjectMention) errors.push(`Predication ${expression.id} has no subject entity or unresolved mention.`);
          if (arg.mentionId && !mentionIds.has(arg.mentionId)) errors.push(`Predication ${expression.id} references missing mention ${arg.mentionId}.`);
        }
        if (!VALID_TENSES.has(expression.grammaticalTense)) errors.push(`Predication ${expression.id} has invalid grammaticalTense.`);
        if (!expression.eventFrame || !expression.eventFrame.id || expression.eventFrame.predicate !== expression.predicate) errors.push(`Predication ${expression.id} has a missing or inconsistent event/state frame.`);
        if (!['simple','progressive','perfect','habitual','unknown'].includes(expression.aspect)) errors.push(`Predication ${expression.id} has an invalid aspect.`);
        if (!expression.temporalFrame || typeof expression.temporalFrame.referenceTime !== 'string' || !Array.isArray(expression.temporalFrame.temporalAdverbials)) errors.push(`Predication ${expression.id} has an invalid temporal frame.`);
        if (!expression.completeness || !['complete','underspecified','unresolved','not_applicable'].includes(expression.completeness.status) || !Array.isArray(expression.completeness.missingRoles)) errors.push(`Predication ${expression.id} has invalid completeness metadata.`);
        const requiredRoles = safeArray(expression.argumentRequirements?.requiredRoles);
        const missingRoles = requiredRoles.filter(role => !args.some(arg => arg.role === role && arg.entityId));
        if (missingRoles.length && expression.completeness?.status === 'complete') errors.push(`Predication ${expression.id} omits required roles (${missingRoles.join(', ')}) but is marked complete.`);
        if (safeArray(expression.argumentRequirements?.missingRoles).some(role => !missingRoles.includes(role))) warnings.push(`Predication ${expression.id} lists a missing role that is not missing in its arguments.`);
        for (const participant of safeArray(expression.eventFrame?.participants)) if (participant.entityId && !entityIds.has(participant.entityId)) errors.push(`Event frame ${expression.eventFrame.id} references missing participant ${participant.entityId}.`);
      } else if (expression.type === 'OPERATOR') {
        if (!operatorTypes.has(expression.operatorType) || !expression.operator) errors.push(`Operator ${expression.id} is missing valid operator metadata.`);
        if (!expression.scope?.targetId) errors.push(`Operator ${expression.id} has no explicit scope target.`);
        if (expression.operatorType === 'NEGATION' && expression.operator !== 'NOT') errors.push(`Negation operator ${expression.id} must use NOT.`);
        if (expression.operatorType === 'POLARITY' && expression.operator !== 'UNKNOWN') errors.push(`Polarity operator ${expression.id} must use UNKNOWN.`);
        if (expression.operatorType === 'UNRESOLVED_SCOPE' && (!expression.surfaceText || !expression.scope?.targetId)) warnings.push(`Unresolved-scope operator ${expression.id} should preserve the source phrase and scope target.`);
        if (expression.operatorType === 'MODAL' && !modalOperators.has(expression.operator)) errors.push(`Modal operator ${expression.id} uses unsupported operator ${expression.operator}.`);
        if (!['whole_expression','predicate','argument','quantifier_body','clause','unknown'].includes(expression.scope?.scopeKind)) warnings.push(`Operator ${expression.id} uses an unfamiliar scope kind ${expression.scope?.scopeKind}.`);
        if (expression.operatorType === 'QUANTIFIER') {
          if (!quantifiers.has(expression.operator)) errors.push(`Quantifier operator ${expression.id} uses unsupported quantifier ${expression.operator}.`);
          if (!expression.variable) errors.push(`Quantifier operator ${expression.id} has no bound variable.`);
          if (!expression.restrictor?.entityId || !entityIds.has(expression.restrictor.entityId)) errors.push(`Quantifier operator ${expression.id} has no valid restrictor entity.`);
          const binding = expression.variableBinding;
          if (!binding?.variable || binding.variable !== expression.variable || !binding.role || binding.restrictorEntityId !== expression.restrictor?.entityId) errors.push(`Quantifier operator ${expression.id} has no consistent variable binding.`);
          let scopedId = expression.scope?.targetId; const seenScope = new Set(); let boundArgument = null;
          while (scopedId && !seenScope.has(scopedId)) { const scoped = expressionMap.get(scopedId); if (!scoped) break; seenScope.add(scopedId); if (scoped.type === 'PREDICATION') { boundArgument = safeArray(scoped.arguments).find(a => a.role === binding?.role); break; } if (scoped.type === 'OPERATOR') scopedId = scoped.scope?.targetId; else if (scoped.type === 'CONNECTIVE') scopedId = scoped.consequentId || safeArray(scoped.operandIds)[0]; else break; }
          if (!boundArgument || boundArgument.variableId !== expression.variable || boundArgument.bindingEntityId !== expression.restrictor?.entityId) errors.push(`Quantifier operator ${expression.id} is not bound to the corresponding predication argument.`);
        }
      } else if (expression.type === 'CONNECTIVE') {
        const arity = expression.antecedentId && expression.consequentId ? 2 : safeArray(expression.operandIds).length;
        if (!connectives.has(expression.connective)) errors.push(`Connective ${expression.id} uses unsupported connective ${expression.connective}.`);
        if (arity < 2) errors.push(`Connective ${expression.id} must reference at least two operands.`);
        if (['CONDITIONAL','EXCEPTION','CONCESSIVE'].includes(expression.connective) && !(expression.antecedentId && expression.consequentId)) errors.push(`Directed connective ${expression.id} must have antecedent and consequent references.`);
        if (expression.connective === 'CONDITIONAL' && expression.logicalStatus !== 'conditional_not_asserted') errors.push(`Conditional connective ${expression.id} must preserve conditional_not_asserted status.`);
        if (expression.connective === 'EXCEPTION' && expression.logicalStatus !== 'exception_relation_asserted') errors.push(`Exception connective ${expression.id} must preserve exception_relation_asserted status.`);
        if (expression.connective === 'WHEN' && expression.logicalStatus !== 'when_clause_not_asserted') errors.push(`WHEN connective ${expression.id} must preserve when_clause_not_asserted status.`);
        if (expression.connective === 'CONCESSIVE' && expression.logicalStatus !== 'concessive_relation_asserted') errors.push(`CONCESSIVE connective ${expression.id} must preserve concessive_relation_asserted status.`);
        if (expression.connective === 'OR' && expression.disjunctionSemantics !== 'inclusive_or_unspecified') warnings.push(`OR connective ${expression.id} does not specify whether the disjunction is exclusive; default interpretation must remain inclusive-or-unspecified.`);
        const marker = String(expression.marker || '').toLowerCase();
        const expectedType = marker === 'unless' ? 'EXCEPTION' : (marker === 'when' ? 'WHEN' : (marker === 'if' ? 'CONDITIONAL' : null));
        if (expectedType && expression.connective !== expectedType) errors.push(`Connective ${expression.id} uses marker “${marker}” but connective type ${expression.connective}; expected ${expectedType}.`);
        if (expression.connective === 'EXCEPTION') {
          const antecedentNode = expressionMap.get(expression.antecedentId);
          if (!antecedentNode || antecedentNode.type !== 'OPERATOR' || antecedentNode.operatorType !== 'NEGATION' || antecedentNode.operator !== 'NOT') {
            errors.push(`EXCEPTION connective ${expression.id} must represent its antecedent as NOT(P), not as P or an unscoped condition.`);
          }
          if (expression.conditionMetadata?.effect && expression.conditionMetadata.effect !== 'exception_to_assertion') errors.push(`EXCEPTION connective ${expression.id} conflicts with condition effect ${expression.conditionMetadata.effect}.`);
          if (expression.conditionMetadata?.logicalStatus && expression.conditionMetadata.logicalStatus !== 'exception_relation_asserted') errors.push(`EXCEPTION connective ${expression.id} conflicts with its condition logicalStatus metadata.`);
        }
        if (expression.connective === 'WHEN') {
          if (expression.conditionMetadata?.effect && expression.conditionMetadata.effect !== 'temporal_condition_for_assertion') errors.push(`WHEN connective ${expression.id} has non-temporal condition effect ${expression.conditionMetadata.effect} in its compatibility metadata.`);
          if (expression.conditionMetadata?.logicalStatus && expression.conditionMetadata.logicalStatus !== 'when_clause_not_asserted') errors.push(`WHEN connective ${expression.id} conflicts with its condition logicalStatus metadata.`);
        }
        if (expression.connective === 'CONDITIONAL') {
          if (expression.conditionMetadata?.effect && expression.conditionMetadata.effect !== 'condition_for_assertion') errors.push(`CONDITIONAL connective ${expression.id} conflicts with condition effect ${expression.conditionMetadata.effect}.`);
          if (expression.conditionMetadata?.logicalStatus && expression.conditionMetadata.logicalStatus !== 'conditional_not_asserted') errors.push(`CONDITIONAL connective ${expression.id} conflicts with its condition logicalStatus metadata.`);
        }
        if (expression.connective === 'CONCESSIVE' && !safeArray(expression.evidenceRefs).length) errors.push(`CONCESSIVE connective ${expression.id} must retain source evidence for its clauses.`);
      }
    }
    // Referential integrity and acyclic scope graph.
    const childIds = expression => {
      if (expression.type === 'OPERATOR') return [expression.scope?.targetId].filter(Boolean);
      if (expression.type === 'CONNECTIVE') return [expression.antecedentId, expression.consequentId, ...safeArray(expression.operandIds)].filter(Boolean);
      return [];
    };
    for (const expression of expressions) {
      for (const childId of childIds(expression)) if (!expressionMap.has(childId)) errors.push(`Expression ${expression.id} scopes or connects to missing expression ${childId}.`);
    }
    const rootIds = safeArray(model.rootExpressionIds);
    if (new Set(rootIds).size !== rootIds.length) errors.push('The root expression list contains duplicate identifiers.');
    if (expressions.length && !rootIds.length) errors.push('The semantic model contains expressions but no root expression.');
    const visiting = new Set(); const visited = new Set();
    function visit(id) {
      if (visiting.has(id)) { errors.push(`Expression containment cycle detected at ${id}.`); return; }
      if (visited.has(id)) return;
      const node = expressionMap.get(id); if (!node) return;
      visiting.add(id); for (const child of childIds(node)) visit(child); visiting.delete(id); visited.add(id);
    }
    for (const rootId of rootIds) {
      if (!expressionMap.has(rootId)) errors.push(`Root expression ${rootId} does not exist.`);
      else visit(rootId);
    }
    for (const expression of expressions) {
      if (!visited.has(expression.id)) {
        errors.push(`Expression ${expression.id} is not reachable from any declared root expression.`);
        visit(expression.id); // Also inspect disconnected components for cycles.
      }
    }
    const relationIds = new Set();
    const relationTypes = new Set(['CAUSE','CONTRADICTS','SUPPORTS','ATTACKS','RELATED_TO']);
    for (const relation of relations) {
      if (!relation.id || relationIds.has(relation.id)) errors.push(`Missing or duplicate relation id: ${relation.id || '(empty)'}`);
      relationIds.add(relation.id);
      if (!relationTypes.has(relation.type)) errors.push(`Relation ${relation.id} uses unsupported type ${relation.type}.`);
      if (!expressionMap.has(relation.sourceExpressionId)) errors.push(`Relation ${relation.id} has a missing source expression.`);
      if (!expressionMap.has(relation.targetExpressionId)) errors.push(`Relation ${relation.id} has a missing target expression.`);
      for (const ref of safeArray(relation.evidenceRefs)) if (!evidenceIds.has(ref)) errors.push(`Relation ${relation.id} references missing evidence ${ref}.`);
      if (relation.type === 'CAUSE' && relation.verification !== 'not_independently_verified') warnings.push(`CAUSE relation ${relation.id} must not be treated as independently verified.`);
      if (relation.type === 'CAUSE' && relation.attribution?.kind !== 'source_asserted') warnings.push(`CAUSE relation ${relation.id} should preserve source_asserted attribution.`);
    }
    if (model.acceptanceBoundary?.requiresHumanReview !== true) errors.push('The semantic model must require human review.');
    if (model.acceptanceBoundary?.acceptedIntoKnowledgeBase !== false) errors.push('A candidate semantic model must not silently enter the knowledge base.');
    if (model.acceptanceBoundary?.objectiveTruthEstablished !== false) errors.push('The semantic model must not claim objective truth was established.');
    const valid = errors.length === 0;
    const unresolvedItemCount = safeArray(model.unresolvedItems).length;
    const status = !valid ? 'invalid' : (unresolvedItemCount ? 'partial' : (warnings.length ? 'valid_with_warnings' : 'valid'));
    return {
      valid, status,
      errors, warnings, errorCount: errors.length, warningCount: warnings.length,
      expressionCount: expressions.length, entityCount: entities.length, mentionCount: mentions.length,
      evidenceCount: evidence.length, relationCount: relations.length, unresolvedItemCount,
      requiresHumanReview: model.acceptanceBoundary?.requiresHumanReview === true,
      objectiveTruthEstablished: model.acceptanceBoundary?.objectiveTruthEstablished === true
    };
  }

  function evaluate(record) { return buildSemanticModel(record); }
  return { VERSION, PROFILE, buildSemanticModel, validateSemanticModel, evaluate };
});
