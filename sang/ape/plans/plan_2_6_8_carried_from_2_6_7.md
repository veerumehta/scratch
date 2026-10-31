# Plan: what 2.6.8 carries from 2.6.7 (sonnet-runtime, 2026-10-30)

The list of work deliberately left out of 2.6.7, each with what is known. Nothing here is started. Order is by what blocks a consumer first.

1. **Provenance index and resolver.** The guide's topic index (id, title, date, byte offsets, slice sha) stored beside a guideline file, a per-file edition and
   published date that survives a new version of the set, and a resolver that reads a `SourceRef`'s slice and checks its digest. Storage needs nothing new
   (guideline sets, `fabric.blob`); `SourceRef` already carries topic id, edition and byte span. Plan: `plan_source_documents_as_blob_content`. jaci builds the index
   as data beside its mapping file in the meantime.
2. **Job lint gates from the workbench survey.** K3 maintainer note (warn), K4 invisible characters (warn, beside `tidy_text`), K7 a mnemonic inside an ownership
   disclaimer adds no dependency edge, K9 a placeholder like N/A in `calculation_context` counts as empty, K10 the ontology-miss message lists sibling fields.
   Measure-first, built only if they fire on a real set: K8 a job repeats itself, K11 a vague qualifier, P1 the writer line against "see another section". K1, K2, K5, K6
   are not carried: they ship only if a real set shows them. Each runs the skeptic questions before it is built.
3. **The case and subject words beyond the metrics key.** The remaining `loan_*` docstring examples (renamed as their files are touched), and the persisted or wire
   names kept in 2.6.x: the `loan:<id>` graph IRI prefix (to be made configurable), the page-identity `loan_number` kind, the rag collection name. Plan:
   `plan_case_and_subject_words`.
4. **The coverage page's filter.** A server-side filter parameter on the coverage routes (by status, by job), now that rows page by `job_limit` and `clause_limit`; the page
   filters in the browser today.
5. **A per-link API field**, only if the Solution page needs link detail: the `check_links` rows live in job metadata and no route serves them.
6. **Pack-provided helpers.** A pack's own helper functions for its rules: the rule executor offers none today (rules call the rules library only). A question for the
   user, not a build.
7. **Deferred rules-library helpers** from sonnet-packs' survey: `latest` and `explains`. A change to the library bumps its patch version (1.1.3), per the user's ruling.
8. **Review notes not yet taken**, from `scripts/local/.reviews/accepted.md` and the `TODO(slug)` markers in the tree: read them at the start of the round.
9. **Cross-reference heading read as a topic** (`jazzx_sdk/pipelines/policy/markdown_guide.py`, `read_markdown_guide`): in the June 2026 Selling Guide the heading `### B2-1.5-02, Loan Eligibility.` (line 33378) is the sentence `See B2-1.5-02, Loan Eligibility.` (line 9223) set as a heading after a page break, so the reader yields a second topic `B2-1.5-02 (2)` (389 topics) and splits B6-1-01's content. Rule to build: a heading whose id repeats an earlier topic id and whose text matches a `See <id>, <title>.` sentence elsewhere continues the previous topic (388 topics, B6-1-01 whole). Changes unit ids: state the effect on the Pulte pack's 389-unit coverage and links (jaci regenerates). Raised by opus-xrepo from the jaci review.

Not carried: anything needing a provider call (the writer's measuring run on a real guide, adoption of generated jobs) waits for the user's own typed approval of a figure.
