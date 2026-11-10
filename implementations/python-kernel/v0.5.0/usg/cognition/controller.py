from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from ..config import Config
from ..errors import BudgetExceeded, InvariantViolation
from ..storage.schema import WriterRole
from ..util import canonical_json


@dataclass(frozen=True)
class Task:
    id: int
    kind: str
    payload: dict
    attempts: int
    token: str


class TaskQueue:
    """Durable bounded queue; lease tokens fence out crashed/stale workers."""
    def __init__(self, db, capacity=1000):
        self.db, self.capacity = db, capacity

    def enqueue(self, key, kind, payload, priority=10, max_attempts=3):
        if kind not in {"INGEST", "LEARN", "AUDIT"} or not 1 <= max_attempts <= 10:
            raise InvariantViolation("invalid task", "SG-GOV-009")
        if type(priority) is not int or not 0<=priority<=100:raise ValueError('task priority')
        body = canonical_json(payload)
        if len(body) > 1_000_000:
            raise BudgetExceeded("task payload too large")
        with self.db.write(WriterRole.QUEUE) as t:
            existing = t.scalar("SELECT task_id FROM task_queue WHERE dedup_key=?", (key,))
            if existing is not None:
                return existing
            if t.scalar("SELECT COUNT(*) FROM task_queue WHERE state IN ('READY','RUNNING')") >= self.capacity:
                raise BudgetExceeded("task queue is full")
            return t.execute("INSERT INTO task_queue(dedup_key,kind,payload,state,priority,max_attempts,available_at,enqueued_at) VALUES(?,?,?,'READY',?,?,?,?)",
                             (key, kind, body, priority, max_attempts, self.db.clock.now(), self.db.clock.now())).lastrowid

    def claim(self, lease_seconds=120):
        if not 1 <= lease_seconds <= 3600:
            raise ValueError("lease out of bounds")
        now = self.db.clock.now()
        with self.db.write(WriterRole.QUEUE) as t:
            t.execute("UPDATE task_queue SET state=CASE WHEN attempts>=max_attempts THEN 'DEAD' ELSE 'READY' END,lease_token=NULL WHERE state='RUNNING' AND lease_until<=?", (now,))
            row = t.one("SELECT * FROM task_queue WHERE state='READY' AND available_at<=? ORDER BY priority-CAST((?-enqueued_at)/60 AS INTEGER),task_id LIMIT 1", (now,now))
            if row is None:
                return None
            token = uuid.uuid4().hex
            t.execute("UPDATE task_queue SET state='RUNNING',attempts=attempts+1,lease_until=?,lease_token=? WHERE task_id=?", (now+lease_seconds, token, row["task_id"]))
            return Task(row["task_id"], row["kind"], json.loads(row["payload"]), row["attempts"]+1, token)

    def renew(self, task, lease_seconds=120):
        if not 1<=lease_seconds<=3600:raise ValueError('lease out of bounds')
        now=self.db.clock.now()
        with self.db.write(WriterRole.QUEUE) as t:
            updated=t.execute("UPDATE task_queue SET lease_until=? WHERE task_id=? AND state='RUNNING' AND lease_token=? AND lease_until>?",(now+lease_seconds,task.id,task.token,now)).rowcount
            if not updated:raise InvariantViolation('stale worker lease','SG-GOV-007')
        return now+lease_seconds

    def finish(self, task, result=None, error=None):
        with self.db.write(WriterRole.QUEUE) as t:
            row = t.one("SELECT * FROM task_queue WHERE task_id=?", (task.id,))
            if not row or row["state"] != "RUNNING" or row["lease_token"] != task.token or row["lease_until"] <= self.db.clock.now():
                raise InvariantViolation("stale worker lease", "SG-GOV-007")
            state = "DONE" if error is None else "DEAD" if row["attempts"] >= row["max_attempts"] else "READY"
            t.execute("UPDATE task_queue SET state=?,result=?,error=?,lease_token=NULL,available_at=? WHERE task_id=?",
                      (state, canonical_json(result) if result is not None else None, error[:500] if error else None,
                       self.db.clock.now() + (min(300, 2**row["attempts"]) if error else 0), task.id))


class Workspace:
    def __init__(self, db, capacity=200):
        self.db, self.capacity = db, capacity

    def snapshot(self, key):
        with self.db.read() as r:
            row = r.one("SELECT * FROM workspace WHERE task_key=?", (key,))
        return (row["version"], json.loads(row["body"])) if row else (0, [])

    def commit(self, key, expected_version, references):
        if len(references) > self.capacity or any(not isinstance(x, str) or x.startswith("W:") for x in references):
            raise InvariantViolation("workspace accepts bounded persistent references only", "SG-GOV-007")
        with self.db.write(WriterRole.QUEUE) as t:
            current = t.scalar("SELECT version FROM workspace WHERE task_key=?", (key,), 0)
            if current != expected_version:
                raise InvariantViolation("stale workspace snapshot", "SG-GOV-007")
            t.execute("INSERT INTO workspace(task_key,version,body) VALUES(?,?,?) ON CONFLICT(task_key) DO UPDATE SET version=excluded.version,body=excluded.body",
                      (key, current+1, canonical_json(references)))
        return current+1


class ResourceGovernor:
    def __init__(self, config=None):
        self.config = config or Config()

    def plan(self, *, input_chars, free_ram_mb=1024, queued=0):
        if input_chars < 0 or free_ram_mb < 0 or queued < 0:raise ValueError('negative resource measurement')
        if input_chars > self.config["max_source_chars"] or queued >= 1000:
            return "DEFER"
        if free_ram_mb < 128:
            return "DEFER"
        if free_ram_mb < 512:
            return "RULES_ONLY"
        return "RULES_THEN_OPTIONAL_LOCAL"
