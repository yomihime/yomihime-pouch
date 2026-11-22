[CmdletBinding()]
param(
    [ValidateSet('Menu','Local','Lan','Firewall')][string]$Action = 'Menu',
    [ValidateRange(1,65535)][int]$Port = 3000
)
$ErrorActionPreference = 'Stop'
$exe = Join-Path $PSScriptRoot 'bin\new-api.exe'

if ($Action -eq 'Menu') {
    while ($true) {
        Write-Host "`nNew API 网关    端口 $Port"
        Write-Host '安装：1 下载最新版  2 离线导入'
        Write-Host '启动：3 本机初始化  4 局域网使用'
        Write-Host '维护：5 配置防火墙（管理员）  6 更新最新版  7 测试网关  0 退出'
        try {
            switch (Read-Host '请选择') {
                '1' { & "$PSScriptRoot\Install.ps1" }
                '2' {
                    $file = (Read-Host '官方 EXE 的完整路径（同目录需有 checksums-windows.txt）').Trim('"')
                    & "$PSScriptRoot\Install.ps1" -SourceFile $file
                }
                '3' { $Action = 'Local' }
                '4' { $Action = 'Lan' }
                '5' { $Action = 'Firewall' }
                '6' { & "$PSScriptRoot\Install.ps1" -Update }
                '7' { & "$PSScriptRoot\Test-Gateway.ps1" -BaseUrl "http://127.0.0.1:$Port/v1" }
                '0' { return }
            }
        } catch { Write-Warning $_.Exception.Message }
        if ($Action -ne 'Menu') { break }
    }
}
if (!(Test-Path -LiteralPath $exe -PathType Leaf)) { throw '请先从菜单下载或导入 New API。' }
if ($Action -eq 'Firewall') {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (!$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw '请右键 Start.cmd，以管理员身份运行，再选择配置防火墙。'
    }
    $rule = @{
        Name = 'Yomihime-NewApiGateway'
        Direction = 'Inbound'
        Action = 'Allow'
        Enabled = 'True'
        Profile = 'Private'
        Program = $exe
        Protocol = 'TCP'
        LocalPort = $Port
        RemoteAddress = 'LocalSubnet'
    }
    if (Get-NetFirewallRule -Name $rule.Name -ErrorAction SilentlyContinue) {
        Set-NetFirewallRule @rule
    } else {
        New-NetFirewallRule @rule -DisplayName 'New API Gateway (private LAN)' | Out-Null
    }
    Write-Host "已允许专用网络本地子网访问 TCP $Port。"
    return
}

$bind = '127.0.0.1'
if ($Action -eq 'Lan') { $bind = '0.0.0.0' }
$data = [IO.Directory]::CreateDirectory((Join-Path $PSScriptRoot 'data')).FullName
$oldHost = $env:HOST
$oldPort = $env:PORT
Push-Location -LiteralPath $data
try {
    $env:HOST = $bind
    $env:PORT = [string]$Port
    Write-Host "管理台 http://127.0.0.1:$Port  |  监听 $bind  |  Ctrl+C 停止"
    if ($Action -eq 'Lan') {
        Write-Host "客户端地址 http://<mini PC 的局域网 IPv4>:$Port/v1 （可用 ipconfig 查看）"
    }
    & $exe
    if ($LASTEXITCODE -ne 0) { throw "New API 退出，错误码 $LASTEXITCODE。" }
} finally {
    Pop-Location
    $env:HOST = $oldHost
    $env:PORT = $oldPort
}
