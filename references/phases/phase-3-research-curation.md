---
phase_id: "3-curation"
covers: ["3", "3.5", "3.6"]
subagent_type: general-purpose
inputs_from_state: ["scope", "research_queries", "research_checklist", "nb_id"]
outputs_to_state: ["evidence_registry", "research_batches", "completed_phases", "next_phase"]
next_phase_on_success: "3.7"
estimated_runtime_minutes: 25-80
---

# Phase 3 / 3.5 / 3.6 — Research, Curation, Coverage

> **Subagent contract:** You are a fresh-context subagent. On entry:
> 1. Read workspace state at the path given in the dispatch prompt (`state.json`).
> 2. Execute every step in this file in order.
> 3. On exit, call `python3 $SKILL_ROOT/references/scripts/workspace.py mark-complete $WORKSPACE 3.6 3.7`.
> 4. Return a ≤200-word summary to the orchestrator: queries run, total sources found, sources after curation, node-coverage status.
> 5. Do **not** load other phase files. Do **not** attempt to run Phase 3.7.

---

## Phase 3 — Deep Research (Parallel Fan-Out)

> Query execution rules for each runner are in
> `$SKILL_ROOT/references/phases/phase-3-query-runner.md`.
> Each query angle runs in a dedicated sub-subagent with its own temp notebook,
> eliminating the `research status` race condition.

Source priority guidance by jurisdiction: load `$SKILL_ROOT/references/source-priority.md`.

### Stage 1 — Create temp notebooks (sequential, 5-second gap)

For each query in `RESEARCH_QUERIES`, create a dedicated temp notebook. The 5-second sleep
between creations avoids concurrent-creation API rate limits.

```bash
NB_TEMP_1=$(notebooklm create "research-temp-q1-$NB_ID" --json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id',''))")
sleep 5
NB_TEMP_2=$(notebooklm create "research-temp-q2-$NB_ID" --json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id',''))")
sleep 5
# Repeat for NB_TEMP_3, NB_TEMP_4, NB_TEMP_5 only if N ≥ 3 / 4 / 5
```

### Stage 2 — Dispatch query runners (parallel)

Dispatch ALL query sub-subagents simultaneously in a single Agent tool call. Each runner
loads `$SKILL_ROOT/references/phases/phase-3-query-runner.md` and receives:

```
SKILL_ROOT  = <absolute path to hybrid skill root>
WORKSPACE   = <absolute path to current workspace>
NB_ID       = <assigned temp notebook ID for this runner — NB_TEMP_N>
QUERY_ID    = <query_id from RESEARCH_QUERIES[N]>
QUERY_STRING = <verbatim query string from RESEARCH_QUERIES[N], in jurisdiction language>
NODES       = <nodes list from RESEARCH_QUERIES[N]>
JURISDICTION = <from state.json scope>
```

Wait for ALL sub-subagent summaries before proceeding to Stage 3.

### Stage 3 — Collect results + cleanup temp notebooks

After all runners return their source lists, delete the temp notebooks to avoid clutter:

```bash
notebooklm notebook delete "$NB_TEMP_1" -y
notebooklm notebook delete "$NB_TEMP_2" -y
# Repeat for all NB_TEMP_N
# If the delete command is unavailable, empty each notebook instead:
#   notebooklm source clean --yes -n "$NB_TEMP_N"
```

Hold the N source lists in memory as arrays (one per runner). Proceed to Phase 3.5 to merge
and curate. The curation logic in Phase 3.5 is unchanged — it receives N source arrays
instead of N sequential JSON files, but applies the same dedup and filtering rules.

---

## Phase 3.5 — Source Curation + Evidence Registry (Rhino)

This phase does two things: (1) applies notebooklm's curation rules to remove noise, and (2) builds a lightweight node-tagged Evidence Registry that replaces the raw JSON blobs in Claude's context going forward. This is the primary mechanism for preventing context rot.

### Step A — Deduplication and filtering

Execute the curation script to perform exact and fuzzy deduplication:

```bash
python3 "$SKILL_ROOT/references/scripts/curate_sources.py" /tmp/research_*_"$NB_ID".json > /tmp/curated_sources.json
```

### Step B — Build the Evidence Registry

For each surviving source, create one Evidence Registry entry using **only the title, URL, and the query batch it came from** (Claude cannot read source content at this stage — that content lives inside NotebookLM). The node tag is assigned based on which query produced the source, using the `RESEARCH_QUERIES` → node mapping from Phase 1.

**Evidence Registry entry format:**
```
| # | Title | URL | Tier | Node(s) | Batch | Pub. Date | Enforcement Date |
```

Tier is assigned from the URL domain:
- Tier 1 (Primary): `.gov`, `.edu` official court/legislative domains, official gazette domains
- Tier 2 (Academic): law review / university repository / SSRN / HeinOnline domains
- Tier 3 (Specialized): law firm, bar association, legal news domains

The `Pub. Date` and `Enforcement Date` columns are left as `?` at this stage — they will be populated after Phase 4.5 when NotebookLM returns the Source Overview note. For Tier 1 sources (statutes, regulations, cases), both columns must be filled before Phase 5.6. For Tier 2 and Tier 3 sources, only `Pub. Date` is required.

**Present the Evidence Registry** as a compact table. This table now replaces all raw JSON blobs in context — release `/tmp/research_[i]_$NB_ID.json` content from working memory.

Example (dates filled after Phase 4.5):
```
| #  | Title                             | URL                  | Tier | Node(s) | Batch | Pub. Date  | Enforcement Date |
|----|-----------------------------------|----------------------|------|---------|-------|------------|-----------------|
| 1  | Ley 20.744 — Régimen de Contrato  | infoleg.gob.ar/...   | T1   | 2       | Q1    | 1976-05-13 | 1976-05-13      |
| 2  | CSJN — Vizzoti c/ AMSA            | csjn.gov.ar/...      | T1   | 1       | Q1    | 2004-09-14 | 2004-09-14      |
| 3  | Doctrina del despido — RDLSS      | dialnet.unirioja.es/ | T2   | 3       | Q2    | 2019-03-01 | —               |
```

Immediately proceed to Phase 3.6 — do not pause for user input. Notify:

> "Found [N_total] sources across [N] queries. After curation and deduplication, [N_curated] sources in the Evidence Registry. Proceeding to node satisfaction check."

---

## Phase 3.6 — Node Satisfaction Check

Before importing anything, verify the Evidence Registry provides adequate coverage for each checklist node. This is the gap-detection step that Rhino adds — finding thin coverage now, while there is still time to fix it.

For each node in `RESEARCH_CHECKLIST`:
1. Count how many Evidence Registry entries are tagged to that node.
2. Check whether the count meets the node's acceptance criterion.

**If any node has zero sources tagged to it**, run one targeted supplemental search before proceeding:

```bash
notebooklm source add-research "[targeted query for the gap — in jurisdiction language]" --mode deep -n "$NB_ID"
notebooklm research status --json -n "$NB_ID" > /tmp/research_gap_$NB_ID.json
```

Apply Phase 3.5 curation rules to the gap batch and add surviving sources to the Evidence Registry with the appropriate node tag.

**If a node has sources but they are thin** (e.g., only 1 Tier 3 source for a node that needs primary authority), flag it with a `⚠ Thin` marker in the Evidence Registry but proceed — the Verification note in Phase 5 will surface this as a research gap.

Present the updated Evidence Registry with node coverage summary:

```
Node coverage:
  Node 1 [Primary authority]: 3 sources (T1: 2, T2: 1) ✓
  Node 2 [Statutory framework]: 2 sources (T1: 2) ✓
  Node 3 [Doctrine/academic]: 2 sources (T2: 2) ✓
  Node 4 [Recent developments]: 1 source (T3: 1) ⚠ Thin
```

### Autonomous state write (replaces Checkpoint 1 halt)

Build the evidence-registry JSON (one row per surviving source with fields `id`, `title`, `url`, `tier`, `nodes`, `batch`, `pub_date`, `enforce_date`, `import_status: "pending"`, `queryable_status: "pending"`) and write it to `$WORKSPACE/evidence_registry.json`.

Then persist to `state.json` and advance:

```bash
python3 "$SKILL_ROOT/references/scripts/workspace.py" update "$WORKSPACE" \
  --set evidence_registry="$(cat $WORKSPACE/evidence_registry.json)"
python3 "$SKILL_ROOT/references/scripts/workspace.py" mark-complete "$WORKSPACE" 3.6 3.7
```

No user pause. The orchestrator dispatches Subagent B (Phase 3.7) automatically.
