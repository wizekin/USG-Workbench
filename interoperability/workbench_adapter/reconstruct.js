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
  const SUPPORTED_OPS = new Set(['PREDICATE_APP','HOLDS','NOT','MODAL','QUANTIFIER','CONNECTIVE']);
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
    if (model?.profile !== SOURCE_PROFILE) errors.push('Unexpected Workbench profile.');
    if (model?.version !== SOURCE_VERSION) errors.push('Unexpected Workbench version.');
    if (!model?.source || typeof model.source.text !== 'string' || typeof model.source.language !== 'string') {
      errors.push('Workbench source must contain exact text and a language tag.');
    }
    const sourceText = String(model?.source?.text || '');
    const unique = (items, label) => {
      const ids = new Set();
      for (const item of arr(items)) {
        if (!item?.id || ids.has(item.id)) errors.push('Missing or duplicate ' + label + ' id: ' + (item?.id || '(empty)'));
        ids.add(item?.id);
      }
      return ids;
    };
    const entityIds = unique(model.entities, 'entity');
    const mentionIds = unique(model.mentions, 'mention');
    const evidenceIds = unique(model.evidence, 'evidence');
    const unresolvedIds = unique(model.unresolvedItems, 'unresolved-item');
    const expressions = new Map();
    for (const x of arr(model.expressions)) {
      if (!x?.id || expressions.has(x.id)) errors.push('Missing or duplicate expression id: ' + (x?.id || '(empty)'));
      expressions.set(x?.id, x);
    }
    for (const entity of arr(model.entities)) {
      if (!String(entity.canonicalText || '').trim()) errors.push('Entity ' + entity.id + ' has no canonical text.');
    }
    for (const m of arr(model.mentions)) {
      if (m.entityId && !entityIds.has(m.entityId)) errors.push('Mention ' + m.id + ' has a missing entity.');
      if (m.antecedentEntityId && !entityIds.has(m.antecedentEntityId)) errors.push('Mention ' + m.id + ' has a missing antecedent entity.');
      if (!m.entityId && m.resolutionStatus !== 'unresolved') errors.push('Unlinked mention ' + m.id + ' must remain unresolved.');
      if (m.sourceSpan) {
        const { start, end } = m.sourceSpan;
        if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end < start || end > sourceText.length) {
          errors.push('Mention ' + m.id + ' has an invalid source span.');
        } else if (sourceText.slice(start, end) !== m.surfaceText) errors.push('Mention ' + m.id + ' span does not match its surface text.');
      }
    }
    for (const e of arr(model.evidence)) {
      if (!Number.isInteger(e.start) || !Number.isInteger(e.end) || e.start < 0 || e.end < e.start ||
          e.end > sourceText.length || sourceText.slice(e.start, e.end) !== e.quote) {
        errors.push('Evidence ' + e.id + ' is not aligned to source text.');
      }
    }
    for (const item of arr(model.unresolvedItems)) {
      if (!['unresolved','unsupported','ambiguous'].includes(item.status)) errors.push('Unresolved item ' + item.id + ' has invalid status.');
      if (item.evidenceRef && !evidenceIds.has(item.evidenceRef)) errors.push('Unresolved item ' + item.id + ' has missing evidence.');
    }
    const operatorTypes = new Set(['NEGATION','MODAL','QUANTIFIER','POLARITY','UNRESOLVED_SCOPE']);
    const modalOperators = new Set(['MIGHT','MAY','COULD','CAN','MUST','SHOULD','WILL','WOULD','POSSIBLE','NECESSARY','OBLIGATORY','POSSIBLE_OR_ABILITY','EXPECTED','UNKNOWN']);
    const quantifiers = new Set(['FORALL','EXISTS','EXACTLY_ONE','AT_LEAST_ONE','AT_MOST_ONE']);
    const connectives = new Set(['CONDITIONAL','EXCEPTION','WHEN','AND','OR','CONTRAST','CONCESSIVE']);
    for (const x of expressions.values()) {
      for (const ref of arr(x.evidenceRefs)) if (!evidenceIds.has(ref)) errors.push('Expression ' + x.id + ' references missing evidence ' + ref + '.');
      if (x.type === 'PREDICATION') {
        const args = arr(x.arguments);
        if (!x.predicate) errors.push('Predication ' + x.id + ' has no predicate.');
        if (args.filter(a => a.role === 'subject').length !== 1) errors.push('Predication ' + x.id + ' must have exactly one subject.');
        if (new Set(args.map(a => a.role)).size !== args.length) errors.push('Predication ' + x.id + ' has duplicate argument roles.');
        for (const a of args) {
          if (a.entityId && !entityIds.has(a.entityId)) errors.push('Argument in ' + x.id + ' references missing entity.');
          if (a.mentionId && !mentionIds.has(a.mentionId)) errors.push('Argument in ' + x.id + ' references missing mention.');
          if (a.bindingEntityId && !entityIds.has(a.bindingEntityId)) errors.push('Argument in ' + x.id + ' has missing binding entity.');
          if (a.variableId && !a.bindingEntityId) errors.push('Argument in ' + x.id + ' has a variable without a binding entity.');
        }
        const subject = args.find(a => a.role === 'subject');
        if (subject && !subject.entityId && (!subject.mentionId || !arr(model.mentions).some(m => m.id === subject.mentionId && m.resolutionStatus === 'unresolved'))) {
          errors.push('Predication ' + x.id + ' must have a linked subject or explicit unresolved subject mention.');
        }
        if (!['past','present','future','unknown'].includes(x.grammaticalTense)) errors.push('Predication ' + x.id + ' has invalid tense.');
        if (!['simple','progressive','perfect','habitual','unknown'].includes(x.aspect)) errors.push('Predication ' + x.id + ' has invalid aspect.');
        if (!x.eventFrame?.id || x.eventFrame.predicate !== x.predicate) errors.push('Predication ' + x.id + ' has missing or inconsistent event frame.');
        if (!x.temporalFrame || typeof x.temporalFrame.referenceTime !== 'string' || !Array.isArray(x.temporalFrame.temporalAdverbials)) {
          errors.push('Predication ' + x.id + ' has invalid temporal metadata.');
        }
        if (!['complete','underspecified','unresolved','not_applicable'].includes(x.completeness?.status) ||
            !Array.isArray(x.completeness?.missingRoles)) errors.push('Predication ' + x.id + ' has invalid completeness metadata.');
        for (const p of arr(x.eventFrame?.participants)) {
          if (p.entityId && !entityIds.has(p.entityId)) errors.push('Event frame ' + x.eventFrame.id + ' references missing participant.');
          if (p.bindingEntityId && !entityIds.has(p.bindingEntityId)) errors.push('Event frame ' + x.eventFrame.id + ' references missing binding entity.');
        }
      } else if (x.type === 'OPERATOR') {
        if (!operatorTypes.has(x.operatorType) || !x.operator) errors.push('Operator ' + x.id + ' has invalid operator metadata.');
        if (!expressions.has(x.scope?.targetId)) errors.push('Operator ' + x.id + ' has missing scope target.');
        if (x.operatorType === 'NEGATION' && x.operator !== 'NOT') errors.push('Negation ' + x.id + ' must use NOT.');
        if (x.operatorType === 'POLARITY' && x.operator !== 'UNKNOWN') errors.push('Unknown polarity ' + x.id + ' must use UNKNOWN.');
        if (x.operatorType === 'MODAL' && !modalOperators.has(x.operator)) errors.push('Modal ' + x.id + ' uses an unsupported operator.');
        if (x.operatorType === 'QUANTIFIER') {
          if (!quantifiers.has(x.operator) || !x.variable || !x.restrictor?.entityId || !entityIds.has(x.restrictor.entityId)) {
            errors.push('Quantifier ' + x.id + ' lacks a supported operator, variable, or restrictor.');
          }
          const binding = x.variableBinding;
          if (!binding?.variable || binding.variable !== x.variable || !binding.role ||
              binding.restrictorEntityId !== x.restrictor?.entityId) errors.push('Quantifier ' + x.id + ' has inconsistent variable binding.');
          let cursor = x.scope?.targetId, bound = null;
          const seen = new Set();
          while (cursor && !seen.has(cursor)) {
            seen.add(cursor);
            const child = expressions.get(cursor);
            if (!child) break;
            if (child.type === 'PREDICATION') { bound = arr(child.arguments).find(a => a.role === binding?.role); break; }
            if (child.type === 'OPERATOR') cursor = child.scope?.targetId;
            else if (child.type === 'CONNECTIVE') cursor = child.consequentId || arr(child.operandIds)[0];
            else break;
          }
          if (!bound || bound.variableId !== x.variable || bound.bindingEntityId !== x.restrictor?.entityId) {
            errors.push('Quantifier ' + x.id + ' is not bound to the corresponding predication argument.');
          }
        }
      } else if (x.type === 'CONNECTIVE') {
        const refs = x.antecedentId && x.consequentId ? [x.antecedentId,x.consequentId] : arr(x.operandIds);
        if (!connectives.has(x.connective)) errors.push('Connective ' + x.id + ' uses unsupported type.');
        if (refs.length < 2 || refs.some(ref => !expressions.has(ref))) errors.push('Connective ' + x.id + ' has invalid operands.');
        if (['CONDITIONAL','EXCEPTION','CONCESSIVE'].includes(x.connective) && !(x.antecedentId && x.consequentId)) {
          errors.push('Directed connective ' + x.id + ' lacks antecedent/consequent roles.');
        }
        const expectedStatus = { CONDITIONAL:'conditional_not_asserted', EXCEPTION:'exception_relation_asserted',
          WHEN:'when_clause_not_asserted', CONCESSIVE:'concessive_relation_asserted' }[x.connective];
        if (expectedStatus && x.logicalStatus !== expectedStatus) errors.push('Connective ' + x.id + ' has inconsistent logical status.');
        const marker = String(x.marker || '').toLowerCase();
        const expectedType = marker === 'unless' ? 'EXCEPTION' : marker === 'when' ? 'WHEN' : marker === 'if' ? 'CONDITIONAL' : null;
        if (expectedType && x.connective !== expectedType) errors.push('Connective ' + x.id + ' marker/type mismatch.');
        if (x.connective === 'EXCEPTION') {
          const ant = expressions.get(x.antecedentId);
          if (!ant || ant.type !== 'OPERATOR' || ant.operatorType !== 'NEGATION' || ant.operator !== 'NOT') {
            errors.push('EXCEPTION ' + x.id + ' must retain NOT(P) as its antecedent.');
          }
        }
        if (x.connective === 'CONCESSIVE' && !arr(x.evidenceRefs).length) errors.push('CONCESSIVE ' + x.id + ' requires evidence.');
      } else {
        errors.push('Expression ' + x.id + ' has unsupported Workbench expression type.');
      }
    }
    const childRefs = x => x.type === 'OPERATOR' ? [x.scope?.targetId].filter(Boolean) :
      x.type === 'CONNECTIVE' ? (x.antecedentId && x.consequentId ? [x.antecedentId,x.consequentId] : arr(x.operandIds)) : [];
    for (const x of expressions.values()) for (const ref of childRefs(x)) {
      if (!expressions.has(ref)) errors.push('Expression ' + x.id + ' references missing child ' + ref + '.');
    }
    const roots = arr(model.rootExpressionIds);
    if (new Set(roots).size !== roots.length) errors.push('Duplicate root expression IDs.');
    if (expressions.size && !roots.length) errors.push('Expressions exist but no roots are declared.');
    const visiting = new Set(), visited = new Set();
    function visit(id) {
      if (visiting.has(id)) { errors.push('Expression cycle detected at ' + id); return; }
      if (visited.has(id)) return;
      const x = expressions.get(id); if (!x) return;
      visiting.add(id); for (const ref of childRefs(x)) visit(ref); visiting.delete(id); visited.add(id);
    }
    for (const id of roots) {
      if (!expressions.has(id)) errors.push('Missing root expression ' + id + '.');
      else visit(id);
    }
    if (visited.size !== expressions.size) errors.push('One or more expressions are unreachable from declared roots.');
    const relationIds = unique(model.relations, 'relation');
    const relationTypes = new Set(['CAUSE','CONTRADICTS','SUPPORTS','ATTACKS','RELATED_TO']);
    for (const r of arr(model.relations)) {
      if (!relationTypes.has(r.type)) errors.push('Relation ' + r.id + ' has unsupported type.');
      if (!expressions.has(r.sourceExpressionId) || !expressions.has(r.targetExpressionId)) errors.push('Relation ' + r.id + ' has missing expression endpoint.');
      for (const ref of arr(r.evidenceRefs)) if (!evidenceIds.has(ref)) errors.push('Relation ' + r.id + ' has missing evidence.');
    }
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
      if (!supported.has(x.id) && !['REF','UNRESOLVED_REF'].includes(x.op)) {
        partial.push(x.id); diagnostics.push('Expression ' + x.id + ' has no exact Workbench-native constructor mapping.');
      }
    }

    // Resolve expression IDs before assembling records; preserve native IDs only
    // when carried explicitly by the canonical projection.
    for (const x of expressions.values()) {
      if (x.op === 'HOLDS' && arr(x.operandRefs).length === 1) {
        const child = expressions.get(x.operandRefs[0]);
        if (child?.op === 'PREDICATE_APP') {
          wbExpressionId.set(x.id, nativeId(child, nativeId(x, x.id)));
          continue;
        }
      }
      wbExpressionId.set(x.id, nativeId(x, x.id));
    }
    const expressionsOut = [];
    for (const x of expressions.values()) {
      if (!supported.has(x.id)) continue;
      const outId = wbExpressionId.get(x.id);
      const refs = arr(x.operandRefs);
      const evidenceRefs = arr(x.params?.evidenceRefs).map(ref => wbEvidenceId.get(ref)).filter(Boolean);
      // HOLDS is the canonical SIT → PROP boundary wrapper. It has no separate
      // Workbench expression record; its child PREDICATION is the native node.
      if (x.op === 'HOLDS') continue;
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
          completeness: clone(x.params?.completeness || { status: 'unresolved', missingRoles: [] }),
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
        if (p.force) out.force = p.nativeForce || p.force;
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

    // Canonical-only records have no exact Workbench 0.5.1 native fields.
    for (const ref of arr(document.mapping?.unmappedRefs)) partial.push(ref);
    for (const collection of ['assertions','contexts','derivations']) {
      for (const item of arr(document[collection])) partial.push(item.id || collection);
    }
    for (const collection of ['concepts','frames','roles','relations']) {
      for (const item of arr(document.definitions?.[collection])) partial.push(item.id || collection);
    }
    for (const source of arr(document.sources)) {
      if (source.id !== document.primarySourceRef) partial.push(source.id);
      if (source.id === document.primarySourceRef &&
          (source.uri || source.anchor || (source.sourceType && source.sourceType !== 'USER_INPUT') ||
           (source.trustTier && source.trustTier !== 'UNKNOWN') ||
           (source.sensitivity && source.sensitivity !== 'UNKNOWN'))) partial.push(source.id);
    }
    for (const expression of expressions.values()) {
      if (arr(expression.annotations?.spans).length || arr(expression.annotations?.ruleIds).length ||
          Object.keys(expression.annotations?.languageFeatures || {}).length) partial.push(expression.id);
    }
    const model = { profile: SOURCE_PROFILE, version: SOURCE_VERSION, canonical: true,
      compatibilityView: 'record.claims',
      source: { text: sourceText, language: primary.language || 'und', sourceId: nativeSourceId },
      entities: entitiesOut, mentions: mentionsOut, evidence: evidenceOut,
      expressions: expressionsOut, relations: relationsOut, rootExpressionIds,
      unresolvedItems: unresolvedOut,
      buildNotes: [...(native ? arr(native.buildNotes) : []), ...arr(document.mapping?.notes), ...diagnostics] };

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
