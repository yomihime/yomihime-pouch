# Helpers for explicitly confirmed reinstallation. Dot-source after Common.ps1.
function Resolve-InstallDirectory {
    param([string]$Path)
    $value = $Path.Trim().Trim('"').Replace('/', '\')
    if ($value -notmatch '^[a-zA-Z]:\\' -or $value -match '[\x00-\x1f"<>|?*\[\]]' -or $value.Substring(2).Contains(':')) {
        throw 'Use an absolute local directory, for example E:\Media Stack. Network paths and wildcard characters are not supported.'
    }
    foreach ($part in $value.Substring(3).TrimEnd('\').Split('\')) {
        if ($part -in @('.','..') -or $part -match '[. ]$' -or $part -match '^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)') { throw "Invalid directory component: $part" }
    }
    $resolved = [IO.Path]::GetFullPath($value).TrimEnd('\')
    if ($resolved.Length -le 2) { throw 'Do not install to a drive root.' }
    if (-not (Test-Path -LiteralPath ([IO.Path]::GetPathRoot($resolved)))) { throw "Drive not found: $resolved" }
    if ([IO.DriveInfo]::new([IO.Path]::GetPathRoot($resolved)).DriveType -eq [IO.DriveType]::Network) { throw 'Install programs on a local disk, not a mapped network drive.' }
    if ((Test-Path -LiteralPath $resolved) -and -not (Test-Path -LiteralPath $resolved -PathType Container)) { throw "Not a directory: $resolved" }
    foreach ($protected in @($env:windir, $env:ProgramFiles, ${env:ProgramFiles(x86)})) {
        if ($protected -and ($resolved -ieq $protected -or $resolved.StartsWith($protected.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase))) { throw "Choose a directory outside $protected" }
    }
    $source = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\')
    if ($source -ieq $resolved -or ($source.StartsWith($resolved + '\', [StringComparison]::OrdinalIgnoreCase) -and $source -ine "$resolved\Scripts")) {
        throw 'Keep installer scripts outside the deployment directory, or directly in its Scripts subdirectory.'
    }
    $ancestor = $resolved
    while ($ancestor) {
        if (Test-Path -LiteralPath $ancestor) {
            if ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked installation path is not supported: $ancestor" }
        }
        $ancestor = Split-Path -Parent $ancestor
    }
    return $resolved
}
function Confirm-Reinstallation {
    param([string[]]$Existing)
    Write-Host ($Existing -join "`n") -ForegroundColor Yellow
    Write-Host 'Force install stops services, backs up programs/data, then replaces programs and repairs service settings.'
    Write-Host 'Databases, user configuration, service accounts and existing service environment are retained.'
    $answer = Read-Host '检测到已有安装，是否强制安装？[y/N]'
    return ($null -ne $answer -and $answer.Trim() -ieq 'y')
}
function Assert-ReinstallOwnership {
    # Never repair an unrelated service merely because its name matches.
    foreach ($name in $script:Services) {
        if (-not (Has-Service $name)) { continue }
        $key = "HKLM:\SYSTEM\CurrentControlSet\Services\$name"
        $service = Get-ItemProperty -LiteralPath $key
        $parameters = Get-ItemProperty -LiteralPath "$key\Parameters"
        $expected = if ($name -eq 'MediaStackEmby') { "$script:Root\Emby\system\EmbyServer.exe" } else { "$script:Root\MetaTube\bin\metatube-server.exe" }
        if ($service.ImagePath.Trim('"') -ine "$script:Root\Tools\nssm.exe" -or $parameters.Application.Trim('"') -ine $expected) {
            throw "Service $name is not owned by this installation. No service changes made."
        }
    }
    foreach ($relative in @('', 'Emby', 'Emby\system', 'Emby\programdata', 'MetaTube', 'MetaTube\bin', 'MetaTube\data', 'Tools', 'Scripts', 'Logs', 'Backups', 'Staging', 'Downloads')) {
        $path = if ($relative) { Join-Path $script:Root $relative } else { $script:Root }
        if (-not (Test-Path -LiteralPath $path)) { continue }
        $item = Get-Item -LiteralPath $path -Force
        if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Unsupported installation path: $path" }
    }
}
function Backup-Reinstallation {
    param([string]$Destination)
    $names = @($script:Services | Where-Object { Has-Service $_ })
    $running = @($names | Where-Object { (Get-Service $_).Status -eq 'Running' })
    foreach ($name in $names) {
        if ((Get-Service $name).Status -notin @('Running','Stopped')) { throw "Service state must be Running or Stopped before reinstall: $name" }
    }
    New-Item -ItemType Directory -Path $Destination -ErrorAction Stop | Out-Null
    Write-Host "Pre-reinstall backup: $Destination"
    try {
        foreach ($name in $running) { (Get-Service $name).Stop() }
        foreach ($name in $names) { (Get-Service $name).WaitForStatus('Stopped', [TimeSpan]::FromSeconds(45)) }
        # A manually launched instance must not share a database with the installer.
        $active = @(Get-CimInstance Win32_Process -Filter "Name='EmbyServer.exe' OR Name='metatube-server.exe'")
        if ($active.Count -gt 0) { throw 'An Emby/MetaTube process remains active. Close it before reinstalling.' }
        foreach ($port in @(8096,8080)) {
            if (@(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue).Count -gt 0) { throw "Port $port is still occupied after stopping MediaStack." }
        }
        foreach ($relative in @('Emby\system','Emby\programdata','MetaTube\bin','MetaTube\data','Tools','Scripts','Logs')) {
            $source = Join-Path $script:Root $relative
            if (-not (Test-Path -LiteralPath $source)) { continue }
            # Reject links instead of silently omitting linked user data from recovery.
            $links = @(Get-ChildItem -LiteralPath $source -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
            if ($links.Count -gt 0) { throw "Backup source contains links: $source. Reinstallation aborted." }
            $target = Join-Path $Destination $relative
            & robocopy.exe $source $target /E /COPY:DAT /DCOPY:DAT /XJ /R:1 /W:1 /NP /NFL /NDL | Out-Null
            if ($LASTEXITCODE -ge 8) { throw "Backup failed for $source (robocopy $LASTEXITCODE)." }
            foreach ($file in @(Get-ChildItem -LiteralPath $source -File -Recurse -Force)) {
                $copy = Join-Path $target $file.FullName.Substring($source.Length + 1)
                if (-not (Test-Path -LiteralPath $copy -PathType Leaf)) { throw "Missing backup file: $copy" }
                if ((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash) { throw "Backup verification failed: $copy" }
            }
        }
        foreach ($file in @('versions.json','proxy-settings.json')) {
            $source = Join-Path $script:Root $file
            if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination $Destination }
        }
        foreach ($name in $names) {
            & reg.exe export "HKLM\SYSTEM\CurrentControlSet\Services\$name" (Join-Path $Destination "$name.reg") /y | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Service configuration backup failed: $name" }
        }
        @{ CompletedAt=(Get-Date).ToString('o'); PreviouslyRunning=$running; Note='Program/data hashes verified; service credentials are not exported. Restore matching programs and data together.' } |
            ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Destination 'backup-complete.json') -Encoding UTF8
    } catch {
        foreach ($name in $running) {
            try { Start-StackService $name } catch { Write-Warning "Could not restore previous running state: $name" }
        }
        throw
    }
}
