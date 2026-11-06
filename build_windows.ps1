# build_windows.ps1 - BolgeForge native Windows build + test (no make required).
#
# Usage:
#   .\build_windows.ps1            # build mb_ref.exe + run the make-test equivalent
#   .\build_windows.ps1 -Rebuild   # + tools/resynthesize.py all --check (~5 min)
#   .\build_windows.ps1 -Clean     # remove mb_ref.exe and the .build solver dll
#   .\build_windows.ps1 -Help
#
# Requirements: a C compiler (MinGW-w64 gcc recommended, or cc/clang) and
# Python 3.10+ on PATH. On Windows `python3` is usually a Microsoft Store
# stub, so this script probes `py -3` first, then `python`, then `python3`.
# It never uses `make`, `rm`, `/tmp` or the `python3` command name.
[CmdletBinding()]
param(
    [switch]$Rebuild,
    [switch]$Clean,
    [switch]$Help
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

if ($Help) {
    Get-Content -LiteralPath "$PSScriptRoot\build_windows.ps1" -TotalCount 14
    return
}

function Find-Exe([string[]]$Names) {
    foreach ($n in $Names) {
        $cmd = Get-Command $n -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    return $null
}

function Test-PythonCmd([string]$Exe, [string[]]$PrefixArgs) {
    try {
        $allArgs = @($PrefixArgs) + @('--version')
        $out = & $Exe @allArgs 2>&1 | Out-String
        return ($out -match 'Python 3\.\d+')
    } catch {
        return $false
    }
}

function Invoke-Python([string[]]$MyArgs) {
    $allArgs = @($script:PythonArgs) + @($MyArgs)
    & $script:PythonExe @allArgs
}

$cc = Find-Exe @('gcc', 'cc', 'clang')
if (-not $cc) {
    Write-Error 'No C compiler found. Install MinGW-w64 gcc (e.g. via WinLibs or TDM-GCC) and put it on PATH, then retry.'
    exit 1
}
Write-Host "CC: $cc"

$script:PythonExe = $null
$script:PythonArgs = @()
$pyExe = Find-Exe @('py')
if ($pyExe -and (Test-PythonCmd $pyExe @('-3'))) { $script:PythonExe = $pyExe; $script:PythonArgs = @('-3') }
if (-not $script:PythonExe) {
    foreach ($cand in @('python', 'python3')) {
        $exe = Find-Exe @($cand)
        if ($exe -and (Test-PythonCmd $exe @())) { $script:PythonExe = $exe; $script:PythonArgs = @(); break }
    }
}
if (-not $script:PythonExe) {
    Write-Error 'No working Python 3 found (tried py -3, python, python3). Install Python 3.10+ from python.org and retry.'
    exit 1
}
Write-Host "Python: $script:PythonExe $($script:PythonArgs -join ' ')"
Invoke-Python @('--version')

$mbRef = Join-Path $PSScriptRoot 'mb_ref.exe'
$env:MB_REF = $mbRef

if ($Clean) {
    foreach ($f in @($mbRef, (Join-Path $PSScriptRoot '.build\sp_solver.dll'))) {
        if (Test-Path -LiteralPath $f) { Remove-Item -LiteralPath $f -Force; Write-Host "removed $f" }
    }
    return
}

Write-Host '--- build mb_ref.exe ---'
& $cc -O2 -Wall -o $mbRef (Join-Path $PSScriptRoot 'oracle\mb_ref.c')
if ($LASTEXITCODE -ne 0) { Write-Error 'gcc failed'; exit 1 }
if (-not (Test-Path -LiteralPath $mbRef)) { Write-Error 'mb_ref.exe was not produced'; exit 1 }
Write-Host "built $mbRef"

function Run-Step([string]$Name, [scriptblock]$Body) {
    Write-Host "--- $Name ---"
    & $Body
    if ($LASTEXITCODE -ne 0) { Write-Error "$Name FAILED (exit $LASTEXITCODE)"; exit 1 }
}

Run-Step 'test-oracle (52 tests)' { Invoke-Python @('-m', 'unittest', 'discover', '-s', 'tests', '-v') }
Run-Step 'test-corpus'            { Invoke-Python @('test_corpus.py') }
Run-Step 'test-compressed'        { Invoke-Python @('tools\test_compressed.py') }
Run-Step 'test-quines'            { Invoke-Python @('tools\test_quines.py') }
Run-Step 'test-independent'       { Invoke-Python @('tools\test_independent.py') }
Run-Step 'compact-cat --check'    { Invoke-Python @('tools\build_compact_cat.py', '--check') }

if ($Rebuild) {
    Run-Step 'test-rebuild (~5 min)' { Invoke-Python @('tools\resynthesize.py', 'all', '--check') }
}

Write-Host 'ALL WINDOWS CHECKS PASSED'
