# Separating code from data: what actually belongs in a conf file

Status: assessment, 2026-09-11. Decides nothing. Written against japes `138cc90` on `v2.5.2`,
prompted by `pipelines/catalog.py`.

## The short answer

`pipelines/catalog.py`'s entries should not stay embedded in code, and they should not move to a
conf file either. Every field in them describes code shipped in the same package, so the honest
fix is to **derive** them rather than restate them somewhere else. A YAML file holding the same
hand-maintained mirror is the current problem moved further from the thing it mirrors.

The part that genuinely wants externalizing is different and smaller: **which pipelines exist**, so
a pack can contribute one without editing SDK source.

## The test I would apply to any registry

Three questions, in order. Only the second produces a conf file.

1. **Does it describe code shipped in this package?** Then derive it. A second copy drifts, and a
   second copy in another file format drifts unobserved.
2. **Does a deployment need to vary it?** Then it is configuration, and it belongs outside the
   distribution entirely (env, a mounted file, the pack).
3. **Does a pack need to extend it?** Then the registry must be *open* -- a `register_*` entry
   point -- which is a code change to the mechanism, not a data file.

"Code versus data" is the wrong axis. The useful axis is **who owns the value and who can check
it.**

## Why `pipelines/catalog.py` fails question 1 today

Six entries, each declaring `module`, `turn_type`, `entrypoint`, `steps`, `wraps`. Every one of
those is a fact about code in `jazzx_sdk/pipelines/`, restated by hand.

**Half the restatement is checked; the half that drifts is not.**
`tests/test_pipeline_catalog.py:62`, `test_registered_modules_are_actually_importable`, does the
real thing: it imports every `contract.module` and asserts `hasattr` for both `turn_type` and
`entrypoint`. So those three fields cannot silently rot, and any claim that the registry is wholly
unverified is wrong.

What that test does not touch is **`steps`** -- nothing anywhere compares a contract's step ids to
a pipeline the builder actually produces. That is the field with the ambiguity below, and it is the
one a reader is most likely to trust.

Three tests are also misleading rather than useful. `test_chat_contract_matches_its_real_module`
(and its `document_ingest` and `investigation_loop` siblings) read in full:

```python
contract = PIPELINE_REGISTRY["chat"]
assert contract.module == "jazzx_sdk.pipelines.chat"
assert contract.wraps == ["InteractiveAgent"]
assert contract.turn_type == "ChatTurn"
assert contract.entrypoint == "run_chat_turn"
```

They never import anything: the registry is asserted against literals restating the registry. They
would pass unchanged if `ChatTurn` were deleted. The importability test covers what they claim to,
so they are redundant as well as misnamed -- and a name like "matches its real module" on a body
that reads no module is the kind of thing that stops someone writing the check that is missing.

**And one field has an unstated meaning.** `steps` is documented as "step ids, in pipeline order",
but measured against the builders it is the *maximal* set, not what a default build produces:

| Pipeline | `steps` declares | `build_*()` default produces |
|---|---|---|
| `vocabulary_build` | + `decide`, `merge` | neither (`with_decide`/`with_merge` default False) |
| `policy_extract` | + `decide` | without it (`with_decide=False`) |
| `investigation_loop` | + `sentinel`, `persist` | neither (both flags default False) |

That is a defensible semantic -- "every step this pipeline can have" -- and it is nowhere written
down. A reader checking the catalog against a running pipeline finds a mismatch and cannot tell
whether it is a bug.

So one field is unverified and ambiguous, and three tests dress up a restatement as a check.
**Moving the entries to YAML fixes neither, and makes both harder to notice**: the mirror and the
thing mirrored would no longer sit in the same language, so no import, no type and no test
naturally spans them.

## What the derived version looks like

```python
@dataclass(frozen=True)
class PipelineContract:
    pipeline_id: str
    module: str
    description: str          # the one field a human must write
    wraps: tuple[str, ...]    # and this one: intent, not structure

    @property
    def turn_type(self) -> type: ...      # resolved from the module
    @property
    def entrypoint(self) -> Callable: ... # resolved from the module
    def steps(self, **flags) -> list[str]:
        """The step ids `build_*_pipeline(**flags)` actually produces."""
```

`description` and `wraps` stay declared, because they are editorial: what the pipeline is *for*,
and which primitive it is *about*, are not recoverable from the code. Everything else is looked up,
so it cannot be wrong. `steps` becomes a function of the flags, which also answers the
maximal-versus-default ambiguity by refusing to have a single answer.

The test then does what its name already claims: import the module, resolve each attribute, and
compare the built pipeline's step ids against the contract.

## Where a conf file does belong

**Question 3, not question 1.** Today `PIPELINE_REGISTRY` is a module-level dict a pack cannot add
to without patching the SDK. The codebase already solves this a dozen ways elsewhere --
`register_failure_rule`, `register_model_card`, `register_model_pricing`,
`register_compaction_strategy`, `register_connector_class`, `register_document_steps`,
`register_signal_tags`, `TemplateRegistry.register_dict`, `ToolRegistry.register_tool` -- but of
the five catalogs, only `connectors` and `channels` have one:

| Catalog | Lines | Extension point |
|---|---|---|
| `modes/catalog.py` | 246 | none |
| `connectors/catalog.py` | 176 | `register_connector_class` |
| `experts/catalog.py` | 164 | none |
| `platform_catalog.py` | 130 | none |
| `pipelines/catalog.py` | 127 | none |
| `channels/catalog.py` | 37 | has one |

So the pattern is established and the catalogs are the part that did not adopt it. A pack
declaring a pipeline in its own manifest -- which *is* a conf file, the pack's own -- and the SDK
reading it at load, is question 2 and question 3 answered together, and it puts the data where the
thing that varies lives rather than in a new SDK-side file.

## What I am not claiming

- **That the other four catalogs have the same defect.** I measured `pipelines`; the others were
  only counted. `modes/catalog.py` at 246 lines is the natural next one to check, since
  `pipelines/catalog.py`'s own docstring says it "mirrors `jazzx_sdk.modes.catalog`'s shape
  exactly" -- if the shape was copied, the unverified-mirror property may have been copied with it.
- **That literal-in-code is wrong in general.** `channels/catalog.py` is 37 lines of genuinely
  static facts with an extension point already. Nothing to fix.
- **That this is urgent.** No consumer is broken by it. It is a correctness-of-documentation
  problem and a closed-registry problem, not a runtime defect.

## Sequencing, if we do it

1. **Make the existing tests real.** Import the module, assert the attributes resolve, compare
   built steps against the contract. This finds any drift that exists today before anything moves.
2. **Derive the derivable fields**, leaving `description` and `wraps` declared.
3. **Open the registry**, so a pack can contribute a pipeline. Decide then whether the pack
   declares it in its manifest (data, pack-side) or through `register_pipeline` (code), which is a
   question about who writes pipelines, not about file formats.

Step 1 is worth doing even if 2 and 3 never happen, and it is small: `steps` is the only field
without a real check, and three redundant tests can go at the same time.
