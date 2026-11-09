"""Current semantic view: historical parses remain inspectable via view=all."""

CURRENT_ASSERTION = """a.lifecycle NOT IN ('DEFERRED','REJECTED','DEPRECATED') AND NOT EXISTS (
 SELECT 1 FROM evidence own_e JOIN candidate own_c ON own_c.candidate_id=own_e.candidate_id
 JOIN candidate newer ON newer.source_id=own_c.source_id AND newer.unit_start=own_c.unit_start
 AND newer.unit_end=own_c.unit_end AND newer.candidate_id>own_c.candidate_id
 WHERE own_e.evidence_id=a.evidence_id
)"""
