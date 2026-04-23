---
phase_id: "4-indexing"
covers: ["4","4.1","4.5"]
subagent_type: general-purpose
inputs_from_state: ["evidence_registry","nb_id","scope"]
outputs_to_state: ["evidence_registry","imports","source_overview_note_id","completed_phases","next_phase"]
next_phase_on_success: "5"
estimated_runtime_minutes: 15-40
---

# Phase 4 + 4.1 + 4.5 — Import, Queryability Spot-Check, Source Overview

> **Subagent contract:** import Evidence Registry URLs via batch-import.py; run the
> queryability spot-check for every T1 source (including article-level probes
> for long statutes and the two-part court-decision check); run the Source
> Overview prompt for date enrichment; update `evidence_registry[*].import_status`,
> `queryable_status`, `pub_date`, `enforce_date` in state.json;
> set next_phase=5; return ≤200-word summary. Replace the original Checkpoint 2
> halt with an autonomous state write.

## Phase 4 — Import Curated Sources & Verify

Import each URL from the Evidence Registry. Use `source add` — this is the only path that writes sources into the notebook's queryable source store.

```bash
# Write all Evidence Registry URLs to a temp file (one per line)
python3 -c "
urls = [
    # paste each URL from the Evidence Registry here, one per line, quoted
]
import sys
path = f'/tmp/urls_{sys.argv[1]}.txt'
open(path, 'w').write('\n'.join(urls))
print(f'URLs written to {path}')
" "$NB_ID"

# Copy the reference script to /tmp for execution
cp /Users/agustinsilvazambrano/.claude/skills/notebooklm-legal-research-rhino/references/batch-import.py /tmp/batch_import.py

# CRITICAL EXECUTION RULE: Run the batch import EXACTLY ONCE synchronously.
# DO NOT execute it as a background task and then re-execute it in the foreground.
# NB_ID passed as argument, never embedded in the script
IMPORT_RESULT=$(python3 /tmp/batch_import.py "$NB_ID" "/tmp/urls_${NB_ID}.txt")
echo "$IMPORT_RESULT"
```

```bash
# Parse the result: mark Evidence Registry entries
python3 -c "
import json, sys
result = json.loads(sys.argv[1])
print(f'Imported: {len(result[\"imported\"])}')
print(f'Failed:   {len(result[\"failed\"])}')
print(f'Skipped (JS-shell or unreachable): {len(result.get(\"skipped\", []))}')
for f in result['failed']:
    print(f'  [IMPORT FAILED] {f[\"url\"]}: {f[\"error\"]}')
for s in result.get('skipped', []):
    print(f'  [SKIPPED — NOT CRAWLABLE] {s[\"url\"]}: {s[\"reason\"]} — apply Phase 3.7 B1 resolution rules')
" "$IMPORT_RESULT"
```

**Failure handling:** The batch script handles errors per-URL without aborting. Failed URLs appear in the JSON `failed` array and are printed above. Mark each as `[IMPORT FAILED]` in the Evidence Registry and continue.

After all import attempts:

```bash
notebooklm source clean --dry-run -n "$NB_ID"
notebooklm source clean --yes -n "$NB_ID"
notebooklm source list --json -n "$NB_ID"
```

**Zero-source gate:** If the source list is empty after cleanup, do not proceed. Tell the user:
> "All sources failed to import. Would you like to retry with different queries, add sources manually, or abort?"

**Post-import wrong-jurisdiction scan:** Scan the final source list for titles or URLs signalling a different country. Remove any found:
```bash
notebooklm source delete <source_id> -n "$NB_ID" -y
```

Update the Evidence Registry: mark each entry as `Imported ✓` or `[IMPORT FAILED]`. Remove failed entries from the Registry.

Notify the user and immediately continue to Phase 4.5:
> "Here are the [N] imported sources. **Proceeding to analysis now** — reply at any point to add or remove sources."

---

---

## Phase 4.1 — Queryability Spot-Check (Primary Sources Only)

> Spot-check execution rules for each runner are in
> `$SKILL_ROOT/references/phases/phase-4-spot-check-runner.md`.
> Each T1 source is checked in a parallel sub-subagent. `notebooklm ask` is read-only,
> so all runners query the same main notebook (`$NB_ID`) safely in parallel.

Do **not** run spot-checks for Tier 2/3 sources — the cost in API calls is not justified for secondary materials.

### Dispatch spot-check runners (parallel)

Build the list of T1 sources from the Evidence Registry (import_status = "imported").
Dispatch one spot-check sub-subagent per T1 source simultaneously in a single Agent tool call.
Each runner loads `$SKILL_ROOT/references/phases/phase-4-spot-check-runner.md` and receives:

```
SOURCE_ID       = <evidence registry id>
TITLE           = <source title>
SOURCE_TYPE     = "statute" | "case" | "regulation" | "constitutional_provision"
CENTRAL_ISSUE   = <5-word summary of the research question, in REPORT_LANGUAGE>
CITED_ARTICLES  = [<list of article numbers cited in T2/T3 sources, empty if not a statute>]
NB_ID           = <main research notebook ID — same for all runners>
REPORT_LANGUAGE = <from state.json scope>
SKILL_ROOT      = <absolute path to hybrid skill root>
```

Wait for ALL runner summaries before proceeding.

### Collect results + update Evidence Registry

After all runners return, update the Evidence Registry entries in state.json with the returned `queryable_status` and `flags` for each source.

```
| #  | Title | URL | Tier | ... | Import | Queryable |
|----|-------|-----|------|-----|--------|-----------|
| 1  | Ley 20.744 | ... | T1 | ... | ✓ | Queryable ✓ |
| 2  | Halabi c/ PEN | ... | T1 | ... | ✓ | Queryable ✓ |
| 3  | Acordada 32/2014 | ... | T1 | ... | ✓ | NOT QUERYABLE — DISCLOSED |
```

Notify the user:
> "Queryability spot-check complete. [M] of [N] primary sources queryable. [K] sources are not queryable and will be disclosed as [SECONDARY ONLY] in Verification Notes. Proceeding to Source Overview."

---

## Phase 4.5 — Source Overview Note + Date Enrichment (Rhino)

**Skip condition:** Skip this phase ONLY if `LEGALLY_RELEVANT_DATE = "not applicable"` (purely academic or doctrinal research with no specific factual scenario — no dispute, no transaction, no compliance question). In that case, write "N/A — academic/doctrinal matter" for all date fields in the Evidence Registry and proceed directly to Checkpoint 2.

**Do NOT skip for advisory matters** (where `LEGALLY_RELEVANT_DATE = "today"`). For advisory research the Source Overview answers whether indexed sources ARE current — i.e., whether the statute version in the notebook is the currently in-force version and whether secondary sources are analyzing law that has since changed. That question is just as important as temporal applicability for past-date matters.

Before analysis begins, ask NotebookLM to produce a compact metadata list that includes publication and enforcement dates. This provides the date data needed to complete the Evidence Registry and run the Phase 5.6 temporal applicability check without triggering prompt timeouts from heavy legal synthesis.

Send this prompt **in `REPORT_LANGUAGE`**:

```bash
notebooklm ask "<SOURCE_OVERVIEW_PROMPT>" --save-as-note --note-title "SourceOverview" -n "$NB_ID"
```

Where `<SOURCE_OVERVIEW_PROMPT>` is the prompt from `references/analysis-prompts.md` (Phase 4.5 section).

After the note is saved, retrieve it:
```bash
notebooklm note list --json -n "$NB_ID"
notebooklm note get <sourceoverview-note-id> -n "$NB_ID"
```

**Date enrichment step:** Parse the Source Overview response and update the Evidence Registry with the dates returned for each source:

- For **Tier 1 primary sources** (statutes, regulations, decrees, cases): extract both the publication date (date of official gazette publication or court decision date) and the enforcement/entry-into-force date where they differ. If NotebookLM cannot determine the enforcement date, mark it `?` and add a `⚠` flag — this source requires manual date confirmation before Phase 5.6.
- For **Tier 2 and Tier 3 sources** (articles, commentary, analysis): extract only the publication date. Note whether the underlying primary sources they discuss have been amended or superseded since that date, if NotebookLM can determine this.

After updating the Evidence Registry, release the Source Overview note content from Claude's context. The note remains in the notebook and can be retrieved on-demand in Phase 6 if source-to-section alignment is unclear.


### Autonomous state write (replaces Checkpoint 2 halt)

```bash
python3 "$SKILL_ROOT/references/scripts/workspace.py" mark-complete "$WORKSPACE" 4.5 5
```
