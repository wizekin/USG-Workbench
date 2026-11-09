@echo off
setlocal
cd /d "%~dp0\.."
echo USG Semantic Workbench v0.5.4 - automated test suite
node --check app.js || goto :failed
node --check server.js || goto :failed
node --check semantic-core.js || goto :failed
node --check semantic-composer.js || goto :failed
node --check tests\smoke_test.js || goto :failed
node --check tests\semantic_foundation_test.js || goto :failed
node --check tests\composition_test.js || goto :failed
node --check tests\app_composition_test.js || goto :failed
node --check tests\server_timeout_test.js || goto :failed
node tests\semantic_foundation_test.js || goto :failed
node tests\composition_test.js || goto :failed
node tests\app_composition_test.js
if errorlevel 1 exit /b 1
node tests\app_failure_audit_test.js || goto :failed
node tests\smoke_test.js || goto :failed
node tests\server_timeout_test.js || goto :failed
echo.
echo All automated tests passed.
exit /b 0
:failed
echo.
echo Test suite failed. Review the first failing command above.
exit /b 1
