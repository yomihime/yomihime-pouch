[CmdletBinding()]
param(
    [ValidateNotNullOrEmpty()]
    [string]$InstallDir = "NapCat",

    [ValidatePattern('^\d*$')]
    [string]$QQ = ""
)

# Windows PowerShell 5.1 compatible.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Manual Shell only. OneKey / NapCatInstaller.exe is intentionally not used.
# Keep this variant when adding a future OneKey installer; the two deployment
# models have different portability, QQ ownership and failure modes.
$NapCatUrl = "https://github.com/NapNeko/NapCatQQ/releases/latest/download/NapCat.Shell.zip"

# Official Tencent QQ x64 installer, only used when a normal QQ installation is not found.
$QQUrl = "https://qqdl.gtimg.cn/qqfile/QQNT/9.9.33/release/497e2f1f/QQ_9.9.33_260813_x64_01.exe"
$QQSha256 = "B25C0D3CE9DF764074A9118D0DED927E1B2D7EBF60E306112E8DF18A040EC492"

# Required download order.
$DownloadRoutes = @(
    "http://127.0.0.1:7890",
    "http://127.0.0.1:7897",
    ""
)

function Write-StatusStep([string]$Text) {
    Write-Host ""
    Write-Host "==> $Text" -ForegroundColor Cyan
}

function Write-StatusOk([string]$Text) {
    Write-Host "[OK] $Text" -ForegroundColor Green
}

function Write-StatusWarning([string]$Text) {
    Write-Host "[!]  $Text" -ForegroundColor Yellow
}

function Resolve-AbsolutePath([string]$Path) {
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath(
        [System.IO.Path]::Combine((Get-Location).Path, $Path)
    )
}

function Confirm-SafeInstallPath([string]$Path) {
    $normalizedPath = $Path.TrimEnd('\')
    $volumeRoot = [System.IO.Path]::GetPathRoot($Path).TrimEnd('\')

    if ($normalizedPath -ieq $volumeRoot) {
        throw "InstallDir cannot be a drive root: $Path"
    }

    $currentDirectory = (Resolve-AbsolutePath (Get-Location).Path).TrimEnd('\')
    if ($normalizedPath -ieq $currentDirectory) {
        throw "InstallDir cannot be the current working directory: $Path"
    }

    if (-not [string]::IsNullOrWhiteSpace($MyInvocation.ScriptName)) {
        $scriptPath = Resolve-AbsolutePath $MyInvocation.ScriptName
        $pathPrefix = $normalizedPath + [System.IO.Path]::DirectorySeparatorChar

        if ($scriptPath.StartsWith($pathPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "InstallDir cannot contain the installer script itself: $Path"
        }
    }
}

function Test-ZipArchive([string]$Path) {
    if (-not [System.IO.File]::Exists($Path)) {
        return $false
    }

    $info = New-Object System.IO.FileInfo($Path)
    if ($info.Length -lt 100KB) {
        return $false
    }

    $stream = [System.IO.File]::OpenRead($Path)

    try {
        return (
            $stream.ReadByte() -eq 0x50 -and
            $stream.ReadByte() -eq 0x4B
        )
    }
    finally {
        $stream.Dispose()
    }
}

function Test-ExecutableInstaller([string]$Path) {
    if (-not [System.IO.File]::Exists($Path)) {
        return $false
    }

    $info = New-Object System.IO.FileInfo($Path)
    if ($info.Length -lt 50MB) {
        return $false
    }

    $stream = [System.IO.File]::OpenRead($Path)

    try {
        return (
            $stream.ReadByte() -eq 0x4D -and
            $stream.ReadByte() -eq 0x5A
        )
    }
    finally {
        $stream.Dispose()
    }
}

function Invoke-DownloadWithFallback(
    [string]$Url,
    [string]$Destination,
    [ValidateSet("zip", "exe")]
    [string]$Kind,
    [string]$ExpectedSha256 = ""
) {
    if ($null -eq (Get-Command curl.exe -ErrorAction SilentlyContinue)) {
        throw "curl.exe not found. Windows 10/11 normally includes curl.exe."
    }

    foreach ($route in $DownloadRoutes) {
        $partialPath = $Destination + ".part"

        if ([System.IO.File]::Exists($partialPath)) {
            [System.IO.File]::Delete($partialPath)
        }

        $curlArguments = @(
            "--fail",
            "--location",
            "--connect-timeout", "10",
            "--retry", "1",
            "--retry-delay", "1",
            "--output", $partialPath
        )

        if ([string]::IsNullOrEmpty($route)) {
            Write-Host "Trying direct..."
            $curlArguments += @("--proxy", "", "--noproxy", "*")
        }
        else {
            Write-Host "Trying proxy $route ..."
            $curlArguments += @("--proxy", $route)
        }

        $curlArguments += $Url

        & curl.exe @curlArguments
        $curlExitCode = $LASTEXITCODE

        if ($curlExitCode -ne 0) {
            if ([System.IO.File]::Exists($partialPath)) {
                [System.IO.File]::Delete($partialPath)
            }
            continue
        }

        if ($Kind -eq "zip") {
            $isValid = Test-ZipArchive $partialPath
        }
        else {
            $isValid = Test-ExecutableInstaller $partialPath
        }

        if (-not $isValid) {
            Write-StatusWarning "Downloaded file failed format/size validation."
            [System.IO.File]::Delete($partialPath)
            continue
        }

        if (-not [string]::IsNullOrEmpty($ExpectedSha256)) {
            $actualHash = (Get-FileHash -LiteralPath $partialPath -Algorithm SHA256).Hash.ToUpperInvariant()

            if ($actualHash -ne $ExpectedSha256.ToUpperInvariant()) {
                Write-StatusWarning "SHA256 mismatch."
                Write-Host "Expected: $ExpectedSha256"
                Write-Host "Actual  : $actualHash"
                [System.IO.File]::Delete($partialPath)
                continue
            }

            Write-StatusOk "SHA256 verified."
        }

        if ([System.IO.File]::Exists($Destination)) {
            [System.IO.File]::Delete($Destination)
        }

        [System.IO.File]::Move($partialPath, $Destination)

        if ([string]::IsNullOrEmpty($route)) {
            Write-StatusOk "Downloaded directly."
        }
        else {
            Write-StatusOk "Downloaded via $route"
        }

        return
    }

    throw "All download routes failed: $Url"
}

function Resolve-QQExecutable([string]$Candidate) {
    if ([string]::IsNullOrWhiteSpace($Candidate)) {
        return $null
    }

    $candidatePath = $Candidate.Trim()

    if ($candidatePath.StartsWith('"')) {
        $endQuote = $candidatePath.IndexOf('"', 1)
        if ($endQuote -gt 1) {
            $candidatePath = $candidatePath.Substring(1, $endQuote - 1)
        }
    }
    else {
        $candidatePath = $candidatePath -replace ',\d+$', ''
    }

    if ([System.IO.File]::Exists($candidatePath)) {
        if ([System.IO.Path]::GetFileName($candidatePath) -ieq "QQ.exe") {
            return $candidatePath
        }

        $parent = [System.IO.Path]::GetDirectoryName($candidatePath)
        if (-not [string]::IsNullOrEmpty($parent)) {
            $qqExecutable = [System.IO.Path]::Combine($parent, "QQ.exe")
            if ([System.IO.File]::Exists($qqExecutable)) {
                return $qqExecutable
            }
        }
    }

    if ([System.IO.Directory]::Exists($candidatePath)) {
        $qqExecutable = [System.IO.Path]::Combine($candidatePath, "QQ.exe")
        if ([System.IO.File]::Exists($qqExecutable)) {
            return $qqExecutable
        }
    }

    return $null
}

function Find-InstalledQQ {
    $registryKeys = @(
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\QQ",
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\QQ",
        "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\QQ"
    )

    foreach ($key in $registryKeys) {
        try {
            $item = Get-ItemProperty -Path $key -ErrorAction Stop

            foreach ($value in @($item.InstallLocation, $item.DisplayIcon)) {
                $resolved = Resolve-QQExecutable $value
                if (-not [string]::IsNullOrEmpty($resolved)) {
                    return $resolved
                }
            }

            if (-not [string]::IsNullOrWhiteSpace($item.UninstallString)) {
                $uninstallCommand = $item.UninstallString.Trim()

                if ($uninstallCommand.StartsWith('"')) {
                    $endQuote = $uninstallCommand.IndexOf('"', 1)
                    if ($endQuote -gt 1) {
                        $uninstallCommand = $uninstallCommand.Substring(1, $endQuote - 1)
                    }
                }
                else {
                    $space = $uninstallCommand.IndexOf(" ")
                    if ($space -gt 0) {
                        $uninstallCommand = $uninstallCommand.Substring(0, $space)
                    }
                }

                $resolved = Resolve-QQExecutable $uninstallCommand
                if (-not [string]::IsNullOrEmpty($resolved)) {
                    return $resolved
                }
            }
        }
        catch {
            # Continue to the next registry location.
        }
    }

    $commonCandidates = @(
        "$env:ProgramFiles\Tencent\QQNT\QQ.exe",
        "${env:ProgramFiles(x86)}\Tencent\QQNT\QQ.exe",
        "$env:LOCALAPPDATA\Programs\Tencent\QQNT\QQ.exe"
    )

    foreach ($candidate in $commonCandidates) {
        if (-not [string]::IsNullOrWhiteSpace($candidate) -and [System.IO.File]::Exists($candidate)) {
            return $candidate
        }
    }

    return $null
}

function Find-NapCatShellDirectory([string]$Root) {
    $directories = @($Root)

    $directories += Get-ChildItem `
        -LiteralPath $Root `
        -Directory `
        -Recurse `
        -ErrorAction SilentlyContinue |
        ForEach-Object { $_.FullName }

    foreach ($directory in $directories) {
        $mainExecutable = Join-Path $directory "NapCatWinBootMain.exe"
        $hookLibrary = Join-Path $directory "NapCatWinBootHook.dll"
        $mainModule = Join-Path $directory "napcat.mjs"

        if (
            [System.IO.File]::Exists($mainExecutable) -and
            [System.IO.File]::Exists($hookLibrary) -and
            [System.IO.File]::Exists($mainModule)
        ) {
            return $directory
        }
    }

    return $null
}

# ── Environment check ───────────────────────────────────────────────────────

if ($PSVersionTable.PSVersion.Major -lt 5) {
    throw "Windows PowerShell 5.1 or newer is required."
}

$Root = Resolve-AbsolutePath $InstallDir
Confirm-SafeInstallPath $Root

$NapCatZip = Join-Path $Root "NapCat.Shell.zip"
$QQInstaller = Join-Path $Root "QQ-Setup.exe"

Write-Host ""
Write-Host "NapCat portable manual-Shell installer" -ForegroundColor Magenta
Write-Host "Target   : $Root"
Write-Host "Mode     : system-installed QQ + NapCat.Shell.zip"
Write-Host "Download : 127.0.0.1:7890 -> 127.0.0.1:7897 -> direct"
Write-Host "OneKey   : NOT USED"
Write-Host "Portable : NapCat directory only (QQ remains system-installed)"
Write-Host ""

# ── 1. Prepare a clean portable directory ───────────────────────────────────

Write-StatusStep "Prepare clean install directory"

if ([System.IO.Directory]::Exists($Root)) {
    $entries = [System.IO.Directory]::GetFileSystemEntries($Root)

    if ($entries.Length -gt 0) {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $backup = $Root + ".backup-" + $stamp

        while ([System.IO.Directory]::Exists($backup)) {
            Start-Sleep -Seconds 1
            $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
            $backup = $Root + ".backup-" + $stamp
        }

        Write-StatusWarning "Existing directory found."
        Write-Host "Backup -> $backup"

        [System.IO.Directory]::Move($Root, $backup)
    }
    else {
        [System.IO.Directory]::Delete($Root)
    }
}

[System.IO.Directory]::CreateDirectory($Root) | Out-Null
Write-StatusOk "Created $Root"

# ── 2. Ensure a normal system QQ installation exists ────────────────────────

Write-StatusStep "Check normal QQ installation"

$QQExecutable = Find-InstalledQQ

if ([string]::IsNullOrEmpty($QQExecutable)) {
    Write-StatusWarning "Normal installed QQ was not found."
    Write-Host "Downloading official Tencent QQ x64 installer..."

    Invoke-DownloadWithFallback `
        -Url $QQUrl `
        -Destination $QQInstaller `
        -Kind "exe" `
        -ExpectedSha256 $QQSha256

    Write-Host ""
    Write-Host "QQ installer will open now." -ForegroundColor Yellow
    Write-Host "Install QQ normally, then let the installer close." -ForegroundColor Yellow
    Write-Host ""

    $process = Start-Process `
        -FilePath $QQInstaller `
        -PassThru `
        -Wait

    Write-Host "QQ installer exit code: $($process.ExitCode)"

    Start-Sleep -Seconds 2
    $QQExecutable = Find-InstalledQQ

    if ([string]::IsNullOrEmpty($QQExecutable)) {
        throw @"
QQ installation was not detected after the installer closed.

Please install QQ normally and then run this script again.
"@
    }
}

Write-StatusOk "QQ found:"
Write-Host "  $QQExecutable"

try {
    $version = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($QQExecutable)
    if (-not [string]::IsNullOrWhiteSpace($version.FileVersion)) {
        Write-Host "QQ FileVersion: $($version.FileVersion)"
    }
}
catch {
    Write-StatusWarning "Unable to read the QQ file version."
}

# ── 3. Download manual Shell ────────────────────────────────────────────────

Write-StatusStep "Download NapCat.Shell.zip"

Invoke-DownloadWithFallback `
    -Url $NapCatUrl `
    -Destination $NapCatZip `
    -Kind "zip"

Write-Host "NapCat Shell SHA256: $((Get-FileHash -LiteralPath $NapCatZip -Algorithm SHA256).Hash)"

# ── 4. Extract to a relative Shell folder ───────────────────────────────────

Write-StatusStep "Extract NapCat Shell"

$ExtractDir = Join-Path $Root "Shell"
[System.IO.Directory]::CreateDirectory($ExtractDir) | Out-Null

Expand-Archive `
    -LiteralPath $NapCatZip `
    -DestinationPath $ExtractDir `
    -Force

$ShellDir = Find-NapCatShellDirectory $ExtractDir

if ([string]::IsNullOrEmpty($ShellDir)) {
    throw @"
NapCat Shell runtime was not found after extraction.

Expected files include:
  NapCatWinBootMain.exe
  NapCatWinBootHook.dll
  napcat.mjs
"@
}

Write-StatusOk "Shell runtime found during installation:"
Write-Host "  $ShellDir"
Write-Host ""
Write-Host "Note: this absolute path is not written into the runtime launcher."

# ── 5. Create portable launchers ────────────────────────────────────────────

Write-StatusStep "Create portable launcher"

$StartPs1 = Join-Path $Root "start-napcat.ps1"
$StartCmd = Join-Path $Root "start-napcat.cmd"
$QQFile = Join-Path $Root "qq.txt"

$portableLauncherPs1 = @'
param(
    [ValidatePattern('^\d*$')]
    [string]$QQ = ""
)

$ErrorActionPreference = "Stop"

# Always derive the installation root from this script.
$Root = $PSScriptRoot

if ([string]::IsNullOrEmpty($Root)) {
    $Root = Split-Path -Parent $MyInvocation.MyCommand.Path
}

# If no QQ was supplied on the command line, read an optional portable qq.txt.
if ([string]::IsNullOrWhiteSpace($QQ)) {
    $QQFile = Join-Path $Root "qq.txt"

    if (Test-Path -LiteralPath $QQFile -PathType Leaf) {
        $QQ = (Get-Content -LiteralPath $QQFile -TotalCount 1).Trim()
    }
}

if (-not [string]::IsNullOrWhiteSpace($QQ) -and $QQ -notmatch '^\d+$') {
    throw "QQ must contain digits only."
}

# Do not inherit download proxy environment variables.
$ProxyVariables = @(
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "all_proxy"
)

foreach ($name in $ProxyVariables) {
    [Environment]::SetEnvironmentVariable($name, $null, "Process")
}

[Environment]::SetEnvironmentVariable("NO_PROXY", "*", "Process")
[Environment]::SetEnvironmentVariable("no_proxy", "*", "Process")

# Search for NapCat Shell relative to this launcher's directory.
$SearchRoot = Join-Path $Root "Shell"

if (-not (Test-Path -LiteralPath $SearchRoot -PathType Container)) {
    throw "Portable Shell directory not found: $SearchRoot"
}

$ShellDir = $null
$Directories = @($SearchRoot)

$Directories += Get-ChildItem `
    -LiteralPath $SearchRoot `
    -Directory `
    -Recurse `
    -ErrorAction SilentlyContinue |
    ForEach-Object { $_.FullName }

foreach ($directory in $Directories) {
    $Main = Join-Path $directory "NapCatWinBootMain.exe"
    $Hook = Join-Path $directory "NapCatWinBootHook.dll"
    $Mjs = Join-Path $directory "napcat.mjs"

    if (
        (Test-Path -LiteralPath $Main -PathType Leaf) -and
        (Test-Path -LiteralPath $Hook -PathType Leaf) -and
        (Test-Path -LiteralPath $Mjs -PathType Leaf)
    ) {
        $ShellDir = $directory
        break
    }
}

if ([string]::IsNullOrEmpty($ShellDir)) {
    throw "NapCat Shell runtime was not found under: $SearchRoot"
}

# Official launcher choice: Windows 11 uses launcher.bat; Windows 10 uses launcher-win10.bat.
$OSBuild = [Environment]::OSVersion.Version.Build

if ($OSBuild -ge 22000) {
    $Preferred = "launcher.bat"
    $Fallback = "launcher-win10.bat"
}
else {
    $Preferred = "launcher-win10.bat"
    $Fallback = "launcher.bat"
}

$Launcher = Join-Path $ShellDir $Preferred

if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) {
    $Launcher = Join-Path $ShellDir $Fallback
}

if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) {
    throw "No supported NapCat Windows launcher was found in: $ShellDir"
}

Write-Host ""
Write-Host "NapCat root : $Root" -ForegroundColor Cyan
Write-Host "Shell       : $ShellDir" -ForegroundColor Cyan
Write-Host "Launcher    : $([System.IO.Path]::GetFileName($Launcher))" -ForegroundColor Cyan

Set-Location -LiteralPath $ShellDir

if ([string]::IsNullOrWhiteSpace($QQ)) {
    & $Launcher
}
else {
    Write-Host "QQ          : $QQ" -ForegroundColor Cyan
    & $Launcher $QQ
}
'@

Set-Content -LiteralPath $StartPs1 -Value $portableLauncherPs1 -Encoding UTF8

$portableLauncherCmd = @'
@echo off
chcp 65001 >nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-napcat.ps1" %*
pause
'@

Set-Content -LiteralPath $StartCmd -Value $portableLauncherCmd -Encoding ASCII

if (-not [string]::IsNullOrWhiteSpace($QQ)) {
    Set-Content -LiteralPath $QQFile -Value $QQ -Encoding ASCII
    Write-StatusOk "Saved default QQ to portable qq.txt"
}

Write-StatusOk "Portable launcher created:"
Write-Host "  $StartCmd"

# ── 6. Write deployment notes ───────────────────────────────────────────────

$NotesPath = Join-Path $Root "README-NapCat.txt"

$Notes = @"
NapCat portable manual-Shell deployment
=======================================

This deployment intentionally does not use:
- NapCat OneKey
- NapCatInstaller.exe
- NapCat.44498.Shell style green QQ runtime

It uses:
- a normal system-installed QQ
- official NapCat.Shell.zip

PORTABILITY
-----------

The generated launchers do not contain the install-time absolute path.
You may move the entire NapCat folder and then run start-napcat.cmd.

QQ remains a system-installed dependency and is not included in this directory.

Expected relative layout:

  NapCat\
    start-napcat.cmd
    start-napcat.ps1
    qq.txt              optional default QQ
    Shell\
      ...

QQ ACCOUNT
----------

If qq.txt exists, its first line is used as the default QQ account.
You can override it temporarily with:

  start-napcat.cmd 123456789

DOWNLOAD POLICY
---------------

Installation downloads try:

1. http://127.0.0.1:7890
2. http://127.0.0.1:7897
3. direct

RUNTIME NETWORK
---------------

The launcher clears HTTP_PROXY, HTTPS_PROXY, ALL_PROXY and their lowercase
variants for the child process. It does not change the Windows system proxy,
Clash TUN, VPN or system routing.

ASTRBOT / ONEBOT V11
--------------------

AstrBot reverse WebSocket listen:
  0.0.0.0:6199

NapCat WebSocket Client:
  ws://127.0.0.1:6199/ws

If a token is enabled, use the same token on both sides.

QQ detected during installation:
  $QQExecutable
"@

Set-Content -LiteralPath $NotesPath -Value $Notes -Encoding UTF8

# ── 7. Clean up downloaded installers and archives ──────────────────────────

if ([System.IO.File]::Exists($NapCatZip)) {
    [System.IO.File]::Delete($NapCatZip)
}

if ([System.IO.File]::Exists($QQInstaller)) {
    [System.IO.File]::Delete($QQInstaller)
}

Write-StatusStep "Finished"

Write-Host "Install root : $Root" -ForegroundColor Green
Write-Host "Start        : $StartCmd" -ForegroundColor Green

if (-not [string]::IsNullOrWhiteSpace($QQ)) {
    Write-Host "Default QQ   : stored in .\qq.txt" -ForegroundColor Green
}

Write-Host ""
Write-Host "The generated runtime launcher contains no hard-coded install path." -ForegroundColor Yellow
Write-Host "You can move the NapCat directory after installation; QQ remains system-installed." -ForegroundColor Yellow
