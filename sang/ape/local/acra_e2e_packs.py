"""Build the two scratch packs of the Acra end-to-end run as directories: Acra's K-Studio jobs, and ours.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

`acra-e2e-kstudio` is Acra's two JTBDSets imported as jobs (a core and a program overlay each), the way the
import route writes a draft. `acra-e2e-ours` is the seed pack's skeleton (profiles, schemas, metrics, documents)
with our extracted jobs and the code written from them, per program, and the ledger that links them. Neither
touches a published pack. Reads only the bundle and the seed; no loan data.

    python scripts/local/acra_e2e_packs.py [--bundle DIR] [--out DIR]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
from pathlib import Path
from typing import Any

import yaml

from jazzx_sdk.pack.jtbd_import import import_program_sets, write_import_to_draft

ROOT = Path("/Users/sangit/src/japes")
SEED = ROOT / "plato" / "data" / "seed_packs" / "acra_dscr_policy"
BUNDLE = ROOT / "docs" / "status" / "Acra" / "acra_bundle"
OUT = Path("/Users/sangit/src/.scratch/sang/ape/local/acra_e2e/packs")
KSTUDIO_ID, OURS_ID = "acra-e2e-kstudio", "acra-e2e-ours"
KSTUDIO_FILES = {"standard": "acra_New_Guideline_JTBD.json", "platinum_select": "acra_New_Guideline_JTBD_Platinum.json"}
OURS_POLICIES = {"standard": ("DSCR_STANDARD", "standard_policy.yaml"),
                 "platinum_select": ("DSCR_PLATINUM_SELECT", "platinum_policy.yaml")}


class _Files:
    """A draft store held in a dict: what `write_import_to_draft` needs, with no database."""

    def __init__(self) -> None:
        self.drafts: dict[str, dict[str, str]] = {}
        self.notes: dict[str, str] = {}

    async def get(self, pack_id: str) -> dict[str, Any] | None:
        return {} if pack_id in self.drafts else None

    async def open(self, pack_id: str, *, files: dict[str, str] | None = None, **_: Any) -> dict[str, Any]:
        self.drafts[pack_id] = dict(files or {})
        return {}

    async def read_file(self, pack_id: str, rel_path: str) -> str | None:
        return self.drafts[pack_id].get(rel_path)

    async def write_file(self, pack_id: str, rel_path: str, content: str, **_: Any) -> None:
        self.drafts[pack_id][rel_path] = content

    async def set_notes(self, pack_id: str, notes: str) -> None:
        self.notes[pack_id] = notes

    async def files(self, pack_id: str) -> dict[str, bytes]:
        return {k: v.encode() for k, v in self.drafts[pack_id].items()}

    async def delete_file(self, pack_id: str, rel_path: str, **_: Any) -> bool:
        return self.drafts[pack_id].pop(rel_path, None) is not None


async def build_kstudio(bundle: Path, out: Path) -> Path:
    sets = {program: json.loads((bundle / "2_kstudio_jtbds" / name).read_text())
            for program, name in KSTUDIO_FILES.items()}
    imported = await import_program_sets(sets, pack_id=KSTUDIO_ID)
    drafts = _Files()
    await write_import_to_draft(drafts, KSTUDIO_ID, imported, version="0.0.1", domain="commercial_lending",
                                segment="dscr", notes="Acra K-Studio JTBDs, scratch pack for the end-to-end run")
    root = out / KSTUDIO_ID
    shutil.rmtree(root, ignore_errors=True)
    manifest = yaml.safe_load(drafts.drafts[KSTUDIO_ID]["pack_manifest.yaml"])
    manifest["conductor"] = {"pre_loop": [{"kind": "policy_assessment"}]}
    drafts.drafts[KSTUDIO_ID]["pack_manifest.yaml"] = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True)
    for rel, text in drafts.drafts[KSTUDIO_ID].items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    return root


def build_ours(bundle: Path, out: Path) -> Path:
    root = out / OURS_ID
    shutil.rmtree(root, ignore_errors=True)
    shutil.copytree(SEED, root)
    for old in (root / "policies").glob("*.yaml"):
        old.unlink()
    for program, (policy_id, filename) in OURS_POLICIES.items():
        rules = yaml.safe_load((bundle / "3_sdk_jtbds" / filename).read_text())["rules"]
        policy = {"policy_id": policy_id, "version": "1.0.0", "name": f"{program} (our extraction)",
                  "description": f"Our jobs and the code written from them, {program}",
                  "policy_type": "institutional", "pack_id": OURS_ID, "jurisdiction": "US",
                  "effective_date": "2026-08-17T00:00:00Z", "status": "draft", "scope": "product",
                  "overlay_id": program, "rules": rules}
        (root / "policies" / f"{program}.yaml").write_text(yaml.safe_dump({"policies": [policy]}, sort_keys=False,
                                                                           allow_unicode=True))
    shutil.copy(bundle / "3_sdk_jtbds" / "ledger.yaml", root / "ledger.yaml")
    manifest = yaml.safe_load((root / "pack_manifest.yaml").read_text())
    manifest["pack_id"] = OURS_ID
    manifest["programs"] = {program: [policy_id] for program, (policy_id, _) in OURS_POLICIES.items()}
    (root / "pack_manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))
    return root


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bundle", type=Path, default=BUNDLE)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    print(asyncio.run(build_kstudio(args.bundle, args.out)))
    print(build_ours(args.bundle, args.out))


if __name__ == "__main__":
    main()
