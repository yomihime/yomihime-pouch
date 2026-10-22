# Completely offline syntax preflight, no admin rights or network required.
$ErrorActionPreference = 'Stop'
$failed = $false
foreach ($file in @(Get-ChildItem -LiteralPath $PSScriptRoot -File -Filter '*.ps1' -Recurse)) {
    $tokens = $null
    $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$parseErrors) | Out-Null
    if ($parseErrors.Count -gt 0) {
        $failed = $true
        foreach ($err in $parseErrors) { Write-Error "Syntax: $($file.Name) line $($err.Extent.StartLineNumber): $($err.Message)" -ErrorAction Continue }
    } else { Write-Host "Syntax OK: $($file.Name)" }
}
if ($failed) { exit 1 }
Write-Host 'All PowerShell files parsed successfully.' -ForegroundColor Green
