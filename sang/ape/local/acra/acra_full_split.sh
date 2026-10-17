#!/bin/bash
# Splits the whole funded Acra loan file (about 429 pages) with the seed pack's registry taxonomy.
# Aggregate figures only; report lands in ape/local/coverage/ingest_full/split_vision.json.
# Cost: a few tenths of a dollar (40 pages cost about $0.04); the vision budget caps it at $5.
set -u
cd /Users/sangit/src/japes || exit 1
exec python scripts/local/acra_full_package_split.py "$@"
