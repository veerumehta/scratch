#!/usr/bin/env bash
# Recent CI runs, and the failing log of the newest one. Read-only (gh reads only).
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
# Checking CI otherwise means a `gh run list` to find an id, then a `gh run view "$(...)"` that
# interpolates it back in, which is exactly the command-substitution shape that trips a permission
# prompt every time. The id never leaves this script.
#
# Usage:
#   ./scripts/local/ci_status.sh                       # recent runs, all branches
#   ./scripts/local/ci_status.sh --branch plato        # recent runs for one branch
#   ./scripts/local/ci_status.sh --branch plato --log  # + the failing log of the newest run
#   ./scripts/local/ci_status.sh --workflow tests.yml --branch dev --log
#   ./scripts/local/ci_status.sh --lines 80 --log      # more of the log tail (default 40)

set -uo pipefail

BRANCH=""
WORKFLOW=""
SHOW_LOG=0
LIMIT=8
LINES=40

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch)   BRANCH="$2"; shift 2 ;;
    --workflow) WORKFLOW="$2"; shift 2 ;;
    --log)      SHOW_LOG=1; shift ;;
    --limit)    LIMIT="$2"; shift 2 ;;
    --lines)    LINES="$2"; shift 2 ;;
    *)          echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

args=(run list --limit "$LIMIT")
[[ -n "$BRANCH"   ]] && args+=(--branch "$BRANCH")
[[ -n "$WORKFLOW" ]] && args+=(--workflow "$WORKFLOW")

echo "=== recent runs ==="
gh "${args[@]}" --json workflowName,headBranch,status,conclusion,createdAt,databaseId \
  --template '{{range .}}{{.workflowName}}	{{.headBranch}}	{{.status}}	{{.conclusion}}	{{.databaseId}}
{{end}}'

if [[ "$SHOW_LOG" -eq 1 ]]; then
  # The newest run matching the same filters, so --log always describes the listing above.
  id=$(gh "${args[@]}" --json databaseId --jq '.[0].databaseId' 2>/dev/null)
  if [[ -z "$id" ]]; then
    echo "no run found for those filters" >&2
    exit 1
  fi
  echo
  echo "=== failing steps of run $id (last $LINES lines) ==="
  gh run view "$id" --log-failed 2>&1 | tail -n "$LINES"
fi
