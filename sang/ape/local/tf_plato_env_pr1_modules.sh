#!/usr/bin/env bash
# PR 1 of 2 -- terraform-azure-jaxi-modules. Steps 1 and 2 of the "Managing Environment Variables
# in BE and FE Services" guide: declare in the module, wire into the container app.
#
# Adds the six env vars plato needs and the module does not yet pass:
#   PLATO_TENANTS, PLATO_PACK_BLOB_BACKEND, PLATO_PACK_BLOB_CONTAINER,
#   STORAGE__CONNECTION_STRING, OTEL_SAMPLER_RATIO, GEMINI_API_KEY
#
# module-dev is the only module with a japes-plato container app, so it is the only one changed.
#
# BOTH FILES IN THIS MODULE USE CRLF LINE ENDINGS (and main.tf carries a BOM). The edits below go
# through bytes and match each file's own endings, because the first version of this script read
# and wrote text: that silently rewrote all 5537 lines of variable.tf from CRLF to LF, and the PR
# then showed both files as deleted and recreated with no reviewable change in them.
#
#   ./tf_plato_env_pr1_modules.sh              edit and commit on the branch
#   ./tf_plato_env_pr1_modules.sh --rebuild    reset the branch to origin/main first, then edit
#
# Edits and commits LOCALLY only. Publishing is ./tf_plato_env_publish.sh 1.
set -euo pipefail

echo "STALE: the terraform repos were updated externally and now carry this change." >&2
echo "  terraform-azure-jaxi-modules/main already has all six plato env vars and the 3 variables." >&2
echo "  terraform-azure-jaxi/dev already passes them and sets japes_plato_pack_blob_container." >&2
echo "  Still unset in devenv.auto.tfvars: japes_plato_environment, japes_plato_tenants," >&2
echo "  japes_plato_pack_blob_backend. Re-derive before running anything here." >&2
exit 1


REPO="${TF_MODULES_REPO:-/Users/sangit/src/terraform-azure-jaxi-modules}"
BRANCH="feat/add-plato-pack-storage-and-tenants-env-vars"
BODY="${TMPDIR:-/tmp}/plato_pr1_body.md"
REBUILD=0
[ "${1:-}" = "--rebuild" ] && REBUILD=1

cd "$REPO"
[ -z "$(git status --porcelain)" ] || { echo "refusing: $REPO has uncommitted changes" >&2; exit 1; }

git fetch origin main
if [ "$REBUILD" = "1" ]; then
    # -C: move the branch back onto origin/main, discarding what it held. The commit it discards
    # is local; a branch already pushed needs a force-push afterwards.
    git switch -C "$BRANCH" origin/main
else
    git switch -c "$BRANCH" origin/main 2>/dev/null || git switch "$BRANCH"
fi

python3 - <<'PY'
from pathlib import Path

CRLF = "\r\n"


def load(path):
    """The file as text, plus its own line ending.

    Bytes, not `read_text`: that applies universal-newline translation, so a CRLF file comes back
    as LF and writing it out again rewrites every line. The BOM on main.tf survives the round trip
    for the same reason -- it stays in the string and goes back out unchanged.
    """
    data = Path(path).read_bytes()
    return data.decode("utf-8"), (CRLF if CRLF.encode() in data else "\n")


NEW_VARS = '''
############################ japes-plato: pack storage and tenancy ############################

variable "japes_plato_tenants" {
  description = "PLATO_TENANTS for the japes-plato application: comma-separated tenant ids this replica serves. Required on a deployed tier -- every request carries X-Tenant-Id, and the job roles serve no request so they cannot infer which tenants exist."
  type        = string
  default     = ""
}

variable "japes_plato_pack_blob_backend" {
  description = "PLATO_PACK_BLOB_BACKEND for the japes-plato application: exactly 'azure' to store published assistant-pack archives in blob storage. Any other value is treated as local container disk, where an archive does not survive a restart while its database row does -- so pack upload refuses on a deployed tier unless this is azure."
  type        = string
  default     = ""
}

variable "japes_plato_pack_blob_container" {
  description = "PLATO_PACK_BLOB_CONTAINER for the japes-plato application: the blob container published pack archives are written to. Required whenever japes_plato_pack_blob_backend is azure; without it the archives would go to common's default container rather than plato's own."
  type        = string
  default     = ""
}
'''

# Anchored on the plato container's last env block rather than a line number.
ANCHOR = '''      env {
        name  = "APP_NAME"
        value = var.japes_plato_app_name
      }
'''

NEW_ENV = '''      env {
        name  = "PLATO_TENANTS"
        value = var.japes_plato_tenants
      }
      env {
        name  = "PLATO_PACK_BLOB_BACKEND"
        value = var.japes_plato_pack_blob_backend
      }
      env {
        name  = "PLATO_PACK_BLOB_CONTAINER"
        value = var.japes_plato_pack_blob_container
      }
      # The same key-vault secret other containers in this module already read for blob access, so
      # this adds no new secret -- only the name plato's storage layer looks it up under.
      # common.core.storage raises without it, so an azure pack backend is unusable until it is set.
      env {
        name  = "STORAGE__CONNECTION_STRING"
        value = data.azurerm_key_vault_secret.kernel_storage_connection_string.value
      }
      # The module-wide variable other containers here already read, so no new variable and no
      # tfvars change: devenv.auto.tfvars sets it to 0.2 and passes it in. Plato was the container
      # missing the env block, and the code's own default is 1.0 -- so without this an apply that
      # converges the container's env would drop the hand-entered value and trace every request.
      env {
        name  = "OTEL_SAMPLER_RATIO"
        value = var.otel_sampler_ratio
      }
      # The third provider. Plato is satisfied by any one of ANTHROPIC / OPENAI / AZURE_OPENAI /
      # GEMINI and already receives the first two, so this is not blocking -- it matters the day an
      # assistant pack names a Gemini model. Added now because it costs nothing: the key-vault
      # secret and its data source already exist here and three other containers read them.
      env {
        name  = "GEMINI_API_KEY"
        value = data.azurerm_key_vault_secret.gemini_api_key.value
      }
'''

# -- Step 1: declare in the module ------------------------------------------------------------
path = Path("module-dev/aca/variable.tf")
text, eol = load(path)
if "japes_plato_tenants" in text:
    print(f"{path}: already applied")
else:
    path.write_bytes(
        (text.rstrip("\r\n") + eol + NEW_VARS.replace("\n", eol)).encode("utf-8"))
    print(f"{path}: 3 variables appended, {'CRLF' if eol == CRLF else 'LF'} preserved")

# -- Step 2: wire into the container app ------------------------------------------------------
path = Path("module-dev/aca/main.tf")
text, eol = load(path)
if "PLATO_PACK_BLOB_BACKEND" in text:
    print(f"{path}: already applied")
else:
    anchor = ANCHOR.replace("\n", eol)
    if text.count(anchor) != 1:
        raise SystemExit(f"{path}: APP_NAME anchor matched {text.count(anchor)} times, expected 1")
    path.write_bytes(
        text.replace(anchor, anchor + NEW_ENV.replace("\n", eol)).encode("utf-8"))
    print(f"{path}: 6 env blocks inserted, {'CRLF' if eol == CRLF else 'LF'} preserved")
PY

# --stat first and on its own line, because a whole-file rewrite is only obvious there: it was
# visible in the counts of the first attempt and went unread until review caught it.
git --no-pager diff --stat
echo
git --no-pager diff

git add module-dev/aca/variable.tf module-dev/aca/main.tf
if git diff --cached --quiet; then
    echo "nothing new to commit; branch $BRANCH already carries the change"
else
    git commit -q -m "feat: add plato pack-storage and tenant env vars to the aca module"
    echo "committed on $BRANCH"
fi

cat > "$BODY" <<'BODY'
Adds six environment variables to the `japes_plato_service_app` container app in `module-dev/aca`.
No other container app is touched, and `module-dev` is the only module with a japes-plato app.

| Variable | Source | Why |
|---|---|---|
| `PLATO_TENANTS` | new `japes_plato_tenants` | Required on a deployed tier: every request carries `X-Tenant-Id`, and the `job:*` roles serve no request so they cannot infer which tenants exist. Reported as a degradation at `/info` today, and the chat routes answer 503. |
| `PLATO_PACK_BLOB_BACKEND` | new `japes_plato_pack_blob_backend` | Must be exactly `azure` for published assistant-pack archives to be durable. Left local, the archive is written to container disk and lost on restart while its immutable database row survives, so the upload route refuses on a deployed tier. |
| `PLATO_PACK_BLOB_CONTAINER` | new `japes_plato_pack_blob_container` | The blob container those archives go to. Without it they would land in `common`'s default container rather than plato's own. |
| `STORAGE__CONNECTION_STRING` | existing `data.azurerm_key_vault_secret.kernel_storage_connection_string` | **No new secret.** It is the same key-vault secret several containers in this module already read; plato's storage layer looks it up under this name, and `common.core.storage` raises without it. |
| `OTEL_SAMPLER_RATIO` | existing `var.otel_sampler_ratio` | **No new variable and no tfvars change** — the environment already sets it (`0.2` on dev-daily) and passes it to this module; plato is simply the one container app with no env block for it. The application's own default is `1.0`, so without this an apply that converges the container's environment would trace every request. |
| `GEMINI_API_KEY` | existing `data.azurerm_key_vault_secret.gemini_api_key` | **No new secret.** The same key-vault secret three other containers in this module already read. Plato is satisfied by any one of ANTHROPIC / OPENAI / AZURE_OPENAI / GEMINI and already gets the first two, so this is not blocking — it matters when an assistant pack names a Gemini model, and adding it now costs nothing. |

All three new variables default to `""`, so no environment's behaviour changes until its own
`.auto.tfvars` sets a value, and a blank value is read as not-configured by the application.

Resource modified: `azurerm_container_app.japes_plato_service_app` (`module-dev/aca/main.tf`).

Both files in this module use CRLF line endings, and the additions keep them, so the diff is the
added lines only -- 21 in `variable.tf`, 36 in `main.tf` -- with nothing else touched.

Merge before the `terraform-azure-jaxi` PR, which pins this module at `?ref=main`.
BODY

cat <<EOF

PR body written to $BODY

This script touched nothing outside your machine. To push the branch and open the PR against
main, run:

  ./tf_plato_env_publish.sh 1
EOF
