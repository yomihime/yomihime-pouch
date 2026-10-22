# Installs MediaStack; existing deployments require explicit y/N confirmation and a verified backup.
param([switch]$Upgrade, [string]$InstallDir)
. (Join-Path $PSScriptRoot 'Common.ps1')
. (Join-Path $PSScriptRoot 'Install-Recovery.ps1')
if ($Upgrade) { throw 'Use Update.ps1 to upgrade an installed stack.' }
if ([string]::IsNullOrWhiteSpace($InstallDir)) {
    $selected = Read-Host "部署目录（回车使用 $script:Root）"
    $InstallDir = if ([string]::IsNullOrWhiteSpace($selected)) { $script:Root } else { $selected }
}
$script:Root = Resolve-InstallDirectory -Path $InstallDir
Assert-Host
Write-Host "Deployment directory: $script:Root" -ForegroundColor Cyan
$existing = @()
foreach ($service in $script:Services) {
    if (Has-Service $service) { $existing += "Service: $service ($((Get-Service $service).Status))" }
}
foreach ($relative in @('Emby\system', 'Emby\programdata', 'MetaTube\bin', 'MetaTube\data')) {
    $path = Join-Path $script:Root $relative
    if (Test-Path -LiteralPath $path) {
        if (-not (Test-Path -LiteralPath $path -PathType Container)) { $existing += "Occupied path: $path" }
        elseif (@(Get-ChildItem -LiteralPath $path -Force).Count -gt 0) { $existing += "Non-empty directory: $path" }
    }
}
$reinstall = $existing.Count -gt 0
if ($reinstall) {
    if (-not (Confirm-Reinstallation -Existing $existing)) {
        Write-Host 'Installation cancelled. No deployment files or services changed.'
        return
    }
    Assert-ReinstallOwnership
}
$originalServices = @($script:Services | Where-Object { Has-Service $_ })
$stamp = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8)
$stage = Join-Path $script:Root "Staging\initial-$stamp"
if (-not $reinstall) {
    foreach ($port in @(8096,8080)) {
        if (@(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue).Count -gt 0) {
            throw "TCP port $port is already in use. Resolve conflict before installation."
        }
    }
}
Ensure-Dirs
$settings = @{ Root=$script:Root } | ConvertTo-Json
$settings | Set-Content -LiteralPath "$script:Root\Scripts\mediastack-settings.json" -Encoding UTF8
if ($PSScriptRoot -ine "$script:Root\Scripts") {
    try { $settings | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'mediastack-settings.json') -Encoding UTF8 }
    catch { Write-Warning "Unable to remember the directory in the source folder. Use $script:Root\Scripts for subsequent operations." }
}
New-Item -ItemType Directory $stage -Force | Out-Null

Write-Host 'Step 1/5: Official tools' -ForegroundColor Cyan
$null = Download-Tool 'https://www.7-zip.org/a/7zr.exe' "$script:Root\Tools\7zr.exe"
$nssmZip = Download-Tool 'https://nssm.cc/ci/nssm-2.24-101-g897c7ad.zip' "$script:Root\Downloads\nssm-2.24-101-g897c7ad.zip"
Extract-Zip $nssmZip (Join-Path $stage 'nssm')
$nssmFiles = @(Get-ChildItem (Join-Path $stage 'nssm') -Recurse -Filter nssm.exe -File | Where-Object { $_.Directory.Name -eq 'win64' })
if ($nssmFiles.Count -ne 1) { throw 'Cannot locate NSSM win64 binary.' }
# Existing NSSM may still be hosting a running service. Never overwrite it here.
if (-not (Test-Path "$script:Root\Tools\nssm.exe")) {
    Copy-Item $nssmFiles[0].FullName "$script:Root\Tools\nssm.exe"
}

Write-Host 'Step 2/5: Stable releases (never beta)' -ForegroundColor Cyan
$emby = Get-Asset 'MediaBrowser/Emby.Releases' '^embyserver-win-x64-[0-9.]+\.7z$' 'Emby x64'
$server = Get-Asset 'metatube-community/metatube-server-releases' '^metatube-server-windows-amd64\.zip$' 'MetaTube server'
$plugin = Get-Asset 'metatube-community/jellyfin-plugin-metatube' '^Emby\.MetaTube@.*\.zip$' 'MetaTube Emby plugin'
$embyPkg = Save-Asset $emby
$serverPkg = Save-Asset $server
$pluginPkg = Save-Asset $plugin

Write-Host 'Step 3/5: Extract and validate before installing' -ForegroundColor Cyan
Extract-7z $embyPkg (Join-Path $stage 'emby')
Extract-Zip $serverPkg (Join-Path $stage 'server')
Extract-Zip $pluginPkg (Join-Path $stage 'plugin')
$embyExe = Find-One (Join-Path $stage 'emby') 'EmbyServer.exe'
if ($embyExe.Directory.Name -ine 'system') { throw 'Unexpected Emby archive structure (EmbyServer.exe not directly in system folder).' }
# MetaTube Windows ZIP contains e.g. metatube-server-windows-amd64.exe.
# Select the expected filename from the verified GitHub release asset, then install to a stable path.
$expectedServerExe = ([IO.Path]::GetFileNameWithoutExtension([string]$server.Asset.name) + '.exe')
$metaExe = Find-One (Join-Path $stage 'server') $expectedServerExe
Write-Host "MetaTube binary found: $($metaExe.Name) -> metatube-server.exe" -ForegroundColor Green
$metaDll = Find-One (Join-Path $stage 'plugin') 'MetaTube.dll'
if ($reinstall) {
    # Refuse a known downgrade; do not use old programs with a newer database.
    $oldVersion = $null
    foreach ($candidate in @("$script:Root\Emby\system\EmbyServer.dll", "$script:Root\Emby\system\EmbyServer.exe")) {
        if (Test-Path -LiteralPath $candidate) {
            $value = [Diagnostics.FileVersionInfo]::GetVersionInfo($candidate).ProductVersion
            if ($value -match '(\d+\.\d+\.\d+\.\d+)') { $oldVersion = [version]$Matches[1]; break }
        }
    }
    if ($null -eq $oldVersion -and (Test-Path "$script:Root\versions.json")) {
        $value = (Get-Content "$script:Root\versions.json" -Raw | ConvertFrom-Json).Emby
        if ($value -match '(\d+\.\d+\.\d+\.\d+)') { $oldVersion = [version]$Matches[1] }
    }
    if ($emby.Version -notmatch '(\d+\.\d+\.\d+\.\d+)') { throw 'Cannot determine candidate Emby version.' }
    $newVersion = [version]$Matches[1]
    if ($null -eq $oldVersion -and @(Get-ChildItem "$script:Root\Emby\programdata" -Force -ErrorAction SilentlyContinue).Count -gt 0) {
        throw 'Cannot determine existing Emby version safely. Existing data retained; inspect version before reinstall.'
    }
    if ($null -ne $oldVersion -and $newVersion -lt $oldVersion) { throw "Refusing Emby downgrade from $oldVersion to $newVersion." }
    $recovery = Join-Path $script:Root "Backups\reinstall-$stamp"
    Backup-Reinstallation -Destination $recovery
    Write-Host "Backup verified. Recovery files: $recovery" -ForegroundColor Green
}
try {
if (Test-Path -LiteralPath "$script:Root\Emby\system") {
    # Both absolute paths must remain within this installation; preserve old binaries.
    $oldSystem = [IO.Path]::GetFullPath("$script:Root\Emby\system")
    $retained = [IO.Path]::GetFullPath((Join-Path $stage 'previous-emby-system'))
    $boundary = [IO.Path]::GetFullPath($script:Root).TrimEnd('\') + '\'
    if (-not $oldSystem.StartsWith($boundary, [StringComparison]::OrdinalIgnoreCase) -or -not $retained.StartsWith($boundary, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected program replacement path.' }
    Move-Item -LiteralPath $oldSystem -Destination $retained
}
Move-Item -LiteralPath $embyExe.Directory.FullName -Destination "$script:Root\Emby\system"
Copy-Item $metaExe.FullName "$script:Root\MetaTube\bin\metatube-server.exe" -Force
New-Item -ItemType Directory "$script:Root\Emby\programdata\plugins" -Force | Out-Null
Copy-Item $metaDll.FullName "$script:Root\Emby\programdata\plugins\MetaTube.dll" -Force

Write-Host 'Step 4/5: Register native Windows services' -ForegroundColor Cyan
# Services run as LocalSystem by default. For authenticated NAS SMB access,
# switch Emby to a dedicated local Windows service account in services.msc.
Register-ServiceApp -Name 'MediaStackMetaTube' -Exe "$script:Root\MetaTube\bin\metatube-server.exe" `
    -WorkingDir "$script:Root\MetaTube\data" -Arguments @('-dsn', "$script:Root\MetaTube\data\metatube.db", '-port', '8080', '-db-auto-migrate') -Repair:$reinstall
Register-ServiceApp -Name 'MediaStackEmby' -Exe "$script:Root\Emby\system\EmbyServer.exe" `
    -WorkingDir "$script:Root\Emby\system" -Arguments @('-service') -Repair:$reinstall
# Firewall: Emby accessible on LAN, MetaTube only to the local host.
if (Get-Command New-NetFirewallRule -ErrorAction SilentlyContinue) {
    if (-not (Get-NetFirewallRule -DisplayName 'MediaStack Emby allow LAN' -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName 'MediaStack Emby allow LAN' -Direction Inbound -Protocol TCP -LocalPort 8096 -RemoteAddress LocalSubnet -Action Allow -Profile Any | Out-Null
    }
    if (-not (Get-NetFirewallRule -DisplayName 'MediaStack MetaTube block LAN' -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName 'MediaStack MetaTube block LAN' -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Block -Profile Any | Out-Null
    }
}

Write-Host 'Step 5/5: Apply persistent local scraping proxy and start services' -ForegroundColor Cyan
# Keep service proxy independent of installer downloads; not system-wide.
# Persistent Proxy works once the local HTTP/mixed port is available, even if not open during installation.
if ($originalServices.Count -eq 0) {
    $null = Set-ServiceProxy -Mode 'Proxy'
} else {
    foreach ($service in $script:Services) {
        if ($service -notin $originalServices) {
            Invoke-Nssm set $service AppEnvironmentExtra "HTTP_PROXY=$script:ProxyUrl" "HTTPS_PROXY=$script:ProxyUrl" 'NO_PROXY=localhost,127.0.0.1,::1'
        }
    }
    Write-Host 'Existing service environment retained; default proxy applied only to newly created services.'
}
if (-not (Test-LocalProxy)) { Write-Warning '127.0.0.1:7897 is not listening now. Scraping will require this proxy; switch to Direct explicitly if desired.' }
Start-StackService 'MediaStackMetaTube'
# Give MetaTube its first opportunity to create SQLite tables, then remove auto-migration switch.
$ready = $false
for ($i=0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    $s = Get-Service 'MediaStackMetaTube'
    if ($s.Status -ne 'Running') { break }
    if ((Test-Path "$script:Root\MetaTube\data\metatube.db") -and ((Get-Item "$script:Root\MetaTube\data\metatube.db").Length -gt 0)) { $ready = $true; break }
}
if ($ready) {
    Wait-StackHealth -Names @('MediaStackMetaTube')
    Stop-Service 'MediaStackMetaTube'
    (Get-Service 'MediaStackMetaTube').WaitForStatus('Stopped', [TimeSpan]::FromSeconds(30))
    Invoke-Nssm set MediaStackMetaTube AppParameters ('-dsn "{0}" -port 8080' -f "$script:Root\MetaTube\data\metatube.db")
    Start-StackService 'MediaStackMetaTube'
} else {
    throw 'MetaTube database not detected. Installation incomplete; inspect logs. Migration flag retained.'
}
Start-StackService 'MediaStackEmby'
$manifest = [ordered]@{ InstalledAt=(Get-Date).ToString('o'); Root=$script:Root; Emby=$emby.Version; MetaTubeServer=$server.Version; MetaTubePlugin=$plugin.Version; EmbyPackage=$emby.Asset.name; ServerPackage=$server.Asset.name; PluginPackage=$plugin.Asset.name }
$manifest | ConvertTo-Json | Set-Content -LiteralPath "$script:Root\versions.json" -Encoding UTF8
# Keep the management scripts together with data/programs for future migration.
foreach ($file in @(Get-ChildItem -LiteralPath $PSScriptRoot -File | Where-Object { $_.Extension -in @('.ps1','.cmd','.md') })) {
    $destination = Join-Path "$script:Root\Scripts" $file.Name
    if ($file.FullName -ine $destination) { Copy-Item -LiteralPath $file.FullName -Destination $destination -Force }
}
Wait-StackHealth
Write-Host "Installation scripts copied to $script:Root\Scripts." -ForegroundColor Green
Write-Host 'Software/services prepared; Premiere activation, SMB identity, and MetaTube URL still require setup.' -ForegroundColor Green
Write-Host 'Emby: http://localhost:8096 | MetaTube: http://127.0.0.1:8080'
Write-Host 'New services use proxy http://127.0.0.1:7897; existing services retain their environment.'
Write-Host 'To change: Scripts\Start-Proxy.cmd Proxy / Direct / Auto / Status'
} catch {
    # A failed deployment may already have migrated data. Never automatically roll binaries back alone.
    if ($reinstall) {
        foreach ($service in $script:Services) {
            if (Has-Service $service) {
                try {
                    $s = Get-Service $service
                    if ($s.Status -ne 'Stopped') { $s.Stop(); $s.WaitForStatus('Stopped', [TimeSpan]::FromSeconds(45)) }
                } catch { Write-Warning "Could not stop $service after failed reinstall; inspect before manual recovery." }
            }
        }
        Write-Warning "Reinstallation failed. Original programs/data/config backup: $recovery. No automatic rollback performed."
    }
    throw
}
