[CmdletBinding()]
param([string]$SourceFile, [switch]$Update)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')

if ($PSBoundParameters.ContainsKey('SourceFile')) {
    $source = Get-Item -LiteralPath $SourceFile
    if ($source.Name -notmatch '^new-api-v[0-9][\w.-]*\.exe$') { throw '请保留官方 EXE 的原始文件名。' }
    $name = $source.Name
    $manifest = Join-Path $source.DirectoryName 'checksums-windows.txt'
    $pattern = '^\s*([0-9a-f]{64})\s+\*?' + [regex]::Escape($name) + '\s*$'
    $entries = @(Select-String -LiteralPath $manifest -Pattern $pattern)
    if ($entries.Count -ne 1) { throw "请将同一 Release 的官方 checksums-windows.txt 与 $name 放在一起。" }
    $expected = $entries[0].Matches[0].Groups[1].Value
} else {
    $asset = Get-LatestWindowsAsset
    $name = $asset.Name
    $expected = $asset.Hash
}
Write-Host "目标程序 $name"
$bin = [IO.Directory]::CreateDirectory((Join-Path $PSScriptRoot 'bin')).FullName
$exe = Join-Path $bin 'new-api.exe'
$installed = Test-Path -LiteralPath $exe
if ($installed) {
    if ((Get-FileHash -LiteralPath $exe).Hash -eq $expected) {
        Write-Host '已安装此版本，SHA256 校验通过。'
        return
    }
    if (!$Update) { throw '已有其他版本。请先停机、备份，再选择更新。' }
}
$tempFile = Join-Path $bin ([Guid]::NewGuid().ToString() + '.download')
try {
    if ($PSBoundParameters.ContainsKey('SourceFile')) { Copy-Item -LiteralPath $source.FullName -Destination $tempFile }
    else { Invoke-ReleaseFetch $asset.Url $tempFile }
    if ((Get-FileHash -LiteralPath $tempFile).Hash -ne $expected) { throw "$name 的 SHA256 校验失败。" }
    if ($installed) {
        [IO.File]::Replace($tempFile, $exe, (Join-Path $bin 'new-api.previous.exe'))
    } else {
        [IO.File]::Move($tempFile, $exe)
    }
    Write-Host "已校验并安装 $name。"
} finally {
    if (Test-Path -LiteralPath $tempFile) { Remove-Item -LiteralPath $tempFile }
}
