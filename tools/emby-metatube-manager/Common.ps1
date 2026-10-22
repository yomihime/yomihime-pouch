# MediaStack shared helpers. Windows PowerShell 5.1+, native Windows only.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$settingsPath = Join-Path $PSScriptRoot 'mediastack-settings.json'
$parent = Split-Path -Parent $PSScriptRoot
if ((Split-Path -Leaf $PSScriptRoot) -ieq 'Scripts' -and ((Test-Path -LiteralPath (Join-Path $parent 'versions.json')) -or (Test-Path -LiteralPath (Join-Path $parent 'Tools\nssm.exe')))) {
    $script:Root = $parent
} elseif (Test-Path -LiteralPath $settingsPath) {
    $script:Root = [string]((Get-Content -LiteralPath $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json).Root)
    if ([string]::IsNullOrWhiteSpace($script:Root)) { throw "Missing Root in $settingsPath" }
} else {
    $script:Root = if (Test-Path 'D:\') { 'D:\MediaStack' } else { Join-Path $env:SystemDrive 'MediaStack' }
}
$script:Root = $script:Root.TrimEnd('\')
if ($script:Root -notmatch '^[a-zA-Z]:\\.+' -or $script:Root -match '[\x00-\x1f"<>|?*\[\]]') { throw 'Invalid deployment root in settings. Select an absolute local directory.' }
$script:Root = [IO.Path]::GetFullPath($script:Root).TrimEnd('\')
if ($script:Root.Length -le 2 -or $script:Root.Substring(2).Contains(':')) { throw 'Invalid deployment root in settings.' }
$script:ProxyUrl = 'http://127.0.0.1:7897' # HTTP or mixed HTTP/SOCKS listener (not SOCKS-only)
$script:Services = @('MediaStackEmby', 'MediaStackMetaTube')

function Assert-Host {
    param([switch]$ReadOnly)
    if (-not [Environment]::Is64BitOperatingSystem -or $PSVersionTable.PSVersion.Major -lt 5) { throw 'Windows x64 / Windows PowerShell 5.1+ required.' }
    $p = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $ReadOnly -and -not $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Please run as Administrator.' }
    if (-not $ReadOnly -and -not (Test-Path -LiteralPath ([IO.Path]::GetPathRoot($script:Root)))) { throw "Deployment drive not found: $script:Root" }
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
}

# Local checks always bypass system/service proxies and never follow redirects.
function Get-LocalHealth {
    param([string]$Name, [string]$Url)
    Add-Type -AssemblyName System.Net.Http
    $handler = [System.Net.Http.HttpClientHandler]::new()
    $handler.UseProxy = $false
    $handler.AllowAutoRedirect = $false
    $client = [System.Net.Http.HttpClient]::new($handler)
    $client.Timeout = [TimeSpan]::FromSeconds(3)
    $response = $null
    try {
        $response = $client.GetAsync($Url).GetAwaiter().GetResult()
        if (-not $response.IsSuccessStatusCode) { return $false }
        $data = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult() | ConvertFrom-Json
        if ($Name -eq 'MediaStackEmby') { return [bool]$data.Version }
        return [bool]($data.data.app -and $data.data.version)
    } catch { return $false }
    finally {
        if ($null -ne $response) { $response.Dispose() }
        $client.Dispose()
        $handler.Dispose()
    }
}
function Start-StackService {
    param([string]$Name)
    $service = Get-Service -Name $Name -ErrorAction Stop
    if ($service.Status -eq 'Stopped') { $service.Start() }
    $service.WaitForStatus('Running', [TimeSpan]::FromSeconds(45))
}
function Wait-StackHealth {
    param([string[]]$Names = $script:Services, [int]$TimeoutSec = 60, [int]$StableSamples = 3)
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSec)
    $consecutive = 0
    do {
        $healthy = $true
        foreach ($name in $Names) {
            $service = Get-Service -Name $name -ErrorAction SilentlyContinue
            $url = if ($name -eq 'MediaStackEmby') { 'http://127.0.0.1:8096/System/Info/Public' } else { 'http://127.0.0.1:8080/' }
            if ($null -eq $service -or $service.Status -ne 'Running' -or -not (Get-LocalHealth $name $url)) { $healthy = $false }
        }
        if ($healthy) { $consecutive++ } else { $consecutive = 0 }
        if ($consecutive -ge $StableSamples) { return }
        if ([DateTime]::UtcNow -ge $deadline) { break }
        Start-Sleep -Seconds 2
    } while ($true)
    throw "Service/HTTP readiness failed: $($Names -join ', '). Files may be deployed; application readiness is NOT confirmed. Inspect $script:Root\Logs and Emby\programdata\logs."
}
function Ensure-Dirs {
    foreach ($p in @('Emby', 'MetaTube\bin', 'MetaTube\data', 'Tools', 'Scripts', 'Downloads', 'Backups', 'Logs', 'Staging', 'Previous', 'Emby\transcoding')) {
        New-Item -ItemType Directory -Path (Join-Path $script:Root $p) -Force | Out-Null
    }
}
function Test-LocalProxy {
    param([int]$TimeoutMs = 700)
    $u = [Uri]$script:ProxyUrl
    $client = New-Object System.Net.Sockets.TcpClient
    $async = $null
    try {
        $async = $client.BeginConnect($u.DnsSafeHost, $u.Port, $null, $null)
        if (-not $async.AsyncWaitHandle.WaitOne($TimeoutMs, $false)) { return $false }
        $client.EndConnect($async)
        return $client.Connected
    } catch { return $false }
    finally {
        if ($null -ne $async) { $async.AsyncWaitHandle.Close() }
        $client.Close()
    }
}
# Explicit HTTP client transports prevent inherited system proxy from defeating direct fallback.
# Uses bounded attempts: local HTTP proxy first if its port is open, then genuinely direct.
function Invoke-Fetch {
    param(
        [Parameter(Mandatory=$true)][string]$Url,
        [string]$OutFile,
        [hashtable]$Headers = @{},
        [int]$ProxyTimeoutSec = 180,
        [int]$DirectTimeoutSec = 900
    )
    Add-Type -AssemblyName System.Net.Http
    $modes = if (Test-LocalProxy) { @('Proxy', 'Direct') } else { @('Direct') }
    $errorMessages = @()
    foreach ($mode in $modes) {
        $handler = $null; $client = $null; $request = $null; $response = $null
        $src = $null; $dst = $null; $reader = $null; $cts = $null
        try {
            $handler = [System.Net.Http.HttpClientHandler]::new()
            $handler.UseProxy = ($mode -eq 'Proxy')
            if ($mode -eq 'Proxy') {
                $handler.Proxy = [System.Net.WebProxy]::new($script:ProxyUrl)
            }
            $handler.AutomaticDecompression = [Net.DecompressionMethods]::GZip -bor [Net.DecompressionMethods]::Deflate
            $client = [System.Net.Http.HttpClient]::new($handler)
            $client.Timeout = [TimeSpan]::FromSeconds($(if ($mode -eq 'Proxy') { $ProxyTimeoutSec } else { $DirectTimeoutSec }))
            # Cancellation applies to the complete download, including stream reads,
            # not merely to receiving HTTP response headers.
            $cts = [System.Threading.CancellationTokenSource]::new()
            $cts.CancelAfter([TimeSpan]::FromSeconds($(if ($mode -eq 'Proxy') { $ProxyTimeoutSec } else { $DirectTimeoutSec })))
            $request = [System.Net.Http.HttpRequestMessage]::new([System.Net.Http.HttpMethod]::Get, [Uri]$Url)
            $request.Headers.TryAddWithoutValidation('User-Agent', 'MediaStack-Windows-Installer/2.0') | Out-Null
            foreach ($name in $Headers.Keys) { $request.Headers.TryAddWithoutValidation([string]$name, [string]$Headers[$name]) | Out-Null }
            Write-Host "HTTP [$mode]: $Url" -ForegroundColor Cyan
            $response = $client.SendAsync($request, [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead, $cts.Token).GetAwaiter().GetResult()
            $response.EnsureSuccessStatusCode() | Out-Null
            $src = $response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
            if ($OutFile) {
                $parent = Split-Path -Parent $OutFile
                if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
                $dst = [System.IO.FileStream]::new($OutFile, [IO.FileMode]::Create, [IO.FileAccess]::Write, [IO.FileShare]::None)
                $buffer = [byte[]]::new(131072)
                while ($true) {
                    $bytesRead = $src.ReadAsync($buffer, 0, $buffer.Length, $cts.Token).GetAwaiter().GetResult()
                    if ($bytesRead -eq 0) { break }
                    $dst.Write($buffer, 0, $bytesRead)
                }
                $dst.Flush()
                Write-Host "Saved via $mode : $OutFile" -ForegroundColor Green
                return $OutFile
            }
            $reader = [System.IO.StreamReader]::new($src, [Text.Encoding]::UTF8)
            return $reader.ReadToEnd()
        } catch {
            $errorMessages += "${mode}: $($_.Exception.Message)"
            Write-Warning "HTTP [$mode] failed: $($_.Exception.Message)"
            # Windows disallows deleting a partially downloaded file while the stream is open.
            if ($null -ne $dst) { $dst.Dispose(); $dst = $null }
            if ($OutFile -and (Test-Path -LiteralPath $OutFile)) {
                try { Remove-Item -LiteralPath $OutFile -Force -ErrorAction Stop }
                catch { Write-Warning "Unable to clean up partial download (close file locks): $OutFile" }
            }
        } finally {
            if ($null -ne $reader) { $reader.Dispose() }
            if ($null -ne $dst) { $dst.Dispose() }
            if ($null -ne $src) { $src.Dispose() }
            if ($null -ne $response) { $response.Dispose() }
            if ($null -ne $request) { $request.Dispose() }
            if ($null -ne $client) { $client.Dispose() }
            if ($null -ne $handler) { $handler.Dispose() }
            if ($null -ne $cts) { $cts.Dispose() }
        }
    }
    throw "Unable to fetch $Url ($($errorMessages -join ' | ')). Check proxy, direct connectivity, TLS and DNS."
}
function Get-Asset {
    param([string]$Repo, [string]$Regex, [string]$Label)
    Write-Host "Getting latest stable release: $Label" -ForegroundColor Cyan
    $json = Invoke-Fetch -Url "https://api.github.com/repos/$Repo/releases/latest" -Headers @{ 'Accept'='application/vnd.github+json' } -ProxyTimeoutSec 25 -DirectTimeoutSec 40
    $release = $json | ConvertFrom-Json
    if ($release.prerelease -or $release.draft) { throw "Unexpected pre-release for $Label" }
    $matchingAssets = @($release.assets | Where-Object { $_.name -cmatch $Regex })
    if ($matchingAssets.Count -ne 1) { throw "Expected one $Label asset, found $($matchingAssets.Count). Check official release manually." }
    return [pscustomobject]@{ Repo=$Repo; Version=[string]$release.tag_name; Asset=$matchingAssets[0] }
}
function Save-Asset {
    param($AssetInfo)
    $asset = $AssetInfo.Asset
    $path = Join-Path (Join-Path $script:Root 'Downloads') ("{0}_{1}" -f $AssetInfo.Version, $asset.name)
    $digestProperty = $asset.PSObject.Properties['digest']
    $digest = if ($null -ne $digestProperty) { [string]$digestProperty.Value } else { '' }
    $hashExpected = if ($digest -match '^sha256:([0-9a-fA-F]{64})$') { $Matches[1] } else { $null }
    if (Test-Path $path) {
        if ((Get-Item $path).Length -lt 10000) { Remove-Item $path -Force }
        elseif ($hashExpected -and ((Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash -ine $hashExpected)) {
            Write-Warning "Existing cached file failed official checksum, discarding: $path"
            Remove-Item $path -Force
        }
    }
    if (-not (Test-Path $path)) {
        $temporary = "$path.partial"
        if (Test-Path $temporary) { Remove-Item $temporary -Force }
        try {
            $null = Invoke-Fetch -Url $asset.browser_download_url -OutFile $temporary
            if ((Get-Item $temporary).Length -lt 10000) { throw "Suspiciously small package: $temporary" }
            if ($hashExpected) {
                if ((Get-FileHash -Algorithm SHA256 -LiteralPath $temporary).Hash -ine $hashExpected) { throw "SHA256 mismatch: $temporary" }
            }
            Move-Item -LiteralPath $temporary -Destination $path -Force
        } finally {
            if (Test-Path $temporary) { Remove-Item $temporary -Force }
        }
    }
    if ($hashExpected) {
        if ((Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash -ine $hashExpected) { throw "SHA256 mismatch: $path" }
        Write-Host 'Official GitHub SHA256 verified.' -ForegroundColor Green
    } else {
        Write-Warning "No official SHA256 in GitHub release API for $($asset.name): provenance is official release, integrity digest unavailable."
    }
    return $path
}
function Download-Tool {
    param([string]$Url, [string]$Destination)
    if (-not (Test-Path $Destination)) {
        $tmp = "$Destination.partial"
        try {
            $null = Invoke-Fetch -Url $Url -OutFile $tmp -ProxyTimeoutSec 80 -DirectTimeoutSec 120
            if ((Get-Item $tmp).Length -lt 10000) { throw "Tool download invalid: $tmp" }
            Move-Item $tmp $Destination -Force
        } finally { if (Test-Path $tmp) { Remove-Item $tmp -Force } }
    }
    if ((Get-Item $Destination).Length -lt 10000) { throw "Tool download invalid: $Destination" }
    return $Destination
}
function Extract-7z {
    param([string]$Archive, [string]$Destination)
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    & (Join-Path $script:Root 'Tools\7zr.exe') x $Archive ("-o$Destination") '-y' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "7-Zip extraction failed: $Archive" }
}
function Extract-Zip {
    param([string]$Archive, [string]$Destination)
    Expand-Archive -LiteralPath $Archive -DestinationPath $Destination -Force
}
function Find-One {
    param([string]$Directory, [string]$Filter)
    $found = @(Get-ChildItem -LiteralPath $Directory -Recurse -File -Filter $Filter)
    if ($found.Count -ne 1) {
        $available = @(Get-ChildItem -LiteralPath $Directory -Recurse -File |
            Select-Object -First 15 -ExpandProperty Name)
        throw "Expected exactly one $Filter in $Directory, got $($found.Count). Files present: $($available -join ', ')"
    }
    return $found[0]
}
function Has-Service {
    param([string]$Name)
    return [bool](Get-Service -Name $Name -ErrorAction SilentlyContinue)
}
function ConvertTo-NativeArgument {
    param([AllowEmptyString()][string]$Value)
    # Windows CommandLineToArgvW / C runtime escaping. No command shell involved.
    $escaped = [regex]::Replace($Value, '(\\*)"', '$1$1\"')
    $escaped = [regex]::Replace($escaped, '(\\+)$', '$1$1')
    return '"' + $escaped + '"'
}
function Invoke-Nssm {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
    $info = New-Object Diagnostics.ProcessStartInfo
    $info.FileName = Join-Path $script:Root 'Tools\nssm.exe'
    $info.Arguments = (@($Arguments | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' ')
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $process = New-Object Diagnostics.Process
    $process.StartInfo = $info
    try {
        $null = $process.Start()
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        $outputText = $stdout.GetAwaiter().GetResult()
        $errorText = $stderr.GetAwaiter().GetResult()
        if ($outputText) { Write-Host $outputText.TrimEnd() }
        if ($errorText) { Write-Host $errorText.TrimEnd() }
        if ($process.ExitCode -ne 0) { throw "NSSM failed (exit $($process.ExitCode)): $($Arguments -join ' ')" }
    } finally { $process.Dispose() }
}
function Register-ServiceApp {
    param([string]$Name, [string]$Exe, [string]$WorkingDir, [string[]]$Arguments, [switch]$Repair)
    if (Has-Service $Name) {
        if (-not $Repair) { throw "Service already exists: $Name" }
        if ((Get-Service $Name).Status -ne 'Stopped') { throw "Stop service before repair: $Name" }
        # Update in place: preserve the service logon account, password and environment.
        Invoke-Nssm set $Name Application $Exe
    } else {
        Invoke-Nssm install $Name $Exe
    }
    $commandLine = (@($Arguments | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' ')
    Invoke-Nssm set $Name AppParameters $commandLine
    Invoke-Nssm set $Name AppDirectory $WorkingDir
    Invoke-Nssm set $Name AppExit Default Exit
    Invoke-Nssm set $Name Start SERVICE_DELAYED_AUTO_START
    Invoke-Nssm set $Name AppStdout (Join-Path $script:Root "Logs\$Name.stdout.log")
    Invoke-Nssm set $Name AppStderr (Join-Path $script:Root "Logs\$Name.stderr.log")
    Invoke-Nssm set $Name AppRotateFiles 1
    Invoke-Nssm set $Name AppRotateBytes 10485760
}
function Set-ServiceProxy {
    param([ValidateSet('Proxy','Direct','Auto')][string]$Mode='Proxy')
    $chosen = $Mode
    if ($Mode -eq 'Auto') { $chosen = if (Test-LocalProxy) { 'Proxy' } else { 'Direct' } }
    # Read both first; retain unrelated service environment variables.
    $original = @{}
    foreach ($service in $script:Services) {
        if (-not (Has-Service $service)) { throw "Service missing: $service" }
        $parameters = Get-ItemProperty -LiteralPath "HKLM:\SYSTEM\CurrentControlSet\Services\$service\Parameters"
        $property = $parameters.PSObject.Properties['AppEnvironmentExtra']
        $original[$service] = @()
        if ($null -ne $property) { $original[$service] = @($property.Value | Where-Object { $null -ne $_ }) }
    }
    $changed = @()
    $settingsFile = Join-Path $script:Root 'proxy-settings.json'
    $temporary = $settingsFile + '.' + [guid]::NewGuid().ToString('N') + '.tmp'
    try {
        foreach ($service in $script:Services) {
            $environment = @($original[$service] | Where-Object { $_ -notmatch '^(?i:HTTP_PROXY|HTTPS_PROXY|NO_PROXY)=' })
            if ($chosen -eq 'Proxy') {
                $bypass = @('localhost','127.0.0.1','::1')
                foreach ($entry in @($original[$service] | Where-Object { $_ -match '^(?i:NO_PROXY)=' })) { $bypass += $entry.Substring($entry.IndexOf('=') + 1).Split(',') }
                $bypass = @($bypass | ForEach-Object { $_.Trim() } | Where-Object { $_ } | Select-Object -Unique)
                $environment += @("HTTP_PROXY=$script:ProxyUrl", "HTTPS_PROXY=$script:ProxyUrl", ('NO_PROXY=' + ($bypass -join ',')))
            }
            $changed += $service
            if ($environment.Count -gt 0) { Invoke-Nssm set $service AppEnvironmentExtra @environment }
            else { Invoke-Nssm reset $service AppEnvironmentExtra }
        }
        $info = [ordered]@{ RequestedMode=$Mode; AppliedMode=$chosen; ProxyUrl=$script:ProxyUrl; UpdatedAt=(Get-Date).ToString('o'); Note='Restart services for changes to take effect; no per-request runtime fallback.' }
        $info | ConvertTo-Json | Set-Content -LiteralPath $temporary -Encoding UTF8
        if (Test-Path -LiteralPath $settingsFile) { [IO.File]::Replace($temporary, $settingsFile, [System.Management.Automation.Language.NullString]::Value) }
        else { [IO.File]::Move($temporary, $settingsFile) }
    } catch {
        foreach ($service in $changed) {
            try {
                $previousEnvironment = @($original[$service])
                if ($previousEnvironment.Count -gt 0) { Invoke-Nssm set $service AppEnvironmentExtra @previousEnvironment }
                else { Invoke-Nssm reset $service AppEnvironmentExtra }
            } catch { Write-Warning "Could not restore previous environment for $service; inspect before restarting." }
        }
        throw
    } finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
    Write-Host "Service proxy configured: $chosen (requested: $Mode). Restart both services to apply." -ForegroundColor Green
    return $chosen
}
