#!/usr/bin/env bash
# Every Acra DSCR comparison over one set of extraction runs (local Plato on :8000).
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
#   acra_review_all.sh coverage/runs_YYYYMMDD.json [out_dir]
#
# 1. our JTBDs vs our Python rules, per guideline       -> <out>/ours/coverage_report.{json,xlsx}
# 2. Acra's JTBD files vs our Python rules, per guideline -> <out>/acra/coverage_report.{json,xlsx}
# 3. programs and Acra-vs-ours set comparisons          -> <out>/compare/compare_sets.{json,xlsx}
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
runs="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
out="${2:-$here/coverage/review_$(date +%Y%m%d)}"
py=/Users/sangit/src/japes/.venv/bin/python
cd /Users/sangit/src/japes
"$py" -u "$here/acra_coverage_report.py" --runs "$runs" --jobs ours --out "$out/ours"
"$py" -u "$here/acra_coverage_report.py" --runs "$runs" --jobs acra --out "$out/acra"
"$py" -u "$here/acra_compare_sets.py" --runs "$runs" --out "$out/compare"
echo "wrote $out"
