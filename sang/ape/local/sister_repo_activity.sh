#!/bin/bash
# Recent commits across sibling repos under ~/src/. Read-only (fetch + log only).
#
# Usage:
#   ./scripts/local/sister_repo_activity.sh
#   ./scripts/local/sister_repo_activity.sh juno eval-service
#   ./scripts/local/sister_repo_activity.sh --days 1
#   ./scripts/local/sister_repo_activity.sh --no-fetch
#
# SISTER_REPOS_SRC_DIR overrides the assumed ~/src/ root.

set -e

SRC_DIR="${SISTER_REPOS_SRC_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

DEFAULT_REPOS=(juno eval-service macer jaci kernel client-api knowledge_hub jazzx-assistant assistant)

DAYS=7
DO_FETCH=1
SINCE_LAST=0
MARK=0
REPOS=()
STATE_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.last_scan"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --days)
            DAYS="$2"
            shift 2
            ;;
        --no-fetch)
            DO_FETCH=0
            shift
            ;;
        --since-last)
            SINCE_LAST=1
            shift
            ;;
        --mark)
            MARK=1
            shift
            ;;
        *)
            REPOS+=("$1")
            shift
            ;;
    esac
done

if [ ${#REPOS[@]} -eq 0 ]; then
    REPOS=("${DEFAULT_REPOS[@]}")
fi

for repo in "${REPOS[@]}"; do
    path="$SRC_DIR/$repo"
    echo "== $repo =="
    if [ ! -d "$path/.git" ]; then
        echo "(not a git repo at $path — skipping)"
        echo
        continue
    fi
    (
        cd "$path"
        if [ "$DO_FETCH" -eq 1 ]; then
            git fetch --quiet --all 2>/dev/null || echo "(fetch failed — showing local state)"
        fi
        range_desc="the last ${DAYS} day(s)"
        last=""
        if [ "$SINCE_LAST" -eq 1 ]; then
            last="$(grep -E "^${repo} " "$STATE_FILE" 2>/dev/null | tail -1 | awk '{print $2}')"
        fi

        if [ -n "$last" ]; then
            range_desc="since $(date -r "$last" +%Y-%m-%d 2>/dev/null || echo "the last mark")"
            commits="$(git log --oneline --all --since="@${last}" --date=short \
                --pretty=format:"%h %ad %an %s" 2>/dev/null | sort -k2,2 -u | sort -k2,2r)"
        else
            commits="$(git log --oneline --since="${DAYS} days ago" --all --date=short \
                --pretty=format:"%h %ad %an %s" | sort -k2,2 -u | sort -k2,2r)"
        fi

        if [ -z "$commits" ]; then
            echo "(no commits ${range_desc})"
        else
            echo "$commits"
        fi

        if [ "$MARK" -eq 1 ]; then
            # The newest commit across every ref, which is the frontier this scan actually covered.
            # Epoch plus one second: git's --since is inclusive, so marking the newest commit's
            # own timestamp reports that commit again on the very next run.
            newest_epoch="$(git log -1 --all --pretty=format:'%ct')"
            [ -n "$newest_epoch" ] || newest_epoch="$(date -u +%s)"
            newest="$((newest_epoch + 1))"
            # Append rather than rewrite: the history of when someone looked is itself useful when
            # a regression turns out to predate the last check.
            printf '%s %s (scanned %s)\n' "$repo" "$newest" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
                >> "$STATE_FILE"
            echo "(marked at $(git log -1 --all --date=short --pretty=format:'%ad'))"
        fi
    )
    echo
done
