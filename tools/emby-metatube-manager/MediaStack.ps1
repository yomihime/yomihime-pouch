param(
    [ValidateSet('Menu','StartServices','OpenEmby','ServiceStatus','Install','Update','Backup','Test','Proxy','Direct','Auto','Status','Syntax')]
    [string]$Action = 'Menu',
    [switch]$Elevated
)
$ErrorActionPreference = 'Stop'
$actions = @('StartServices','OpenEmby','ServiceStatus','Install','Test','Backup','Update','Status','Proxy','Direct','Auto','Syntax')
function Invoke-Action([string]$Selected) {
    if ($Selected -eq 'OpenEmby') {
        Start-Process 'http://127.0.0.1:8096'
        return 0
    }
    if ($Selected -eq 'Install') {
        & "$PSHOME\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'Start-Install.ps1') | Out-Host
        return $LASTEXITCODE
    }
    $file = switch ($Selected) {
        'Install' { 'Install.ps1' }
        'Update' { 'Update.ps1' }
        'Backup' { 'Backup.ps1' }
        'Test' { 'Test-MediaStack.ps1' }
        'Syntax' { 'Check-Syntax.ps1' }
        'StartServices' { 'Service-Control.ps1' }
        'ServiceStatus' { 'Service-Control.ps1' }
        default { 'Set-Proxy.ps1' }
    }
    if ($Selected -in @('StartServices','Update','Backup','Proxy','Direct','Auto')) {
        $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
        if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
            if ($Elevated) { throw 'Administrator rights were not granted.' }
            # Validated action only; quote script path for spaces. No shell interpolation.
            $process = Start-Process -FilePath "$PSHOME\powershell.exe" -Verb RunAs -Wait -PassThru -ArgumentList @(
                '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"{0}"' -f $PSCommandPath), '-Action', $Selected, '-Elevated'
            )
            return $process.ExitCode
        }
    }
    & "$PSHOME\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'Check-Syntax.ps1') | Out-Host
    if ($LASTEXITCODE -ne 0) { return $LASTEXITCODE }
    if ($Selected -eq 'Syntax') { return 0 }
    $extra = @()
    if ($file -eq 'Set-Proxy.ps1') { $extra = @('-Mode', $Selected) }
    if ($file -eq 'Service-Control.ps1') { $extra = @('-Action', $(if ($Selected -eq 'StartServices') { 'Start' } else { 'Status' })) }
    & "$PSHOME\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot $file) @extra | Out-Host
    return $LASTEXITCODE
}
try {
    if ($Action -ne 'Menu') { exit (Invoke-Action $Action) }
    do {
        Write-Host "`nEmby + MetaTube Manager | 请在目标机操作 | 安装时可选择部署目录" -ForegroundColor Cyan
        Write-Host '日常：1 启动服务  2 打开 Emby 网页  3 查看服务与 HTTP 状态'
        Write-Host '维护：4 安装/强制安装  5 诊断  6 备份  7 升级'
        Write-Host '代理：8 查看代理  9 设置/启用代理  10 直连  11 自动选择'
        Write-Host '检查：12 离线语法检查  0 退出'
        $choice = Read-Host '请选择'
        if ($choice -eq '0') { break }
        if ($choice -notmatch '^([1-9]|1[0-2])$') { continue }
        try {
            $code = Invoke-Action $actions[[int]$choice - 1]
            if ($code -ne 0) { Write-Warning "Action failed (exit $code). Read the output above." }
        } catch { Write-Warning $_.Exception.Message }
    } while ($true)
} catch {
    Write-Error $_ -ErrorAction Continue
    exit 1
} finally {
    if ($Elevated) { $null = Read-Host 'Press Enter to close this administrator window' }
}
