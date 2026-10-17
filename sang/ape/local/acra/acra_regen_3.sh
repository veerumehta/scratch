#!/bin/bash
# Acra regeneration 3: the synced seed plus the fold and data_mapping blocks (/Users/sangit/src/japes/scripts/local/acra/acra_template_extra.yaml),
# on a fresh trial pack, then the same phases as regen 2. Compare with ape/local/coverage/regen_2.
# 1) pins local Plato to the v2.6.3 tip (the fold and data-mapping code), migrates, restarts it. This kills
#    any run in flight on local Plato (the ingest case run): wait for that to finish first, or SKIP_UPGRADE=1.
# 2) runs the regen: 4 extractions, code, alignment, and about 28 judge calls: a regen 2 cost plus the judges.
# Needs the provider keys in japes' .env and the Acra seed pack published for tenant acra-lending.
set -u
HERE=/Users/sangit/src/.scratch/sang/ape/local
if [ "${SKIP_UPGRADE:-}" != "1" ]; then
  "$HERE/local_plato_upgrade.sh" || { echo "upgrade or restart failed; not running the regen"; exit 1; }
  for _ in $(seq 1 60); do curl -fsS -o /dev/null http://localhost:8000/ 2>/dev/null && break; sleep 2; done
fi
"$HERE/plato_worktree.sh" status
export ACRA_TEMPLATE_EXTRA=/Users/sangit/src/japes/scripts/local/acra/acra_template_extra.yaml
TRIAL="${TRIAL:-acra-regen-3b}"   # a trial pack id that already exists as a draft cannot be re-seeded
exec "$HERE/acra_regen.sh" "$TRIAL" "$HERE/coverage/regen_${TRIAL#acra-regen-}"
