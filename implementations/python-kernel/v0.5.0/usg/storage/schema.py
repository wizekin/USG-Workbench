"""SQLite schema (spec Part 11 §11.3), delivered as ordered migrations so each
implementation part adds its own tables. Also declares the *sole-writer table
ownership* map (SG-GOV-008): every table is writable only by the writer role(s)
that own it, enforced in code by ``WriteTxn``.
"""

from __future__ import annotations

from enum import Enum


class WriterRole(str, Enum):
    REGISTRY = "REGISTRY"  # identity: ids, mappings
    PROMOTION = "PROMOTION"  # authoritative dictionary / trusted instances
    CANDIDATE_STORE = "CANDIDATE_STORE"  # provisional records, candidates
    PROVENANCE = "PROVENANCE"  # sources, spans, certificates, evidence (append-only)
    HISTORY = "HISTORY"  # process history, ingest ledger (append-only)
    RELEASE = "RELEASE"  # rulebook, sealed manifest, meta (install-time only)
    CACHE = "CACHE"  # derived, regenerable data
    QUEUE = "QUEUE"  # durable task queue
    LEDGER = "LEDGER"  # big-model budget ledger
    CALIBRATOR = "CALIBRATOR"  # automatic constant calibration records
    EVALUATION = "EVALUATION"  # epistemic status changes (evaluation process only)
    AUDIT = "AUDIT"  # hash-chained audit log


MIGRATION_1_CORE = """
CREATE TABLE meta (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
) STRICT;

CREATE TABLE schema_migration (
  version    INTEGER PRIMARY KEY,
  name       TEXT NOT NULL,
  applied_at REAL NOT NULL
) STRICT;

-- identity ------------------------------------------------------------------
CREATE TABLE id_sequence (
  space   TEXT PRIMARY KEY,
  next_id INTEGER NOT NULL CHECK (next_id > 0)
) STRICT;

CREATE TABLE registry_entry (
  space            TEXT    NOT NULL,
  id               INTEGER NOT NULL CHECK (id > 0),
  record_kind      TEXT    NOT NULL,
  sem_kind         TEXT,
  status           TEXT    NOT NULL,
  version          INTEGER NOT NULL CHECK (version >= 1),
  primary_domain   INTEGER,
  tombstone        INTEGER NOT NULL DEFAULT 0 CHECK (tombstone IN (0,1)),
  replaced_by      TEXT,
  tombstone_reason TEXT,
  PRIMARY KEY (space, id)
) STRICT, WITHOUT ROWID;

CREATE TABLE idempotency_key (
  key        TEXT PRIMARY KEY,
  space      TEXT NOT NULL,
  id         INTEGER NOT NULL,
  created_at REAL NOT NULL
) STRICT;

-- audit: append-only, hash chained (SG-FND-006, SG-SEC-009) ---------------------
CREATE TABLE audit_log (
  seq        INTEGER PRIMARY KEY AUTOINCREMENT,
  at         REAL    NOT NULL,
  actor      TEXT    NOT NULL,
  event      TEXT    NOT NULL,
  ref        TEXT    NOT NULL,
  detail     TEXT    NOT NULL DEFAULT '',
  prev_hash  TEXT    NOT NULL,
  entry_hash TEXT    NOT NULL
) STRICT;
CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;

-- sealed code/data manifest (replaces out-of-band human release; SG-FND-005) ----
CREATE TABLE sealed_manifest (
  name      TEXT PRIMARY KEY,
  kind      TEXT NOT NULL,
  sha256    TEXT NOT NULL,
  sealed_at REAL NOT NULL
) STRICT;

-- big-model budget ledger (tiny free-plan quotas) ------------------------------
CREATE TABLE model_budget_ledger (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  at            REAL    NOT NULL,
  backend       TEXT    NOT NULL,
  task_type     TEXT    NOT NULL,
  status        TEXT    NOT NULL CHECK (status IN ('RESERVED','OK','FAILED')),
  input_tokens  INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  digest_hash   TEXT,
  detail        TEXT    NOT NULL DEFAULT ''
) STRICT;
CREATE INDEX ledger_by_time ON model_budget_ledger(at);
CREATE INDEX ledger_by_digest ON model_budget_ledger(digest_hash);

CREATE TABLE model_breaker (
  backend              TEXT PRIMARY KEY,
  consecutive_failures INTEGER NOT NULL,
  cooldown_until       REAL NOT NULL
) STRICT;

-- automatic calibration of the constants register -----------------------------
CREATE TABLE constant_calibration (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  at        REAL NOT NULL,
  name      TEXT NOT NULL,
  old_value TEXT NOT NULL,
  new_value TEXT NOT NULL,
  run_id    TEXT NOT NULL,
  evidence  TEXT NOT NULL DEFAULT ''
) STRICT;
"""


MIGRATION_2_DICTIONARY = """
CREATE TABLE domain (
  domain_id     INTEGER PRIMARY KEY,
  name          TEXT NOT NULL UNIQUE,
  parent_domain INTEGER,
  status        TEXT NOT NULL DEFAULT 'ACTIVE'
) STRICT;

-- sources are immutable once registered (spec Part 2 §2.12) ---------------------
CREATE TABLE source (
  source_id   INTEGER PRIMARY KEY,
  type        TEXT NOT NULL,
  language    TEXT NOT NULL,
  text_hash   TEXT NOT NULL,
  anchor      TEXT CHECK (anchor IS NULL OR json_valid(anchor)),
  trust_tier  TEXT NOT NULL CHECK (trust_tier IN ('QUARANTINE','STANDARD','TRUSTED')),
  sensitivity TEXT NOT NULL CHECK (sensitivity IN ('PUBLIC','INTERNAL','SENSITIVE')),
  genre       TEXT,
  uri         TEXT,
  stored_text BLOB NOT NULL,
  text_codec  TEXT NOT NULL,
  text_len    INTEGER NOT NULL CHECK (text_len > 0),
  created_at  REAL NOT NULL
) STRICT;
CREATE INDEX source_by_hash ON source(text_hash);
CREATE TRIGGER source_immutable BEFORE UPDATE OF type, language, text_hash, anchor, stored_text, text_codec, text_len ON source
BEGIN SELECT RAISE(ABORT, 'source text is immutable'); END;
CREATE TRIGGER source_no_delete BEFORE DELETE ON source
BEGIN SELECT RAISE(ABORT, 'sources are never deleted'); END;

-- dictionary: only PROMOTED records live here --------------------------------------
CREATE TABLE concept (
  concept_id          INTEGER PRIMARY KEY,
  sem_kind            TEXT NOT NULL,
  canonical_label     TEXT NOT NULL,
  definition_complete INTEGER NOT NULL CHECK (definition_complete IN (0,1)),
  lifecycle           TEXT NOT NULL,
  version             INTEGER NOT NULL CHECK (version >= 1),
  grammar_version     TEXT NOT NULL,
  ontology_release    TEXT NOT NULL,
  origin              TEXT NOT NULL,
  value_domain        INTEGER REFERENCES concept(concept_id),
  doc                 TEXT NOT NULL DEFAULT ''
) STRICT;
CREATE INDEX concept_by_label ON concept(canonical_label);

CREATE TABLE concept_domain (
  concept_id INTEGER NOT NULL REFERENCES concept(concept_id),
  domain_id  INTEGER NOT NULL REFERENCES domain(domain_id),
  is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0,1)),
  PRIMARY KEY (concept_id, domain_id)
) STRICT, WITHOUT ROWID;

CREATE TABLE concept_definition (
  definition_id INTEGER PRIMARY KEY,
  concept_id    INTEGER NOT NULL REFERENCES concept(concept_id),
  def_version   INTEGER NOT NULL CHECK (def_version >= 1),
  scope         TEXT NOT NULL,
  valid_from    TEXT NOT NULL,
  superseded_by INTEGER REFERENCES concept_definition(definition_id),
  content_hash  TEXT NOT NULL,
  UNIQUE (concept_id, def_version, scope)
) STRICT;

CREATE TABLE definition_constraint (
  constraint_id INTEGER PRIMARY KEY,
  definition_id INTEGER NOT NULL REFERENCES concept_definition(definition_id),
  class         TEXT NOT NULL CHECK (class IN ('ESSENTIAL','TYPICAL','CONTINGENT','CONTEXTUAL')),
  provenance    TEXT NOT NULL CHECK (provenance IN ('DEFINITIONAL','EMPIRICAL','ASSUMED')),
  expr          TEXT NOT NULL CHECK (json_valid(expr)),
  evidence_id   INTEGER
) STRICT;

CREATE TABLE relation_def (
  relation_id INTEGER PRIMARY KEY,
  name        TEXT NOT NULL UNIQUE,
  category    TEXT NOT NULL CHECK (category IN ('LOGICAL','ASSOCIATIVE','EPISTEMIC')),
  body        TEXT NOT NULL CHECK (json_valid(body)),
  version     INTEGER NOT NULL CHECK (version >= 1),
  status      TEXT NOT NULL
) STRICT;

-- sparse typed graph; weights only with a recorded scoring model (SG-KNW-002) ------
CREATE TABLE relation_edge (
  src_id       INTEGER NOT NULL,
  relation_id  INTEGER NOT NULL REFERENCES relation_def(relation_id),
  tgt_id       INTEGER NOT NULL,
  domain_id    INTEGER NOT NULL REFERENCES domain(domain_id),
  xdom         INTEGER NOT NULL DEFAULT 0 CHECK (xdom IN (0,1)),
  qualifiers   TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(qualifiers)),
  weight       REAL,
  weight_model TEXT,
  assertion_id INTEGER,
  status       TEXT NOT NULL DEFAULT 'ACTIVE',
  PRIMARY KEY (src_id, relation_id, tgt_id, domain_id),
  CHECK (weight IS NULL OR weight_model IS NOT NULL)
) STRICT, WITHOUT ROWID;
CREATE INDEX edge_by_target ON relation_edge(tgt_id, relation_id);

CREATE TABLE frame_def (
  frame_id       INTEGER NOT NULL,
  frame_version  INTEGER NOT NULL CHECK (frame_version >= 1),
  name           TEXT NOT NULL,
  layer          INTEGER NOT NULL CHECK (layer BETWEEN 1 AND 3),
  authority      TEXT NOT NULL CHECK (authority IN ('GRAMMAR','DOMAIN')),
  situation_kind TEXT NOT NULL,
  abstract       INTEGER NOT NULL CHECK (abstract IN (0,1)),
  kernel         INTEGER NOT NULL CHECK (kernel IN (0,1)),
  status         TEXT NOT NULL,
  content_hash   TEXT NOT NULL,
  n_roles        INTEGER NOT NULL,
  body           TEXT NOT NULL CHECK (json_valid(body)),
  PRIMARY KEY (frame_id, frame_version)
) STRICT, WITHOUT ROWID;
CREATE UNIQUE INDEX frame_by_name ON frame_def(name, frame_version);
CREATE TRIGGER frame_def_immutable BEFORE UPDATE OF name, layer, authority, abstract, content_hash, n_roles, body ON frame_def
BEGIN SELECT RAISE(ABORT, 'frame versions are immutable; propose a new version'); END;
CREATE TRIGGER frame_def_no_delete BEFORE DELETE ON frame_def
BEGIN SELECT RAISE(ABORT, 'frame versions are never deleted'); END;

CREATE TABLE frame_role (
  frame_id       INTEGER NOT NULL,
  frame_version  INTEGER NOT NULL,
  role_index     INTEGER NOT NULL CHECK (role_index >= 0),
  name           TEXT NOT NULL,
  tier           INTEGER NOT NULL CHECK (tier IN (1,2)),
  parent_role    TEXT,
  requiredness   TEXT NOT NULL CHECK (requiredness IN ('REQUIRED','OPTIONAL')),
  card_min       INTEGER NOT NULL,
  card_max       INTEGER NOT NULL,
  expected_kind  TEXT NOT NULL,
  expected_class INTEGER REFERENCES concept(concept_id),
  origin_frame   TEXT NOT NULL,
  PRIMARY KEY (frame_id, frame_version, role_index),
  UNIQUE (frame_id, frame_version, name),
  FOREIGN KEY (frame_id, frame_version) REFERENCES frame_def(frame_id, frame_version),
  CHECK (tier = 1 OR parent_role IS NOT NULL)
) STRICT, WITHOUT ROWID;

CREATE TABLE frame_parent (
  frame_id        INTEGER NOT NULL,
  frame_version   INTEGER NOT NULL,
  parent_frame_id INTEGER NOT NULL,
  parent_version  INTEGER NOT NULL,
  link_kind       TEXT NOT NULL CHECK (link_kind IN ('SPECIALIZES','STRUCTURAL_INSTANCE_OF')),
  role_map        TEXT NOT NULL CHECK (json_valid(role_map)),
  PRIMARY KEY (frame_id, frame_version, parent_frame_id),
  FOREIGN KEY (frame_id, frame_version) REFERENCES frame_def(frame_id, frame_version),
  FOREIGN KEY (parent_frame_id, parent_version) REFERENCES frame_def(frame_id, frame_version)
) STRICT, WITHOUT ROWID;

-- instances: provisional/candidate store (CANDIDATE_STORE writes) -------------------
CREATE TABLE referent (
  referent_id      INTEGER PRIMARY KEY,
  source_id        INTEGER NOT NULL REFERENCES source(source_id),
  sem_kind         TEXT NOT NULL,
  number           TEXT NOT NULL,
  cardinality      TEXT CHECK (cardinality IS NULL OR json_valid(cardinality)),
  genericity       TEXT NOT NULL,
  scope            TEXT NOT NULL,
  introduced_kind  TEXT NOT NULL,
  introduced_space TEXT,
  introduced_id    INTEGER,
  individual_ids   TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(individual_ids)),
  span_start       INTEGER,
  span_end         INTEGER,
  CHECK (introduced_kind = 'WORLD' OR introduced_id IS NOT NULL),
  CHECK (scope <> 'RESOLVED_INDIVIDUAL' OR individual_ids <> '[]')
) STRICT;

CREATE TABLE referent_class (
  referent_id   INTEGER NOT NULL REFERENCES referent(referent_id),
  concept_space TEXT NOT NULL CHECK (concept_space IN ('CONCEPT','P')),
  concept_id    INTEGER NOT NULL,
  PRIMARY KEY (referent_id, concept_space, concept_id)
) STRICT, WITHOUT ROWID;

CREATE TABLE frame_instance (
  instance_id    INTEGER PRIMARY KEY,
  frame_id       INTEGER NOT NULL,
  frame_version  INTEGER NOT NULL,
  source_id      INTEGER REFERENCES source(source_id),
  certificate_id INTEGER,
  FOREIGN KEY (frame_id, frame_version) REFERENCES frame_def(frame_id, frame_version)
) STRICT;

CREATE TABLE binding (
  instance_id  INTEGER NOT NULL REFERENCES frame_instance(instance_id),
  role_index   INTEGER NOT NULL,
  role_name    TEXT NOT NULL,
  ord          INTEGER NOT NULL DEFAULT 0,
  value_state  TEXT NOT NULL CHECK (value_state IN ('SPECIFIED','UNSPECIFIED','UNKNOWN','NOT_APPLICABLE','WITHHELD')),
  basis        TEXT CHECK (basis IS NULL OR basis IN ('EXPLICIT','GRAMMATICAL','BACKGROUND')),
  filler_kind  TEXT CHECK (filler_kind IS NULL OR filler_kind IN ('REFERENT','INSTANCE','EXPR','LITERAL','TIME','KIND_REF')),
  filler_space TEXT,
  filler_id    INTEGER,
  literal      TEXT CHECK (literal IS NULL OR json_valid(literal)),
  span_start   INTEGER,
  span_end     INTEGER,
  rule         TEXT,
  PRIMARY KEY (instance_id, role_index, ord),
  -- defence in depth: hole states never carry content, SPECIFIED always has a basis (no invented content)
  CHECK ((value_state = 'SPECIFIED') = (filler_kind IS NOT NULL)),
  CHECK ((value_state = 'SPECIFIED') = (basis IS NOT NULL))
) STRICT, WITHOUT ROWID;

CREATE TABLE assertion (
  assertion_id      INTEGER PRIMARY KEY,
  content_type      TEXT NOT NULL CHECK (content_type IN ('INSTANCE','NODE','EDGE','PROPERTY')),
  content_space     TEXT NOT NULL,
  content_id        INTEGER NOT NULL,
  origin            TEXT NOT NULL CHECK (origin IN ('SOURCE_TEXT','GRAMMATICAL','BACKGROUND_INFERENCE','IMPORTED_RESOURCE','CURATED')),
  epistemic_status  TEXT NOT NULL CHECK (epistemic_status IN ('SOURCE_ASSERTED','INFERRED','VERIFIED','DISPUTED','UNKNOWN')),
  commitment        TEXT NOT NULL CHECK (commitment IN ('AUTHOR','ATTRIBUTED','NONE')),
  attributed_space  TEXT,
  attributed_id     INTEGER,
  eval_context      TEXT NOT NULL,
  eval_context_name TEXT,
  definition_ref    TEXT,
  alt_group         INTEGER,
  source_id         INTEGER REFERENCES source(source_id),
  evidence_id       INTEGER,
  lifecycle         TEXT NOT NULL,
  grammar_version   TEXT NOT NULL,
  ontology_release  TEXT NOT NULL,
  CHECK (source_id IS NOT NULL OR origin IN ('IMPORTED_RESOURCE','CURATED')),                       -- I-08
  CHECK (origin <> 'BACKGROUND_INFERENCE' OR epistemic_status <> 'SOURCE_ASSERTED'),               -- SG-EVD-003
  CHECK (origin NOT IN ('SOURCE_TEXT','GRAMMATICAL') OR epistemic_status <> 'INFERRED'),
  CHECK (commitment <> 'ATTRIBUTED' OR attributed_id IS NOT NULL)
) STRICT;
CREATE INDEX assertion_by_content ON assertion(content_space, content_id);
CREATE INDEX assertion_by_source ON assertion(source_id);
CREATE INDEX assertion_by_status ON assertion(epistemic_status, lifecycle);
"""

# (version, name, DDL). Later parts of the implementation append migrations.
MIGRATIONS: list[tuple[int, str, str]] = [
    (1, "core", MIGRATION_1_CORE),
    (2, "dictionary_and_instances", MIGRATION_2_DICTIONARY),
]

# table -> roles allowed to INSERT/UPDATE/DELETE. Later migrations register more.
TABLE_OWNERS: dict[str, frozenset[WriterRole]] = {
    "meta": frozenset({WriterRole.RELEASE}),
    "schema_migration": frozenset({WriterRole.RELEASE}),
    "id_sequence": frozenset({WriterRole.REGISTRY}),
    "registry_entry": frozenset({WriterRole.REGISTRY}),
    "idempotency_key": frozenset({WriterRole.REGISTRY}),
    "audit_log": frozenset({WriterRole.AUDIT}),
    "sealed_manifest": frozenset({WriterRole.RELEASE}),
    "model_budget_ledger": frozenset({WriterRole.LEDGER}),
    "model_breaker": frozenset({WriterRole.LEDGER}),
    "constant_calibration": frozenset({WriterRole.CALIBRATOR}),
}
_DICT = frozenset({WriterRole.PROMOTION, WriterRole.RELEASE})
for _t in ("domain", "concept", "concept_domain", "concept_definition", "definition_constraint", "relation_def",
           "relation_edge", "frame_def", "frame_role", "frame_parent"):
    TABLE_OWNERS[_t] = _DICT
TABLE_OWNERS["source"] = frozenset({WriterRole.PROVENANCE})
for _t in ("referent", "referent_class", "frame_instance", "binding"):
    TABLE_OWNERS[_t] = frozenset({WriterRole.CANDIDATE_STORE})
TABLE_OWNERS["assertion"] = frozenset({WriterRole.CANDIDATE_STORE, WriterRole.EVALUATION, WriterRole.PROMOTION})


def register_migration(version: int, name: str, ddl: str, owners: dict[str, set[WriterRole] | frozenset[WriterRole]]) -> None:
    """Used by later implementation parts to add tables + ownership."""
    if any(v == version for v, _, _ in MIGRATIONS):
        return
    MIGRATIONS.append((version, name, ddl))
    MIGRATIONS.sort()
    for t, roles in owners.items():
        TABLE_OWNERS[t] = frozenset(roles)


register_migration(3, "unattended_runtime", """
CREATE TABLE candidate (
 candidate_id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL REFERENCES source(source_id),
 unit_start INTEGER NOT NULL, unit_end INTEGER NOT NULL, dedup_key TEXT NOT NULL UNIQUE,
 payload TEXT NOT NULL CHECK(json_valid(payload)), report TEXT NOT NULL CHECK(json_valid(report)),
 outcome TEXT NOT NULL CHECK(outcome IN ('RESOLVED','AMBIGUOUS','UNRESOLVED')),
 lifecycle TEXT NOT NULL, reason TEXT NOT NULL, created_at REAL NOT NULL,
 CHECK(unit_start>=0 AND unit_end>unit_start)
) STRICT;
CREATE TABLE evidence (
 evidence_id INTEGER PRIMARY KEY, candidate_id INTEGER NOT NULL REFERENCES candidate(candidate_id),
 body TEXT NOT NULL CHECK(json_valid(body)), content_hash TEXT NOT NULL
) STRICT;
CREATE TRIGGER evidence_no_update BEFORE UPDATE ON evidence BEGIN SELECT RAISE(ABORT,'immutable evidence'); END;
CREATE TRIGGER evidence_no_delete BEFORE DELETE ON evidence BEGIN SELECT RAISE(ABORT,'immutable evidence'); END;
CREATE TABLE expression (
 node_id INTEGER PRIMARY KEY, body TEXT NOT NULL CHECK(json_valid(body)), structural_hash TEXT NOT NULL,
 full_hash TEXT NOT NULL, grammar_version TEXT NOT NULL, ontology_release TEXT NOT NULL
) STRICT;
CREATE INDEX expression_by_hash ON expression(structural_hash);
CREATE TRIGGER expression_no_update BEFORE UPDATE ON expression BEGIN SELECT RAISE(ABORT,'immutable expression'); END;
CREATE TRIGGER expression_no_delete BEFORE DELETE ON expression BEGIN SELECT RAISE(ABORT,'immutable expression'); END;
CREATE TABLE claim_index (
 assertion_id INTEGER NOT NULL REFERENCES assertion(assertion_id), frame TEXT NOT NULL,
 role TEXT NOT NULL, referent_id INTEGER, label TEXT, concept TEXT,
 PRIMARY KEY(assertion_id,frame,role,referent_id)
) STRICT;
CREATE INDEX claims_frame ON claim_index(frame,role,label);
CREATE TABLE ingest_ledger (
 source_id INTEGER NOT NULL REFERENCES source(source_id), pipeline_version TEXT NOT NULL,
 unit_start INTEGER NOT NULL, unit_end INTEGER NOT NULL, candidate_id INTEGER NOT NULL REFERENCES candidate(candidate_id),
 PRIMARY KEY(source_id,pipeline_version,unit_start,unit_end)
) STRICT;
CREATE TABLE issue (
 code TEXT PRIMARY KEY, count INTEGER NOT NULL, last_seen REAL NOT NULL,
 risk_floor INTEGER NOT NULL DEFAULT 1 CHECK(risk_floor BETWEEN 1 AND 4)
) STRICT;
CREATE TABLE lexical_mapping (
 language TEXT NOT NULL, form TEXT NOT NULL, concept TEXT NOT NULL, sense TEXT NOT NULL,
 provenance TEXT NOT NULL, status TEXT NOT NULL, version INTEGER NOT NULL,
 PRIMARY KEY(language,form,concept,sense)
) STRICT;
CREATE TABLE provisional (
 provisional_id INTEGER PRIMARY KEY, language TEXT NOT NULL, form TEXT NOT NULL, context TEXT NOT NULL,
 expires_at REAL NOT NULL, status TEXT NOT NULL, UNIQUE(language,form,context)
) STRICT;
CREATE TABLE identity_mapping (
 mapping_id INTEGER PRIMARY KEY, left_id INTEGER NOT NULL REFERENCES concept(concept_id),
 right_id INTEGER NOT NULL REFERENCES concept(concept_id), scope TEXT NOT NULL,
 grade TEXT NOT NULL, status TEXT NOT NULL, certificate TEXT NOT NULL CHECK(json_valid(certificate)), version INTEGER NOT NULL,
 CHECK(left_id<>right_id)
) STRICT;
CREATE TABLE learning_candidate (
 candidate_id INTEGER PRIMARY KEY, signature TEXT NOT NULL UNIQUE, action TEXT NOT NULL,
 payload TEXT NOT NULL CHECK(json_valid(payload)), stage TEXT NOT NULL, veto TEXT,
 created_at REAL NOT NULL, expires_at REAL NOT NULL
) STRICT;
CREATE TABLE pattern_occurrence (
 signature TEXT NOT NULL, origin TEXT NOT NULL, source_id INTEGER NOT NULL REFERENCES source(source_id),
 candidate_id INTEGER NOT NULL REFERENCES candidate(candidate_id),
 PRIMARY KEY(signature,origin)
) STRICT;
CREATE TABLE promotion_bundle (
 bundle_id INTEGER PRIMARY KEY, candidate_id INTEGER NOT NULL REFERENCES learning_candidate(candidate_id),
 state TEXT NOT NULL CHECK(state IN ('CANARY','ACTIVE','ROLLED_BACK')),
 panel TEXT NOT NULL CHECK(json_valid(panel)), observations INTEGER NOT NULL DEFAULT 0,
 errors INTEGER NOT NULL DEFAULT 0, previous_bundle INTEGER REFERENCES promotion_bundle(bundle_id), created_at REAL NOT NULL
) STRICT;
CREATE TABLE bundle_dependency (
 bundle_id INTEGER NOT NULL REFERENCES promotion_bundle(bundle_id), dependency INTEGER NOT NULL REFERENCES promotion_bundle(bundle_id),
 PRIMARY KEY(bundle_id,dependency), CHECK(bundle_id<>dependency)
) STRICT;
CREATE TABLE task_queue (
 task_id INTEGER PRIMARY KEY AUTOINCREMENT, dedup_key TEXT NOT NULL UNIQUE, kind TEXT NOT NULL,
 payload TEXT NOT NULL CHECK(json_valid(payload)), state TEXT NOT NULL CHECK(state IN ('READY','RUNNING','DONE','DEAD')),
 priority INTEGER NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL,
 lease_until REAL NOT NULL DEFAULT 0, lease_token TEXT, available_at REAL NOT NULL, result TEXT, error TEXT
) STRICT;
CREATE INDEX task_ready ON task_queue(state,available_at,priority);
CREATE TABLE workspace (
 task_key TEXT PRIMARY KEY, version INTEGER NOT NULL, body TEXT NOT NULL CHECK(json_valid(body))
) STRICT;
CREATE TABLE process_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT, at REAL NOT NULL, task_key TEXT NOT NULL, event TEXT NOT NULL,
 body TEXT NOT NULL CHECK(json_valid(body))
) STRICT;
CREATE TRIGGER history_no_update BEFORE UPDATE ON process_history BEGIN SELECT RAISE(ABORT,'append-only history'); END;
CREATE TRIGGER history_no_delete BEFORE DELETE ON process_history BEGIN SELECT RAISE(ABORT,'append-only history'); END;
CREATE TABLE inference_cache (
 cache_key TEXT PRIMARY KEY, dependencies TEXT NOT NULL, body TEXT NOT NULL CHECK(json_valid(body)), created_at REAL NOT NULL
) STRICT;
CREATE TABLE benchmark_run (
 run_id TEXT PRIMARY KEY, at REAL NOT NULL, body TEXT NOT NULL CHECK(json_valid(body))
) STRICT;
""", {
 "candidate": {WriterRole.CANDIDATE_STORE}, "evidence": {WriterRole.PROVENANCE},
 "expression": {WriterRole.CANDIDATE_STORE}, "claim_index": {WriterRole.CANDIDATE_STORE},
 "ingest_ledger": {WriterRole.HISTORY}, "issue": {WriterRole.HISTORY},
 "lexical_mapping": {WriterRole.RELEASE, WriterRole.PROMOTION}, "provisional": {WriterRole.CANDIDATE_STORE},
 "identity_mapping": {WriterRole.REGISTRY}, "learning_candidate": {WriterRole.CANDIDATE_STORE, WriterRole.PROMOTION},
 "pattern_occurrence": {WriterRole.CANDIDATE_STORE}, "promotion_bundle": {WriterRole.PROMOTION},
 "bundle_dependency": {WriterRole.PROMOTION}, "task_queue": {WriterRole.QUEUE}, "workspace": {WriterRole.QUEUE},
 "process_history": {WriterRole.HISTORY}, "inference_cache": {WriterRole.CACHE}, "benchmark_run": {WriterRole.HISTORY},
})

register_migration(4, "general_rule_requests", """
CREATE TABLE general_rule_request (
 digest_hash TEXT PRIMARY KEY, digest TEXT NOT NULL CHECK(json_valid(digest)),
 state TEXT NOT NULL CHECK(state IN ('PENDING','DONE')), created_at REAL NOT NULL, candidate_id INTEGER
) STRICT;
""", {"general_rule_request": {WriterRole.HISTORY}})



register_migration(5, "definitions_context_calibration", """
CREATE TABLE definition_metadata (
 definition_id INTEGER PRIMARY KEY REFERENCES concept_definition(definition_id),
 complete INTEGER NOT NULL CHECK(complete IN (0,1)), content_hash TEXT NOT NULL
) STRICT;
CREATE TABLE conflict_cluster (
 cluster_hash TEXT NOT NULL, assertion_id INTEGER NOT NULL REFERENCES assertion(assertion_id),
 polarity INTEGER NOT NULL CHECK(polarity IN (0,1)), context TEXT NOT NULL,
 PRIMARY KEY(cluster_hash,assertion_id)
) STRICT, WITHOUT ROWID;
CREATE TABLE calibration_observation (
 observation_key TEXT PRIMARY KEY, category TEXT NOT NULL, confidence REAL NOT NULL CHECK(confidence>=0 AND confidence<=1),
 correct INTEGER NOT NULL CHECK(correct IN (0,1)), origin TEXT NOT NULL, at REAL NOT NULL
) STRICT;
CREATE TABLE semantic_hypothesis (
 hypothesis_id TEXT PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL CHECK(json_valid(body)),
 origins TEXT NOT NULL CHECK(json_valid(origins)), counterexamples TEXT NOT NULL CHECK(json_valid(counterexamples)),
 state TEXT NOT NULL CHECK(state IN ('SHADOW','REJECTED')), created_at REAL NOT NULL
) STRICT;
CREATE TRIGGER constraint_no_update BEFORE UPDATE ON definition_constraint
BEGIN SELECT RAISE(ABORT,'definition constraints are immutable'); END;
CREATE TRIGGER constraint_no_delete BEFORE DELETE ON definition_constraint
BEGIN SELECT RAISE(ABORT,'definition constraints are immutable'); END;
CREATE TRIGGER definition_immutable BEFORE UPDATE OF concept_id,def_version,scope,valid_from,content_hash ON concept_definition
BEGIN SELECT RAISE(ABORT,'definition versions are immutable'); END;
CREATE TRIGGER definition_no_delete BEFORE DELETE ON concept_definition
BEGIN SELECT RAISE(ABORT,'definition versions are retained'); END;
CREATE TRIGGER definition_metadata_no_update BEFORE UPDATE ON definition_metadata
BEGIN SELECT RAISE(ABORT,'definition metadata is immutable'); END;
CREATE TRIGGER definition_metadata_no_delete BEFORE DELETE ON definition_metadata
BEGIN SELECT RAISE(ABORT,'definition metadata is immutable'); END;
""", {"definition_metadata": {WriterRole.PROMOTION}, "conflict_cluster": {WriterRole.EVALUATION},
      "calibration_observation": {WriterRole.CALIBRATOR}, "semantic_hypothesis": {WriterRole.CANDIDATE_STORE}})

register_migration(6, "rollback_dependencies_and_queue_age", """
ALTER TABLE task_queue ADD COLUMN enqueued_at REAL NOT NULL DEFAULT 0;
UPDATE task_queue SET enqueued_at=available_at;
CREATE TABLE rule_claim_dependency (
 assertion_id INTEGER NOT NULL REFERENCES assertion(assertion_id), bundle_id INTEGER NOT NULL REFERENCES promotion_bundle(bundle_id),
 PRIMARY KEY(assertion_id,bundle_id)
) STRICT, WITHOUT ROWID;
CREATE TABLE canary_observation (
 bundle_id INTEGER NOT NULL REFERENCES promotion_bundle(bundle_id), observation_key TEXT NOT NULL,
 error INTEGER NOT NULL CHECK(error IN (0,1)), PRIMARY KEY(bundle_id,observation_key)
) STRICT, WITHOUT ROWID;
INSERT INTO meta(key,value) VALUES('installation_id',lower(hex(randomblob(16))));
""", {"rule_claim_dependency": {WriterRole.CANDIDATE_STORE}, "canary_observation": {WriterRole.PROMOTION}})

register_migration(7, "referent_usage_and_current_views", """
CREATE TABLE assertion_ref (
 assertion_id INTEGER NOT NULL REFERENCES assertion(assertion_id), referent_id INTEGER NOT NULL REFERENCES referent(referent_id),
 PRIMARY KEY(assertion_id,referent_id)
) STRICT, WITHOUT ROWID;
INSERT OR IGNORE INTO assertion_ref
 SELECT a.assertion_id,CAST(substr(j.value,10) AS INTEGER) FROM assertion a
 JOIN expression e ON a.content_space='NODE' AND a.content_id=e.node_id, json_tree(e.body) j
 WHERE j.key='ref' AND j.type='text' AND j.value GLOB 'REFERENT:[0-9]*';
CREATE INDEX candidate_unit_version ON candidate(source_id,unit_start,unit_end,candidate_id);
""", {"assertion_ref": {WriterRole.CANDIDATE_STORE}})
