<#
Create GitHub issues from docs/BACKLOG_ISSUES.md

This script is intentionally small and robust: it runs in DRY RUN mode by default (no token required) and will print the API payloads it
would POST. To make changes, supply `-Post` and export a token in the runner environment as `$env:GITHUB_TOKEN`.
#>

param(
  [switch]$Post
)

#########################################
# Configuration
#########################################
$owner = 'SamitDharia'
$repo  = 'Autonomous-Trading-Agent'
$base  = "https://api.github.com/repos/$owner/$repo"
$headers = @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'repo-agent'; 'Accept' = 'application/vnd.github+json' }

if ($Post -and -not $env:GITHUB_TOKEN) {
  Write-Host "No GITHUB_TOKEN found in environment. Export token and re-run with -Post when you want to make changes. Ex: `$env:GITHUB_TOKEN = '<token>'`" -ForegroundColor Yellow
  exit 1
} elseif (-not $env:GITHUB_TOKEN) {
  Write-Host "No GITHUB_TOKEN found; proceeding in DRY RUN mode (no remote changes will be made)." -ForegroundColor Yellow
}

function Invoke-Api([string]$Method, [string]$Url, $Body) {
  $json = if ($Body) { $Body | ConvertTo-Json -Depth 5 } else { $null }
  if ($Post) {
    return Invoke-RestMethod -Uri $Url -Method $Method -Headers $headers -Body $json -ErrorAction Stop
  } else {
    Write-Host "DRY RUN: $Method $Url" -ForegroundColor Cyan
    if ($json) { Write-Host $json }
    return $null
  }
}

#########################################
# Ensure milestone exists
#########################################
try { $milestones = Invoke-RestMethod -Uri "$base/milestones?state=open" -Headers $headers -Method Get -ErrorAction Stop } catch { $milestones = @() }
$ms = $milestones | Where-Object { $_.title -eq 'Backlog v1.0' }
if (-not $ms) {
  $mBody = @{ title = 'Backlog v1.0'; state = 'open'; description = "Imported from docs/BACKLOG.md on $(Get-Date -Format o)" }
  Invoke-Api -Method Post -Url "$base/milestones" -Body $mBody | Out-Null
  Write-Host "Milestone created or queued (Post mode)." -ForegroundColor Green
} else { Write-Host "Milestone exists: $($ms.title)" -ForegroundColor Green }

#########################################
# Ensure labels exist
#########################################
$labelsToEnsure = @(
  @{ name = 'epic'; color = '0e8a16'; description = 'High level epic' },
  @{ name = 'task'; color = '1d76db'; description = 'Work item / task' },
  @{ name = 'backlog'; color = 'd4c5f9'; description = 'Backlog item' }
)
try { $existing = Invoke-RestMethod -Uri "$base/labels" -Headers $headers -Method Get -ErrorAction Stop } catch { $existing = @() }
foreach ($lab in $labelsToEnsure) {
  if ($existing.name -contains $lab.name) { Write-Host "Label exists: $($lab.name)" }
  else { Invoke-Api -Method Post -Url "$base/labels" -Body $lab | Out-Null; Write-Host "Label created or queued: $($lab.name)" }
}

#########################################
# Parse prepared issues file
#########################################
$issueFile = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) '..\docs\BACKLOG_ISSUES.md'
if (-not (Test-Path $issueFile)) { Write-Host "Prepared issues file not found: $issueFile" -ForegroundColor Yellow; exit 1 }
$issuesText = Get-Content $issueFile -Raw

$blocks = $issuesText -split "(?m)^---\s*$" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
$parsed = @()
foreach ($b in $blocks) {
  $lines = $b -split "`n"
  $titleLine = $lines | Where-Object { $_ -match '^Title:' } | Select-Object -First 1
  if (-not $titleLine) { continue }
  $title = ($titleLine -replace '^Title:\s*','').Trim()
  $bodyIndex = ($lines | Select-String -Pattern '^Body:' -List | ForEach-Object { $lines.IndexOf($_.ToString()) })
  if ($bodyIndex -ge 0) {
    $labelsLineIndex = ($lines | Where-Object { $_ -match '^Labels:' } | ForEach-Object { $lines.IndexOf($_) })
    if ($labelsLineIndex -ge 0) { $bodyLines = $lines[($bodyIndex+1)..($labelsLineIndex-1)] }
    else { $bodyLines = $lines[($bodyIndex+1)..($lines.Length-1)] }
    $body = ($bodyLines -join "`n").Trim()
  } else { $body = '' }
  $labels = $lines | Where-Object { $_ -match '^Labels:' } | ForEach-Object { ($_ -replace '^Labels:\s*','').Trim() } | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
  if (-not $labels) { $labels = @('backlog') }
  $parsed += @{ title = $title; body = $body; labels = $labels }
}

try { $msList = Invoke-RestMethod -Uri "$base/milestones?state=open" -Headers $headers -Method Get -ErrorAction Stop } catch { $msList = @() }
$milestoneNumber = ($msList | Where-Object { $_.title -eq 'Backlog v1.0' }).number

foreach ($p in $parsed) {
  $payload = @{ title = $p.title; body = $p.body; labels = $p.labels; milestone = $milestoneNumber }
  $res = Invoke-Api -Method Post -Url "$base/issues" -Body $payload
  if ($Post -and $res) { Write-Host "Created: $($res.html_url)" -ForegroundColor Green } else { Write-Host "Prepared issue: $($p.title)" -ForegroundColor Green }
}

Write-Host "Done. Rerun with -Post to actually create items (requires valid token and repo access)." -ForegroundColor Cyan
<#
Create GitHub issues from docs/BACKLOG_ISSUES.md

Usage:
  - Export a personal access token with Issues write access into $env:GITHUB_TOKEN
  - Dry-run: run .\scripts\create_github_issues.ps1 (no changes sent)
  - Post: run .\scripts\create_github_issues.ps1 -Post
#>

param(
  [switch]$Post
)

$owner = 'SamitDharia'
$repo  = 'Autonomous-Trading-Agent'
$base  = "https://api.github.com/repos/$owner/$repo"
$headers = @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'repo-agent'; 'Accept' = 'application/vnd.github+json' }

if (-not $env:GITHUB_TOKEN) {
  Write-Host "No GITHUB_TOKEN found in environment. Export token and re-run. Ex: `$env:GITHUB_TOKEN = '<token>'`" -ForegroundColor Yellow
  exit 1
}

function Invoke-Api([string]$Method, [string]$Url, $Body) {
  $json = if ($Body) { $Body | ConvertTo-Json -Depth 5 } else { $null }
  if ($Post) {
    return Invoke-RestMethod -Uri $Url -Method $Method -Headers $headers -Body $json -ErrorAction Stop
  } else {
    Write-Host "DRY RUN: $Method $Url" -ForegroundColor Cyan
    if ($json) { Write-Host $json }
    return $null
  }
}

try { $milestones = Invoke-RestMethod -Uri "$base/milestones?state=open" -Headers $headers -Method Get -ErrorAction Stop } catch { $milestones = @() }
$ms = $milestones | Where-Object { $_.title -eq 'Backlog v1.0' }
if (-not $ms) {
  $mBody = @{ title = 'Backlog v1.0'; state = 'open'; description = "Imported from docs/BACKLOG.md on $(Get-Date -Format o)" }
  Invoke-Api -Method Post -Url "$base/milestones" -Body $mBody | Out-Null
  Write-Host "Milestone created or queued (Post mode)." -ForegroundColor Green
} else { Write-Host "Milestone exists: $($ms.title)" -ForegroundColor Green }

$labelsToEnsure = @(
  @{ name = 'epic'; color = '0e8a16'; description = 'High level epic' },
  @{ name = 'task'; color = '1d76db'; description = 'Work item / task' },
  @{ name = 'backlog'; color = 'd4c5f9'; description = 'Backlog item' }
)
try { $existing = Invoke-RestMethod -Uri "$base/labels" -Headers $headers -Method Get -ErrorAction Stop } catch { $existing = @() }
foreach ($lab in $labelsToEnsure) {
  if ($existing.name -contains $lab.name) { Write-Host "Label exists: $($lab.name)" }
  else { Invoke-Api -Method Post -Url "$base/labels" -Body $lab | Out-Null; Write-Host "Label created or queued: $($lab.name)" }
}

$issueFile = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) '..\docs\BACKLOG_ISSUES.md'
if (-not (Test-Path $issueFile)) { Write-Host "Prepared issues file not found: $issueFile" -ForegroundColor Yellow; exit 1 }
$issuesText = Get-Content $issueFile -Raw

$blocks = $issuesText -split "(?m)^---\s*$" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
$parsed = @()
foreach ($b in $blocks) {
  $titleLine = ($b -split "`n") | Where-Object { $_ -match '^Title:' } | Select-Object -First 1
  if (-not $titleLine) { continue }
  $title = ($titleLine -replace '^Title:\s*','').Trim()
  $bodyStart = ($b -split "`n") | Select-String -Pattern '^Body:' -List | Select-Object -First 1
  if ($bodyStart) {
    $bodyIndex = ($b -split "`n").IndexOf($bodyStart.ToString())
    $labelsLine = ($b -split "`n") | Where-Object { $_ -match '^Labels:' } | Select-Object -First 1
    if ($labelsLine) { $bodyLines = ($b -split "`n")[($bodyIndex+1)..( ($b -split "`n").IndexOf($labelsLine) - 1 )] }
    else { $bodyLines = ($b -split "`n")[($bodyIndex+1)..($b -split "`n").Length] }
    $body = ($bodyLines -join "`n").Trim()
  } else { $body = '' }
  $labels = ($b -split "`n") | Where-Object { $_ -match '^Labels:' } | ForEach-Object { ($_ -replace '^Labels:\s*','').Trim() } | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
  if (-not $labels) { $labels = @('backlog') }
  $parsed += @{ title = $title; body = $body; labels = $labels }
}

try { $msList = Invoke-RestMethod -Uri "$base/milestones?state=open" -Headers $headers -Method Get -ErrorAction Stop } catch { $msList = @() }
$milestoneNumber = ($msList | Where-Object { $_.title -eq 'Backlog v1.0' }).number

foreach ($p in $parsed) {
  $payload = @{ title = $p.title; body = $p.body; labels = $p.labels; milestone = $milestoneNumber }
  $res = Invoke-Api -Method Post -Url "$base/issues" -Body $payload
  if ($Post -and $res) { Write-Host "Created: $($res.html_url)" -ForegroundColor Green } else { Write-Host "Prepared issue: $($p.title)" -ForegroundColor Green }
}

Write-Host "Done." -ForegroundColor Cyan
<#
Usage:
  - Export a personal access token with Issues write access into `$env:GITHUB_TOKEN` for this PowerShell session.
  - Dry-run (default): run `.\scripts\create_github_issues.ps1` (no changes will be posted).
  - To actually post: run `.\scripts\create_github_issues.ps1 -Post`.
param(
  [switch]$Post
)

#########################################
# Configuration
#########################################
$owner = 'SamitDharia'
$repo  = 'Autonomous-Trading-Agent'
$base  = "https://api.github.com/repos/$owner/$repo"
$headers = @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'repo-agent'; 'Accept' = 'application/vnd.github+json' }

if (-not $env:GITHUB_TOKEN) {
  Write-Host "No GITHUB_TOKEN found in environment. Export token and re-run. Ex: `$env:GITHUB_TOKEN = '<token>'`" -ForegroundColor Yellow
  exit 1
}

function Invoke-Api([string]$Method, [string]$Url, $Body) {
  $json = if ($Body) { $Body | ConvertTo-Json -Depth 5 } else { $null }
  if ($Post) {
    return Invoke-RestMethod -Uri $Url -Method $Method -Headers $headers -Body $json -ErrorAction Stop
  } else {
    Write-Host "DRY RUN: $Method $Url" -ForegroundColor Cyan
    if ($json) { Write-Host $json }
    return $null
  }
}

try {
  # 1) Create milestone if not exists (open)
  $milestones = Invoke-RestMethod -Uri "$base/milestones?state=open" -Headers $headers -Method Get -ErrorAction Stop
} catch {
  $milestones = @()
}
$ms = $milestones | Where-Object { $_.title -eq 'Backlog v1.0' }
if (-not $ms) {
  $mBody = @{ title = 'Backlog v1.0'; state = 'open'; description = "Imported from docs/BACKLOG.md on $(Get-Date -Format o)" }
  Invoke-Api -Method Post -Url "$base/milestones" -Body $mBody | Out-Null
  Write-Host "Milestone created or queued (Post mode)." -ForegroundColor Green
} else {
  Write-Host "Milestone exists: $($ms.title)" -ForegroundColor Green
}

#########################################
# Ensure labels exist
#########################################
$labelsToEnsure = @(
  @{ name = 'epic'; color = '0e8a16'; description = 'High level epic' },
  @{ name = 'task'; color = '1d76db'; description = 'Work item / task' },
  @{ name = 'backlog'; color = 'd4c5f9'; description = 'Backlog item' }
)
try { $existing = Invoke-RestMethod -Uri "$base/labels" -Headers $headers -Method Get -ErrorAction Stop } catch { $existing = @() }
foreach ($lab in $labelsToEnsure) {
  if ($existing.name -contains $lab.name) { Write-Host "Label exists: $($lab.name)" }
  else { Invoke-Api -Method Post -Url "$base/labels" -Body $lab | Out-Null; Write-Host "Label created or queued: $($lab.name)" }
}

#########################################
# Read prepared issues and create
#########################################
$issueFile = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) '..\docs\BACKLOG_ISSUES.md'
if (-not (Test-Path $issueFile)) { Write-Host "Prepared issues file not found: $issueFile" -ForegroundColor Yellow; exit 1 }
$issuesText = Get-Content $issueFile -Raw

# Parse blocks separated by '---'
$blocks = $issuesText -split "(?m)^---\s*$" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
$parsed = @()
foreach ($b in $blocks) {
  $titleLine = ($b -split "`n") | Where-Object { $_ -match '^Title:' } | Select-Object -First 1
  if (-not $titleLine) { continue }
  $title = ($titleLine -replace '^Title:\s*','').Trim()
  $bodyStart = ($b -split "`n") | Select-String -Pattern '^Body:' -List | Select-Object -First 1
  if ($bodyStart) {
    $bodyIndex = ($b -split "`n").IndexOf($bodyStart.ToString())
    $labelsLine = ($b -split "`n") | Where-Object { $_ -match '^Labels:' } | Select-Object -First 1
    if ($labelsLine) {
      $bodyLines = ($b -split "`n")[($bodyIndex+1)..( ($b -split "`n").IndexOf($labelsLine) - 1 )]
    } else {
      $bodyLines = ($b -split "`n")[($bodyIndex+1)..($b -split "`n").Length]
    }
    $body = ($bodyLines -join "`n").Trim()
  } else { $body = '' }
  $labels = ($b -split "`n") | Where-Object { $_ -match '^Labels:' } | ForEach-Object { ($_ -replace '^Labels:\s*','').Trim() } | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
  if (-not $labels) { $labels = @('backlog') }
  $parsed += @{ title = $title; body = $body; labels = $labels }
}

try { $msList = Invoke-RestMethod -Uri "$base/milestones?state=open" -Headers $headers -Method Get -ErrorAction Stop } catch { $msList = @() }
$milestoneNumber = ($msList | Where-Object { $_.title -eq 'Backlog v1.0' }).number

foreach ($p in $parsed) {
  $payload = @{ title = $p.title; body = $p.body; labels = $p.labels; milestone = $milestoneNumber }
  $res = Invoke-Api -Method Post -Url "$base/issues" -Body $payload
  if ($Post -and $res) { Write-Host "Created: $($res.html_url)" -ForegroundColor Green }
  else { Write-Host "Prepared issue: $($p.title)" -ForegroundColor Green }
}

Write-Host "Done." -ForegroundColor Cyan





























































































Write-Host "Done. Rerun with -Post to actually create items (requires valid token and repo access)." -ForegroundColor Cyan}  Write-Host "Prepared issue: $($p.title)" -ForegroundColor Green  Invoke-Api -Method Post -Url "$base/issues" -Body $payload | Out-Null  $payload = @{ title = $p.title; body = $p.body; labels = $p.labels; milestone = $milestoneNumber }foreach ($p in $parsed) {# 5) Create issues (or dry-run print)$milestoneNumber = ($msList | Where-Object { $_.title -eq 'Backlog v1.0' }).number$msList = try { Invoke-RestMethod -Uri "$base/milestones?state=open" -Headers $headers -Method Get -ErrorAction Stop } catch { @() }# 4) Find milestone number (if any)}  $parsed += @{ title = $title; body = $body; labels = $labels }  if (-not $labels) { $labels = @('backlog') }  $labels = ($b -split "`n") | Where-Object { $_ -match '^Labels:' } | ForEach-Object { ($_ -replace '^Labels:\s*','').Trim() } | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }  } else { $body = '' }    $body = ($bodyLines -join "`n").Trim()    }      ($b -split "`n")[($bodyIndex+1)..($b -split "`n").Length]    } else {      ($b -split "`n")[($bodyIndex+1)..( ($b -split "`n").IndexOf($labelsLine) - 1 )]    $bodyLines = if ($labelsLine) {    $labelsLine = ($b -split "`n") | Where-Object { $_ -match '^Labels:' } | Select-Object -First 1    $bodyIndex = ($b -split "`n").IndexOf($bodyStart.ToString())  if ($bodyStart) {  $bodyStart = ($b -split "`n") | Select-String -Pattern '^Body:' -List | Select-Object -First 1  # Body is lines after 'Body:' until 'Labels:' or end  $title = ($titleLine -replace '^Title:\s*','').Trim()  if (-not $titleLine) { continue }  $titleLine = ($b -split "`n") | Where-Object { $_ -match '^Title:' } | Select-Object -First 1  # First line '##' or title; look for 'Title: ' lineforeach ($b in $blocks) {$parsed = @()$blocks = $issuesText -split "(?m)^---\s*$" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }# Simple parser: split by '---' blocks$issuesText = Get-Content $issueFile -Raw$issueFile = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) '..\docs\BACKLOG_ISSUES.md'# 3) Read prepared issues file}  else { Invoke-Api -Method Post -Url "$base/labels" -Body $lab | Out-Null; Write-Host "Label prepared: $($lab.name)" }  if ($existing.name -contains $lab.name) { Write-Host "Label exists: $($lab.name)" }foreach ($lab in $labelsToEnsure) {$existing = try { Invoke-RestMethod -Uri "$base/labels" -Headers $headers -Method Get -ErrorAction Stop } catch { @() })  @{ name = 'backlog'; color = 'd4c5f9'; description = 'Backlog item' }  @{ name = 'task'; color = '1d76db'; description = 'Work item / task' },  @{ name = 'epic'; color = '0e8a16'; description = 'High level epic' },$labelsToEnsure = @(# 2) Ensure labels exist}  Write-Host "Milestone exists: $($ms.title)" -ForegroundColor Green} else {  Write-Host "Milestone prepared (or would be created in Post mode)." -ForegroundColor Green  Invoke-Api -Method Post -Url "$base/milestones" -Body $mBody | Out-Null  $mBody = @{ title = 'Backlog v1.0'; state = 'open'; description = "Imported from docs/BACKLOG.md on $(Get-Date -Format o)" }if (-not $ms) {$ms = $milestones | Where-Object { $_.title -eq 'Backlog v1.0' }$milestones = try { Invoke-RestMethod -Uri "$base/milestones?state=open" -Headers $headers -Method Get -ErrorAction Stop } catch { @() }# 1) Create milestone if not exists (open)}  }    return $null    if ($json) { Write-Host $json }    Write-Host "DRY RUN: $Method $Url" -ForegroundColor Cyan  } else {    return Invoke-RestMethod -Uri $Url -Method $Method -Headers $headers -Body $json -ErrorAction Stop  if ($Post) {  $json = if ($Body) { $Body | ConvertTo-Json -Depth 5 } else { $null }function Invoke-Api([string]$Method, [string]$Url, $Body) {}  Write-Host "No GITHUB_TOKEN found in environment. Export token and re-run. Ex: $env:GITHUB_TOKEN = '<token>'" -ForegroundColor Yellowif (-not $env:GITHUB_TOKEN) {$headers = @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'repo-agent'; 'Accept' = 'application/vnd.github+json' }$base  = "https://api.github.com/repos/$owner/$repo"$repo  = 'Autonomous-Trading-Agent'$owner = 'SamitDharia'# Configuration)  [switch]$Postparam(#>This script will create a milestone "Backlog v1.0", ensure labels `epic`, `task`, and `backlog` exist, then create the issues listed in `docs/BACKLOG_ISSUES.md`.  - To actually post: `.
eate_github_issues.ps1 -Post`eate_github_issues.ps1 -WhatIf` or run without `-Post`.