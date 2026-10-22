# Consistent local backup of config/db while services are stopped.
param([switch]$LeaveStopped)
. (Join-Path $PSScriptRoot 'Common.ps1')
Assert-Host
Ensure-Dirs
$running = @($script:Services | Where-Object { (Has-Service $_) -and (Get-Service $_).Status -eq 'Running' })
$existing = @($script:Services | Where-Object { Has-Service $_ })
foreach ($service in $existing) {
    if ((Get-Service $service).Status -notin @('Running','Stopped')) { throw "Service in transitional/paused state: $service. Resolve state before backup." }
}
$target = Join-Path $script:Root ('Backups\snapshot-' + ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8)))
New-Item -ItemType Directory $target -Force | Out-Null
try {
    foreach ($service in $running) { Stop-Service $service -ErrorAction Stop }
    foreach ($service in $running) { (Get-Service $service).WaitForStatus('Stopped', [TimeSpan]::FromSeconds(40)) }
    $jobs = @(
        @{ Source="$script:Root\Emby\programdata"; Target="$target\Emby-programdata" },
        @{ Source="$script:Root\MetaTube\data"; Target="$target\MetaTube-data" }
    )
    foreach ($job in $jobs) {
        if (Test-Path $job.Source) {
            New-Item -ItemType Directory -Path $job.Target -Force | Out-Null
            & robocopy.exe $job.Source $job.Target /E /COPY:DAT /DCOPY:DAT /XJ /R:1 /W:1 /NP /NFL /NDL | Out-Null
            if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE): $($job.Source)" }
        }
    }
    if (Test-Path "$script:Root\versions.json") { Copy-Item "$script:Root\versions.json" "$target\versions.json" }
    Write-Host "Backup completed: $target" -ForegroundColor Green
    Write-Warning 'Backup is on the same disk. Copy snapshots to Synology or another storage for real protection.'
} finally {
    if (-not $LeaveStopped) {
        foreach ($service in $running) { Start-Service $service -ErrorAction Continue }
    }
}
