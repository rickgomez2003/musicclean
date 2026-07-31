#!/usr/bin/env bash
set -Eeuo pipefail

REPO="rickgomez2003/musicclean"
TITLE="Sprint 3 - Exact Duplicate Detection and Reports"

BODY="$(cat <<'EOF'
## Objective

Use stored BLAKE3 hashes to identify exact duplicate audio files and quantify
potentially reclaimable disk space.

## Tasks

- [ ] Add scalable duplicate-group database queries
- [ ] Sort duplicate groups by reclaimable space
- [ ] Add root and minimum-size filters
- [ ] Add terminal table output
- [ ] Add JSON report output
- [ ] Add UTF-8 CSV report output
- [ ] Add duplicate statistics to `musicclean stats`
- [ ] Add duplicate and report tests
- [ ] Enforce Ruff, MyPy, Pytest, and coverage in CI
- [ ] Validate with a representative TrueNAS or FreeBSD library

## Safety

Sprint 3 is report-only. It must not move, rename, modify, quarantine, or delete
music files.
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
        --milestone "0.4 Duplicate Engine" \
        --label "duplicates" \
        --label "database" \
        --label "performance" \
        --label "testing"
fi
