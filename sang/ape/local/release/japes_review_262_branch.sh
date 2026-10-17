#!/bin/bash
# The v2.6.2 parameters for scripts/local/review_branch_from_version.sh: one squash commit of the
# v2.6.2 tip on a new remote branch review/v2.6.2 off dev (dev and the 2.6.1 squash untouched), and a
# local v2.6.3 cut from the same tip. Nothing is pushed until you type y.
exec /Users/sangit/src/.scratch/sang/ape/local/review_branch_from_version.sh \
  --src v2.6.2 --branch review/v2.6.2 --next v2.6.3 \
  --message "v2.6.2 (plato v0.2.3): document registry and job shapes, dated pack versions and release report, decision corrections, solution view and assistant chat, JTBD set lint, typed conditions, case runs from the runs page" \
  "$@"
