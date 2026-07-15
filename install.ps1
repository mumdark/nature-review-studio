<#
.SYNOPSIS
  Install nature-review-studio v1.4.1 from a flat release directory.

.DESCRIPTION
  Copies <ReleaseRoot>/skill/ to $GlobalSkillsRoot/nature-review-studio,
  sets NRS_ROOT to <ReleaseRoot>, and verifies SKILL.md frontmatter
  and required references.
#>
param(
    [string]$ReleaseRoot,
    [string]$GlobalSkillsRoot
)

$ErrorActionPreference = "Stop"

if (-not $ReleaseRoot) {
    $ReleaseRoot = (Resolve-Path "$PSScriptRoot").Path
}
$ReleaseRoot = (Resolve-Path $ReleaseRoot).Path

if (-not $GlobalSkillsRoot) {
    if ($env:CODEX_HOME) {
        $GlobalSkillsRoot = Join-Path $env:CODEX_HOME "skills"
    } else {
        $GlobalSkillsRoot = "$HOME\.codex\skills"
    }
}

$Source = Join-Path $ReleaseRoot "skill"
$Dest   = Join-Path $GlobalSkillsRoot "nature-review-studio"

if (-not (Test-Path $Source)) {
    Write-Error "[fatal] source skill not found at $Source"
    exit 1
}

# Backup existing install
if (Test-Path $Dest) {
    $Stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
    $Backup = "${Dest}_backup_${Stamp}"
    Write-Host "Backing up existing install to $Backup ..."
    Move-Item $Dest $Backup
}

# Copy skill/
Write-Host "Copying $Source -> $Dest"
New-Item -ItemType Directory -Force -Path $GlobalSkillsRoot | Out-Null
Copy-Item -Recurse -Force $Source $Dest

# Persist NRS_ROOT
$envFile = Join-Path $Dest ".nrs_root"
"NRS_ROOT=$ReleaseRoot" | Out-File -FilePath $envFile -Encoding utf8
Write-Host "Wrote NRS_ROOT=$ReleaseRoot to $envFile"

# Verify
$skill = Join-Path $Dest "SKILL.md"
if (Test-Path $skill) {
    $head = Get-Content $skill -TotalCount 1
    if ($head -eq "---") {
        Write-Host "OK frontmatter starts with ---"
    } else {
        Write-Host "WARN frontmatter does not start with ---"
    }
} else {
    Write-Error "SKILL.md missing after copy"
    exit 2
}

foreach ($ref in @("workflow.md","review-axes.md","response-axes.md","adversarial-checklist.md","source-basis.md","render-docx.md")) {
    $p = Join-Path $Dest "references\$ref"
    if (-not (Test-Path $p)) { Write-Error "missing reference $p"; exit 3 }
}
Write-Host ""
Write-Host "[ok] Installed nature-review-studio v1.4.1 to $Dest"
Write-Host "     NRS_ROOT=$ReleaseRoot"
Write-Host "     Optional: run Update workflow in Codex to refresh the install."
