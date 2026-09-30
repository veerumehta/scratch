# Plan: the application turn store (the chat runtime page's §5, §6, §10 gaps)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: plan, 2026-09-30, on `v2.5.7`; approved to build. Closes what `plan_chat_runtime_coordinator.md`
left against jazzx-assistant's "Requirements on plato 2.5.6 for chat.py" page: §5 (the coordinator
takes only `commit` and `reconcile` hooks, no begin / fail / interrupt), §6 (`caller_managed`
folded into `none`; best-effort persistence always awaited), §10 (abandonment never records an
interruption).

## Design

`runs.ChatTurnStore`, a protocol, the application's records behind the coordinator:

```python
class ChatTurnStore(Protocol):
    async def begin(self, run, *, token) -> BeginResult: ...
    async def commit(self, run, chat_run, *, token) -> Any: ...        # marker
    async def fail(self, run, error, *, token) -> Any: ...             # marker
    async def interrupt(self, run, reason, *, token) -> Any: ...       # marker
    async def reconcile(self, run) -> ReconcileOutcome | tuple[ReconcileOutcome, Any]: ...
```

- `BeginResult(question=None, history=None, data=None, recorded="now" | "existing",
  terminal_required=True, marker=None, rejection: ChatError | None = None)`. The coordinator
  applies it to the turn the factory built: `question` becomes `turn.message`, `history`
  `turn.history` (the authoritative snapshot), `data` `turn.begun` (for `prepare` and every
  stage). A `rejection` fails the run with that error and writes nothing further.
- Order: factory (side-effect free) → `begin` → lifecycle → the terminal mutation for the outcome
  (`commit` for completed, `fail` for failed, `interrupt` for interrupted or abandoned), each at
  most once per execution, ordered against the terminal event by `DurabilityPolicy`, and only
  when `terminal_required`.
- `token` is the run's claim token (the fencing token an adapter can check).
- Every mutation, `begin` included, is protected: shielded from cancellation for
  `commit_grace_seconds`; past it (or cancelled out of it) the state is `indeterminate`, to
  `reconcile`; a `commit_before_delivery` turn whose commit is not confirmed fails. `reconcile`
  may return the resulting marker.
- `CoordinatedTurn.mutation` names the terminal mutation attempted (`begin` when begin itself did
  not settle); `commit_marker` is what it returned.
- `commit=` / `reconcile=` stay as the one-hook adapter (`HookTurnStore`): a store with commit
  and reconcile only, whose begin writes nothing and whose fail / interrupt are no-ops. Passing
  both a store and hooks is refused.
- §6: `caller_managed` is a `DurabilityPolicy` value: no store mutation at all, the `ChatRun` on
  the result for the caller to commit and deliver. (The journal is japes' run record, written
  under every policy.) `delivery_before_best_effort_persist` takes
  `follow_up="await" | "retain"`: `retain` hands the write to a task the coordinator holds,
  observes and settles in `close` (reported in its `SettleReport`), and the result resolves at
  the transfer.
- §10: `interrupt_on_abandon: bool = False`: an abandoned turn records `interrupt` only when set.

## Out of scope

Cross-replica fencing beyond passing the token (the adapter's, as the page says).
