/* USG-SEM/1.0 -> Workbench USG-SR/0.5.1 reconstruction adapter.
 * Reconstructs semantic fields from the canonical document. A verified native
 * snapshot is consulted only for archival/workflow fields; it never supplies
 * or overwrites canonical meaning.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.USGWorkbenchReconstructionAdapter = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const SOURCE_PROFILE = 'USG-SR/0.5.1';
  const SOURCE_VERSION = '0.5.1';
  const NAMESPACE = 'org.usg.workbench.v0.5.4';
  const SUPPORTED_OPS = new Set(['PREDICATE_APP','NOT','MODAL','QUANTIFIER','CONNECTIVE']);
  const WORKBENCH_CONNECTIVES = new Set(['CONDITIONAL','EXCEPTION','WHEN','AND','OR','CONTRAST','CONCESSIVE']);

  function arr(v) { return Array.isArray(v) ? v : []; }
  function clone(v) { return v === undefined ? undefined : JSON.parse(JSON.stringify(v)); }
  function opaqueId(kind, nativeId) {
    const bytes = new TextEncoder().encode(String(nativeId));
    const hex = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
    return 'wb:' + kind + ':' + (hex || 'empty');
  }
  function stable(value) {
    if (Array.isArray(value)) return '[' + value.map(stable).join(',') + ']';
    if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + stable(value[k])).join(',') + '}';
    return JSON.stringify(value);
  }
  async function sha256(value) {
    const c = globalThis.crypto;
    if (!c?.subtle || typeof TextEncoder === 'undefined') throw new Error('Snapshot verification requires Web Crypto and TextEncoder.');
    const bytes = new TextEncoder().encode(value);
    const digest = await c.subtle.digest('SHA-256', bytes);
    return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
  }
  async function verifyNativeSnapshot(document) {
    const payload = document?.extensions?.[NAMESPACE];
    if (!payload || !payload.nativeModel || !payload.nativeModelDigest || !payload.canonicalProjectionDigest) {
      return { present: false, valid: false, nativeValid: false, projectionValid: false };
    }
    const nativeActual = await sha256(stable(payload.nativeModel));
    const projection = clone(document);
    projection.extensions = {};
    const projectionActual = await sha256(stable(projection));
    const nativeValid = nativeActual === payload.nativeModelDigest;
    const projectionValid = projectionActual === payload.canonicalProjectionDigest;
    return { present: true, valid: nativeValid && projectionValid, nativeValid, projectionValid };
  }
  function cpToUtf16(source, offset) {
    if (!Number.isInteger(offset) || offset < 0 || offset > Array.from(source).length) {
      throw new Error('Canonical Unicode code-point offset is outside the source.');
    }
    return Array.from(source).slice(0, offset).join('').length;
  }
  function nativeId(record, fallback) {
    return typeof record?.nativeId === 'string' && record.nativeId.length ? record.nativeId : fallback;
  }
  function requireMap(map, ref, label) {
    if (!map.has(ref)) throw new Error(label + ' references missing canonical record ' + ref);
    return map.get(ref);
  }

  function validateWorkbenchStructure(model) {
    const errors = [];
    const entityIds = new Set(arr(model.entities).map(x => x.id));
    const mentionIds = new Set(arr(model.mentions).map(x => x.id));
    const evidenceIds = new Set(arr(model.evidence).map(x => x.id));
    const expressions = new Map(arr(model.expressions).map(x => [x.id, x]));
    for (const m of arr(model.mentions)) {
      if (m.entityId && !entityIds.has(m.entityId)) errors.push('Mention ' + m.id + ' has a missing entity.');
      if (m.antecedentEntityId && !entityIds.has(m.antecedentEntityId)) errors.push('Mention ' + m.id + ' has a missing antecedent entity.');
    }
    for (const e of arr(model.evidence)) {
      if (e.start < 0 || e.end < e.start || e.end > model.source.text.length ||
          model.source.text.slice(e.start, e.end) !== e.quote) errors.push('Evidence ' + e.id + ' is not aligned to source text.');
    }
    for (const x of expressions.values()) {
      for (const ref of arr(x.evidenceRefs)) if (!evidenceIds.has(ref)) errors.push('Expression ' + x.id + ' references missing evidence ' + ref + '.');
      if (x.type === 'PREDICATION') {
        for (const a of arr(x.arguments)) {
          if (a.entityId && !entityIds.has(a.entityId)) errors.push('Argument in ' + x.id + ' references missing entity.');
          if (a.mentionId && !mentionIds.has(a.mentionId)) errors.push('Argument in ' + x.id + ' references missing mention.');
          if (a.bindingEntityId && !entityIds.has(a.bindingEntityId)) errors.push('Argument in ' + x.id + ' has missing binding entity.');
        }
      } else if (x.type === 'OPERATOR') {
        if (!expressions.has(x.scope?.targetId)) errors.push('Operator ' + x.id + ' has missing scope target.');
      } else if (x.type === 'CONNECTIVE') {
        const refs = x.antecedentId && x.consequentId ? [x.antecedentId, x.consequentId] : arr(x.operandIds);
        if (refs.length < 2 || refs.some(ref => !expressions.has(ref))) errors.push('Connective ' + x.id + ' has invalid operands.');
      }
    }
    const roots = arr(model.rootExpressionIds);
    if (roots.some(ref => !expressions.has(ref))) errors.push('A root expression reference is missing.');
    const visiting = new Set(), visited = new Set();
    function visit(id) {
      if (visiting.has(id)) { errors.push('Expression cycle detected at ' + id); return; }
      if (visited.has(id)) return;
      const x = expressions.get(id); if (!x) return;
      visiting.add(id);
      const refs = x.type === 'OPERATOR' ? [x.scope?.targetId] :
        x.type === 'CONNECTIVE' ? (x.antecedentId && x.consequentId ? [x.antecedentId,x.consequentId] : arr(x.operandIds)) : [];
      for (const ref of refs) visit(ref);
      visiting.delete(id); visited.add(id);
    }
    for (const id of roots) visit(id);
    if (visited.size !== expressions.size) errors.push('One or more reconstructed expressions are unreachable from declared roots.');
    return { valid: errors.length === 0, errors };
  }

  async function contractToWorkbench(document, options) {
    options = options || {};
    if (!document || typeof document !== 'object' || document.profileId !== 'USG-SEM/1.0') {
      throw new Error('A USG-SEM/1.0 document is required.');
    }
    const snapshot = await verifyNativeSnapshot(document);
    const payload = document.extensions?.[NAMESPACE];
    const native = snapshot.valid && payload?.sourceProfile === SOURCE_PROFILE &&
      payload?.sourceVersion === SOURCE_VERSION && payload?.nativeModel?.profile === SOURCE_PROFILE &&
      payload?.nativeModel?.version === SOURCE_VERSION ? payload.nativeModel : null;
    const partial = [];
    const diagnostics = [];
    if (!snapshot.present) diagnostics.push('No Workbench native snapshot is available; archival-only fields cannot be restored.');
    else if (!snapshot.valid) diagnostics.push('Native restoration was blocked because the native or canonical-projection digest did not verify.');
    if (payload && (payload.sourceProfile !== SOURCE_PROFILE || payload.sourceVersion !== SOURCE_VERSION)) {
      diagnostics.push('Native snapshot profile/version does not match Workbench USG-SR/0.5.1.');
    }

    const sources = new Map(arr(document.sources).map(x => [x.id, x]));
    const primary = requireMap(sources, document.primarySourceRef, 'primarySourceRef');
    const sourceText = primary.text;
    if (typeof sourceText !== 'string') throw new Error('Primary canonical source has no exact text.');
    const nativeSourceId = native?.source?.sourceId || primary.nativeId || primary.id;
    const referents = new Map(arr(document.referents).map(x => [x.id, x]));
    const mentions = new Map(arr(document.mentions).map(x => [x.id, x]));
    const evidence = new Map(arr(document.evidence).map(x => [x.id, x]));
    const expressions = new Map(arr(document.expressions).map(x => [x.id, x]));
    const wbEntityId = new Map(), wbMentionId = new Map(), wbEvidenceId = new Map(), wbExpressionId = new Map();

    const entitiesOut = arr(document.referents).map((r, i) => {
      const id = nativeId(r, r.id);
      wbEntityId.set(r.id, id);
      return { id, canonicalText: r.label || r.surfaceText || r.id,
        type: r.nativeType || 'unknown', aliases: arr(r.aliases).slice(),
        identityStatus: String(r.identity?.status || 'UNKNOWN').toLowerCase() };
    });
    const mentionsOut = [];
    for (const m of mentions.values()) {
      const id = nativeId(m, m.id);
      wbMentionId.set(m.id, id);
      if (m.sourceSpan && m.sourceSpan.sourceRef !== document.primarySourceRef) {
        partial.push(m.id); diagnostics.push('Mention ' + m.id + ' uses a non-primary source span.');
      }
      const out = { id, entityId: m.referentRef ? wbEntityId.get(m.referentRef) || null : null,
        surfaceText: String(m.surfaceText || ''), mentionType: m.mentionType || 'unknown',
        resolutionStatus: String(m.resolutionStatus || 'UNKNOWN').toLowerCase() };
      if (m.antecedentReferentRef) out.antecedentEntityId = wbEntityId.get(m.antecedentReferentRef) || null;
      if (m.sourceSpan && m.sourceSpan.sourceRef === document.primarySourceRef) {
        out.sourceSpan = { start: cpToUtf16(sourceText, m.sourceSpan.start), end: cpToUtf16(sourceText, m.sourceSpan.end) };
      }
      mentionsOut.push(out);
    }

    const evidenceOut = [];
    for (const e of evidence.values()) {
      const id = native?.evidence?.find(x => opaqueId('evidence', x.id) === e.id)?.id || e.id;
      wbEvidenceId.set(e.id, id);
      if (e.span?.sourceRef !== document.primarySourceRef) {
        partial.push(e.id); diagnostics.push('Evidence ' + e.id + ' does not target the primary Workbench source.');
        continue;
      }
      const start = cpToUtf16(sourceText, e.span.start), end = cpToUtf16(sourceText, e.span.end);
      const quote = sourceText.slice(start, end);
      if (quote !== e.quote) {
        partial.push(e.id); diagnostics.push('Evidence ' + e.id + ' quote does not match its canonical span.');
        continue;
      }
      evidenceOut.push({ id, sourceText, quote, start, end,
        exactSourceMatch: e.alignmentStatus === 'EXACT',
        modelQuote: e.nativeModelQuote ?? null,
        modelQuoteVerified: e.nativeModelQuoteVerified ?? null,
        verificationMeaning: e.nativeVerificationMeaning || 'source_alignment_only_not_semantic_entailment' });
    }

    const expressionId = ref => wbExpressionId.get(ref) || requireMap(expressions, ref, 'expressionRef').nativeId || ref;
    const supported = new Set();
    for (const x of expressions.values()) if (SUPPORTED_OPS.has(x.op)) supported.add(x.id);
    // A node is reconstructable only when every meaning-bearing child is reconstructable.
    let changed = true;
    while (changed) {
      changed = false;
      for (const x of expressions.values()) {
        if (!supported.has(x.id)) continue;
        const children = x.op === 'PREDICATE_APP' ? arr(x.operandRefs) :
          x.op === 'CONNECTIVE' ? arr(x.operandRefs) : arr(x.operandRefs);
        if (children.some(ref => !supported.has(ref) && !['REF','UNRESOLVED_REF'].includes(expressions.get(ref)?.op))) {
          supported.delete(x.id); changed = true;
        }
      }
    }
    for (const x of expressions.values()) {
      if (!supported.has(x.id)) { partial.push(x.id); diagnostics.push('Expression ' + x.id + ' has no exact Workbench-native constructor mapping.'); }
    }

    // Resolve expression IDs before assembling records; preserve native IDs only
    // when carried explicitly by the canonical projection.
    for (const x of expressions.values()) wbExpressionId.set(x.id, nativeId(x, x.id));
    const expressionsOut = [];
    for (const x of expressions.values()) {
      if (!supported.has(x.id)) continue;
      const outId = wbExpressionId.get(x.id);
      const refs = arr(x.operandRefs);
      const evidenceRefs = arr(x.params?.evidenceRefs).map(ref => wbEvidenceId.get(ref)).filter(Boolean);
      if (x.op === 'PREDICATE_APP') {
        const roles = arr(x.params?.roles);
        if (roles.length !== refs.length) {
          partial.push(x.id); diagnostics.push('Predicate application ' + x.id + ' has role/operand arity mismatch.');
          continue;
        }
        const bindings = arr(x.params?.argumentBindings);
        const args = [];
        let invalid = false;
        for (let i = 0; i < refs.length; i++) {
          const child = expressions.get(refs[i]);
          const binding = bindings[i] || {};
          if (!child || !['REF','UNRESOLVED_REF'].includes(child.op)) { invalid = true; break; }
          const arg = { role: String(roles[i]).toLowerCase(), entityId: null, mentionId: null };
          if (child.op === 'REF') {
            const ref = child.params?.ref;
            if (wbEntityId.has(ref)) arg.entityId = wbEntityId.get(ref);
            else { invalid = true; break; }
          } else {
            if (child.params?.mentionRef && wbMentionId.has(child.params.mentionRef)) arg.mentionId = wbMentionId.get(child.params.mentionRef);
          }
          if (binding.mentionRef && wbMentionId.has(binding.mentionRef)) arg.mentionId = wbMentionId.get(binding.mentionRef);
          if (binding.variableId) arg.variableId = binding.variableId;
          if (binding.bindingReferentRef && wbEntityId.has(binding.bindingReferentRef)) arg.bindingEntityId = wbEntityId.get(binding.bindingReferentRef);
          args.push(arg);
        }
        if (invalid) { partial.push(x.id); diagnostics.push('Predicate application ' + x.id + ' contains an unsupported argument node.'); continue; }
        const frame = x.params?.eventFrame || {};
        expressionsOut.push({ id: outId, type: 'PREDICATION', predicate: x.params?.predicate,
          arguments: args, argumentRequirements: clone(x.params?.argumentRequirements || { requiredRoles: [], missingRoles: [] }),
          grammaticalTense: x.params?.grammaticalTense || 'unknown', aspect: x.params?.aspect || 'unknown',
          temporalFrame: clone(x.params?.temporalFrame || { referenceTime: 'unspecified', temporalAdverbials: [] }),
          eventFrame: { id: frame.nativeFrameId || outId + ':frame', kind: frame.kind || 'unknown',
            predicate: frame.predicate || x.params?.predicate,
            participants: arr(frame.participants).map(p => ({ role: p.role,
              entityId: p.referentRef ? wbEntityId.get(p.referentRef) || null : null,
              variableId: p.variableId || null,
              bindingEntityId: p.bindingReferentRef ? wbEntityId.get(p.bindingReferentRef) || null : null })),
            attributes: clone(frame.attributes || []) },
          attribution: clone(x.params?.attribution || {}), provenance: clone(x.params?.provenance || {}),
          completeness: clone(x.params?.completeness || { status: 'unknown', missingRoles: [] }),
          evidenceRefs, sourceClaimId: x.params?.nativeSourceClaimId || null });
      } else if (['NOT','MODAL','QUANTIFIER'].includes(x.op)) {
        const p = x.params || {};
        const operatorType = x.op === 'NOT' ? 'NEGATION' : x.op === 'MODAL' ? 'MODAL' : 'QUANTIFIER';
        const target = refs[0];
        if (!target || !supported.has(target)) { partial.push(x.id); continue; }
        const out = { id: outId, type: 'OPERATOR', operatorType,
          operator: p.operator || (x.op === 'NOT' ? 'NOT' : 'UNKNOWN'),
          scope: { targetId: wbExpressionId.get(target) || target, scopeKind: p.scopeKind || 'whole_expression' },
          evidenceRefs };
        if (p.force) out.force = p.force;
        if (p.variable) out.variable = p.variable;
        if (p.restrictor) out.restrictor = { predicate: p.restrictor.predicate || null,
          entityId: p.restrictor.referentRef ? wbEntityId.get(p.restrictor.referentRef) || null : null };
        if (p.variableBinding) out.variableBinding = { variable: p.variableBinding.variable || null,
          role: p.variableBinding.role || null,
          restrictorEntityId: p.variableBinding.restrictorReferentRef ? wbEntityId.get(p.variableBinding.restrictorReferentRef) || null : null };
        if (p.surfaceText) out.surfaceText = p.surfaceText;
        expressionsOut.push(out);
      } else if (x.op === 'CONNECTIVE') {
        const p = x.params || {};
        const roles = arr(p.operandRoles);
        if (!WORKBENCH_CONNECTIVES.has(p.connective)) {
          partial.push(x.id); diagnostics.push('Connective ' + x.id + ' is not supported by Workbench 0.5.1.'); continue;
        }
        const out = { id: outId, type: 'CONNECTIVE', connective: p.connective,
          logicalStatus: p.logicalStatus || null, marker: p.marker || null,
          evidenceRefs, attribution: clone(p.attribution || {}) };
        if (roles.length === refs.length && roles[0] === 'antecedent' && roles[1] === 'consequent' && refs.length === 2) {
          out.antecedentId = wbExpressionId.get(refs[0]) || refs[0];
          out.consequentId = wbExpressionId.get(refs[1]) || refs[1];
          if (p.antecedentInterpretation) out.antecedentInterpretation = p.antecedentInterpretation;
          if (p.conditionMetadata) out.conditionMetadata = {
            effect: p.conditionMetadata.effect || null, logicalStatus: p.conditionMetadata.logicalStatus || null,
            consequence: p.conditionMetadata.consequence || null,
            consequenceInterpretation: p.conditionMetadata.consequenceInterpretation || null,
            consequentClaimId: p.conditionMetadata.nativeConsequentClaimId || null };
        } else {
          out.operandIds = refs.map(ref => wbExpressionId.get(ref) || ref);
          if (p.disjunctionSemantics) out.disjunctionSemantics = p.disjunctionSemantics;
        }
        expressionsOut.push(out);
      }
    }

    const expressionOutIds = new Set(expressionsOut.map(x => x.id));
    const rootExpressionIds = [];
    for (const ref of arr(document.rootExpressionRefs)) {
      if (supported.has(ref) && expressionOutIds.has(wbExpressionId.get(ref))) rootExpressionIds.push(wbExpressionId.get(ref));
      else { partial.push(ref); diagnostics.push('Root ' + ref + ' could not be reconstructed natively.'); }
    }
    const relationsOut = [];
    for (const r of arr(document.expressionRelations)) {
      const from = wbExpressionId.get(r.sourceExpressionRef), to = wbExpressionId.get(r.targetExpressionRef);
      if (!from || !to || !expressionOutIds.has(from) || !expressionOutIds.has(to)) {
        partial.push(r.id); diagnostics.push('Relation ' + r.id + ' has an unsupported endpoint.'); continue;
      }
      relationsOut.push({ id: native?.relations?.find(x => opaqueId('relation', x.id) === r.id)?.id || r.id,
        type: r.type, sourceExpressionId: from, targetExpressionId: to,
        verification: r.nativeVerification || (r.verificationStatus === 'NOT_INDEPENDENTLY_VERIFIED' ? 'not_independently_verified' : 'unknown'),
        status: r.nativeStatus || undefined, note: r.note || '', evidenceRefs: arr(r.evidenceRefs).map(ref => wbEvidenceId.get(ref)).filter(Boolean),
        attribution: clone(r.attribution || {}) });
    }

    const unresolvedOut = [];
    for (const item of arr(document.unresolvedItems)) {
      const out = { id: native?.unresolvedItems?.find(x => opaqueId('unresolved', x.id) === item.id)?.id || item.id,
        status: String(item.nativeStatus || item.status || 'UNRESOLVED').toLowerCase(),
        reason: String(item.reason || 'Canonical unresolved item.'),
        surfaceText: String(item.surfaceText || '') };
      if (item.scopeRef && wbExpressionId.has(item.scopeRef)) out.scope = wbExpressionId.get(item.scopeRef);
      else if (item.scopeLabel) out.scope = item.scopeLabel;
      if (arr(item.evidenceRefs).length && wbEvidenceId.has(item.evidenceRefs[0])) out.evidenceRef = wbEvidenceId.get(item.evidenceRefs[0]);
      unresolvedOut.push(out);
    }

    const model = { profile: SOURCE_PROFILE, version: SOURCE_VERSION, canonical: true,
      compatibilityView: 'record.claims',
      source: { text: sourceText, language: primary.language || 'und', sourceId: nativeSourceId },
      entities: entitiesOut, mentions: mentionsOut, evidence: evidenceOut,
      expressions: expressionsOut, relations: relationsOut, rootExpressionIds,
      unresolvedItems: unresolvedOut, buildNotes: [...arr(document.mapping?.notes), ...diagnostics] };

    // Restore archival-only fields only as diagnostics/payload, not as semantic
    // model instructions or gates. In particular, requiresHumanReview is inert.
    const archivalNativeFields = native ? {
      acceptanceBoundary: clone(native.acceptanceBoundary || null)
    } : null;
    if (archivalNativeFields?.acceptanceBoundary) {
      diagnostics.push('Legacy acceptanceBoundary was retained as inert archival metadata; it was not applied as a validation gate.');
    }

    const validation = validateWorkbenchStructure(model);
    const unmappedRefs = [...new Set(partial)];
    const status = !validation.valid ? 'UNMAPPED' : (unmappedRefs.length || !snapshot.valid ? 'PARTIAL' : 'LOSSLESS');
    return { model, validation, report: {
      status, sourceProfile: document.profileId, targetProfile: SOURCE_PROFILE,
      targetVersion: SOURCE_VERSION, snapshot,
      restoredNativeSnapshot: !!native, archivalNativeFields,
      convertedCounts: { entities: entitiesOut.length, mentions: mentionsOut.length,
        evidence: evidenceOut.length, expressions: expressionsOut.length, relations: relationsOut.length,
        roots: rootExpressionIds.length, unresolvedItems: unresolvedOut.length },
      unmappedRefs, diagnostics: [...new Set(diagnostics)]
    } };
  }

  return { SOURCE_PROFILE, SOURCE_VERSION, NAMESPACE, contractToWorkbench,
    verifyNativeSnapshot, validateWorkbenchStructure, cpToUtf16, opaqueId };
});
