#!/usr/bin/env bash
# Installs a pre-push git hook that refuses unless you set ALLOW_PUSH=1.
#
# This is the layer that permission rules cannot provide. A Claude Code deny rule matches the
# command string it is given, so `git push` typed directly is caught -- but a push from inside a
# script is invisible to it: the tool call is `./some_script.sh`, and the push happens in a
# subprocess the rule never sees. That is exactly how a push got made after it had been forbidden.
#
# A pre-push hook sits below all of that. Git runs it for every push regardless of who invoked it
# or how, so it catches direct commands, scripts, and anything else in this repo.
#
#   ./install_push_guard.sh                        # japes + both terraform repos
#   ./install_push_guard.sh /path/to/repo ...       # named repos
#   ./install_push_guard.sh --uninstall [repos...]  # remove
#
# Pushing yourself afterwards:  ALLOW_PUSH=1 git push -u origin my-branch
set -euo pipefail

DEFAULT_REPOS=(
    /Users/sangit/src/japes
    /Users/sangit/src/terraform-azure-jaxi
    /Users/sangit/src/terraform-azure-jaxi-modules
)

UNINSTALL=0
if [ "${1:-}" = "--uninstall" ]; then
    UNINSTALL=1
    shift
fi

REPOS=("$@")
[ ${#REPOS[@]} -eq 0 ] && REPOS=("${DEFAULT_REPOS[@]}")

MARKER="# claude-push-guard"

for repo in "${REPOS[@]}"; do
    if [ ! -d "$repo/.git" ]; then
        echo "skip (not a git repo): $repo"
        continue
    fi
    # Honours core.hooksPath, so a repo that relocates its hooks still gets the right file.
    hooks_dir=$(git -C "$repo" rev-parse --git-path hooks)
    hooks_dir="$repo/$hooks_dir"
    [ -d "$hooks_dir" ] || mkdir -p "$hooks_dir"
    hook="$hooks_dir/pre-push"

    if [ "$UNINSTALL" = "1" ]; then
        if [ -f "$hook" ] && grep -q "$MARKER" "$hook"; then
            rm "$hook"
            echo "removed: $hook"
        else
            echo "nothing of ours to remove: $hook"
        fi
        continue
    fi

    if [ -f "$hook" ] && ! grep -q "$MARKER" "$hook"; then
        echo "refusing: $hook exists and is not ours -- inspect it first" >&2
        continue
    fi

    cat > "$hook" <<'HOOK'
#!/bin/sh
# claude-push-guard
# Refuses a push unless ALLOW_PUSH=1 is set. Installed by japes/scripts/local/install_push_guard.sh
# so that a push from inside a script is stopped too -- a permission rule only sees the command it
# was handed, and a script's subprocess is not that command.
if [ "${ALLOW_PUSH:-}" = "1" ]; then
    exit 0
fi
echo "pre-push: refused. This repo requires an explicit ALLOW_PUSH=1." >&2
echo "  ALLOW_PUSH=1 git push $*" >&2
exit 1
HOOK
    chmod +x "$hook"
    echo "installed: $hook"
done

if [ "$UNINSTALL" = "0" ]; then
    cat <<'EOF'

Installed. From now on, in these repos:

  git push ...                  -> refused by the hook
  ALLOW_PUSH=1 git push ...     -> allowed

The hook lives in .git/hooks, which is not tracked, so it does not travel to anyone else and is
not part of any commit. Remove it with: ./install_push_guard.sh --uninstall
EOF
fi
