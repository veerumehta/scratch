#!/usr/bin/env bash
# Refresh japes' bundled Acra DSCR seed pack from jaci's copy, which owns it.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
#   scripts/local/sync_dscr_seed_from_jaci.sh [--apply]
#
# Prints the diff between jaci's config/packs/acra_dscr_policy and plato/data/seed_packs/
# acra_dscr_policy first. With --apply it makes the seed an exact copy of jaci's pack (files only
# the seed has are removed), records the jaci commit and pack version in the seed's SYNCED_FROM
# file (jaci's commit, unnamed there so the seed names no consumer), and touches nothing else. It never commits and never writes to jaci.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

JACI="${JACI_DIR:-$HOME/src/jaci}/config/packs/acra_dscr_policy"
SEED=plato/data/seed_packs/acra_dscr_policy
[ -d "$JACI" ] || { echo "no $JACI (set JACI_DIR to jaci's checkout)" >&2; exit 1; }
[ -d "$SEED" ] || { echo "no $SEED: run from japes" >&2; exit 1; }

version() { sed -n 's/^pack_version:[[:space:]]*"\{0,1\}\([^"#[:space:]]*\).*/\1/p' "$1/pack_manifest.yaml" | head -n1; }
echo "jaci   $(git -C "$JACI" rev-parse --short HEAD) pack_version $(version "$JACI")"
echo "seed   pack_version $(version "$SEED")"
echo
if diff -r -q -x __pycache__ -x '.DS_Store' -x SYNCED_FROM "$JACI" "$SEED" >/dev/null; then
  echo "the seed already matches jaci's pack"
  exit 0
fi
diff -r -u -x __pycache__ -x '.DS_Store' -x SYNCED_FROM "$SEED" "$JACI" || true
echo
[ "${1:-}" = "--apply" ] || { echo "dry run; --apply copies jaci's pack over the seed"; exit 0; }

rsync -a --delete --exclude __pycache__ --exclude .DS_Store --exclude SYNCED_FROM "$JACI/" "$SEED/"
printf 'source_commit %s\npack_version %s\n' "$(git -C "$JACI" rev-parse --short HEAD)" "$(version "$SEED")" > "$SEED/SYNCED_FROM"
echo "seed now matches jaci $(git -C "$JACI" rev-parse --short HEAD) (pack_version $(version "$SEED"))"
git status --short -- "$SEED" | head -20
