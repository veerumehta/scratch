"""Job identity of a trial pack's jobs, counts only: sections against the template's list, mnemonics, prefixes, slug lengths.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Reads the trial pack's draft over the local Plato (policy text only, no loan data) and prints one JSON object per policy.

    python acra_identity_measure.py --pack acra-regen-6
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import Counter

import httpx
import yaml

API = "http://localhost:8000/api/v1"
HEAD = {"x-tenant-id": "acra-lending"}


def _key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower().replace("&", "and"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", required=True)
    args = parser.parse_args()
    with httpx.Client(timeout=60, headers=HEAD) as http:
        def read(path: str) -> str:
            return http.get(f"{API}/packs/drafts/{args.pack}", params={"path": path}).json()["content"]

        template = yaml.safe_load(read("jtbd_template.yaml"))
        listed = {_key(name) for name in template["sections"]}
        for policy in ("acra-standard", "acra-platinum"):
            document = yaml.safe_load(read(f"policies/{policy}.yaml")) or {}
            rules = [r for p in document.get("policies") or [] for r in p.get("rules") or []]
            jobs = [r for r in rules if ((r.get("condition") or {}).get("type") == "procedure"
                                         or ((r.get("domain_extensions") or {}).get("jtbd") is not None))]
            meta = [((r.get("domain_extensions") or {}).get("jtbd") or {}) for r in jobs]
            mnemonics = [m["mnemonic"] for m in meta if m.get("mnemonic")]
            slugs = [len(m.split("-", 1)[1]) for m in mnemonics if "-" in m]
            sections = [m.get("section") for m in meta if m.get("section")]
            by_id_section = [r["rule_id"].split(".")[1] if r["rule_id"].count(".") > 1 else "" for r in jobs]
            print(json.dumps({
                "policy": policy, "rules": len(rules), "jobs": len(jobs),
                "with_mnemonic": len(mnemonics), "without_mnemonic": len(jobs) - len(mnemonics),
                "unique_mnemonics": len(set(mnemonics)),
                "with_section": len(sections),
                "section_listed": sum(1 for s in sections if _key(s) in listed),
                "id_section_listed": sum(1 for s in by_id_section if _key(s.replace("_", " ")) in listed),
                "prefixes": dict(Counter(m.split("-")[0] for m in mnemonics).most_common()),
                "slug_len_median": statistics.median(slugs) if slugs else None,
                "slug_len_max": max(slugs) if slugs else None,
                "mnemonic_len_max": max((len(m) for m in mnemonics), default=None),
                "derived_prefix_notes": sum(1 for r in jobs if "derived from the section name" in json.dumps(r)),
                "sections_used": dict(Counter(sections).most_common()),
            }, indent=1))


if __name__ == "__main__":
    main()
