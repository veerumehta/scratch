#!/bin/sh
# Run the document suites and ruff for one worktree: run_doc_checks.sh <worktree> [pytest args...]
# With no pytest args it runs the document-area test files named below.
set -eu
tree="${1:?usage: run_doc_checks.sh <worktree> [pytest args...]}"
shift
venv=/Users/sangit/src/japes/.venv/bin
cd "$tree"
if [ "$#" -eq 0 ]; then
  set -- tests/test_chunk_locator.py tests/test_doc_pipeline_gaps.py tests/test_extract.py \
    tests/test_documents_extract.py tests/test_page_readers.py tests/test_locator_modes.py \
    tests/test_local_cache.py
fi
PYTHONPATH=. "$venv/pytest" -q "$@"
"$venv/ruff" check jazzx_sdk/tools/documents jazzx_sdk/agents/document jazzx_sdk/pipelines/document
