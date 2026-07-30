#!/usr/bin/env bash
set -Eeuo pipefail

REPO="rickgomez2003/musicclean"
TITLE="Sprint 2 - Metadata, Hashing, and Incremental Scanning"

BODY="$(cat <<'EOF'
## Objective

Add technical audio analysis and efficient incremental rescanning.

## Tasks

- [ ] Add Mutagen metadata extraction
- [ ] Add BLAKE3 whole-file hashing
- [ ] Expand and migrate the SQLite schema
- [ ] Skip analysis for unchanged files
- [ ] Capture codec, bitrate, sample rate, bit depth, channels, and duration
- [ ] Capture common tags and MusicBrainz identifiers
- [ ] Detect embedded artwork
- [ ] Add live scan progress
- [ ] Add migration, hash, metadata, and database tests
- [ ] Validate on Windows and GitHub Actions
- [ ] Validate against a TrueNAS or FreeBSD music path

## Safety

This sprint must not move, rename, modify, or delete music files.
EOF
)"

if gh issue list \
    --repo "$REPO" \
    --state all \
    --search "\"$TITLE\" in:title" \
    --json title \
    --jq '.[].title' |
    grep -Fqx "$TITLE"; then
    echo "Issue already exists: $TITLE"
else
    gh issue create \
        --repo "$REPO" \
        --title "$TITLE" \
        --body "$BODY" \
        --assignee "@me" \
        --milestone "0.3 Metadata" \
        --label "metadata" \
        --label "database" \
        --label "performance" \
        --label "testing"
fi
