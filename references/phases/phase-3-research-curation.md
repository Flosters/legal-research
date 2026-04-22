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

## Phase 3 — Deep Research (Node-Anchored)

Run the N queries confirmed in Phase 1, using the exact strings recorded in `RESEARCH_QUERIES`. Write all query strings in the **jurisdiction's primary language** — not in report language. Anchor every query with the full country name in that language (e.g., `"Argentina contrato de trabajo indemnización por despido"`, `"Brasil direito tributário ICMS"`). Deep-research results are not geographically filtered — omitting the country name reliably pulls in sources from neighbouring jurisdictions.

Source priority guidance by jurisdiction: load `$SKILL_ROOT/references/source-priority.md`.

Capture `research status` immediately after each query completes, before starting the next. This is critical: `research status` only reflects the most recently completed session.

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

---

## Phase 3.5 — Source Curation + Evidence Registry (Rhino)

This phase does two things: (1) applies notebooklm's curation rules to remove noise, and (2) builds a lightweight node-tagged Evidence Registry that replaces the raw JSON blobs in Claude's context going forward. This is the primary mechanism for preventing context rot.

### Step A — Deduplication and filtering (per batch, then cross-batch)

Load each `/tmp/research_[i]_$NB_ID.json`. Each file has structure `{ "tasks": [ { "query": "...", "sources": [...] } ] }`. Extract `tasks[*].sources[*]` from each file.

Apply these rules per batch first, then cross-batch:

1. **Drop report-only entries** — remove any source where `result_type == 5` and `url` is empty or absent.
2. **Drop missing URLs** — remove any source with no `url` field or empty `url`.
3. **Exact-title deduplication** — group sources with identical titles (case-insensitive). Keep the highest-quality domain: `.gov` / `.edu` / official court domains > `.org` > `.com` > law-firm domains. If tied, keep first occurrence.
4. **Near-duplicate title deduplication** — group sources whose titles share ≥80% of word tokens OR where one title is a substring of the other (after stripping punctuation). Apply same domain-quality tie-breaking.
5. **Wrong-jurisdiction filter** — drop any source whose URL's hostname ends with a ccTLD belonging to a different country than the target jurisdiction, or whose title contains an explicit foreign-country keyword. **Use netloc-based suffix matching** — never a substring check on the raw URL string.

   ```bash
   # Wrong-jurisdiction filter — load reference script and run
   SOURCES_JSON=$(echo "$SOURCES_JSON" | python3 \
     $SKILL_ROOT/references/scripts/jurisdiction-filter.py \
     "$JURISDICTION")
   ```

   `$JURISDICTION` must match a key in `JURISDICTION_TLDS` inside `$SKILL_ROOT/references/scripts/jurisdiction-filter.py` (e.g. `"Argentina"`). To add a new jurisdiction, edit that file.

After per-batch deduplication, merge all batches and apply rules 3–4 again cross-batch.

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
