"""Import a JTBD set into a pack folder with `import_jtbdset`.

Usage: PYTHONPATH=<japes worktree> python packs_build_pack.py <jtbds.json> <out dir> <pack id>

Author: Virendra Mehta <virendra.mehta@jazzx.ai>
"""
import json, sys, shutil
from pathlib import Path
import yaml
from jazzx_sdk.pipelines.policy.jtbdset import import_jtbdset

def build(jtbds: Path, out: Path, pack_id: str):
    if out.exists(): shutil.rmtree(out)
    (out / "policies").mkdir(parents=True)
    artifact = json.loads(jtbds.read_text())
    imported = import_jtbdset(artifact, pack_id=pack_id, metrics_key="loan_metrics")
    for policy in imported.policies:
        doc = {"policies": [policy.model_dump(mode="json", exclude_none=True)]}
        (out / "policies" / f"{policy.policy_id.lower()}.yaml").write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100))
    manifest = {"pack_id": pack_id, "pack_version": "0.1.0", "certification_status": "draft",
                "domain": "residential_lending", "segment": "mortgage", "policies": {"dir": "policies"},
                "programs": {"core": [], **imported.programs}}
    (out / "pack_manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))
    (out / "jtbd_template.yaml").write_text("# Author: Virendra Mehta <virendra.mehta@jazzx.ai>\nmetrics_key: loan_metrics\n")
    base = sum(1 for p in imported.policies if p.scope.value == "institution" for _ in p.rules)
    over = {p.overlay_id: len(p.rules) for p in imported.policies if p.scope.value == "product"}
    print(out.name, "policies", len(imported.policies), "base rules", base, "overlays", over)
    return imported

if __name__ == "__main__":
    build(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
