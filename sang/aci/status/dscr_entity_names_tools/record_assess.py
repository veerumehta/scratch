"""pytest plugin: record every in-process DSCR assessment (input record -> answer) to $ASSESS_LOG."""
import json, os
import jazzx_sdk.pack.assessment as mod

_orig = mod.assess
_log = open(os.environ["ASSESS_LOG"], "w")


async def assess(pack, record, *a, **kw):
    answer = await _orig(pack, record, *a, **kw)
    if getattr(pack, "pack_id", "") == "acra-dscr-policy":
        _log.write(json.dumps({"record": record, "answer": answer.model_dump(mode="json")}, default=str) + "\n")
        _log.flush()
    return answer


mod.assess = assess
