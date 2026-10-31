# Pulte: publishing the June 2026 Selling Guide as a guideline set (prepared, not run)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>
Date: 2026-10-30
Status: prepared; waits for the user's approval, because publishing writes to the shared local Plato (tenant `pulte`).

## What is published

One file, `Fannie Mae June 2026 Selling Guide.md` (kernel-lab `codec-suite/workflows/guidelines/`, read in place,
not copied into jaci). Edition "Published June 3, 2026". 2,598,374 bytes, sha256
`e4ec9b2181e1c918de50a2212e4c736e2005ca093db3d942e593e360a4cae767` (also in
`config/packs/pulte_home_mortgage_policy/coverage/fannie_selling_guide_topic_index.yaml`, which holds the
topic offsets and slice digests against this exact file).

## The call (one command once approved)

`PACK_TENANTS` now maps the Pulte pack folders to `pulte`, so `open_plato(pack=...)` picks the tenant:

```
JACI_PLATO_URL=http://localhost:8000/api/v1 .venv/bin/python - <<'EOF'
import asyncio
from pathlib import Path
from jaci.scenarios.shared.plato import open_plato

GUIDE = Path("/Users/sangit/src/kernel-lab/codec-suite/workflows/guidelines/Fannie Mae June 2026 Selling Guide.md")

async def main():
    async with open_plato(pack="pulte_home_mortgage_policy") as plato:
        print(await plato.publish_guideline(
            "fannie-mae-selling-guide",
            [(GUIDE.name, GUIDE.read_bytes(), "text/markdown")],
            note="Fannie Mae Selling Guide, Published June 3, 2026",
            effective_from="2026-06-03",
            idempotency_key="pulte-fannie-selling-guide-2026-06"))

asyncio.run(main())
EOF
```

The reply names the version (`G<n>`, an integer `n`) and the version digest. A second call with the same file
answers 409 `unchanged`.

## The pack's pin (fill from the reply, before the first publish of the pack)

`pin_of` reads a `guidelines:` key in the manifest with `set`, `version` (an integer) and `digest`. It cannot
hold a placeholder, so it is not in `pack_manifest.yaml` yet. After the call, add to
`config/packs/pulte_home_mortgage_policy/pack_manifest.yaml`:

```
guidelines:
  set: fannie-mae-selling-guide
  version: <n from the reply>
  digest: <digest from the reply>
```

Do it before the pack's first publish: a published pack version is immutable, so adding the pin afterwards
needs a `pack_version` bump (ask first).

## Order

1. Publish the guideline set (above).
2. Add the pin stanza to the policy pack manifest.
3. `scripts/publish_packs_to_plato.py pulte_home_mortgage_policy pulte_home_mortgage_core` (tenant `pulte`
   from `PACK_TENANTS`).
4. The blueprint seed (`pulte-home-mortgage`, owned by `sonnet-packs`) can then validate.

## Not decided here

- Whether the pin belongs on the policy pack alone (it is what the rules are certified against) or also on the
  assistant; the SDK pins one guideline per manifest.
- The SourceRef type (doc id, topic id, edition, sha, offsets) lands in runtime's adoption build; the index keys
  (`topic_id`, `start`, `end`, `sha256`, `date`, `edition`) are plain so they map onto it.
