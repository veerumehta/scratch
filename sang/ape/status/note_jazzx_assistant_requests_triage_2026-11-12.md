# jazzx-assistant requests on the chat pipeline: triage, 2026-11-12

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Source: the team's Notion page "japes-requests on v2.7.0 chat pipeline" (R1 to R32). Triage by opus-xrepo; checked against `japes-v27` (v2.7.2) for R1, R3, R6, R13, R16 and R18. Decides the 2.7.2 slice; the rest is queued here.

## Confirmed in the code

- R3: a skill's `reasoning_effort` rebuilds the sub-agent's model settings from the spec alone (`agents/interactive/agent.py` near line 1020) and drops the builder's `self._model_settings`. Which fields are lost (`verbosity`, `include_usage`) is not checked.
- R13: `SessionRegistry.drain` closes sessions one after another against one shared deadline (`runs/session.py` near line 308).
- R16: a degraded grounded source is not cached (`cacheable=not degraded`) and has no attempt cap, so it is fetched again each turn (`pipelines/grounding.py` near line 455).
- R1: an unparseable gate verdict always returns the fallback refusal (`agents/interactive/gate.py` near line 95).
- R6: `JazzXRuntime._build_server_app` forwards no `lifespan`, `readiness_provider` or `app_version`.
- R18: the kernel client timeout is the literal 120.0 (`clients/kernel_client.py` near line 127; a named constant or option is needed).

## 2.7.2 slice (user said yes, 2026-11-12), in order

1. Defects: R3, R13, R16.
2. Small general options: R1; R2 with R29 (strict step-error handler, declared errors logged at INFO, a stage-keyed code and message map); R6 (forward the three, add `configure_app`); R7 (strict Knowledge Hub client on the shared pool); R18 (timeout option); R19 (httpx transport errors are transient).
3. Security: R28 (do not persist identity headers on `TurnRun`, or a redact hook).
4. R22: a live tee, `on_event` on `ChatCoordinator`, called after each journaled event (the store wake-up covers the polling half).

The user is open to more in 2.7.2: next candidates, in order, R30 (agent per turn), R31 (compose turn context and artifacts), R32 (stage output on `on_step`, a public tracer protocol), R4, R5, R10 (blocking `subprocess.run` in async tools), R11, R15, R17.

## Not now

R23 to R27 (multi-pod coordinator: hard-cancel reasons, claim affinity, hooks for runs that never execute, replacement gating, commit fields): the team keeps its own coordinator; build when they commit to adopting it. R8, R9, R12, R14, R20, R21: small, queue.

## Reply to the team

Tell them: the slice above is in 2.7.2; the store wake-up is built and a follower no longer waits out a poll interval; `ChatTurnHandle.result()` can return before the best-effort commit finishes under `delivery_before_best_effort_persist` (wait on the commit, not on `result()`); R23 to R27 wait for their adoption decision.
