#!/usr/bin/env bash

set -Eeuo pipefail

REPO="rickgomez2003/musicclean"

echo "Repository configuration:"
gh repo view "$REPO" \
    --json \
nameWithOwner,visibility,description,defaultBranchRef,hasIssuesEnabled,hasProjectsEnabled,hasWikiEnabled,hasDiscussionsEnabled,deleteBranchOnMerge,mergeCommitAllowed,rebaseMergeAllowed,squashMergeAllowed,repositoryTopics \
    --jq '{
        repository: .nameWithOwner,
        visibility: .visibility,
        description: .description,
        default_branch: .defaultBranchRef.name,
        issues: .hasIssuesEnabled,
        projects: .hasProjectsEnabled,
        wiki: .hasWikiEnabled,
        discussions: .hasDiscussionsEnabled,
        delete_branch_on_merge: .deleteBranchOnMerge,
        merge_commits: .mergeCommitAllowed,
        rebase_merges: .rebaseMergeAllowed,
        squash_merges: .squashMergeAllowed,
        topics: [.repositoryTopics[].name]
    }'

echo
echo "Branches:"
gh api "repos/$REPO/branches" --jq '.[].name'

echo
echo "Labels:"
gh label list --repo "$REPO" --limit 100

echo
echo "Milestones:"
gh api "repos/$REPO/milestones?state=all&per_page=100" \
    --jq '.[] | "\(.title) | \(.state) | open issues: \(.open_issues)"'

echo
echo "Issues:"
gh issue list \
    --repo "$REPO" \
    --state all \
    --limit 100
