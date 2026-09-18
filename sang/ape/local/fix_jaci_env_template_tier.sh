#!/usr/bin/env bash
# jaci's .env.template says JAPES_ENVIRONMENT=dev, which meant "my laptop" until japes 2.5.2 and
# now resolves to the dev-daily tier -- so a developer copying the template gets a deployed
# posture: Postgres expected, a tenant list required, X-Tenant-Id on every request.
#
# Changes that one line to `local`. Prints the diff and leaves a .bak; commits nothing.
set -euo pipefail

TEMPLATE="${1:-/Users/sangit/src/jaci/.env.template}"

[ -f "$TEMPLATE" ] || { echo "not found: $TEMPLATE" >&2; exit 1; }

if ! grep -qE '^JAPES_ENVIRONMENT=dev([[:space:]]|#|$)' "$TEMPLATE"; then
    echo "nothing to change: no 'JAPES_ENVIRONMENT=dev' line in $TEMPLATE"
    grep -n 'JAPES_ENVIRONMENT' "$TEMPLATE" || true
    exit 0
fi

cp "$TEMPLATE" "$TEMPLATE.bak"
# The trailing comment goes with it: `dev/staging/prod` is the old tier vocabulary.
sed -i '' -E \
    's|^JAPES_ENVIRONMENT=dev([[:space:]]*#.*)?$|JAPES_ENVIRONMENT=local  # local/dev-daily/staging/production; dev means dev-daily|' \
    "$TEMPLATE"

diff -u "$TEMPLATE.bak" "$TEMPLATE" || true
echo
echo "backup: $TEMPLATE.bak"
