# Upgrade all 3 components with a database snapshot and retained previous binaries.
. (Join-Path $PSScriptRoot 'Common.ps1')
Assert-Host
Ensure-Dirs
if (-not ((Has-Service 'MediaStackEmby') -and (Has-Service 'MediaStackMetaTube'))) { throw 'MediaStack services not found: use Install first.' }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$stage = Join-Path $script:Root "Staging\upgrade-$stamp"
New-Item -ItemType Directory $stage -Force | Out-Null
$emby = Get-Asset 'MediaBrowser/Emby.Releases' '^embyserver-win-x64-[0-9.]+\.7z$' 'Emby x64'
$server = Get-Asset 'metatube-community/metatube-server-releases' '^metatube-server-windows-amd64\.zip$' 'MetaTube server'
$plugin = Get-Asset 'metatube-community/jellyfin-plugin-metatube' '^Emby\.MetaTube@.*\.zip$' 'MetaTube Emby plugin'
if (Test-Path "$script:Root\versions.json") {
    $current = Get-Content "$script:Root\versions.json" -Raw | ConvertFrom-Json
    if ($current.Emby -eq $emby.Version -and $current.MetaTubeServer -eq $server.Version -and $current.MetaTubePlugin -eq $plugin.Version) {
        Wait-StackHealth
        Write-Host 'All tracked components are already at the latest stable releases.' -ForegroundColor Green
        return
    }
}
$embyPkg = Save-Asset $emby
$serverPkg = Save-Asset $server
$pluginPkg = Save-Asset $plugin
Extract-7z $embyPkg (Join-Path $stage 'emby')
Extract-Zip $serverPkg (Join-Path $stage 'server')
Extract-Zip $pluginPkg (Join-Path $stage 'plugin')
$embyExe = Find-One (Join-Path $stage 'emby') 'EmbyServer.exe'
if ($embyExe.Directory.Name -ine 'system') { throw 'Unexpected Emby archive layout.' }
# MetaTube Windows ZIP contains e.g. metatube-server-windows-amd64.exe.
# Select the expected filename from the verified GitHub release asset, then install to a stable path.
$expectedServerExe = ([IO.Path]::GetFileNameWithoutExtension([string]$server.Asset.name) + '.exe')
$metaExe = Find-One (Join-Path $stage 'server') $expectedServerExe
Write-Host "MetaTube binary found: $($metaExe.Name) -> metatube-server.exe" -ForegroundColor Green
$metaDll = Find-One (Join-Path $stage 'plugin') 'MetaTube.dll'
Write-Host 'Backing up all databases/config before upgrade...' -ForegroundColor Cyan
& (Join-Path $PSScriptRoot 'Backup.ps1') -LeaveStopped
if (-not $?) { throw 'Backup script failed.' }
$previous = Join-Path $script:Root "Previous\$stamp"
New-Item -ItemType Directory $previous -Force | Out-Null
# Important: the moved old binaries stay available for rollback.
if (Test-Path "$script:Root\Emby\system") { Move-Item "$script:Root\Emby\system" "$previous\emby-system" }
if (Test-Path "$script:Root\MetaTube\bin\metatube-server.exe") { Copy-Item "$script:Root\MetaTube\bin\metatube-server.exe" "$previous\metatube-server.exe" }
if (Test-Path "$script:Root\Emby\programdata\plugins\MetaTube.dll") { Copy-Item "$script:Root\Emby\programdata\plugins\MetaTube.dll" "$previous\MetaTube.dll" }
Move-Item $embyExe.Directory.FullName "$script:Root\Emby\system"
Copy-Item $metaExe.FullName "$script:Root\MetaTube\bin\metatube-server.exe" -Force
Copy-Item $metaDll.FullName "$script:Root\Emby\programdata\plugins\MetaTube.dll" -Force
$manifest = [ordered]@{ UpdatedAt=(Get-Date).ToString('o'); Root=$script:Root; Emby=$emby.Version; MetaTubeServer=$server.Version; MetaTubePlugin=$plugin.Version; EmbyPackage=$emby.Asset.name; ServerPackage=$server.Asset.name; PluginPackage=$plugin.Asset.name; Previous=$previous }
$manifest | ConvertTo-Json | Set-Content "$script:Root\versions.json" -Encoding UTF8
Write-Warning 'MetaTube schema changes may require first-run -db-auto-migrate. Run it only after snapshot, if release notes require it.'
Start-StackService 'MediaStackMetaTube'
Start-StackService 'MediaStackEmby'
Wait-StackHealth
Write-Host "Upgrade HTTP readiness passed. Previous binaries: $previous" -ForegroundColor Green
