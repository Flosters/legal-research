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
> 3. On exit, call `python3 $SKILL_ROOT/references/scripts/workspace.py mark-complete $WORKSPACE 3.6 4`.
> 4. Return a ≤200-word summary to the orchestrator: queries run, total sources found, sources after curation, node-coverage status.
> 5. Do **not** load other phase files. Do **not** attempt to run Phase 3.7.
>
> **ABORT RULE — read this before executing any step:**
> - You are allowed to run ONLY commands listed explicitly in this file.
> - **FORBIDDEN:** `notebooklm source add-research ... -n "$NB_ID"` — never call `add-research` against the main notebook ID (`$NB_ID`) in Phase 3. The main notebook must remain empty until Phase 4. The ONLY permitted way to run research queries — including gap searches — is `python3 "$SKILL_ROOT/references/scripts/run_research.py"`. Violating this will silently corrupt the notebook with hundreds of uncurated duplicates.
> - If `run_research.py` exits non-zero, return `error: run_research.py failed: <stderr>` immediately. Do NOT check for files. Do NOT run `notebooklm` commands manually. Do NOT try to poll, retry, or diagnose.
> - NEVER copy from `.claude/projects/*/tool-results/` paths — those files are ephemeral session internals.
> - NEVER run `nslookup`, `curl`, `for`, `until`, `case`, `sleep`, or `cp` directly. All multi-step logic must go through the provided Python scripts.
> - If any script exits non-zero: return `error: <script name> failed` to the orchestrator and stop.

---

## Phase 3 — Deep Research

Source priority guidance by jurisdiction: load `$SKILL_ROOT/references/source-priority.md`.

### Stage 1 — Execute Research Queries

**YOUR FIRST ACTION:** Run this command immediately. Do not analyze, plan, or summarise first.

```bash
python3 "$SKILL_ROOT/references/scripts/run_research.py" "$WORKSPACE"
```

This script handles temp notebook creation, query execution, and polling automatically (up to 40 minutes). Wait for it to exit before proceeding.

Once the script completes, the results for all queries will be saved in `/tmp/research_q*_$NB_ID.json`. Hold these results in memory and proceed to Phase 3.5 to merge and curate.
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

**If any node has zero sources tagged to it**, run one targeted supplemental search before proceeding.
**BASH RESTRICTION: never use bash array syntax (`arr=(...)`, `${arr[@]}`).  Use Python for any multi-item iteration.**

```bash
python3 "$SKILL_ROOT/references/scripts/run_research.py" \
  --gap-query "[targeted query for the gap — in jurisdiction language]" \
  --nb-id "$NB_ID" \
  --out "/tmp/research_gap_$NB_ID.json"
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

### Checkpoint 1 — Node Satisfaction & Curation Halt

Build the evidence-registry JSON (one row per surviving source with fields `id`, `title`, `url`, `tier`, `nodes`, `batch`, `pub_date`, `enforce_date`, `import_status: "pending"`, `queryable_status: "pending"`) and write it to `$WORKSPACE/evidence_registry.json`.

STOP. Write state only — do not begin Phase 4. Return immediately to the orchestrator:

```bash
python3 "$SKILL_ROOT/references/scripts/workspace.py" mark-complete "$WORKSPACE" 3.6 4
```
