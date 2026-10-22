param([switch]$Network)
# Read-only checks; NEVER prints Premiere key, service user password or NAS credentials.
. (Join-Path $PSScriptRoot 'Common.ps1')
Assert-Host -ReadOnly
Write-Host '=== MediaStack diagnostics (read-only) ===' -ForegroundColor Cyan
Write-Host "Time: $(Get-Date -Format o)"
Write-Host "Root: $script:Root | proxy: $script:ProxyUrl"
Write-Host "Proxy listener: $(if (Test-LocalProxy) { 'OPEN' } else { 'CLOSED' })"
foreach ($port in @(7897,8080,8096)) {
    $ports = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
    Write-Host "Listening $port : $($ports.Count -gt 0)"
}
foreach ($svc in $script:Services) {
    if (Has-Service $svc) {
        $s = Get-CimInstance Win32_Service -Filter "Name='$svc'"
        Write-Host "Service $svc : State=$($s.State); StartName=$($s.StartName); StartMode=$($s.StartMode)"
        Write-Host 'Service environment omitted (may contain credentials).'
    } else { Write-Warning "Missing service: $svc" }
}
foreach ($p in @('Emby\system\EmbyServer.exe','Emby\programdata','Emby\programdata\plugins\MetaTube.dll','MetaTube\bin\metatube-server.exe','MetaTube\data\metatube.db','versions.json','proxy-settings.json')) {
    Write-Host "Exists $(Join-Path $script:Root $p) : $(Test-Path (Join-Path $script:Root $p))"
}
if (Test-Path "$script:Root\Emby\programdata\logs") {
    Write-Host "Emby log dir: $script:Root\Emby\programdata\logs"
} else { Write-Warning 'Emby portable programdata logs not found yet; inspect Emby dashboard server data path.' }
if ($Network) {
Write-Host 'Testing GitHub API via installer proxy->direct policy...'
try {
    $result = Invoke-Fetch -Url 'https://api.github.com/rate_limit' -Headers @{'Accept'='application/vnd.github+json'} -ProxyTimeoutSec 12 -DirectTimeoutSec 20
    $null = $result | ConvertFrom-Json
    Write-Host 'GitHub API connectivity: OK' -ForegroundColor Green
} catch { Write-Warning "GitHub API connectivity failed: $($_.Exception.Message)" }
Write-Host 'This verifies network/download routing only, NOT successful Emby/MetaTube scraping.'
Write-Host 'Check MetaTube response, Emby metadata search, thumbnail fetching and QSV manually.'

}
Wait-StackHealth -TimeoutSec 10
Write-Host 'Service and HTTP checks passed. Plugin, scraping, SMB and QSV remain manual checks.'
