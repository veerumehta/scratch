# PR #64 review: plato GHCR build workflow

Status: open, awaiting the author. Reviewed 2026-09-02 against the sibling repos' equivalents.

PR: https://github.com/JazzX-LLC/japes/pull/64 (`anilr8`, `PMR-1161` -> `main`, one new file,
`.github/workflows/Build-Push-Plato-Docker-Image-GHCR.yml`, 106 lines).

## Verdict

Merge after one two-character fix. Everything else conforms to a pattern already running in three
repos, so there is nothing else worth holding it for.

## What the comparison established

`Build-and-Publish-docker-image.yml` exists in **macer**, **jazzx-assistant** and **k9**, and the
three are near-identical. Every concern a first read raises turns out to be that shared pattern
rather than anything this PR introduced:

| First impression | Actually |
| --- | --- |
| `permissions` too broad (incl. `actions: write`) | identical in all three siblings |
| GHCR login uses a PAT, not `GITHUB_TOKEN` | identical in all three |
| `sleep 60s` then re-checkout | identical in all three |
| `:latest` moved on every run | identical in all three |

Conforming matters more here than any local improvement: plato becoming the odd one out buys
nothing today. Those points are recorded at the bottom as org-wide cleanup, not PR feedback.

Two places this PR is genuinely **better** than what it copies, both worth keeping:

- a `branch` input. The siblings hardcode main, which cannot work while plato's Dockerfile lives on
  the `plato` branch.
- `JAPES_GIT_COMMIT` / `JAPES_COMMON_COMMIT` build-args. Verified against the Dockerfile on
  `plato`: both are declared as `ARG` (lines 82-83) and the `--mount=type=secret,id=github_token`
  the workflow feeds is consumed at line 50. `GET {prefix}/info` reports the two commits.

## The blocker

`skip_tag_creation` is this PR's own addition -- no sibling has it -- and its two gates disagree on
type:

```yaml
- name: Create tag on selected branch
  if: inputs.skip_tag_creation == 'false'    # string
- name: Wait for 60 sec
  if: inputs.skip_tag_creation == false      # boolean
```

The input is declared `type: boolean`. Actions casts mismatched types to numbers for `==`, so
`false` -> `0` and `'false'` -> `NaN`; the string comparison never matches. The tag is therefore
never created, and *Checkout repository tag* fails on a ref that does not exist. The default path
(`skip_tag_creation: false`) cannot succeed as written.

Fix: `if: inputs.skip_tag_creation != true` on **both** steps, so they agree on one form. Dropping
the input to match the siblings exactly would also be fine -- they always create the tag, and a
duplicate tag fails the run loudly, which is arguably the behaviour wanted.

## Working today, without waiting for the fix

Pre-create the tag and dispatch with `skip_tag_creation=true`:

```bash
git tag v0.1.1 <sha> && git push origin v0.1.1
gh workflow run Build-Push-Plato-Docker-Image-GHCR.yml \
  -f branch=plato -f git_tag=v0.1.1 -f skip_tag_creation=true
```

Immune to the bug by construction: `true == 'false'` is false, so the broken step is *correctly*
skipped; the sleep is skipped too; and the checkout finds the tag that was just pushed. Everything
after that is the proven pattern. `git_tag` has no default, so `-f git_tag=...` is required.

Untested, and it does not matter if the tag is pre-created: whether API/CLI dispatch delivers a
typed boolean or the string `'false'`. If strings, `-f skip_tag_creation=false` would also work,
since the PR's script `await`s `createRef` and so does not depend on the 60s sleep. One dispatch
would settle it.

## Comment to post

```markdown
Conforms to the org pattern (`Build-and-Publish-docker-image.yml` in macer /
jazzx-assistant / k9) — same permissions, same PAT-based GHCR login, same
60s-and-recheckout, same `:latest` + `:<git_tag>`. Good: keeping plato on the
shared shape is worth more than any local improvement, so no comments there.

Two things this does better than the pattern it copies, both worth keeping:
the `branch` input (the siblings hardcode main, which can't work while the
Dockerfile lives on `plato`), and passing `JAPES_GIT_COMMIT` /
`JAPES_COMMON_COMMIT`, which our Dockerfile declares as ARGs and reports
from `GET {prefix}/info`.

One blocker, in the part that isn't from the pattern — `skip_tag_creation`
is gated two different ways:

    - name: Create tag on selected branch
      if: inputs.skip_tag_creation == 'false'    # string
    - name: Wait for 60 sec
      if: inputs.skip_tag_creation == false      # boolean

The input is `type: boolean`. Actions casts mismatched types to numbers for
`==`, so `false` → 0 and `'false'` → NaN: the string comparison never
matches, the tag is never created, and "Checkout repository tag" then fails
on a ref that doesn't exist. The default path (`skip_tag_creation: false`)
can't succeed as written.

Suggest `if: inputs.skip_tag_creation != true` on both steps so they agree on
one form. Dropping the input to match the siblings exactly would also be fine
— they always create the tag, and a duplicate just fails the run loudly.

Until then it works if you pre-create the tag and dispatch with
`skip_tag_creation=true`: the broken condition is then correctly skipped and
the checkout finds the tag.

Not blocking, for later and org-wide rather than here: `actions: write` isn't
used by any step, and `attestations: write` + `id-token: write` are for
provenance attestation that no step performs. Same in all three sibling
workflows, so it's a pattern-level cleanup, not this PR's.
```

## Org-wide follow-ups (not this PR)

Each of these is in all three sibling workflows, so any change belongs in a pass over the pattern
rather than here:

- `actions: write` is granted and used by nothing. `attestations: write` + `id-token: write` are for
  provenance attestation, and no workflow performs one. `contents: write` (tag) and
  `packages: write` (push) are what is actually needed.
- GHCR login uses `DEVOPS_JAZZX_TOKEN`. The PAT is genuinely required for the private submodule
  checkout and the poetry install, but with `packages: write` the built-in `GITHUB_TOKEN` can push
  to the repo's own GHCR.
- `sleep 60s` plus a second checkout exists to survive the branch moving during the wait -- a window
  the sleep itself creates. Capturing the SHA once and building from it removes both.
- `:latest` is moved by every run, including one built from an arbitrary branch. With plato's
  default being `plato` rather than `main`, `latest` will point at unreleased code.
