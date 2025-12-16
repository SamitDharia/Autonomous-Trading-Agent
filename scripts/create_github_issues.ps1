<#
Create GitHub issues from docs/BACKLOG_ISSUES.md

This script runs in DRY RUN mode by default (no token required) and will print the API payloads it
would POST. To make changes, supply -Post and export a token in the runner environment as $env:GITHUB_TOKEN.

Usage:
  .\create_github_issues.ps1                    # Dry-run mode (no changes made)
  .\create_github_issues.ps1 -Post              # Post actual changes to GitHub (requires token)
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

# Set up headers for API calls
$headers = @{
  Authorization = "token $env:GITHUB_TOKEN"
  'User-Agent'   = 'repo-agent'
  'Accept'       = 'application/vnd.github+json'
}

#########################################
# Validation
#########################################
if ($Post -and -not $env:GITHUB_TOKEN) {
  Write-Host "Error: No GITHUB_TOKEN found in environment." -ForegroundColor Red
  Write-Host "When using -Post, you must export GITHUB_TOKEN. Example:" -ForegroundColor Yellow
  Write-Host "`$env:GITHUB_TOKEN = '<your-token>'" -ForegroundColor Cyan
  exit 1
} elseif (-not $env:GITHUB_TOKEN) {
  Write-Host "[DRY RUN MODE] No GITHUB_TOKEN found; running in dry-run (no remote changes will be made)." -ForegroundColor Yellow
}

#########################################
# Helper: API invocation
#########################################
function Invoke-Api([string]$Method, [string]$Url, $Body) {
  $json = if ($Body) { $Body | ConvertTo-Json -Depth 5 } else { $null }
  
  if ($Post) {
    Write-Host "[POST] $Method $Url" -ForegroundColor Cyan
    if ($json) { Write-Host $json }
    try {
      return Invoke-RestMethod -Uri $Url -Method $Method -Headers $headers -Body $json -ErrorAction Stop
    } catch {
      Write-Host "Error: $_" -ForegroundColor Red
      return $null
    }
  } else {
    Write-Host "[DRY RUN] $Method $Url" -ForegroundColor Cyan
    if ($json) { Write-Host $json }
    return $null
  }
}

#########################################
# 1) Create/ensure milestone
#########################################
Write-Host "`n=== Milestone ===" -ForegroundColor Magenta

$milestones = try {
  Invoke-RestMethod -Uri "$base/milestones?state=open" -Headers $headers -Method Get -ErrorAction Stop
} catch {
  @()
}

$ms = $milestones | Where-Object { $_.title -eq 'Backlog v1.0' }

if ($ms) {
  Write-Host "Milestone 'Backlog v1.0' already exists (ID: $($ms.number))." -ForegroundColor Green
} else {
  $mBody = @{
    title       = 'Backlog v1.0'
    state       = 'open'
    description = "Imported from docs/BACKLOG_ISSUES.md on $(Get-Date -Format o)"
  }
  Write-Host "Creating milestone 'Backlog v1.0'..." -ForegroundColor Cyan
  $ms = Invoke-Api -Method Post -Url "$base/milestones" -Body $mBody
  if ($ms) {
    Write-Host "Milestone created: $($ms.html_url)" -ForegroundColor Green
  }
}

#########################################
# 2) Create/ensure labels
#########################################
Write-Host "`n=== Labels ===" -ForegroundColor Magenta

$requiredLabels = @('epic', 'task', 'backlog')
$existingLabels = try {
  Invoke-RestMethod -Uri "$base/labels" -Headers $headers -Method Get -ErrorAction Stop
} catch {
  @()
}

foreach ($label in $requiredLabels) {
  $exists = $existingLabels | Where-Object { $_.name -eq $label }
  if ($exists) {
    Write-Host "Label '$label' already exists." -ForegroundColor Green
  } else {
    $lBody = @{
      name  = $label
      color = "cccccc"
    }
    Write-Host "Creating label '$label'..." -ForegroundColor Cyan
    $created = Invoke-Api -Method Post -Url "$base/labels" -Body $lBody
    if ($created) {
      Write-Host "Label created: $label" -ForegroundColor Green
    }
  }
}

#########################################
# 3) Parse BACKLOG_ISSUES.md and create issues
#########################################
Write-Host "`n=== Issues ===" -ForegroundColor Magenta

$backlogFile = "docs/BACKLOG_ISSUES.md"
if (-not (Test-Path $backlogFile)) {
  Write-Host "Error: $backlogFile not found." -ForegroundColor Red
  exit 1
}

$content = Get-Content $backlogFile -Raw

# Split by --- delimiter
$blocks = $content -split "---" | Where-Object { $_.Trim() }

Write-Host "Parsing $($blocks.Count) issue blocks from $backlogFile..." -ForegroundColor Cyan

$issues = @()

foreach ($block in $blocks) {
  $lines = $block -split "`n" | Where-Object { $_.Trim() }
  if ($lines.Count -lt 2) { continue }
  
  $title = $lines[0].Trim()
  $body = ($lines[1..($lines.Count - 1)] -join "`n").Trim()
  
  # Extract labels from last line if it starts with "Labels:"
  $labels = @()
  if ($body -match "Labels:\s*(.+)$") {
    $labelStr = $matches[1].Trim()
    $labels = $labelStr -split ',\s*' | Where-Object { $_ }
  }
  
  $issues += @{
    title  = $title
    body   = $body
    labels = $labels
  }
}

Write-Host "Parsed $($issues.Count) issues." -ForegroundColor Yellow

# Create each issue
foreach ($issue in $issues) {
  Write-Host "`nCreating issue: $($issue.title)" -ForegroundColor Cyan
  
  $iBody = @{
    title      = $issue.title
    body       = $issue.body
    labels     = $issue.labels
    milestone  = $ms.number
  }
  
  $created = Invoke-Api -Method Post -Url "$base/issues" -Body $iBody
  
  if ($created) {
    Write-Host "Issue created: $($created.html_url)" -ForegroundColor Green
  }
}

Write-Host "`n=== Complete ===" -ForegroundColor Green
