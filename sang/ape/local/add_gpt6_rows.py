#!/usr/bin/env python3
"""Add the GPT-6 Sol and Luna rows to `jazzx_sdk/llm/model_data.json`.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

One-off. Written as a script rather than a hand edit so the row shape is copied from the file's
own schema and the key order stays where the newest OpenAI models go: ahead of the 5.6 rows.
"""

from __future__ import annotations

import json
import pathlib
import subprocess

REPO = pathlib.Path(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                   capture_output=True, text=True, check=True).stdout.strip())
DATA = REPO / "jazzx_sdk" / "llm" / "model_data.json"

RETRIEVED = "2026-09-23T15:59:47Z"
PRICING_SOURCE = "https://developers.openai.com/api/docs/pricing"

# Every reasoning model in this family rejects these; the GPT-6 pages do not list them either way,
# so the family's set is carried over and the provenance note says it was not verified.
_UNSUPPORTED = ["temperature", "top_p", "presence_penalty", "frequency_penalty",
                "logprobs", "top_logprobs", "logit_bias"]
_EFFORTS = ["none", "low", "medium", "high", "xhigh", "max"]
_CAPABILITIES = {"tools": True, "vision": True, "caching": True, "reasoning": True,
                 "structured_output": True, "documents": True}

ROWS = {
    "gpt-6-sol": {
        "pricing": {
            "input": 2.0,
            "output": 10.0,
            "cached_input": 0.2,
            "cache_creation": 2.5,
            "long_context": {
                "threshold_prompt_tokens": 272000,
                "input": 4.0,
                "output": 15.0,
                "cached_input": 0.4,
                "cache_creation": 5.0,
            },
        },
        "card": {
            "provider": "openai",
            "display_name": "GPT-6 Sol",
            "family": "gpt-6",
            "context_window": 1050000,
            "max_output_tokens": 128000,
            "capabilities": dict(_CAPABILITIES),
            "unsupported_request_params": list(_UNSUPPORTED),
            "reasoning_efforts": list(_EFFORTS),
        },
        "provenance": {
            "source": PRICING_SOURCE,
            "retrieved": RETRIEVED,
            "reviewed_by": "",
            "reviewed_on": "",
            "note": "standard tier; long-context columns are 2x input and cache rates and 1.5x "
                    "output above 272k, quoted on the model page. Knowledge cutoff 2026-04-20. "
                    "`unsupported_request_params` carried over from the 5.6 rows, not documented "
                    "for this model.",
        },
    },
    "gpt-6-luna": {
        "pricing": {
            "input": 0.1,
            "output": 0.5,
            "cached_input": 0.01,
            "cache_creation": 0.125,
            "long_context": {
                "threshold_prompt_tokens": 272000,
                "input": 0.2,
                "output": 0.75,
                "cached_input": 0.02,
                "cache_creation": 0.25,
            },
        },
        "card": {
            "provider": "openai",
            "display_name": "GPT-6 Luna",
            "family": "gpt-6",
            "context_window": 1050000,
            "max_output_tokens": 128000,
            "capabilities": dict(_CAPABILITIES),
            "unsupported_request_params": list(_UNSUPPORTED),
            "reasoning_efforts": list(_EFFORTS),
        },
        "provenance": {
            "source": PRICING_SOURCE,
            "retrieved": RETRIEVED,
            "reviewed_by": "",
            "reviewed_on": "",
            "note": "standard tier; long-context columns are 2x input and cache rates and 1.5x "
                    "output above 272k, quoted on the model page. Knowledge cutoff 2026-05-18. "
                    "`unsupported_request_params` carried over from the 5.6 rows, not documented "
                    "for this model.",
        },
    },
}


def main() -> int:
    data = json.loads(DATA.read_text())
    models = data["models"]
    for key in ROWS:
        if key in models:
            print(f"{key} is already present; nothing written")
            return 1

    # Ahead of the 5.6 rows, which is where the file puts a newer model in a family.
    rebuilt: dict = {}
    for key, row in models.items():
        if key == "gpt-5.6-sol":
            rebuilt.update(ROWS)
        rebuilt[key] = row
    data["models"] = rebuilt

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"added {', '.join(ROWS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
