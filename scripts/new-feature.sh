#!/usr/bin/env bash
#
# Start a new feature the Spec Kit way, on its own git branch.
#
# This wraps Spec Kit's create-new-feature.sh so that a feature and its git
# branch are created together and share the SAME name (NNN-slug). That naming
# match is the Spec Kit convention: the branch, the specs/<id>/ folder, and the
# feature id are all identical.
#
# Usage:
#   scripts/new-feature.sh "Add saved search alerts"
#   scripts/new-feature.sh --short-name "resume-import" "Import a resume from PDF"
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SPECIFY_SCRIPT="$REPO_ROOT/.specify/scripts/bash/create-new-feature.sh"

if [ ! -f "$SPECIFY_SCRIPT" ]; then
    echo "Spec Kit is not initialized (missing $SPECIFY_SCRIPT)." >&2
    exit 1
fi

if [ "$#" -eq 0 ]; then
    echo "Usage: scripts/new-feature.sh [--short-name <name>] <feature description>" >&2
    exit 1
fi

cd "$REPO_ROOT"

# Warn if we're not branching from an up-to-date main; keep going so the flow
# still works on a fork or a detached experiment.
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Note: creating this feature from '$CURRENT_BRANCH', not 'main'." >&2
fi

# Create the specs/<id>/ folder and capture the generated feature id.
FEATURE_JSON="$(bash "$SPECIFY_SCRIPT" --json "$@")"
BRANCH_NAME="$(printf '%s' "$FEATURE_JSON" | jq -r '.BRANCH_NAME')"

if [ -z "$BRANCH_NAME" ] || [ "$BRANCH_NAME" = "null" ]; then
    echo "Could not determine the feature id from Spec Kit output:" >&2
    echo "$FEATURE_JSON" >&2
    exit 1
fi

# Cut the matching git branch. The just-created (untracked) spec files follow
# us onto the new branch, so the spec is committed there — not on main.
git switch -c "$BRANCH_NAME"

echo ""
echo "Created feature branch: $BRANCH_NAME"
echo "Spec: specs/$BRANCH_NAME/spec.md"
echo ""
echo "Next, in Claude Code:"
echo "  /speckit-plan       -> design the implementation"
echo "  /speckit-tasks      -> break it into tasks"
echo "  /speckit-implement  -> build it, then open a PR into main"
