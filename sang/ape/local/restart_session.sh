#!/usr/bin/env bash
# Start one of the five japes Claude sessions by name, in its own tmux session, after a reboot.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
#   scripts/local/restart_session.sh opus-xrepo        # fresh session told to read its restart file
#   scripts/local/restart_session.sh sonnet-ui --resume   # reopen its last conversation by name instead
#   scripts/local/restart_session.sh all               # start all five (detached), then attach one
#   scripts/local/restart_session.sh list              # names, tmux sessions, restart files, live or not
#
# Each session saves its state in scripts/local/restart/<name>.md before a shutdown (a restart file
# is NOT in /tmp, which a reboot can clear). A fresh start passes it as the first prompt: the model
# reads the file and CLAUDE.md, reports what it understood and waits. `--resume` asks claude to
# reopen the conversation named <name> (a picker appears if several match); use it when the old
# conversation is still wanted, the restart file otherwise.
#
# Names and where they run: opus-xrepo (tmux japes), sonnet-runtime (jrun), sonnet-ui (jui),
# sonnet-jaci (jaci, in the jaci repo), sonnet-packs (jpacks). A tmux session that already exists is attached, never
# started twice. Local Plato does not come back by itself:
#   /Users/sangit/src/japes/scripts/local/plato_worktree.sh start      (pinned worktree, :8000)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
RESTART_DIR="$HERE/restart"
# The path a session is told to read: the japes checkout's scripts/local symlink, which is stable.
PROMPT_DIR="/Users/sangit/src/japes/scripts/local/restart"
OPUS="claude-opus-5-5"
SONNET="claude-sonnet-5-5"
NAMES=(opus-xrepo sonnet-runtime sonnet-ui sonnet-jaci sonnet-packs)

# name -> "tmux-session working-directory model"
spec() {
    case "$1" in
        opus-xrepo)     echo "japes /Users/sangit/src/japes $OPUS" ;;
        sonnet-runtime) echo "jrun /Users/sangit/src/japes $SONNET" ;;
        sonnet-ui)      echo "jui /Users/sangit/src/japes $SONNET" ;;
        sonnet-jaci)    echo "jaci /Users/sangit/src/jaci $SONNET" ;;
        sonnet-packs)   echo "jpacks /Users/sangit/src/japes $SONNET" ;;
        *) return 1 ;;
    esac
}

usage() { sed -n '2,19p' "${BASH_SOURCE[0]}" | sed -E 's/^# ?//'; }

list() {
    printf '%-15s %-8s %-8s %s\n' name tmux live restart-file
    for name in "${NAMES[@]}"; do
        read -r tmux_name cwd model <<<"$(spec "$name")"
        live=no; tmux has-session -t "$tmux_name" 2>/dev/null && live=yes
        file=missing; [[ -f "$RESTART_DIR/$name.md" ]] && file="$(date -r "$RESTART_DIR/$name.md" '+%m-%d %H:%M')"
        printf '%-15s %-8s %-8s %s\n' "$name" "$tmux_name" "$live" "$file"
    done
}

# start <name> <fresh|resume>: create the tmux session detached and run claude in it.
start() {
    local name="$1" mode="$2" tmux_name cwd model cmd prompt
    read -r tmux_name cwd model <<<"$(spec "$name")"
    if tmux has-session -t "$tmux_name" 2>/dev/null; then
        echo "$name: tmux session '$tmux_name' already exists, not starting another claude in it"
        return 0
    fi
    [[ -d "$cwd" ]] || { echo "$name: $cwd does not exist" >&2; return 1; }
    if [[ "$mode" == "resume" ]]; then
        printf -v cmd 'claude --resume %q --name %q --model %q' "$name" "$name" "$model"
    else
        [[ -f "$RESTART_DIR/$name.md" ]] || {
            echo "$name: no restart file at $RESTART_DIR/$name.md (the session has not saved its state)" >&2
            return 1; }
        prompt="You are $name, restarting after a computer reboot. Read $PROMPT_DIR/$name.md first, then the project CLAUDE.md and your memory index, and do exactly what the restart file says to do first. Do not start new work, send messages or run anything against loan documents until you have reported in one short paragraph what you understood and what is pending."
        printf -v cmd 'claude --name %q --model %q %q' "$name" "$model" "$prompt"
    fi
    tmux new-session -d -s "$tmux_name" -c "$cwd" "$cmd"
    echo "$name: started in tmux '$tmux_name' ($cwd, $model, $mode)"
}

attach() {
    local tmux_name
    read -r tmux_name _ _ <<<"$(spec "$1")"
    if [[ -n "${TMUX:-}" ]]; then tmux switch-client -t "$tmux_name"; else tmux attach -t "$tmux_name"; fi
}

[[ $# -ge 1 ]] || { usage; exit 2; }
target="$1"; mode=fresh
[[ "${2:-}" == "--resume" ]] && mode=resume
command -v tmux >/dev/null || { echo "tmux is not installed" >&2; exit 1; }
command -v claude >/dev/null || { echo "claude is not on PATH" >&2; exit 1; }

case "$target" in
    list) list ;;
    -h|--help) usage ;;
    all)
        for name in "${NAMES[@]}"; do start "$name" "$mode" || true; done
        echo; list; echo; echo "attach with: tmux attach -t japes | jrun | jui | jaci | jpacks" ;;
    *)
        spec "$target" >/dev/null 2>&1 || { echo "unknown name '$target'; one of: ${NAMES[*]}" >&2; exit 2; }
        start "$target" "$mode"
        attach "$target" ;;
esac
