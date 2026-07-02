#!/usr/bin/env bash
# Computes the feature branch name (using create-new-feature.sh in dry-run mode)
# and creates or switches to the branch. Called by the speckit.git.branch hook.
#
# Usage: git-create-branch.sh [--json] <feature_description>
# Outputs JSON: {"BRANCH_NAME":"003-auth","FEATURE_NUM":"003"}

set -e

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT=$(get_repo_root) || exit 1
cd "$REPO_ROOT"

# Compute branch name without touching the filesystem.
# Passes all args through so --number, --short-name, --timestamp work.
FEATURE_INFO=$(bash "$SCRIPT_DIR/create-new-feature.sh" --json --dry-run "$@")

# Extract values — use jq when available, fall back to portable grep/sed.
if command -v jq >/dev/null 2>&1; then
    BRANCH_NAME=$(printf '%s' "$FEATURE_INFO" | jq -r '.BRANCH_NAME')
    FEATURE_NUM=$(printf '%s' "$FEATURE_INFO" | jq -r '.FEATURE_NUM')
else
    BRANCH_NAME=$(printf '%s' "$FEATURE_INFO" | grep -o '"BRANCH_NAME":"[^"]*"' | sed 's/"BRANCH_NAME":"//;s/"$//')
    FEATURE_NUM=$(printf '%s' "$FEATURE_INFO" | grep -o '"FEATURE_NUM":"[^"]*"' | sed 's/"FEATURE_NUM":"//;s/"$//')
fi

if [ -z "$BRANCH_NAME" ]; then
    echo "[specify] Error: could not determine branch name" >&2
    exit 1
fi

# Create the branch if it doesn't exist; switch to it if it does.
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    git checkout "$BRANCH_NAME"
    echo "[specify] Switched to existing branch: $BRANCH_NAME" >&2
else
    git checkout -b "$BRANCH_NAME"
    echo "[specify] Created and switched to branch: $BRANCH_NAME" >&2
fi

# Output JSON consumed by the speckit-specify before_specify hook handler.
if command -v jq >/dev/null 2>&1; then
    jq -cn --arg bn "$BRANCH_NAME" --arg fn "$FEATURE_NUM" \
        '{BRANCH_NAME: $bn, FEATURE_NUM: $fn}'
else
    printf '{"BRANCH_NAME":"%s","FEATURE_NUM":"%s"}\n' \
        "$(json_escape "$BRANCH_NAME")" "$(json_escape "$FEATURE_NUM")"
fi
