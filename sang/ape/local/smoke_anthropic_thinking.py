"""Live smoke for the native Claude path: thinking in each shape, a two-turn tool loop with streaming, and a large non-streaming call.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Requests and tokens are counted by a tap on the Anthropic client itself, not by the code under test, so the report does not depend on
what `AnthropicNativeModel` hands the runner. Without ``--run`` this prints the worst-case cost and stops. With ``--run`` it makes the
calls, but only if that worst case is within ``COST_CEILING_USD``, and prints per shape: whether thinking text streamed, whether
turn two carried the signed block back, whether a 400 came back, and what it cost. A run that reads zero requests or zero cost after a
call that returned fails, because that means the instrumentation is wrong. Needs ``ANTHROPIC_API_KEY``, read from the environment or
else from ``.env.dev-daily``. Run from a japes checkout:

    python scripts/local/smoke_anthropic_thinking.py [--run]
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass, field

from agents import Agent, ModelSettings, Runner

from jazzx_sdk.agents import function_tool_from_schema
from jazzx_sdk.agents.anthropic_native import NONSTREAMING_MAX_TOKENS, AnthropicNativeModel
from jazzx_sdk.agents.interactive.stream_hooks import reasoning_delta_text
from jazzx_sdk.agents.models import resolve_model
from jazzx_sdk.llm.cost import get_model_pricing

LARGE_CALL_MODEL = "claude-haiku-5-5"
#: One model per thinking shape its card carries: adaptive, and an enabled budget.
ADAPTIVE_MODEL = "claude-haiku-5-5"
BUDGET_MODEL = "claude-haiku-4.5"
THINKING_BUDGET_TOKENS = 1_024
SHAPES = (
    (ADAPTIVE_MODEL, {"type": "adaptive", "display": "summarized"}),
    (BUDGET_MODEL, {"type": "enabled", "budget_tokens": THINKING_BUDGET_TOKENS, "display": "summarized"}),
)
COST_CEILING_USD = 2.0
#: Per-call bounds the worst case is computed from.
AGENT_MAX_TOKENS = 4_000
AGENT_MAX_TURNS = 4
LARGE_MAX_TOKENS = NONSTREAMING_MAX_TOKENS + 1_000
INPUT_TOKENS_BOUND = 3_000
PER_MILLION = 1_000_000
ENV_FILE = ".env.dev-daily"
ADD_SCHEMA = {"type": "object", "properties": {"numbers": {"type": "array", "items": {"type": "integer"}}}, "required": ["numbers"]}
INSTRUCTIONS = "Reason through the problem before acting. Use the add tool for every addition, then answer in two sentences."
#: Several dependent steps before the tool call, so the model has reason to think.
PROMPT = ("Three crates hold 14, 9 and 23 apples. Spoilage removes 2 apples from each crate, then half of what remains in total is "
          "sold. Work out the count per crate after spoilage, add them with the tool, and tell me the total before the sale and how "
          "many were sold.")


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    price = get_model_pricing(model)
    return (input_tokens * price.input + output_tokens * price.output) / PER_MILLION


def worst_case_usd() -> float:
    loop = sum(cost_usd(model, AGENT_MAX_TURNS * INPUT_TOKENS_BOUND, AGENT_MAX_TURNS * AGENT_MAX_TOKENS) for model, _ in SHAPES)
    return loop + cost_usd(LARGE_CALL_MODEL, INPUT_TOKENS_BOUND, LARGE_MAX_TOKENS)


@dataclass
class Tap:
    """What the client was asked and what it reported, counted around its own calls."""

    requests: list[dict] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    errors: list[str] = field(default_factory=list)

    def watch(self, client) -> None:
        messages = client.messages
        create, stream = messages.create, messages.stream

        async def tapped_create(**request):
            self.requests.append(request)
            try:
                result = await create(**request)
            except Exception as error:
                self.errors.append(f"{type(error).__name__}: {error}")
                raise
            return self._tapped(result) if request.get("stream") else self._counted(result)

        def tapped_stream(**request):
            self.requests.append(request)
            return _TappedManager(stream(**request), self)

        messages.create, messages.stream = tapped_create, tapped_stream

    def _counted(self, message):
        usage = getattr(message, "usage", None)
        self.input_tokens += _all_input(usage)
        self.output_tokens += getattr(usage, "output_tokens", 0) or 0
        return message

    async def _tapped(self, events):
        async for event in events:
            kind = getattr(event, "type", "")
            if kind == "message_start":
                self.input_tokens += _all_input(getattr(event.message, "usage", None))
            elif kind == "message_delta":
                self.output_tokens += getattr(getattr(event, "usage", None), "output_tokens", 0) or 0
            yield event

    def cost(self, model: str) -> float:
        return cost_usd(model, self.input_tokens, self.output_tokens)


class _TappedManager:
    """A `messages.stream` context manager whose final message is counted."""

    def __init__(self, manager, tap: Tap) -> None:
        self._manager, self._tap = manager, tap

    async def __aenter__(self):
        stream = await self._manager.__aenter__()
        final = stream.get_final_message

        async def counted():
            return self._tap._counted(await final())

        stream.get_final_message = counted
        return stream

    async def __aexit__(self, *exc):
        return await self._manager.__aexit__(*exc)


def _all_input(usage) -> int:
    return sum(getattr(usage, name, 0) or 0 for name in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))


def _signed_thinking_ahead_of_tool_use(request: dict) -> bool:
    """True when the assistant turn holding a tool_use opens with a signed thinking block; consecutive assistant messages are one turn."""
    turns: list[list[dict]] = []
    previous = None
    for message in request.get("messages", []):
        content = message.get("content")
        blocks = content if isinstance(content, list) else [{"type": "text", "text": content}]
        if message.get("role") == "assistant" and previous == "assistant":
            turns[-1].extend(blocks)
        elif message.get("role") == "assistant":
            turns.append(list(blocks))
        previous = message.get("role")
    for blocks in turns:
        kinds = [block.get("type") for block in blocks]
        if "tool_use" in kinds:
            return kinds[0] == "thinking" and bool(blocks[0].get("signature"))
    return False


async def add(arguments: dict) -> str:
    return str(sum(arguments["numbers"]))


async def tool_loop(model_id: str, thinking: dict) -> tuple[float, bool]:
    model, tap = resolve_model(model_id, max_attempts=1), Tap()
    tap.watch(model._inner.provider.client)
    agent = Agent(
        name="smoke", instructions=INSTRUCTIONS, model=model,
        tools=[function_tool_from_schema("add", "Adds a list of integers.", ADD_SCHEMA, add)],
        model_settings=ModelSettings(max_tokens=AGENT_MAX_TOKENS, extra_args={"thinking": thinking}))
    run = Runner.run_streamed(agent, PROMPT, max_turns=AGENT_MAX_TURNS)
    thoughts, calls, failure = [], 0, ""
    try:
        async for event in run.stream_events():
            text = reasoning_delta_text(event)
            if text:
                thoughts.append(text)
            if getattr(event, "type", "") == "run_item_stream_event" and getattr(event.item, "type", "") == "tool_call_item":
                calls += 1
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    carried = len(tap.requests) >= 2 and _signed_thinking_ahead_of_tool_use(tap.requests[1])
    bad_request = any("400" in error or "BadRequest" in error for error in tap.errors)
    cost = tap.cost(model_id)
    print(f"{model_id} thinking={thinking['type']}")
    print(f"  requests {len(tap.requests)}, tool calls {calls}, thinking characters streamed {len(''.join(thoughts))}")
    print(f"  turn two carried the signed thinking block ahead of the tool call: {carried}")
    print(f"  a 400 came back: {bad_request}" + (f" ({tap.errors[0]})" if tap.errors else ""))
    print(f"  tokens in {tap.input_tokens}, out {tap.output_tokens}; cost {cost:.6f} USD; "
          f"runner counted {run.context_wrapper.usage.requests} requests, {run.context_wrapper.usage.output_tokens} output tokens")
    print(f"  answer: {run.final_output!r}" + (f"; failed: {failure}" if failure else ""))
    instrumented = bool(tap.requests) and cost > 0
    if not instrumented:
        print("  FAIL: the tap read zero requests or zero cost after a call, so the instrumentation is wrong")
    runner_agrees = run.context_wrapper.usage.requests == len(tap.requests) and run.context_wrapper.usage.output_tokens == tap.output_tokens
    if instrumented and not runner_agrees:
        print("  FAIL: the usage the runner holds differs from what the client reported")
    ok = instrumented and runner_agrees and not failure and not bad_request and calls >= 1 and len(tap.requests) >= 2 and carried
    return cost, ok


async def large_non_streaming() -> tuple[float, bool]:
    model, tap = AnthropicNativeModel(LARGE_CALL_MODEL), Tap()
    tap.watch(model.provider.client)
    response = await model.get_response("Reply with one word.", "Say ready.", ModelSettings(max_tokens=LARGE_MAX_TOKENS), [], None, [], None)
    cost = tap.cost(LARGE_CALL_MODEL)
    print(f"large call at max_tokens={LARGE_MAX_TOKENS} through the stream: {response.output[0].content[0].text!r}; "
          f"requests {len(tap.requests)}, tokens in {tap.input_tokens}, out {tap.output_tokens}; cost {cost:.6f} USD; "
          f"response usage in {response.usage.input_tokens}, out {response.usage.output_tokens}")
    ok = bool(tap.requests) and cost > 0 and response.usage.output_tokens > 0
    if not ok:
        print("  FAIL: zero requests, cost or response usage after a call that returned")
    return cost, ok


async def main(run: bool) -> int:
    worst = worst_case_usd()
    print(f"worst-case cost {worst:.6f} USD against a ceiling of {COST_CEILING_USD:.2f} USD")
    if worst > COST_CEILING_USD:
        print("refusing: the worst case is over the ceiling")
        return 2
    if not run:
        print("dry run: pass --run to make the calls")
        return 0
    if not os.getenv("ANTHROPIC_API_KEY"):
        from dotenv import load_dotenv

        load_dotenv(ENV_FILE)
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set")
        return 2
    total, passed = 0.0, True
    for model_id, thinking in SHAPES:
        cost, ok = await tool_loop(model_id, thinking)
        total, passed = total + cost, passed and ok
    cost, ok = await large_non_streaming()
    total, passed = total + cost, passed and ok
    print(f"actual cost {total:.6f} USD against a ceiling of {COST_CEILING_USD:.2f} USD")
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    sys.exit(asyncio.run(main(parser.parse_args().run)))
