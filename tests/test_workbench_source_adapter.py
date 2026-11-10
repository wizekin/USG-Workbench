from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specifications" / "usg-sem-1.0.schema.json"
ADAPTER_SCRIPT = r"""
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', async () => {
  try {
    const adapter = require('./interoperability/workbench_adapter');
    const result = await adapter.workbenchToContract(JSON.parse(input));
    process.stdout.write(JSON.stringify(result.document));
  } catch (error) {
    process.stderr.write(error && error.stack ? error.stack : String(error));
    process.exitCode = 1;
  }
});
"""


class WorkbenchSourceAdapterSchemaTests(unittest.TestCase):
    def test_adapter_output_validates_against_usg_sem_1_schema(self):
        source = "😀 Alice needs the tool."
        model = {
            "profile": "USG-SR/0.5.1",
            "version": "0.5.1",
            "canonical": True,
            "source": {"text": source, "language": "en", "sourceId": "schema-fixture"},
            "entities": [{
                "id": "alice", "canonicalText": "Alice", "type": "unknown",
                "aliases": ["Alice"], "identityStatus": "provisional",
            }],
            "mentions": [{
                "id": "alice-mention", "entityId": "alice", "surfaceText": "Alice",
                "mentionType": "noun_phrase", "resolutionStatus": "linked",
                "sourceSpan": {"start": 3, "end": 8},
            }],
            "evidence": [{
                "id": "needs-evidence", "sourceText": source, "quote": "needs",
                "start": 9, "end": 14, "exactSourceMatch": True,
                "verificationMeaning": "source_alignment_only_not_semantic_entailment",
            }],
            "expressions": [{
                "id": "needs-expression", "type": "PREDICATION", "predicate": "NEEDS",
                "arguments": [{"role": "subject", "entityId": "alice", "mentionId": "alice-mention"}],
                "argumentRequirements": {"requiredRoles": ["subject", "object"], "missingRoles": ["object"]},
                "grammaticalTense": "present", "aspect": "simple",
                "temporalFrame": {"referenceTime": "present", "temporalAdverbials": []},
                "eventFrame": {"id": "needs-frame", "kind": "state", "predicate": "NEEDS", "participants": [], "attributes": []},
                "attribution": {"kind": "source_voice", "status": "source_asserted"},
                "provenance": {"method": "test", "ruleId": "TEST-RULE"},
                "completeness": {"status": "underspecified", "missingRoles": ["object"]},
                "evidenceRefs": ["needs-evidence"],
            }],
            "relations": [],
            "rootExpressionIds": ["needs-expression"],
            "unresolvedItems": [],
            "acceptanceBoundary": {
                "requiresHumanReview": True,
                "acceptedIntoKnowledgeBase": False,
                "objectiveTruthEstablished": False,
            },
            "buildNotes": [],
        }
        completed = subprocess.run(
            ["node", "-e", ADAPTER_SCRIPT],
            input=json.dumps(model, ensure_ascii=False),
            text=True,
            capture_output=True,
            cwd=ROOT,
            check=True,
        )
        document = json.loads(completed.stdout)
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
        self.assertEqual(
            [f"{'/'.join(map(str, error.path))}: {error.message}" for error in errors],
            [],
        )
        mention = document["mentions"][0]
        self.assertEqual(mention["sourceSpan"]["start"], 2)
        self.assertEqual(mention["sourceSpan"]["end"], 7)
        self.assertEqual(document["evidence"][0]["span"]["start"], 8)
        self.assertEqual(document["evidence"][0]["span"]["end"], 13)
        self.assertNotIn("acceptanceBoundary", document)
        self.assertTrue(
            document["extensions"]["org.usg.workbench.v0.5.4"]["nativeModel"]["acceptanceBoundary"]["requiresHumanReview"]
        )


if __name__ == "__main__":
    unittest.main()
