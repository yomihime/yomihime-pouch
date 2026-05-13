@echo off
goto :bat
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Git Commit Line-Change Statistics  v1.0.0
:: Double-click / Right-click to run. Also works in terminal:
::   git_stats.cmd
::   git_stats.cmd -Author "Name" -Since "2025-01-01"
::   git_stats.cmd -AllBranches
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:bat
cd /d "%~dp0"
setlocal
set "_PS_TMP=%TEMP%\git_stats_%RANDOM%.ps1"
more +21 "%~f0" > "%_PS_TMP%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%_PS_TMP%" %*
del "%_PS_TMP%" >nul 2>&1
endlocal
echo.
echo Press any key to exit ...
pause >nul
exit /b

param(
    [string]$Author,
    [string]$Since,
    [string]$Until,
    [string]$Branch,
    [switch]$AllBranches
)

# ── Pre-flight checks ───────────────────────────────────────────────────────
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] git is not installed or not in PATH." -ForegroundColor Red
    return
}

$gitRoot = git rev-parse --show-toplevel 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Current directory is not inside a git repository." -ForegroundColor Red
    return
}

# ── Resolve author ───────────────────────────────────────────────────────────
if (-not $Author) {
    $Author = git config user.name
    if (-not $Author) {
        Write-Host "[ERROR] No -Author provided and git config user.name is empty." -ForegroundColor Red
        Write-Host "  Usage: .\git_stats.cmd -Author 'Your Name'" -ForegroundColor Yellow
        return
    }
    Write-Host "[INFO] Author auto-detected: $Author" -ForegroundColor DarkGray
}

# ── Build git log command ────────────────────────────────────────────────────
$gitArgs = @("log", "--author=$Author", '--pretty=format:COMMIT|%H|%aI', "--numstat")
if ($Since)       { $gitArgs += "--since=$Since" }
if ($Until)       { $gitArgs += "--until=$Until" }
if ($AllBranches) { $gitArgs += "--all" }
elseif ($Branch)  { $gitArgs += $Branch }

# ── Header ───────────────────────────────────────────────────────────────────
$repoName    = Split-Path $gitRoot -Leaf
$branchLabel = if ($AllBranches) { "--all--" } elseif ($Branch) { $Branch } else { (git rev-parse --abbrev-ref HEAD) }
$rangeLabel  = "$(if($Since){$Since}else{'*'}) ~ $(if($Until){$Until}else{'*'})"

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Git Commit Statistics  v1.0.0" -ForegroundColor Cyan
Write-Host "  Repo   : $repoName" -ForegroundColor Cyan
Write-Host "  Branch : $branchLabel" -ForegroundColor Cyan
Write-Host "  Author : $Author" -ForegroundColor Cyan
Write-Host "  Range  : $rangeLabel" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# ── Collect & parse git log ──────────────────────────────────────────────────
$logOutput = & git $gitArgs

$commitList  = [System.Collections.ArrayList]::new()
$currentHash = $null; $currentDate = $null; $currentIns = 0; $currentDel = 0

foreach ($line in $logOutput) {
    if ($line -match "^COMMIT\|(.+)\|(.+)$") {
        if ($currentHash) {
            [void]$commitList.Add([PSCustomObject]@{
                Hash = $currentHash; Date = $currentDate
                Insertions = $currentIns; Deletions = $currentDel
            })
        }
        $currentHash = $Matches[1]
        $currentDate = [DateTime]::Parse($Matches[2])
        $currentIns  = 0; $currentDel = 0
    }
    elseif ($line -match "^(\d+)\s+(\d+)\s+") {
        if ($currentHash) {
            $currentIns += [int]$Matches[1]
            $currentDel += [int]$Matches[2]
        }
    }
}
if ($currentHash) {
    [void]$commitList.Add([PSCustomObject]@{
        Hash = $currentHash; Date = $currentDate
        Insertions = $currentIns; Deletions = $currentDel
    })
}
$commits = $commitList.ToArray()

if ($commits.Count -eq 0) {
    Write-Host "No commits found for author: $Author" -ForegroundColor Yellow
    return
}

$sorted    = $commits | Sort-Object Date
$firstDate = $sorted[0].Date.ToString("yyyy-MM-dd")
$lastDate  = $sorted[-1].Date.ToString("yyyy-MM-dd")
Write-Host "Total commits : $($commits.Count)    ($firstDate ~ $lastDate)" -ForegroundColor Green
Write-Host ""

# ── Helpers ──────────────────────────────────────────────────────────────────
function Show-Stats {
    param([string]$Title, [array]$GroupedData)
    Write-Host "--- $Title ---" -ForegroundColor Yellow
    $f = "{0,-20} {1,8} {2,12} {3,12} {4,12}"
    Write-Host ($f -f "Period","Commits","Inserted","Deleted","Changed")
    Write-Host ($f -f "------","-------","--------","-------","-------")
    foreach ($g in $GroupedData) {
        Write-Host ($f -f $g.Period, $g.Commits, "+$($g.Insertions)", "-$($g.Deletions)", ($g.Insertions+$g.Deletions))
    }
    $sC = ($GroupedData | Measure-Object -Property Commits    -Sum).Sum
    $sI = ($GroupedData | Measure-Object -Property Insertions -Sum).Sum
    $sD = ($GroupedData | Measure-Object -Property Deletions  -Sum).Sum
    Write-Host ($f -f "=== TOTAL ===",$sC,"+$sI","-$sD",($sI+$sD)) -ForegroundColor Green
    Write-Host ""
}

function Group-Commits {
    param([array]$Data, [scriptblock]$KeySelector)
    $Data | Group-Object $KeySelector | Sort-Object Name | ForEach-Object {
        [PSCustomObject]@{
            Period     = $_.Name
            Commits    = $_.Count
            Insertions = ($_.Group | Measure-Object -Property Insertions -Sum).Sum
            Deletions  = ($_.Group | Measure-Object -Property Deletions  -Sum).Sum
        }
    }
}

# ── Daily (last 30 days) ────────────────────────────────────────────────────
$c30   = (Get-Date).AddDays(-30)
$daily = Group-Commits ($commits | Where-Object { $_.Date -ge $c30 }) { $_.Date.ToString("yyyy-MM-dd") }
if ($daily) { Show-Stats "Daily (Last 30 Days)" $daily }
else { Write-Host "--- Daily (Last 30 Days) --- No data" -ForegroundColor DarkGray; Write-Host "" }

# ── Weekly (last 12 weeks) ──────────────────────────────────────────────────
$c12w   = (Get-Date).AddDays(-84)
$weekly = Group-Commits ($commits | Where-Object { $_.Date -ge $c12w }) {
    $d  = $_.Date
    $wk = [System.Globalization.CultureInfo]::InvariantCulture.Calendar.GetWeekOfYear(
              $d, [System.Globalization.CalendarWeekRule]::FirstFourDayWeek, [DayOfWeek]::Monday)
    "$($d.Year)-W$($wk.ToString('D2'))"
}
if ($weekly) { Show-Stats "Weekly (Last 12 Weeks)" $weekly }
else { Write-Host "--- Weekly (Last 12 Weeks) --- No data" -ForegroundColor DarkGray; Write-Host "" }

# ── Monthly ──────────────────────────────────────────────────────────────────
Show-Stats "Monthly (All Time)" (Group-Commits $commits { $_.Date.ToString("yyyy-MM") })

# ── Quarterly ────────────────────────────────────────────────────────────────
Show-Stats "Quarterly (All Time)" (Group-Commits $commits {
    $q = [Math]::Ceiling($_.Date.Month / 3); "$($_.Date.Year)-Q$q"
})

# ── Yearly ───────────────────────────────────────────────────────────────────
Show-Stats "Yearly (All Time)" (Group-Commits $commits { $_.Date.Year.ToString() })

# ── Footer ───────────────────────────────────────────────────────────────────
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Generated at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
