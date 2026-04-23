---
phase_id: "3-query-runner"
covers: ["3"]
subagent_type: general-purpose
inputs_from_dispatcher: ["query_string", "query_id", "nodes", "nb_id", "jurisdiction", "skill_root"]
outputs_to_dispatcher: ["query_id", "nodes", "sources"]
estimated_runtime_minutes: 10-20
---

# Phase 3 Query Runner — Single Angle Research

> **Sub-subagent contract:** You are a query runner dispatched by Subagent A for Phase 3.
> `$NB_ID` in this file refers to the **temp notebook** assigned to you by Subagent A —
> NOT the main research notebook. Your job:
> 1. Run the single research query block matching your assigned `$QUERY_ID` on `$NB_ID`.
> 2. Capture `research status` immediately (see rule below).
> 3. Return the source list tagged with `query_id` and `nodes` to Subagent A.
> 4. Do NOT delete `$NB_ID` — Subagent A handles cleanup after all runners return.
> 5. Do NOT proceed to Phase 3.5 — that is Subagent A's responsibility after merging
>    all runner results.

---

## Phase 3 — Deep Research (Node-Anchored)

Run the N queries confirmed in Phase 1, using the exact strings recorded in `RESEARCH_QUERIES`. Write all query strings in the **jurisdiction's primary language** — not in report language. Anchor every query with the full country name in that language (e.g., `"Argentina contrato de trabajo indemnización por despido"`, `"Brasil direito tributário ICMS"`). Deep-research results are not geographically filtered — omitting the country name reliably pulls in sources from neighbouring jurisdictions.

Source priority guidance by jurisdiction: load `$SKILL_ROOT/references/source-priority.md`.

Capture `research status` immediately after each query completes, before starting the next. This is critical: `research status` only reflects the most recently completed session.

Execute only the block matching your assigned `$QUERY_ID`:

```bash
# Query 1 — [angle from RESEARCH_QUERIES[1]] → Node(s): [n]
notebooklm source add-research "[query 1 string — in jurisdiction language]" --mode deep -n "$NB_ID"
notebooklm research status --json -n "$NB_ID" > /tmp/research_1_$NB_ID.json

# Query 2 — [angle from RESEARCH_QUERIES[2]] → Node(s): [n]
notebooklm source add-research "[query 2 string — in jurisdiction language]" --mode deep -n "$NB_ID"
notebooklm research status --json -n "$NB_ID" > /tmp/research_2_$NB_ID.json

# Query 3 — [angle from RESEARCH_QUERIES[3]] → Node(s): [n]
notebooklm source add-research "[query 3 string — in jurisdiction language]" --mode deep -n "$NB_ID"
notebooklm research status --json -n "$NB_ID" > /tmp/research_3_$NB_ID.json

# Query 4 — only if N ≥ 4
notebooklm source add-research "[query 4 string — in jurisdiction language]" --mode deep -n "$NB_ID"
notebooklm research status --json -n "$NB_ID" > /tmp/research_4_$NB_ID.json

# Query 5 — only if N = 5
notebooklm source add-research "[query 5 string — in jurisdiction language]" --mode deep -n "$NB_ID"
notebooklm research status --json -n "$NB_ID" > /tmp/research_5_$NB_ID.json
```

Sources are discovered but not yet imported. Proceed to Phase 3.5.

## Return to Subagent A

Read `/tmp/research_$QUERY_ID_$NB_ID.json` (the status file written by the block you ran).
Extract `tasks[*].sources[*]`. Return to Subagent A in your ≤200-word summary:

```json
{
  "query_id": "<QUERY_ID>",
  "nodes": [<NODES>],
  "sources": [ ... ]
}
```
