# Change Emby + MetaTube scraping proxy without changing machine-wide proxy settings.
# Requires administrator privileges. Default Proxy mode is persistent and survives restart.
param(
    [ValidateSet('Proxy','Direct','Auto','Status')]
    [string]$Mode = 'Status',
    [switch]$NoRestart,
    [string]$ProxyUrl
)
$requestedProxyUrl = $ProxyUrl
. (Join-Path $PSScriptRoot 'Common.ps1')
Assert-Host -ReadOnly:($Mode -eq 'Status')
$savedPath = Join-Path $script:Root 'proxy-settings.json'
if (Test-Path -LiteralPath $savedPath) {
    $saved = Get-Content -LiteralPath $savedPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($saved.ProxyUrl) { $script:ProxyUrl = [string]$saved.ProxyUrl }
}
if ($Mode -eq 'Status' -and $requestedProxyUrl) { throw 'Status is read-only. Use -Mode Proxy -ProxyUrl to change the address.' }
if ($Mode -eq 'Proxy' -and -not $requestedProxyUrl) {
    $answer = Read-Host "代理地址（回车保留 $script:ProxyUrl）"
    if (-not [string]::IsNullOrWhiteSpace($answer)) { $requestedProxyUrl = $answer.Trim() }
}
if ($requestedProxyUrl) { $script:ProxyUrl = $requestedProxyUrl.Trim() }
$proxy = $null
if (-not [Uri]::TryCreate($script:ProxyUrl, [UriKind]::Absolute, [ref]$proxy) -or
    $proxy.Scheme -notin @('http','https') -or -not $proxy.Host -or $proxy.Port -lt 1 -or
    $proxy.UserInfo -or $proxy.Query -or $proxy.Fragment -or $proxy.AbsolutePath -ne '/') {
    throw 'Use an HTTP(S) proxy address such as http://127.0.0.1:7897, without credentials, path or query.'
}
$script:ProxyUrl = $proxy.GetLeftPart([UriPartial]::Authority)
if ($Mode -eq 'Status') {
    Write-Host "Local proxy TCP $($script:ProxyUrl): $(if (Test-LocalProxy) { 'OPEN' } else { 'CLOSED' })"
    if (Test-Path "$script:Root\proxy-settings.json") { Get-Content "$script:Root\proxy-settings.json" -Raw | Write-Host }
    foreach ($svc in $script:Services) {
        if (Has-Service $svc) {
            Write-Host "$svc : $((Get-Service $svc).Status)"
            Write-Host 'Proxy variables are configured per service; inspect locally if needed (environment may contain credentials).'
        } else { Write-Warning "Missing service: $svc" }
    }
    exit 0
}
$null = Set-ServiceProxy -Mode $Mode
if (-not $NoRestart) {
    foreach ($svc in $script:Services) { if ((Get-Service $svc).Status -eq 'Running') { Stop-Service $svc -ErrorAction Stop } }
    foreach ($svc in $script:Services) {
        $s = Get-Service $svc
        $s.WaitForStatus('Stopped', [TimeSpan]::FromSeconds(45))
    }
    foreach ($svc in $script:Services) { Start-StackService $svc }
    Wait-StackHealth
    Write-Host 'Both services restarted with the new proxy environment.' -ForegroundColor Green
} else {
    Write-Warning 'NoRestart specified: service processes still use old settings until they are restarted.'
}
if ($Mode -eq 'Auto') { Write-Warning 'Auto probes once at this execution; it does not monitor/fail over while scraping. Run again if needed.' }
