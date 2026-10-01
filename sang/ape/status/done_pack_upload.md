# Uploading a pack, and what "update" means

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: plan, 2026-09-16. Written against japes `1289f9a` on `v2.5.2`.

Extends `plan_pack_store.md` §Stage 1 ("import a built pack — Studio or jaci's `config/packs/`, via
CI or upload"). That document's header still says *nothing built*, which is now wrong: the
`pack_version` half shipped in 2.5.0-2.5.1 and migration `0004` added `retired_at`. Read this for
the upload surface only; the table design there stands.

## 1. The store layer is done. The gap is one route.

`DbPackVersionStore.publish(manifest, *, archive=bytes, published_by_user_id, visibility)` already
does the work, and the hard parts are already right:

- **Content-addressed blobs** through `offload(dedup=True)`, so two tenants publishing an edited
  `dscr-core 0.1.0` do not overwrite each other — the failure that keyed archives by
  `packs/{pack_id}/{version}.zip` and made an immutable row point at another tenant's bytes.
- **Immutable versions**: an existing row, retired or not, raises `PackVersionExists`.
- **Hardened extraction** in `_unpack`: every member's resolved path is checked against the
  destination before `extractall`, by `is_relative_to` rather than a string prefix, and both
  manifest names are located at the root or one level down.
- **Digest-keyed materialize cache**, with the marker's contents validated rather than trusted.

`seed.py` already builds archives from directories (`pack_archive`) and publishes them
(`seed_packs`, behind `POST {prefix}/packs/initialize`). So the upload feature is: accept bytes over
HTTP and hand them to a function that already exists.

## 2. "Update" is two different asks, and the repo has already answered both

`plan_pack_store.md` §Stage settles this and it is worth restating because the word is ambiguous:

| Ask | Answer | Built? |
|---|---|---|
| Correct a published pack | Publish a **new version**. `publish` refuses an existing one — *"an immutable version that can be replaced is a mutable one with extra steps"* | store yes, route no |
| Edit a pack in place | A separate mutable `pack_draft` row, promoted to a `pack_version` at publish | no |

So this plan covers **upload a new pack, and upload a new version of an existing pack** --
confirmed as the requirement: a new version per update is the accepted shape. Edit-in-place is
Stage 2 and stays out. The consequence for the UI is that a re-upload of the same version is a
409 an operator must be able to act on, not an error to hide: the message has to say *publish a new
version*, and the page should offer the pack's existing versions beside it.

## 3. What has to be built

1. **`POST {prefix}/packs`** — `multipart/form-data` with one `.zip`. Reads the manifest from the
   archive (`_unpack` already locates it under either name), then `publish(manifest, archive=bytes)`.
   Returns the `PackVersionRecord` fields the list route already returns, so the page can render the
   new row without a reload. `409` on `PackVersionExists`, `422` on an archive with no manifest or a
   manifest missing `pack_id`/`pack_version`.
2. **A size cap, before the bytes are read.** `publish` takes `bytes` and `_unpack` wraps them in
   `io.BytesIO`, so the whole archive is resident twice. Uncapped this is the cheapest memory DoS in
   Plato. A declared limit (`PLATO_PACK_UPLOAD_MAX_BYTES`) refused with `413`, checked against
   `Content-Length` *and* while streaming, since the header is a claim. Measured reference: the
   bundled packs zip to 62 KB (`ci-spread-core`) and 20 KB (`dscr_core`), so a few MB is three
   orders of headroom.
3. **A decompression cap.** The member-path check is the traversal defence; it is not a zip-bomb
   defence. `ZipInfo.file_size` summed before `extractall`, refused past a multiple of the archive
   size.
4. **The file picker on the Packs page.** Beside Initialize, behind the same
   `RELAXED_WRITES`/posture gate the other controls now use — see §4, the gate is not the same one.
5. **`published_by_user_id`** from `acting_user_id()`, the way `delete_pack_version` records its
   actor. The column exists.

## 4. Decided: upload works in every posture, including production

Upload is a routine operation, not an operator's debugging tool. Packs are authored offline by
another tool and arrive here continuously, in production included. So `relaxed_only` is the wrong
rule -- it refuses outright outside local/dev-daily with no auth escape -- and the rule is `/config`'s
PATCH instead: `withholding(strict=, auth=)`, which admits a write in any posture once the deployment
has said who may make them.

**That has a consequence worth stating plainly: no shipped wiring sets `PlatoWiring.auth`.** So on a
strict tier, upload is refused until a deployment supplies an auth dependency. Two ways out, and it
is a real choice:

- **Wire an auth dependency.** Correct, and what `withholding`'s docstring means by "a caller
  wanting one rule for both passes `auth`". It is the only option that makes a production upload an
  authorization decision rather than a claim.
- **Accept `identity_required` for this write.** `withholding` takes it and the read routes use it,
  but `create_config_router` deliberately refuses it for *writes*: a gateway-injected header
  identifies who is asking without being an authorization decision. Taking it here would be the
  first write in Plato to accept that, and the reason to consider it is that `require_identity` is
  already on in every deployed tier and the gateway does authenticate.

Recommendation: the auth dependency, with the refusal naming exactly what is missing so the first
operator to hit it knows what to ask for. Until one is wired, upload works on local and dev-daily,
which is where the pack is being iterated anyway.

## 4b. Blob durability, which blocks the feature being real

`PACK_BLOB_BACKEND_ENV` defaults to local storage, and `_pack_blob`'s note is deliberately *not* in
the readiness list -- for a good reason recorded there (it would fail a correctly configured staging
replica's container probe). The consequence for upload is specific: on ACA the archive lands on the
container filesystem, the `pack_version` row commits, and the bytes vanish on the next restart or
scale-out. The row survives, immutable, pointing at a blob that is gone, and `materialize` then
raises rather than serving the pack.

**Upload without `PLATO_PACK_BLOB_BACKEND=azure`, a container, and `STORAGE__CONNECTION_STRING` is a
feature that appears to work and loses data.** Three variables, not two: the azure path resolves through
`common.core.storage`, which raises without the connection string -- and Plato's own durability guard
passes on the backend name alone, so the failure arrives from `common` rather than from the guard. With upload a production path, this is not optional: the storage account belongs on
the same devops request as the database. Upload should additionally refuse when the backend is local
and the posture is deployed -- the one place that condition can be enforced, since the readiness list
cannot carry it.

## 4c. The half that is not upload: activation and reload

**Shipped in 2.5.2, as decided below.** `POST {prefix}/packs/{pack_id}/{version}/activate`,
`PLATO_ACTIVE_PACK` as the durable pointer, and a rebinding reload on the replica that serves the
request. Read the rest of this section for the decisions; the sentences in the present tense about
there being no reload path describe the tree as it was.


Uploading a version puts it in the store. It does not change what this replica serves, and there is
**no runtime reload path anywhere in the tree**. `plato/wiring/default.py:351` states it -- *"setting
PLATO_PACK_DIR through `/v1/config` does not reload a pack"* -- and the degraded note tells the
operator a restart is needed. So "take a new one and enable updates" needs two things the store does
not have:

1. **An activation pointer**: which published version this deployment serves. Today the answer is a
   filesystem path in `PLATO_PACK_DIR`, read once at boot, which the store knows nothing about.
   `plan_pack_store.md` calls this an alias and says aliases give promote and rollback mechanically.
2. **A reload**: rebuild the runtime's assistants from the activated version without restarting,
   materialized from the blob through `materialize`'s digest-keyed cache. `_rewire` is the precedent
   for applying a configuration change to a live process, and it is honest about its own limit --
   it drops the `ClientLayer` singleton and swaps the database engine, and deliberately does not
   touch the pack.

**Decided: one activated version per deployment, and activation is a separate step from upload.**

Per deployment, not per tenant: `PLATO_PACK_DIR` is already one pack per process, so this stays
inside the shape the wiring has rather than making the runtime hold a pack per tenant. The store
remains tenant-scoped underneath -- each tenant's row and blob are its own -- so per-tenant
activation stays available later without a migration; what is deferred is the runtime holding more
than one.

Separate from upload, because that is what makes a production upload safe: publishing a version
changes nothing that is serving, activation is the single act that does, and rollback is
re-activating the previous version rather than uploading again. It also means the offline tool can
push continuously without coordinating with a release.

**Interim that works today:** upload, then restart the replica. On ACA that is a rolling restart and
the pack is read at boot, so it is correct rather than a hack -- it is just a restart per pack
update. Worth having the upload route before activation exists, because the offline tool and CI can
start pushing immediately and the restart is a deployment action they already have.

## 5. Sequencing

1. **The route**, with the two caps, the actor, the `/config` posture rule, and the refusal when the
   blob backend is local on a deployed tier. Useful alone: the offline tool and CI can push a built
   pack immediately, with a restart to serve it.
2. **The page control**, so an operator can upload without a client.
3. **Activation** (§4c.1) -- an alias naming the served version, per deployment or per tenant, which
   is the question to settle first.
4. **Reload** (§4c.2) -- serve the activated version without a restart.

(3) and (4) are the substantial piece and the one the "all the time, even in prod" requirement
really turns on; (1) and (2) are small and unblock the authoring loop.

## 6. What would make this wrong

- **If Studio becomes the only authoring path.** Then the ingress is Studio's API and an operator
  upload is a debugging tool rather than a workflow, which changes the posture answer in §4 —
  `relaxed_only` would then be right after all.
- **If packs stop being archives.** Stage 2's `pack_draft` holds a pack as rows, and a store whose
  primary ingress is structured writes wants a different route than one that takes a zip.
