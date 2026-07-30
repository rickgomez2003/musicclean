#!/usr/bin/env bash

set -Eeuo pipefail

REPO="rickgomez2003/musicclean"
OWNER="rickgomez2003"

DESCRIPTION="Intelligent music library management, duplicate detection, quality analysis, automatic cleanup, and MusicBrainz integration for large collections."

echo "============================================================"
echo "MusicClean GitHub repository setup"
echo "Repository: $REPO"
echo "============================================================"

if ! command -v gh >/dev/null 2>&1; then
    echo "ERROR: GitHub CLI (gh) is not installed."
    echo "Install it from PowerShell with:"
    echo "  winget install --id GitHub.cli --exact"
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "ERROR: GitHub CLI is not authenticated."
    echo "Run:"
    echo "  gh auth login --web --git-protocol https"
    exit 1
fi

echo
echo "Configuring repository features..."

gh repo edit "$REPO" \
    --description "$DESCRIPTION" \
    --enable-issues \
    --enable-projects \
    --enable-wiki \
    --enable-discussions \
    --enable-squash-merge \
    --enable-rebase-merge \
    --enable-merge-commit=false \
    --delete-branch-on-merge \
    --allow-update-branch

echo
echo "Adding repository topics..."

TOPICS=(
    music
    audio
    flac
    python
    truenas
    freebsd
    nas
    duplicate-files
    musicbrainz
    lidarr
    beets
    picard
    sqlite
    metadata
)

for topic in "${TOPICS[@]}"; do
    gh repo edit "$REPO" --add-topic "$topic"
done

echo
echo "Creating or updating labels..."

create_label() {
    local name="$1"
    local color="$2"
    local description="$3"

    gh label create "$name" \
        --repo "$REPO" \
        --color "$color" \
        --description "$description" \
        --force
}

create_label "scanner"       "1D76DB" "Filesystem scanning and indexing"
create_label "database"      "5319E7" "SQLite schema, queries, caching, and migrations"
create_label "metadata"      "0E8A16" "Audio tags, codecs, and media metadata"
create_label "duplicates"    "D93F0B" "Duplicate files, tracks, releases, or folders"
create_label "cleanup"       "FBCA04" "Deletion and filesystem cleanup behavior"
create_label "intelligence"  "0052CC" "Album comparison, scoring, and decision logic"
create_label "plugin"        "006B75" "External integration or plugin development"
create_label "performance"   "FEF2C0" "Performance, concurrency, memory, or I/O"
create_label "testing"       "C5DEF5" "Automated tests and test infrastructure"
create_label "security"      "B60205" "Security, permissions, and destructive-operation controls"
create_label "truenas"       "0B7285" "TrueNAS-specific behavior"
create_label "freebsd"       "6F42C1" "FreeBSD-specific behavior"
create_label "windows"       "0078D4" "Windows-specific behavior"
create_label "linux"         "FCC624" "Linux-specific behavior"
create_label "musicbrainz"   "BA55D3" "MusicBrainz integration"
create_label "picard"        "F4A261" "MusicBrainz Picard integration"
create_label "beets"         "2A9D8F" "beets integration"
create_label "lidarr"        "9B5DE5" "Lidarr integration"

echo
echo "Creating milestones..."

create_milestone() {
    local title="$1"
    local description="$2"

    if gh api \
        "repos/$REPO/milestones?state=all&per_page=100" \
        --jq '.[].title' |
        grep -Fqx "$title"; then
        echo "Milestone already exists: $title"
    else
        gh api \
            --method POST \
            "repos/$REPO/milestones" \
            -f title="$title" \
            -f description="$description" \
            >/dev/null

        echo "Created milestone: $title"
    fi
}

create_milestone "0.1 Foundation"         "Packaging, configuration, CLI, logging, and initial project structure."
create_milestone "0.2 Scanner"            "High-performance filesystem scanner and incremental indexing."
create_milestone "0.3 Metadata"           "Audio metadata extraction, validation, and caching."
create_milestone "0.4 Duplicate Engine"   "Exact duplicate file and duplicate-folder detection."
create_milestone "0.5 Album Intelligence" "Album fingerprints, release comparison, and quality scoring."
create_milestone "0.6 Cleanup"            "Automated cleanup rules and deletion logging."
create_milestone "0.7 Reports"            "CSV, JSON, terminal, and HTML reports."
create_milestone "0.8 Integrations"       "Picard, beets, Lidarr, MusicBrainz, and related integrations."
create_milestone "1.0 Stable"             "Documented and tested stable release."

echo
echo "Creating the Sprint 1 issue..."

ISSUE_TITLE="Sprint 1 - Project Foundation"

if gh issue list \
    --repo "$REPO" \
    --state all \
    --search "\"$ISSUE_TITLE\" in:title" \
    --json title \
    --jq '.[].title' |
    grep -Fqx "$ISSUE_TITLE"; then

    echo "Issue already exists: $ISSUE_TITLE"
else
    ISSUE_BODY="$(cat <<'EOF'
## Objective

Create the initial working foundation for MusicClean.

## Tasks

- [ ] Create the Python package structure
- [ ] Add `pyproject.toml`
- [ ] Add development dependencies
- [ ] Add `config.example.yaml`
- [ ] Implement configuration loading
- [ ] Implement structured logging
- [ ] Implement the initial command-line interface
- [ ] Initialize the SQLite database
- [ ] Implement the first filesystem scanner
- [ ] Add unit tests
- [ ] Add GitHub Actions continuous integration
- [ ] Document Windows and FreeBSD installation

## Initial paths

Download staging area:

`/mnt/Data/Media/Downloads/sabnzdb/complete/music/`

Permanent music library:

`/mnt/Data/Media/Music/`
EOF
)"

    gh issue create \
        --repo "$REPO" \
        --title "$ISSUE_TITLE" \
        --body "$ISSUE_BODY" \
        --assignee "@me" \
        --milestone "0.1 Foundation" \
        --label "scanner" \
        --label "database" \
        --label "testing"

    echo "Created issue: $ISSUE_TITLE"
fi

echo
echo "Creating the GitHub Project if it does not exist..."

if gh project list \
    --owner "$OWNER" \
    --format json \
    --jq '.projects[].title' 2>/dev/null |
    grep -Fqx "MusicClean Development"; then

    echo "Project already exists: MusicClean Development"
else
    if gh project create \
        --owner "$OWNER" \
        --title "MusicClean Development" >/dev/null; then
        echo "Created project: MusicClean Development"
    else
        echo "Project creation was skipped."
        echo "Run 'gh auth refresh -s project' and rerun this script."
    fi
fi

echo
echo "============================================================"
echo "Repository setup completed."
echo "============================================================"
