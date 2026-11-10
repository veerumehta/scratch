"""Seed the local Plato with the guidance-governance demo: two packs and a few assets.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Local data only, no provider calls. Run with the main checkout's python and PYTHONPATH at the v2.7.1 tree:

    PYTHONPATH=/Users/sangit/src/japes-v27 /Users/sangit/src/japes/.venv/bin/python demo_guidance_setup.py [--base http://localhost:8000]

Packs: `demo-guidance-lending` declares a certification forum (two members); `demo-guidance-open` declares none.
Identities are fixed UUIDs (printed at the end); the page's identity box takes one.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import uuid
from pathlib import Path

import httpx

from jazzx_sdk.pack.store import pack_archive

BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "http://localhost:8000"
API = f"{BASE}/api/v1"
SAMPLE = Path("/Users/sangit/src/japes-v27/plato/data/sample_packs/acme-clinical-intake-core")


def person(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"guidance-demo-{name}"))


PEOPLE = {n: person(n) for n in ("alice", "bob", "carol", "dave", "frank")}
FORUM = f"""forums:
  - forum_id: certification-board
    kind: certification
    members: [{PEOPLE['carol']}, {PEOPLE['dave']}]
"""


def publish(pack_id: str, name: str, governance: str | None) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / pack_id
        shutil.copytree(SAMPLE, root)
        manifest = (root / "manifest.yaml").read_text()
        manifest = manifest.replace("pack_id: acme-clinical-intake-core", f"pack_id: {pack_id}")
        manifest = manifest.replace("assistant_id: acme-clinical-intake-core", f"assistant_id: {pack_id}")
        manifest = manifest.replace("name: Clinical Intake", f"name: {name}")
        manifest = manifest.replace("pack_version: 1.1.0", "pack_version: 1.0.0")
        (root / "manifest.yaml").write_text(manifest)
        if governance:
            (root / "governance").mkdir()
            (root / "governance" / "guidance.yaml").write_text(governance)
        data = pack_archive(root)
    r = httpx.post(f"{API}/packs", files={"archive": (f"{pack_id}.zip", data, "application/zip")},
                   data={"notes": "guidance governance demo"}, timeout=60)
    print(f"publish {pack_id}: {r.status_code} {'' if r.status_code == 200 else r.text[:200]}")


def call(method: str, path: str, who: str, **kwargs) -> httpx.Response:
    headers = {"x-user-id": PEOPLE[who], "Idempotency-Key": uuid.uuid4().hex}
    return httpx.request(method, f"{API}{path}", headers=headers, timeout=60, **kwargs)


def draft(pack: str, who: str, text: str, triggers: list[str], **extra) -> dict:
    r = call("PUT", f"/packs/{pack}/guidance", who, json={"guidance": text, "trigger_patterns": triggers, **extra})
    r.raise_for_status()
    return r.json()


def step(pack: str, asset: str, action: str, who: str, **body) -> httpx.Response:
    return call("POST", f"/packs/{pack}/guidance/{asset}/{action}", who, json=body)


def live(pack: str, text: str, triggers: list[str]) -> dict:
    """A deployed first version, so later drafts have something to supersede."""
    asset = draft(pack, "alice", text, triggers)
    assert step(pack, asset["asset_id"], "approve", "bob").status_code == 200
    assert step(pack, asset["asset_id"], "deploy", "bob", allow_unvalidated=True).status_code == 200
    return asset


def main() -> None:
    publish("demo-guidance-lending", "Demo Lending", FORUM)
    publish("demo-guidance-open", "Demo Open", None)
    for pack in ("demo-guidance-lending", "demo-guidance-open"):
        base = live(pack, "Ask for the lease and the rent roll first.", ["lease", "rent roll"])
        base_id = base["asset_id"]
        # a minor change: the owner approves alone
        minor = draft(pack, "alice", "Ask for the lease, the rent roll and the T-12 first.", ["lease", "t-12"],
                      supersedes=base_id, change_class="minor_behavioral")
        step(pack, minor["asset_id"], "approve", "bob")
        # a material change left waiting for its approvals (the demo takes it through them live)
        draft(pack, "alice", "Treat a lease under twelve months as a risk, not a blocker.", ["short lease"],
              supersedes=base_id, change_class="material_behavioral")
    print("people (x-user-id):")
    for name, ident in PEOPLE.items():
        print(f"  {name:6s} {ident}")


main()
