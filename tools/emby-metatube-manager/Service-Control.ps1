# Operates registered services only. No installation, downloads or configuration changes.
param([ValidateSet('Start','Status')][string]$Action = 'Status')
. (Join-Path $PSScriptRoot 'Common.ps1')
Assert-Host -ReadOnly:($Action -eq 'Status')
$names = @('MediaStackMetaTube', 'MediaStackEmby')
if ($Action -eq 'Status') {
    foreach ($name in $names) {
        $service = Get-Service -Name $name -ErrorAction SilentlyContinue
        if ($null -eq $service) { Write-Host "$name : not installed" }
        else { Write-Host "$name : $($service.Status)" }
        $url = if ($name -eq 'MediaStackEmby') { 'http://127.0.0.1:8096/System/Info/Public' } else { 'http://127.0.0.1:8080/' }
        Write-Host "HTTP $url : $(Get-LocalHealth $name $url)"
    }
    return
}
# Validate the whole stack before starting either service.
foreach ($name in $names) {
    $service = Get-Service -Name $name -ErrorAction SilentlyContinue
    if ($null -eq $service) { throw "Service missing: $name. Use Start-Install.cmd on the target PC first." }
    if ($service.Status -notin @('Running','Stopped','StartPending')) { throw "Service $name is $($service.Status). Resolve this state before starting." }
    if ($service.Status -eq 'Stopped') {
        $port = if ($name -eq 'MediaStackEmby') { 8096 } else { 8080 }
        $exe = if ($name -eq 'MediaStackEmby') { 'EmbyServer.exe' } else { 'metatube-server.exe' }
        if (@(Get-CimInstance Win32_Process -Filter "Name='$exe'").Count -gt 0) {
            throw "A $exe process is already running outside the stopped service. Close the foreground/test instance first."
        }
        if (@(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue).Count -gt 0) {
            throw "Port $port is occupied. Close the other instance before starting $name."
        }
    }
}
foreach ($name in $names) { Start-StackService $name }
Wait-StackHealth
Write-Host 'Both services and HTTP endpoints are ready.' -ForegroundColor Green
Write-Host 'Emby: http://127.0.0.1:8096 | MetaTube: http://127.0.0.1:8080/'
