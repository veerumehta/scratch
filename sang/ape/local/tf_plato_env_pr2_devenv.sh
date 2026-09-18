#!/usr/bin/env bash
# PR 2 of 2 -- terraform-azure-jaxi, against the `dev` branch (dev-daily's files live there).
# Steps 3, 4 and 5 of the "Managing Environment Variables in BE and FE Services" guide: declare in
# the environment, pass to the module, set the value.
#
# Run AFTER PR 1 is merged: Jazzx/jaxi/dev/main.tf pins the module at ?ref=main.
#
# Two kinds of change, and the second is the one that fixes the live replica:
#   new    japes_plato_tenants / _pack_blob_backend / _pack_blob_container
#   unset  japes_plato_environment -- declared with default "" and set by no tfvars, which is why
#          the running container reports `environment: local` and takes the laptop branch of every
#          tier decision.
#
# Edits and commits LOCALLY only. Nothing reaches GitHub until you push.
set -euo pipefail

REPO="${TF_ENV_REPO:-/Users/sangit/src/terraform-azure-jaxi}"
BRANCH="feat/add-plato-env-vars-dev-daily"
BODY="${TMPDIR:-/tmp}/plato_pr2_body.md"

cd "$REPO"
[ -z "$(git status --porcelain)" ] || { echo "refusing: $REPO has uncommitted changes" >&2; exit 1; }

git fetch origin dev
git switch -c "$BRANCH" origin/dev 2>/dev/null || git switch "$BRANCH"

python3 - <<'PY'
from pathlib import Path

def edit(path, anchor, addition, marker):
    file = Path(path)
    text = file.read_text()
    if marker in text:
        print(f"{path}: already applied")
        return
    if text.count(anchor) != 1:
        raise SystemExit(f"{path}: anchor matched {text.count(anchor)} times, expected 1")
    file.write_text(text.replace(anchor, anchor + addition))
    print(f"{path}: applied")

# -- Step 3: declare in the environment -------------------------------------------------------
edit(
    "Jazzx/jaxi/dev/variables.tf",
    '''variable "japes_plato_log_level" {
  description = "LOG_LEVEL for the japes-plato application"
  type        = string
  default     = "INFO"
}
''',
    '''
variable "japes_plato_tenants" {
  description = "PLATO_TENANTS for the japes-plato application: comma-separated tenant ids"
  type        = string
  default     = ""
}

variable "japes_plato_pack_blob_backend" {
  description = "PLATO_PACK_BLOB_BACKEND for the japes-plato application: azure, or local disk"
  type        = string
  default     = ""
}

variable "japes_plato_pack_blob_container" {
  description = "PLATO_PACK_BLOB_CONTAINER for the japes-plato application: pack-archive container"
  type        = string
  default     = ""
}
''',
    "japes_plato_tenants",
)

# -- Step 4: pass to the module ---------------------------------------------------------------
edit(
    "Jazzx/jaxi/dev/main.tf",
    "  japes_plato_log_level                     = var.japes_plato_log_level\n",
    """
  japes_plato_tenants             = var.japes_plato_tenants
  japes_plato_pack_blob_backend   = var.japes_plato_pack_blob_backend
  japes_plato_pack_blob_container = var.japes_plato_pack_blob_container
""",
    "japes_plato_tenants",
)

# -- Step 5: set the values -------------------------------------------------------------------
edit(
    "Jazzx/jaxi/dev/devenv.auto.tfvars",
    'japes_plato_app_memory = "1Gi"\n',
    '''
# The tier. Declared with default "" and set by no tfvars until now, so the container carried a
# blank JAPES_ENVIRONMENT -- read as not-configured, which resolved the local tier: identity not
# required, sqlite instead of the service Postgres, and the deployed-only readiness checks skipped.
japes_plato_environment = "dev-daily"

# Tenant ids this replica serves. Every request carries X-Tenant-Id and the job roles sweep this
# list, so a wrong value here reaps the wrong tenant and reports success.
japes_plato_tenants = "acme-hospital"

# Durable pack archives. All three are needed together: the backend must be exactly `azure` (every
# other value is treated as local container disk), the container is plato's own, and
# STORAGE__CONNECTION_STRING comes from the module's existing key-vault secret.
japes_plato_pack_blob_backend   = "azure"
japes_plato_pack_blob_container = "plato"
''',
    "japes_plato_tenants",
)
PY

git --no-pager diff --stat
echo
git --no-pager diff

git add Jazzx/jaxi/dev/variables.tf Jazzx/jaxi/dev/main.tf Jazzx/jaxi/dev/devenv.auto.tfvars
# Conditional, so a re-run after the edits are already in re-writes the PR body and exits clean
# rather than dying on an empty commit.
if git diff --cached --quiet; then
    echo "nothing new to commit; branch $BRANCH already carries the change"
else
    git commit -q -m "feat: set plato env vars for dev-daily"
    echo "committed on $BRANCH"
fi

cat > "$BODY" <<'BODY'
Sets the japes-plato environment for dev-daily. Depends on the merged
`terraform-azure-jaxi-modules` PR, since `Jazzx/jaxi/dev/main.tf` pins the module at `?ref=main`.

**The fix that matters most is a variable that already existed.** `japes_plato_environment` is
declared with `default = ""` and was set by no `.auto.tfvars`, so the running container carried a
blank `JAPES_ENVIRONMENT`. A blank value is read as not-configured, which resolved the *local*
tier: identity not required, the sqlite fallback instead of the service's Postgres, and every
deployed-only readiness check skipped — while `/info` reported `environment: local`, which is also
what a correctly configured laptop reports, so there was nothing to notice. It is now `dev-daily`.

New values:

| Variable | Value | Why |
|---|---|---|
| `japes_plato_environment` | `dev-daily` | Above. Exactly this spelling; `devdaily` and `dev_daily` are refused at boot. |
| `japes_plato_tenants` | `acme-hospital` | Required on a deployed tier. Every request carries `X-Tenant-Id` and the `job:*` roles sweep this list. |
| `japes_plato_pack_blob_backend` | `azure` | Published pack archives must be durable; local disk loses them on restart while the database row survives. |
| `japes_plato_pack_blob_container` | `plato` | Plato's own container in the storage account. |

**Prerequisite:** the `plato` blob container must exist in the dev-env storage account. It is not
created by this PR (it belongs to the storage module, not `aca`) — please confirm it exists or say
where to add it.

Left deliberately unset, with reasons:

- `PLATO_WIRING`, `PROJECT_NAME`, `DESCRIPTION`, `VERSION`, `API_V1_PREFIX`, `DEBUG` — the
  application supplies these itself; a blank terraform value is read as unset and the default
  applies.
- `PLATO_PACK_DIR` — defaults to the assistant pack bundled in the image.
- `PLATO_ACTIVE_PACK` — written durably by the activation route, so a terraform-pinned value would
  fight an operator's rollback.
- `japes_plato_db_async_connection_str` and `japes_plato_kh_api_key` — credentials, which this
  guide puts out of scope. The database itself already exists in terraform: the postgres module
  creates `japes_plato_db` (`database_name_japes_plato`). Please wire the connection string for
  that database the way the other services' are wired.
BODY

cat <<EOF

PR body written to $BODY

This script touched nothing outside your machine. To push the branch and open the PR against
dev, run:

  ./tf_plato_env_publish.sh 2
EOF
