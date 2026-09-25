#!/usr/bin/env python3
"""Retire every pack a demo tenant should not be serving.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    ./scripts/local/retire_stray_packs.py                       # dry run against localhost
    ./scripts/local/retire_stray_packs.py --apply
    ./scripts/local/retire_stray_packs.py --base https://dev-daily-gw.jazzx.dev/plato --apply

One pack per demo tenant. `POST /packs/initialize` publishes the two bundled packs under
`plato/data/seed_packs` into whichever tenant the request names, so running it per tenant left
`ci-spread-core` and `dscr-core` in all four beside each tenant's own.

Retiring is what the store supports: the version is skipped by reads, its number can never be
republished, and the archive stays. Nothing is erased.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

#: tenant -> the one pack_id it serves. Everything else published to that tenant is retired.
KEEP = {
    "acme-hospital": "clinical-intake-core",
    "pulte": "home-mortgage-core",
    "acra-lending": "acra-dscr-core",
    "mesa-verde": "cre-spread-core",
}


def call(base: str, tenant: str, path: str, method: str = "GET") -> dict:
    request = urllib.request.Request(f"{base}/api/v1/{path}", method=method,
                                     headers={"X-Tenant-Id": tenant,
                                              "accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        return {"error": exc.code, "detail": exc.read().decode("utf-8", "replace")[:200]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:8000")
    parser.add_argument("--apply", action="store_true", help="without this, only prints")
    parser.add_argument("--all", action="store_true",
                        help="retire every pack, not just the strays: a clean slate to reseed onto")
    args = parser.parse_args()

    failures = 0
    for tenant, keep in KEEP.items():
        listing = call(args.base, tenant, "packs")
        if not listing.get("available"):
            print(f"{tenant:14} unreadable: {listing.get('detail') or listing.get('reason')}")
            failures += 1
            continue

        stray = [(p["pack_id"], v["version"])
                 for p in listing.get("packs", [])
                 if args.all or p["pack_id"] != keep
                 for v in p.get("versions", [])]
        if not stray:
            print(f"{tenant:14} already serves {keep} alone")
            continue

        for pack_id, version in stray:
            if not args.apply:
                print(f"{tenant:14} would retire {pack_id} {version}")
                continue
            result = call(args.base, tenant, f"packs/{pack_id}/{version}", method="DELETE")
            if result.get("error"):
                failures += 1
                print(f"{tenant:14} FAILED {pack_id} {version}: {result}")
            else:
                print(f"{tenant:14} retired {pack_id} {version}")

    if not args.apply:
        print("\nDry run. Re-run with --apply to retire.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
