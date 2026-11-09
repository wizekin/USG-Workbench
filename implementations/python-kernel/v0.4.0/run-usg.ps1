# No packages, keys, model downloads or network access are required.
$ErrorActionPreference = 'Stop'
$usgCandidates = @()
if ($env:USG_PYTHON) { $usgCandidates += $env:USG_PYTHON }
$usgCandidates += (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
foreach ($usgName in @('python', 'python3')) {
    $usgCommand = Get-Command $usgName -ErrorAction SilentlyContinue
    if ($usgCommand) { $usgCandidates += $usgCommand.Source }
}
foreach ($usgCandidate in $usgCandidates) {
    if (Test-Path -LiteralPath $usgCandidate) {
        & $usgCandidate -c 'import sys; assert sys.version_info >= (3,11)' 2>$null
        if ($LASTEXITCODE -eq 0) {
            $env:PYTHONIOENCODING = 'utf-8'
            Push-Location $PSScriptRoot
            try { & $usgCandidate -m usg @args; $usgExit = $LASTEXITCODE }
            finally { Pop-Location }
            exit $usgExit
        }
    }
}
throw 'Python 3.11+ is required. Set USG_PYTHON to an installed Python executable.'
