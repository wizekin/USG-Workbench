/*
 * USG Workbench v0.5.4 → USG-SEM/1.0 source adapter.
 *
 * This adapter consumes the semantic model emitted by USGSemanticCore.
 * It does not re-parse source text or infer missing semantic structure.
 * Browser global + CommonJS export; SHA-256 integrity uses Web Crypto.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) {
    Object.assign(api, require('./reconstruct'));
    module.exports = api;
  }
  if (root) {
    if (root.USGWorkbenchReconstructionAdapter) Object.assign(api, root.USGWorkbenchReconstructionAdapter);
    root.USGWorkbenchSemAdapter = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const VERSION = '1.0.0';
  const SOURCE_PROFILE = 'USG-SR/0.5.1';
  const NAMESPACE = 'org.usg.workbench.v0.5.4';

  function clone(value) {
    if (value === undefined) return undefined;
    return JSON.parse(JSON.stringify(value));
  }
  function arr(value) { return Array.isArray(value) ? value : []; }
  function stable(value) {
    if (Array.isArray(value)) return '[' + value.map(stable).join(',') + ']';
    if (value && typeof value === 'object') {
      return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + stable(value[k])).join(',') + '}';
    }
    return JSON.stringify(value);
  }
  async function sha256(text) {
    const cryptoObject = typeof globalThis !== 'undefined' ? globalThis.crypto : null;
    if (!cryptoObject || !cryptoObject.subtle || typeof TextEncoder === 'undefined') {
      throw new Error('SHA-256 integrity requires Web Crypto SubtleCrypto and TextEncoder.');
    }
    const bytes = new TextEncoder().encode(text);
    const digest = await cryptoObject.subtle.digest('SHA-256', bytes);
    return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
  }
  function opaqueId(kind, nativeId) {
    const bytes = new TextEncoder().encode(String(nativeId));
    const hex = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
    return 'wb:' + kind + ':' + (hex || 'empty');
  }
  function requireId(value, label) {
    if (typeof value !== 'string' || !value.length) throw new Error(label + ' must be a non-empty string.');
    return value;
  }
  function toCodePointOffset(source, offset, label) {
    if (!Number.isInteger(offset) || offset < 0 || offset > source.length) {
      throw new Error(label + ' is outside the UTF-16 source range.');
    }
    if (offset > 0 && offset < source.length) {
      const before = source.charCodeAt(offset - 1), after = source.charCodeAt(offset);
      if (before >= 0xD800 && before <= 0xDBFF && after >= 0xDC00 && after <= 0xDFFF) {
        throw new Error(label + ' splits a UTF-16 surrogate pair; refusing to move the span boundary.');
      }
    }
    return Array.from(source.slice(0, offset)).length;
  }
  function spanFromNative(source, sourceRef, start, end, label, expectedQuote) {
    const cpStart = toCodePointOffset(source, start, label + '.start');
    const cpEnd = toCodePointOffset(source, end, label + '.end');
    if (end < start) throw new Error(label + ' has end before start.');
    const quote = source.slice(start, end);
    if (expectedQuote !== undefined && expectedQuote !== null && quote !== expectedQuote) {
      throw new Error(label + ' does not align with the exact source substring.');
    }
    return { sourceRef, start: cpStart, end: cpEnd, offsetUnit: 'unicode_code_point' };
  }
  function status(value) {
    const v = String(value || '').toLowerCase();
    if (v === 'resolved') return 'RESOLVED';
    if (v === 'ambiguous') return 'AMBIGUOUS';
    if (v === 'linked') return 'LINKED';
    if (v === 'unresolved') return 'UNRESOLVED';
    return 'UNKNOWN';
  }
  function identityStatus(value) {
    const v = String(value || '').toUpperCase();
    return ['PROVISIONAL','RESOLVED','AMBIGUOUS','UNRESOLVED','DISPUTED','UNKNOWN'].includes(v) ? v : 'UNKNOWN';
  }
  function unresolvedStatus(value) {
    const v = String(value || '').toUpperCase();
    if (v === 'UNRESOLVED' || v === 'UNSUPPORTED' || v === 'AMBIGUOUS') return v;
    if (v === 'INCOMPLETE' || v === 'CONFLICTING' || v === 'RESOURCE_INTERRUPTED') return v;
    return 'UNKNOWN';
  }
  function evidenceStatus(item) {
    if (item.exactSourceMatch === true) return 'EXACT';
    if (item.exactSourceMatch === false) return 'MISMATCH';
    return 'UNVERIFIED';
  }
  function semanticKindForEntity(entity) {
    const type = String(entity.type || '').toLowerCase();
    if (type === 'event') return 'EVENT';
    if (type === 'state') return 'STATE';
    if (type === 'process') return 'PROCESS';
    if (type === 'property') return 'PROPERTY';
    if (type === 'value') return 'VALUE';
    if (type === 'class' || type === 'concept') return 'ENTITY';
    return 'ENTITY';
  }
  function operatorConstructor(node) {
    if (node.operatorType === 'NEGATION' && node.operator === 'NOT') return 'NOT';
    if (node.operatorType === 'MODAL') return 'MODAL';
    if (node.operatorType === 'QUANTIFIER') return 'QUANTIFIER';
    return 'OPAQUE';
  }

  async function workbenchToContract(model, options) {
    options = options || {};
    if (!model || typeof model !== 'object' || Array.isArray(model)) throw new Error('A Workbench semantic model object is required.');
    if (model.profile !== SOURCE_PROFILE) throw new Error('Expected Workbench profile ' + SOURCE_PROFILE + ', received ' + String(model.profile));
    if (model.version !== '0.5.1') throw new Error('Expected Workbench semantic-core version 0.5.1, received ' + String(model.version));
    if (!model.source || typeof model.source.text !== 'string') throw new Error('Workbench model has no exact source text.');
    const sourceText = model.source.text;
    const sourceNativeId = String(model.source.sourceId || options.sourceId || 'primary');
    const sourceRef = opaqueId('source', sourceNativeId);
    const documentId = opaqueId('document', options.documentId || sourceNativeId);
    const entities = arr(model.entities), mentions = arr(model.mentions), evidence = arr(model.evidence);
    const expressions = arr(model.expressions), relations = arr(model.relations);
    const roots = arr(model.rootExpressionIds), unresolved = arr(model.unresolvedItems);
    const entityById = new Map(), mentionById = new Map(), evidenceById = new Map(), expressionById = new Map();
    for (const x of entities) { requireId(x.id, 'entity.id'); if (entityById.has(x.id)) throw new Error('Duplicate Workbench entity id ' + x.id); entityById.set(x.id, x); }
    for (const x of mentions) { requireId(x.id, 'mention.id'); if (mentionById.has(x.id)) throw new Error('Duplicate Workbench mention id ' + x.id); mentionById.set(x.id, x); }
    for (const x of evidence) { requireId(x.id, 'evidence.id'); if (evidenceById.has(x.id)) throw new Error('Duplicate Workbench evidence id ' + x.id); evidenceById.set(x.id, x); }
    for (const x of expressions) { requireId(x.id, 'expression.id'); if (expressionById.has(x.id)) throw new Error('Duplicate Workbench expression id ' + x.id); expressionById.set(x.id, x); }

    const referentRef = id => {
      if (!entityById.has(id)) throw new Error('Expression references missing Workbench entity ' + id);
      return opaqueId('referent', id);
    };
    const mentionRef = id => {
      if (!mentionById.has(id)) throw new Error('Expression references missing Workbench mention ' + id);
      return opaqueId('mention', id);
    };
    const evidenceRef = id => {
      if (!evidenceById.has(id)) throw new Error('Expression references missing Workbench evidence ' + id);
      return opaqueId('evidence', id);
    };
    const expressionRef = id => {
      if (!expressionById.has(id)) throw new Error('Expression references missing Workbench expression ' + id);
      return opaqueId('expr', id);
    };

    const sources = [{
      id: sourceRef, text: sourceText, language: model.source.language || 'und',
      sourceType: 'USER_INPUT', trustTier: 'UNKNOWN', sensitivity: 'UNKNOWN',
      textHash: await sha256(sourceText), hashAlgorithm: 'SHA-256', encoding: 'UTF-8',
      offsetUnit: 'unicode_code_point'
    }];

    const referents = entities.map(entity => ({
      id: opaqueId('referent', entity.id),
      label: requireId(entity.canonicalText, 'entity.canonicalText'),
      semanticKind: semanticKindForEntity(entity),
      aliases: Array.from(new Set(arr(entity.aliases).filter(x => typeof x === 'string'))),
      identity: { status: identityStatus(entity.identityStatus), scope: 'DOCUMENT' },
      nativeId: entity.id, nativeType: entity.type || 'unknown'
    }));

    const partialRefs = [];
    const canonicalMentions = mentions.map(mention => {
      const item = {
        id: opaqueId('mention', mention.id),
        surfaceText: String(mention.surfaceText || ''),
        resolutionStatus: status(mention.resolutionStatus),
        mentionType: mention.mentionType || 'unknown',
        nativeId: mention.id
      };
      if (mention.entityId) item.referentRef = referentRef(mention.entityId);
      else item.referentRef = null;
      if (mention.antecedentEntityId) item.antecedentReferentRef = referentRef(mention.antecedentEntityId);
      if (mention.sourceSpan) {
        const nativeSpan = spanFromNative(sourceText, sourceRef, mention.sourceSpan.start, mention.sourceSpan.end,
          'mention ' + mention.id);
        if (sourceText.slice(mention.sourceSpan.start, mention.sourceSpan.end) === mention.surfaceText) item.sourceSpan = nativeSpan;
        else partialRefs.push(opaqueId('mention', mention.id));
      }
      return item;
    });

    const canonicalEvidence = evidence.map(item => {
      const start = item.start, end = item.end;
      if (item.sourceText !== undefined && item.sourceText !== sourceText) throw new Error('Evidence ' + item.id + ' belongs to a different source string.');
      const expectedQuote = item.exactSourceMatch === true ? item.quote : undefined;
      const span = spanFromNative(sourceText, sourceRef, start, end, 'evidence ' + item.id, expectedQuote);
      return {
        id: opaqueId('evidence', item.id), sourceRef, span, quote: String(item.quote || ''),
        alignmentStatus: evidenceStatus(item), semanticSupportStatus: 'NOT_ESTABLISHED',
        nativeVerificationMeaning: item.verificationMeaning || 'source_alignment_only_not_semantic_entailment',
        nativeModelQuote: item.modelQuote === undefined ? null : item.modelQuote,
        nativeModelQuoteVerified: item.modelQuoteVerified === undefined ? null : item.modelQuoteVerified
      };
    });

    const canonicalExpressions = [];
    const argumentNodes = [];
    const usedExpressionIds = new Set(expressions.map(x => opaqueId('expr', x.id)));
    function addArgumentNode(nativeExpression, argument, index) {
      const id = opaqueId('argument', nativeExpression.id + ':' + index + ':' + argument.role);
      if (usedExpressionIds.has(id)) throw new Error('Generated argument expression id collision: ' + id);
      usedExpressionIds.add(id);
      if (argument.entityId) {
        const ref = referentRef(argument.entityId);
        argumentNodes.push({ id, op: 'REF', sort: 'TERM', operandRefs: [], params: { ref }, nativeId: nativeExpression.id + ':argument:' + index });
      } else {
        const params = { role: argument.role, surfaceText: argument.mentionId && mentionById.get(argument.mentionId)?.surfaceText || null,
          reason: 'Workbench argument has no resolved referent; no referent was invented.' };
        if (argument.mentionId) params.mentionRef = mentionRef(argument.mentionId);
        argumentNodes.push({ id, op: 'UNRESOLVED_REF', sort: 'TERM', operandRefs: [], params,
          interpretationStatus: 'UNRESOLVED', nativeId: nativeExpression.id + ':argument:' + index });
      }
      return id;
    }

    for (const node of expressions) {
      const id = expressionRef(node.id);
      if (node.type === 'PREDICATION') {
        const args = arr(node.arguments);
        const operandRefs = args.map((arg, index) => addArgumentNode(node, arg, index));
        const params = {
          predicate: node.predicate, roles: args.map(arg => String(arg.role || 'other').toUpperCase()),
          argumentRequirements: clone(node.argumentRequirements || {}),
          grammaticalTense: node.grammaticalTense || 'unknown', aspect: node.aspect || 'unknown',
          temporalFrame: clone(node.temporalFrame || {}),
          eventFrame: { nativeFrameId: node.eventFrame?.id || null, kind: node.eventFrame?.kind || 'unknown',
            predicate: node.eventFrame?.predicate || node.predicate,
            participants: arr(node.eventFrame?.participants).map(p => ({ role: p.role,
              referentRef: p.entityId ? referentRef(p.entityId) : null,
              variableId: p.variableId || null,
              bindingReferentRef: p.bindingEntityId ? referentRef(p.bindingEntityId) : null })),
            attributes: clone(node.eventFrame?.attributes || []) },
          attribution: clone(node.attribution || {}), provenance: clone(node.provenance || {}),
          completeness: clone(node.completeness || {}), evidenceRefs: arr(node.evidenceRefs).map(evidenceRef),
          nativeSourceClaimId: node.sourceClaimId || null,
          argumentBindings: args.map(arg => ({ role: arg.role, variableId: arg.variableId || null,
            bindingReferentRef: arg.bindingEntityId ? referentRef(arg.bindingEntityId) : null,
            mentionRef: arg.mentionId ? mentionRef(arg.mentionId) : null })),
        };
        canonicalExpressions.push({ id, op: 'PREDICATE_APP', sort: 'SIT', operandRefs, params,
          interpretationStatus: ['unresolved','underspecified'].includes(String(node.completeness?.status || '').toLowerCase()) ? 'UNRESOLVED' : 'RESOLVED', nativeId: node.id });
      } else if (node.type === 'OPERATOR') {
        const target = expressionRef(node.scope?.targetId);
        const op = operatorConstructor(node);
        const params = { operatorType: node.operatorType, operator: node.operator,
          scopeKind: node.scope?.scopeKind || 'unknown', force: node.force || null,
          variable: node.variable || null,
          restrictor: node.restrictor ? { predicate: node.restrictor.predicate || null,
            referentRef: node.restrictor.entityId ? referentRef(node.restrictor.entityId) : null } : null,
          variableBinding: node.variableBinding ? { variable: node.variableBinding.variable || null,
            role: node.variableBinding.role || null,
            restrictorReferentRef: node.variableBinding.restrictorEntityId ? referentRef(node.variableBinding.restrictorEntityId) : null } : null,
          surfaceText: node.surfaceText || null, evidenceRefs: arr(node.evidenceRefs).map(evidenceRef) };
        if (op === 'OPAQUE') { params.preservationReason = 'Workbench operator kind/polarity has no exact registered USG-SEM constructor mapping.'; partialRefs.push(id); }
        canonicalExpressions.push({ id, op, sort: 'PROP', operandRefs: [target], params,
          interpretationStatus: op === 'OPAQUE' ? 'UNRESOLVED' : 'RESOLVED', nativeId: node.id });
      } else if (node.type === 'CONNECTIVE') {
        let operandRefs, operandRoles;
        if (node.antecedentId && node.consequentId) {
          operandRefs = [expressionRef(node.antecedentId), expressionRef(node.consequentId)];
          operandRoles = ['antecedent', 'consequent'];
        } else {
          operandRefs = arr(node.operandIds).map(expressionRef);
          operandRoles = operandRefs.map((_, index) => 'operand_' + index);
        }
        const params = { connective: node.connective, marker: node.marker || null,
          operandRoles, logicalStatus: node.logicalStatus || null,
          antecedentInterpretation: node.antecedentInterpretation || null,
          conditionMetadata: node.conditionMetadata ? { effect: node.conditionMetadata.effect || null,
            logicalStatus: node.conditionMetadata.logicalStatus || null,
            consequence: node.conditionMetadata.consequence || null,
            consequenceInterpretation: node.conditionMetadata.consequenceInterpretation || null,
            nativeConsequentClaimId: node.conditionMetadata.consequentClaimId || null } : null,
          disjunctionSemantics: node.disjunctionSemantics || null,
          attribution: clone(node.attribution || {}), evidenceRefs: arr(node.evidenceRefs).map(evidenceRef) };
        canonicalExpressions.push({ id, op: 'CONNECTIVE', sort: 'PROP', operandRefs, params,
          interpretationStatus: 'RESOLVED', nativeId: node.id });
      } else {
        const idRef = expressionRef(node.id);
        const childIds = [];
        if (node.scope?.targetId) childIds.push(node.scope.targetId);
        if (node.antecedentId) childIds.push(node.antecedentId);
        if (node.consequentId) childIds.push(node.consequentId);
        childIds.push(...arr(node.operandIds));
        const operandRefs = childIds.map(expressionRef);
        partialRefs.push(idRef);
        canonicalExpressions.push({ id: idRef, op: 'OPAQUE', sort: 'ANY', operandRefs,
          params: { nativeType: node.type || 'unknown',
            preservationReason: 'Unrecognized Workbench expression type; preserved in the namespaced native snapshot without semantic coercion.' },
          interpretationStatus: 'UNRESOLVED', nativeId: node.id });
      }
    }
    canonicalExpressions.push(...argumentNodes);

    const rootExpressionRefs = roots.map(expressionRef);
    const canonicalRelations = relations.map(relation => {
      const id = opaqueId('relation', relation.id);
      const exactVerification = relation.verification === 'not_independently_verified';
      if (!exactVerification) partialRefs.push(id);
      return { id, type: relation.type,
        sourceExpressionRef: expressionRef(relation.sourceExpressionId),
        targetExpressionRef: expressionRef(relation.targetExpressionId),
        verificationStatus: exactVerification ? 'NOT_INDEPENDENTLY_VERIFIED' : 'UNKNOWN',
        nativeVerification: relation.verification || 'unknown',
        nativeStatus: relation.status || null, note: relation.note || null,
        evidenceRefs: arr(relation.evidenceRefs).map(evidenceRef),
        attribution: clone(relation.attribution || {}) };
    });

    const canonicalUnresolved = unresolved.map(item => {
      const out = { id: opaqueId('unresolved', item.id), status: unresolvedStatus(item.status),
        reason: String(item.reason || 'Workbench unresolved item.'), surfaceText: String(item.surfaceText || ''),
        nativeStatus: item.status || 'unknown' };
      if (item.scope && expressionById.has(item.scope)) out.scopeRef = expressionRef(item.scope);
      else if (item.scope) out.scopeLabel = String(item.scope);
      if (item.evidenceRef) out.evidenceRefs = [evidenceRef(item.evidenceRef)];
      return out;
    });

    const buildNotes = arr(model.buildNotes);
    const unmappedRefs = [...new Set(partialRefs)];
    if (buildNotes.length) {
      for (let i = 0; i < buildNotes.length; i++) unmappedRefs.push('wb:warning:' + i);
    }
    const mappingStatus = unmappedRefs.length ? 'PARTIAL' : 'LOSSLESS';
    const derivations = [{
      id: opaqueId('derivation', 'semantic-core:' + model.version),
      method: 'COMPOSITION', component: 'USGSemanticCore/' + model.version,
      ruleIds: Array.from(new Set(expressions.map(x => x.provenance?.ruleId).filter(x => typeof x === 'string' && x.length))),
      inputRefs: [sourceRef], outputRefs: roots.map(expressionRef),
      status: buildNotes.length ? 'INCOMPLETE' : 'VALIDATED', diagnostics: buildNotes.slice()
    }];
    const document = {
      profileId: 'USG-SEM/1.0', documentId, sources, primarySourceRef: sourceRef,
      definitions: { concepts: [], frames: [], roles: [], relations: [] },
      referents, mentions: canonicalMentions, expressions: canonicalExpressions,
      rootExpressionRefs, assertions: [], evidence: canonicalEvidence, contexts: [],
      expressionRelations: canonicalRelations, unresolvedItems: canonicalUnresolved,
      derivations, validation: { structuralStatus: 'NOT_CHECKED', checks: [] },
      mapping: { sourceProfile: SOURCE_PROFILE, sourceVersion: model.version,
        status: mappingStatus, unmappedRefs },
      extensions: { [NAMESPACE]: { adapterVersion: VERSION, sourceProfile: model.profile,
        sourceVersion: model.version, nativeModel: clone(model), nativeModelDigest: await sha256(stable(model)) } }
    };
    const canonicalProjectionDigest = await sha256(stable({ ...document, extensions: {} }));
    document.extensions[NAMESPACE].canonicalProjectionDigest = canonicalProjectionDigest;
    return { document, report: { status: mappingStatus, sourceProfile: SOURCE_PROFILE,
      sourceVersion: model.version, convertedCounts: { sources: sources.length, referents: referents.length,
        mentions: canonicalMentions.length, expressions: canonicalExpressions.length, evidence: canonicalEvidence.length,
        relations: canonicalRelations.length, unresolvedItems: canonicalUnresolved.length },
      unmappedRefs, diagnostics: buildNotes.slice() } };
  }

  async function verifyNativeSnapshot(document) {
    const payload = document?.extensions?.[NAMESPACE];
    if (!payload || !payload.nativeModel || !payload.nativeModelDigest) return { present: false, valid: false };
    const actual = await sha256(stable(payload.nativeModel));
    const projection = clone(document);
    projection.extensions = {};
    const projectionActual = await sha256(stable(projection));
    const nativeValid = actual === payload.nativeModelDigest;
    const projectionValid = projectionActual === payload.canonicalProjectionDigest;
    return { present: true, valid: nativeValid && projectionValid, nativeValid, projectionValid,
      expectedNative: payload.nativeModelDigest, actualNative: actual,
      expectedProjection: payload.canonicalProjectionDigest, actualProjection: projectionActual };
  }

  return { VERSION, SOURCE_PROFILE, NAMESPACE, workbenchToContract, verifyNativeSnapshot,
    toCodePointOffset, spanFromNative, stable };
});
