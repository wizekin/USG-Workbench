#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "USG Semantic Workbench v0.5.4 - automated test suite"
node --check app.js
node --check server.js
node --check generation-correction.js
node --check semantic-core.js
node --check tests/smoke_test.js
node --check tests/semantic_foundation_test.js
node --check semantic-composer.js
node --check tests/composition_test.js
node --check tests/app_composition_test.js
node --check tests/app_failure_audit_test.js
node --check tests/server_timeout_test.js
node --check tests/generation_correction_test.js
node tests/semantic_foundation_test.js
node tests/composition_test.js
node tests/app_composition_test.js
node tests/app_failure_audit_test.js
node tests/smoke_test.js
node tests/server_timeout_test.js
node tests/generation_correction_test.js
