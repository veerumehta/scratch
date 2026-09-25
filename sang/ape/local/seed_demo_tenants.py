"""Build one assistant pack per demo tenant and publish each through the upload route.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    ./scripts/local/seed_demo_tenants.py [--base http://localhost:8000]

Four tenants, four different assistants, so per-tenant serving is visible rather than assumed.
`POST {prefix}/packs` with a multipart zip is what the packs page posts, so this exercises the
path a real publish takes rather than writing to the store directly.

The bundled `plato/data/seed_packs` are domain packs -- policies and vocabulary, no `profile/` --
which publish fine and compose no assistant. These carry a profile, so they serve.
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

import yaml

# From git, not from `__file__`: `scripts/local` is a symlink out of the tree, so walking up
# from this file lands in the checkout it points at.
REPO = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, check=True).stdout.strip())
DEMO = REPO / "plato" / "data" / "demo_pack"

#: tenant -> (pack_id, assistant name, what its one skill does, domain, segment).
#:
#: A tenant is the customer the install belongs to, not the domain: production is one tenant per
#: customer. `acme-hospital` is the id `plato.wiring.default` already defaults a local run to.
#:
#: Each pack id carries its tenant's short name. The store already keys on `(tenant_id, pack_id,
#: version)`, so this is for reading the cross-tenant table rather than for correctness.
TENANTS = {
    "acme-hospital": ("acme-clinical-intake-core", "Clinical Intake",
                      "Collect the reason for the visit, then medications, one question at a time.",
                      "healthcare", "clinical_intake"),
    "pulte": ("pulte-home-mortgage-core", "Home Mortgage Intake",
              "Collect income, employment and the property address for a residential loan.",
              "residential_lending", "mortgage"),
    "acra-lending": ("acra-dscr-core", "Acra DSCR Underwriting",
                     "Collect rent roll and operating expenses, then state the DSCR you computed.",
                     "commercial_lending", "dscr"),
    "mesa-verde": ("mesa-cre-spread-core", "CRE Spreading",
                   "Collect the rent roll and T-12, then spread them into the standard line items.",
                   "commercial_lending", "cre_spread"),
}

#: Above every retired number: the unprefixed first cut was published at 1.0.0 and retiring a
#: version burns it, so a reseed cannot reuse one.
PACK_VERSION = "1.1.0"


def build_pack(tenant: str, pack_id: str, name: str, instructions: str,
               domain: str, segment: str) -> tuple[dict, bytes]:
    """The manifest and the zip, modelled on the bundled demo pack."""
    skill = pack_id.replace("-", "_") + "_intake"
    profile_ref = pack_id.replace("-", "_") + "_agent"

    manifest = yaml.safe_load((DEMO / "manifest.yaml").read_text())
    manifest.update(
        pack_id=pack_id,
        pack_version=PACK_VERSION,
        assistant_id=pack_id,
        name=name,
        description=f"{name}: a scaffold for local testing, one skill.",
        allowed_skills=[skill],
        profile_ref=profile_ref,
        # `publish` reads both off the manifest; without them the row stores "" and None, and
        # the packs table renders two empty columns.
        domain=domain,
        segment=segment,
    )

    profile = {
        "name": profile_ref,
        "persona": "persona.md",
        "conversation": True,
        "skills": [skill],
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        bundle.writestr("manifest.yaml", yaml.safe_dump(manifest, sort_keys=False))
        bundle.writestr("profile/profile.yaml", yaml.safe_dump(profile, sort_keys=False))
        bundle.writestr("profile/persona.md",
                        f"# {name}\n\nYou are {name}. Ask one question at a time and confirm "
                        f"what you heard. Record, do not interpret.\n")
        bundle.writestr(f"profile/skills/{skill}.yaml", yaml.safe_dump(
            {"name": skill, "description": instructions, "instructions": instructions},
            sort_keys=False))
    return manifest, buffer.getvalue()


def upload(base: str, tenant: str, archive: bytes) -> dict:
    """`POST {base}/api/v1/packs`, the multipart form the packs page submits."""
    boundary = "----japes-seed-boundary"
    body = b"".join([
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="archive"; filename="pack.zip"\r\n',
        b"Content-Type: application/zip\r\n\r\n",
        archive,
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    request = urllib.request.Request(
        f"{base}/api/v1/packs", data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                 "X-Tenant-Id": tenant},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        return {"error": exc.code, "detail": exc.read().decode("utf-8", "replace")[:200]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:8000")
    args = parser.parse_args()

    failures = 0
    for tenant, (pack_id, name, instructions, domain, segment) in TENANTS.items():
        _manifest, archive = build_pack(tenant, pack_id, name, instructions, domain, segment)
        result = upload(args.base, tenant, archive)
        if result.get("published"):
            print(f"{tenant:12} {result['pack_id']} {result['version']} "
                  f"({len(archive)} bytes, digest {result['content_digest'][:12]})")
        else:
            failures += 1
            print(f"{tenant:12} FAILED: {result}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
