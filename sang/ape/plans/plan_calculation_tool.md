# The calculation tool for the code writer (sonnet-runtime, 2026-10-20)

Part of `plan_code_yield_hardening.md` item 2 (the companion of running a draft's own cases). Folds into 2.6.5.

Problem: a generated rule's own cases (a context and the verdict it should give) are written by the model, and their expected
verdicts depend on arithmetic it does in its head (75% of 1,200,000, a DSCR from rent and payment). A wrong case is repaired by
sending expected-versus-got back, so mental arithmetic costs repair rounds and sometimes a wrong rule is "fixed" to match a wrong case.

Design (small, bounded, optional):
- `jazzx_sdk/tools/calculate.py`: `Calculator` over the DSL evaluator that already exists (`expressions.evaluate_over_namespace`,
  Decimal, no I/O, no field resolution beyond the inputs given). Bounded by named constants: expression length, number of inputs.
  Never raises into the model: a result is `ok` with a plain decimal string (no exponent), or an error text naming what is wrong
  (a parse error, a missing identifier, division by zero, a non-number input, a limit). A `CalculationLog` records every call, failed
  or not (expression, inputs, result), and `calculate_tool(log)` is the agents-SDK function tool `calculate(expression, inputs)`;
  inputs are a list of `{name, value}` because the SDK's strict tool schemas refuse a free-form object.
- Consumer: `PythonExtractor(calculator=CalculationLog | None)`. With one, the code-writing call gets the tool and a short
  paragraph telling the model to check the arithmetic of its cases with it; without, nothing changes. `PythonExtractor.from_template`
  builds the extractor for the three places that construct it today (`policy_extract_api` twice, `authoring_context`), reading the
  new `JtbdTemplate.calculate: bool = False`, so the tool is a pack's choice, off by default.
- Not built: an output validator that refuses a draft whose cases state a value with no matching tool call. A case's arithmetic is
  not machine-readable (the draft's cases carry contexts and verdicts, not formulas), so a validator would be a guess; the repair
  loop on the case run already catches what the tool misses. `ToolRequiredValueError` stays deferred: no consumer needs it.
- Tests: the calculator (value, inputs, the four errors, the two limits, no exponent notation, the log); the tool invoked the way
  the agents SDK invokes it; the extractor passes the tool and the paragraph only when enabled; `from_template` and the flag.
Effort: S-M, two commits (tool and its log; extractor wiring and flag).
