"""Live smoke for the 2.6.9 model-layer changes: Gemini thinking through the native model, and the OpenAI tiers for a tuple and a oneOf schema.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Without ``--run`` this prints the worst-case cost and stops. With ``--run`` it makes the calls, but only if that worst case is within
``COST_CEILING_USD`` (the 1 USD the user typed). Spend is counted by a tap on each provider's own client, not by the code under test.
Keys come from the environment only (``GEMINI_API_KEY`` or ``GOOGLE_API_KEY``, ``OPENAI_API_KEY``); a missing one skips that part and says so.

Checks, each reported on its own:
1. Gemini 2.5 Flash, ``extra_args["thinking"]`` as a token budget: thought summaries stream as reasoning events, the answer holds none of them.
2. Gemini 3 Flash (preview), thinking level ``low``, a two-turn tool loop: whether the second turn is accepted with the
   ``thought_signature`` replayed (a 400 naming the signature means the replay did not work).
3. OpenAI, a ``tuple`` field and a discriminated union: the request goes out non-strict and the API accepts it, the answer validates.

    python scripts/local/smoke_gemini_thinking_and_schemas.py [--run]
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass, field
from typing import Annotated, Literal, Union

from agents import Agent, ModelSettings, Runner
from pydantic import BaseModel, Field

from jazzx_sdk.agents import function_tool_from_schema
from jazzx_sdk.agents.interactive.stream_hooks import reasoning_delta_text
from jazzx_sdk.agents.models import resolve_model
from jazzx_sdk.llm.cost import get_model_pricing

COST_CEILING_USD = 1.0
GEMINI_BUDGET_MODEL = "gemini-2.5-flash"
GEMINI_LEVEL_MODEL = "gemini-3-flash-preview"
OPENAI_MODEL = "gpt-5.4-nano"
THINKING_BUDGET_TOKENS = 1_024
#: Per-call bounds the worst case is computed from.
GEMINI_MAX_TOKENS = 3_000
GEMINI_MAX_TURNS = 4
OPENAI_MAX_TOKENS = 1_500
OPENAI_CALLS = 2
INPUT_TOKENS_BOUND = 3_000
PER_MILLION = 1_000_000
ADD_SCHEMA = {"type": "object", "properties": {"numbers": {"type": "array", "items": {"type": "integer"}}}, "required": ["numbers"]}
MATH_PROMPT = ("Three crates hold 14, 9 and 23 apples. Spoilage removes 2 apples from each crate, then half of what remains in total is "
               "sold. Work out the count per crate after spoilage, add them with the add tool, and say the total and how many were sold.")
INSTRUCTIONS = "Reason through the problem before acting. Use the add tool for every addition, then answer in two sentences."


class Pair(BaseModel):
    point: tuple[float, float]


class Cat(BaseModel):
    kind: Literal["cat"]
    lives: int


class Dog(BaseModel):
    kind: Literal["dog"]
    tricks: int


class Pet(BaseModel):
    pet: Annotated[Union[Cat, Dog], Field(discriminator="kind")]


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    price = get_model_pricing(model)
    return (input_tokens * price.input + output_tokens * price.output) / PER_MILLION


def worst_case_usd() -> float:
    gemini = sum(cost_usd(m, GEMINI_MAX_TURNS * INPUT_TOKENS_BOUND, GEMINI_MAX_TURNS * GEMINI_MAX_TOKENS)
                 for m in (GEMINI_BUDGET_MODEL, GEMINI_LEVEL_MODEL))
    return gemini + OPENAI_CALLS * cost_usd(OPENAI_MODEL, INPUT_TOKENS_BOUND, OPENAI_MAX_TOKENS)


@dataclass
class GeminiTap:
    """Tokens Gemini's own responses reported, summed around the client's calls (thoughts counted as output)."""

    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    errors: list[str] = field(default_factory=list)

    def watch(self, client) -> None:
        models = client.aio.models
        stream = models.generate_content_stream

        async def tapped(**request):
            self.requests += 1
            try:
                inner = await stream(**request)
            except Exception as error:
                self.errors.append(f"{type(error).__name__}: {error}")
                raise

            async def counted():
                try:
                    async for chunk in inner:
                        usage = getattr(chunk, "usage_metadata", None)
                        if usage is not None:
                            self._last = usage
                        yield chunk
                except Exception as error:
                    self.errors.append(f"{type(error).__name__}: {error}")
                    raise
                finally:
                    last = getattr(self, "_last", None)
                    if last is not None:
                        self.input_tokens += getattr(last, "prompt_token_count", 0) or 0
                        self.output_tokens += (getattr(last, "candidates_token_count", 0) or 0) + (getattr(last, "thoughts_token_count", 0) or 0)
                        self._last = None

            return counted()

        models.generate_content_stream = tapped


async def add(arguments: dict) -> str:
    return str(sum(arguments["numbers"]))


async def gemini_run(model_id: str, thinking, *, tools: bool) -> tuple[float, dict]:
    model, tap = resolve_model(model_id, max_attempts=1), GeminiTap()
    tap.watch(model._inner.provider.client)
    agent = Agent(
        name="smoke", instructions=INSTRUCTIONS, model=model,
        tools=[function_tool_from_schema("add", "Adds a list of integers.", ADD_SCHEMA, add)] if tools else [],
        model_settings=ModelSettings(max_tokens=GEMINI_MAX_TOKENS, extra_args={"thinking": thinking}))
    run = Runner.run_streamed(agent, MATH_PROMPT, max_turns=GEMINI_MAX_TURNS)
    thoughts: list[str] = []
    answer: list[str] = []
    calls, failure = 0, ""
    try:
        async for event in run.stream_events():
            text = reasoning_delta_text(event)
            if text:
                thoughts.append(text)
            data = getattr(event, "data", None)
            if getattr(data, "type", "") == "response.output_text.delta":
                answer.append(data.delta)
            if getattr(event, "type", "") == "run_item_stream_event" and getattr(event.item, "type", "") == "tool_call_item":
                calls += 1
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    cost = cost_usd(model_id, tap.input_tokens, tap.output_tokens)
    thought_text, answer_text = "".join(thoughts), "".join(answer)
    print(f"  final output: {run.final_output!r}; streamed answer characters {len(answer_text)}")
    answer_text = answer_text or str(run.final_output or "")
    leaked = bool(thought_text) and any(line and line in answer_text for line in thought_text.split("\n") if len(line) > 40)
    result = {"thought_chars": len(thought_text), "answer": answer_text.strip(), "calls": calls, "requests": tap.requests,
              "failure": failure, "errors": tap.errors, "leaked": leaked, "cost": cost,
              "tokens": (tap.input_tokens, tap.output_tokens)}
    print(f"{model_id} thinking={thinking!r} tools={tools}")
    print(f"  requests {tap.requests}, tool calls {calls}, thought characters streamed {len(thought_text)}, answer characters {len(answer_text)}")
    print(f"  thoughts leaked into the answer: {leaked}")
    print(f"  tokens in {tap.input_tokens}, out {tap.output_tokens}; cost {cost:.6f} USD" + (f"; failed: {failure}" if failure else ""))
    return cost, result


async def openai_schema(schema: type[BaseModel], prompt: str) -> tuple[float, bool]:
    from openai import AsyncOpenAI

    from jazzx_sdk.llm.providers.openai import OpenAIProvider
    from jazzx_sdk.llm.structured import openai_structured

    provider = OpenAIProvider(api_key=os.environ["OPENAI_API_KEY"])
    spec = openai_structured(schema)
    strict = spec.response_format.get("json_schema", {}).get("strict")
    totals = {"in": 0, "out": 0}
    create = provider.client.chat.completions.create

    async def tapped(**request):
        response = await create(**request)
        usage = getattr(response, "usage", None)
        totals["in"] += getattr(usage, "prompt_tokens", 0) or 0
        totals["out"] += getattr(usage, "completion_tokens", 0) or 0
        return response

    provider.client.chat.completions.create = tapped
    failure, parsed = "", None
    try:
        result = await provider.run(prompt=prompt, output_schema=schema, model=OPENAI_MODEL, max_tokens=OPENAI_MAX_TOKENS)
        parsed = result.parsed if hasattr(result, "parsed") else result.content
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    cost = cost_usd(OPENAI_MODEL, totals["in"], totals["out"])
    print(f"openai {OPENAI_MODEL} schema={schema.__name__}: request strict={strict}")
    print(f"  tokens in {totals['in']}, out {totals['out']}; cost {cost:.6f} USD; answer: {parsed!r}" + (f"; failed: {failure}" if failure else ""))
    ok = strict is False and not failure and parsed is not None and totals["out"] > 0
    del AsyncOpenAI
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
    total, passed = 0.0, True
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        os.environ.setdefault("GEMINI_API_KEY", gemini_key)
        cost, result = await gemini_run(GEMINI_BUDGET_MODEL, THINKING_BUDGET_TOKENS, tools=False)
        total += cost
        ok = (result["thought_chars"] > 0 and result["answer"] and not result["failure"] and not result["leaked"]
              and result["requests"] >= 1 and cost > 0)
        print("  budget thinking:", "PASS" if ok else "FAIL")
        passed = passed and bool(ok)
        cost, result = await gemini_run(GEMINI_LEVEL_MODEL, "low", tools=True)
        total += cost
        replay_refused = any("signature" in e.lower() for e in result["errors"] + [result["failure"]])
        print("  level thinking with a tool loop:", "accepted with the signature replayed" if result["calls"] and not result["failure"]
              else ("REFUSED: the API wants the thought_signature replayed" if replay_refused else f"did not complete ({result['failure'] or 'no tool call'})"))
    else:
        print("GEMINI_API_KEY / GOOGLE_API_KEY not set: Gemini checks skipped")
    if os.getenv("OPENAI_API_KEY"):
        for schema, prompt in ((Pair, "Give the point (1.5, 2.5)."), (Pet, "A cat with 9 lives.")):
            cost, ok = await openai_schema(schema, prompt)
            total += cost
            print(f"  {schema.__name__}:", "PASS" if ok else "FAIL")
            passed = passed and ok
    else:
        print("OPENAI_API_KEY not set: OpenAI checks skipped")
    print(f"actual cost {total:.6f} USD against a ceiling of {COST_CEILING_USD:.2f} USD")
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    sys.exit(asyncio.run(main(parser.parse_args().run)))
