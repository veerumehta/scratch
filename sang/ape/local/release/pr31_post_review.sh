#!/bin/bash
# Posts /tmp/pr31_review.json as one review (event COMMENT) on jazzx-assistant PR #31.
# Review the JSON first. A 422 means a line is outside the diff; nothing is posted then.
set -u
gh api -X POST repos/JazzX-LLC/jazzx-assistant/pulls/31/reviews --input /tmp/pr31_review.json \
  --jq '.html_url'
