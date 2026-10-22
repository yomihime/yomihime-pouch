# Dedicated interactive installer. Run only on the target PC.
param([switch]$Elevated, [string]$InstallDir)
$ErrorActionPreference = 'Stop'
$exitCode = 1
$transcribing = $false
$logPath = $null
try {
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        if ($Elevated) { throw 'Administrator rights were not granted. Run Start-Install.cmd as administrator.' }
        Write-Host 'Requesting administrator access. Installation output appears in the new window.'
        $launchArguments = @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"{0}"' -f $PSCommandPath), '-Elevated'
        )
        if ($InstallDir) {
            if ($InstallDir.Contains('"') -or $InstallDir -match '[\r\n]') { throw 'Invalid installation path argument.' }
            $launchArguments += @('-InstallDir', ('"{0}"' -f $InstallDir.TrimEnd('\')))
        }
        $process = Start-Process -FilePath "$PSHOME\powershell.exe" -Verb RunAs -Wait -PassThru -ArgumentList $launchArguments
        $exitCode = $process.ExitCode
    } else {
        # Store diagnostic output outside source and deployment data, even if D: is absent.
        $logDirectory = Join-Path ([IO.Path]::GetTempPath()) 'MediaStack-InstallerLogs'
        New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
        $logPath = Join-Path $logDirectory ('install-' + [Guid]::NewGuid().ToString('N') + '.log')
        Start-Transcript -LiteralPath $logPath -ErrorAction Stop | Out-Null
        $transcribing = $true
        Write-Host "Installer source: $PSScriptRoot"
        Write-Host 'Target: THIS COMPUTER. Choose the deployment directory in the next step.' -ForegroundColor Cyan
        Write-Host "Installation log: $logPath"
        # Only parse this installation path; unrelated maintenance scripts do not block installation.
        foreach ($name in @('Start-Install.ps1', 'Install.ps1', 'Install-Recovery.ps1', 'Common.ps1')) {
            $path = Join-Path $PSScriptRoot $name
            if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required installer file missing: $path" }
            $tokens = $null
            $parseErrors = $null
            [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$parseErrors) | Out-Null
            if ($parseErrors.Count -gt 0) {
                throw ("Syntax error in {0}: {1}" -f $name, (($parseErrors | ForEach-Object { $_.Message }) -join '; '))
            }
        }
        & (Join-Path $PSScriptRoot 'Install.ps1') -InstallDir $InstallDir
        $exitCode = 0
    }
} catch {
    Write-Host 'INSTALLATION FAILED' -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host $_.InvocationInfo.PositionMessage
    Write-Host 'Existing data has not been automatically cleaned up. Keep the deployment directory when retrying.'
    $exitCode = 1
} finally {
    if ($transcribing) {
        try { Stop-Transcript | Out-Null } catch { Write-Warning 'Unable to close installation transcript.' }
        Write-Host "Installation log: $logPath"
    }
    # The elevated console must remain visible until the user has read/copied the actual error.
    if ($Elevated) { $null = Read-Host 'Press Enter to close this installation window' }
}
exit $exitCode
