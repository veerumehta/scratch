#!/bin/bash
# Pushes the already-created local branch review/v2.6.2 (it exists from the earlier run; nothing was
# pushed). NO_VERIFY=1 skips the pre-push hook (suite and adversarial review) as the earlier
# v2.6.2 push did; JAPES_SKIP_SUITE=1 skips only the suite, the review still runs.
exec /Users/sangit/src/.scratch/sang/ape/local/push_review_branch.sh review/v2.6.2
