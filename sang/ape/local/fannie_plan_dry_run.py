"""Plan batches and writer sections of a chunk-file guide, counts only: no model call, nothing spent.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    python fannie_plan_dry_run.py <root> [--only "Chapter B3"]
"""

from __future__ import annotations

import argparse
import statistics

from jazzx_sdk.pipelines.policy.extract import DEFAULT_MAX_UNIT_CHARS
from jazzx_sdk.pipelines.policy.jtbd import SectionSegmenter
from jazzx_sdk.pipelines.policy.plan_limits import (PLAN_MAX_INPUT_TOKENS, WRITE_SECTION_MAX_TOKENS, PlanTooLarge, estimate_tokens,
                                                    split_by_tokens)
from jazzx_sdk.pipelines.policy.structured_corpus import StructuredCorpus, plan_batches, read_structured_corpus


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--only", help="keep the chapters whose name starts with this (e.g. 'Chapter B3')")
    args = parser.parse_args()
    corpus = read_structured_corpus(args.root)
    if args.only:
        corpus = StructuredCorpus(chapters=[c for c in corpus.chapters if c.name.startswith(args.only)],
                                  edition=corpus.edition, source=corpus.source)
    topics = [t for c in corpus.chapters for t in c.topics]
    print(f"edition {corpus.edition!r}, source {corpus.source!r}: {len(corpus.chapters)} chapters, {len(topics)} topics, "
          f"{sum(t.tokens for t in topics) / 1000:.0f}k tokens (topic median {statistics.median(t.tokens for t in topics):.0f}, "
          f"max {max(t.tokens for t in topics)})")
    try:
        batches = plan_batches(corpus, max_tokens=PLAN_MAX_INPUT_TOKENS, prompt_tokens=2_000)
    except PlanTooLarge as exc:
        print("PLAN BATCHING REFUSED:", exc)
        return
    sizes = [b.tokens for b in batches]
    print(f"plan calls (cap {PLAN_MAX_INPUT_TOKENS} tokens less 2000 for the prompt): {len(batches)} batches, tokens per batch "
          f"min {min(sizes)}, median {statistics.median(sizes):.0f}, max {max(sizes)}; chapters per batch "
          f"{statistics.median(len(b.chapters) for b in batches):.0f} median")
    segmenter = SectionSegmenter(None)
    sections, per_chapter, unit_total = [], [], 0
    for chapter in corpus.chapters:
        units = list(segmenter.units(corpus.documents(chapter.topics)).values())
        unit_total += len(units)
        try:
            pieces = split_by_tokens(units, lambda u: estimate_tokens(u.text), WRITE_SECTION_MAX_TOKENS,
                                     what=lambda u: f"unit {u.citation!r}")
        except PlanTooLarge as exc:
            print("WRITER SPLIT REFUSED:", exc)
            return
        sections += pieces
        per_chapter.append((chapter.name, len(pieces)))
    stokens = [sum(estimate_tokens(u.text) for u in s) for s in sections]
    print(f"units (the segmenter's: headings, clause markers, then at most {DEFAULT_MAX_UNIT_CHARS} characters): {unit_total}")
    print(f"writer sections (cap {WRITE_SECTION_MAX_TOKENS} tokens): {len(sections)}, tokens per section min {min(stokens)}, "
          f"median {statistics.median(stokens):.0f}, max {max(stokens)}; units per section median "
          f"{statistics.median(len(s) for s in sections):.0f}")
    print("sections per chapter, largest:", sorted(per_chapter, key=lambda r: -r[1])[:5])


if __name__ == "__main__":
    main()
