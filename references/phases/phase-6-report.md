---
phase_id: "6"
covers: ["6"]
subagent_type: general-purpose
inputs_from_state: ["scope","evidence_registry","citation_log","cross_exam","analysis_notes","nb_id"]
outputs_to_state: ["report_path","completed_phases","next_phase"]
next_phase_on_success: "done"
estimated_runtime_minutes: 5-15
loads_reference:
  - "$SKILL_ROOT/references/output-templates.md"
  - "$SKILL_ROOT/references/citation-styles.md"
---

# Phase 6 — Report Assembly

> **Subagent contract:** retrieve analysis notes on-demand from notebooklm (Step 1),
> write the HTML report to
> `$WORKSPACE/../legal-research-<slug>-<YYYY-MM-DD>.html` using the template from
> output-templates.md, open the report, record report_path in state.json,
> mark phase 6 complete with next_phase=done.

## Phase 6 — Report Assembly

Load `$SKILL_ROOT/references/output-templates.md` for the HTML design specification, template, and source tier classification guide.

### Step 1 — Retrieve analysis notes

```bash
notebooklm note list --json -n "$NB_ID"
```

Retrieve each analysis note on-demand as needed — **do not load all notes simultaneously**. Retrieve one, extract what is needed for that section of the report, then move on:

```bash
notebooklm note get <note-id> -n "$NB_ID"
```

For the multi-issue variant, retrieve issue-specific notes (e.g., `Issue-1-Rule`, `Issue-2-Application`) as you write each section.

If source-to-section alignment is unclear, retrieve the `SourceOverview` note from Phase 4.5 as a lightweight reference rather than re-reading full analysis notes.

### Step 2 — Write the HTML report

**Localization:** If `REPORT_LANGUAGE` is not English, translate the following static strings before writing — the HTML structure and CSS remain unchanged:
- Cover label: `LEGAL RESEARCH MEMORANDUM`
- Page header right: `CONFIDENTIAL`
- Section headings: `Research Question`, `Legal Analysis`, `Verification Notes`, `Sources Consulted`, `Disclaimer`
- Sub-headings: `Primary Authorities`, `Secondary — Doctrine & Academic`, `Tier 3 — Law Firm & Specialized Commentary`
- Verification field labels: `Opposing position`, `Weakest link`, `Overall confidence`, `Citation mismatches`, `Unverified sources`, `Research gaps`, `Currency flags`, `Temporal applicability`
- Metadata labels: `Legally relevant date`
- Table column headers: `Source`, `Type`, `Status`
- The full disclaimer paragraph
- The footer text

Write the file to `./legal-research-[topic-slug]-[YYYY-MM-DD].html` using the **HTML Template** from `$SKILL_ROOT/references/output-templates.md`. Fill every `<!-- PLACEHOLDER -->` comment:

- **DOC_TITLE** — full document title (topic + jurisdiction)
- **SHORT_TOPIC** — ≤6-word header label
- **DATE_LABEL** — month and year (e.g., "April 2026")
- **JURISDICTION / AREA_OF_LAW / POSTURE / DATE / LANGUAGE / SOURCE_COUNT / CONFIDENCE** — from Phase 1 scope, Evidence Registry, and `CROSS_EXAMINATION_NOTES`
- **LEGALLY_RELEVANT_DATE** — from Phase 1 scope (e.g., "15 August 2023" or "Today — advisory matter")
- **RESEARCH_QUESTION** — precise research question from Phase 1
- **ANALYSIS_CONTENT** — full IRAC/CRAC/CREAC content, written **node by node using the Evidence Registry as the section guide**. For each section, reference only the sources tagged to the relevant node(s). For every citation with status `✓ Verified` or `~ Paraphrase — Consistent` in the Citation Verification Log, add a `<blockquote>` immediately after the rule or application paragraph that cites it. Do **not** add block-quotes for `✗ Citation Mismatch` or `[UNVERIFIED]`.
- **Verification fields** — populate from `CROSS_EXAMINATION_NOTES` (Phase 5.6) and the NotebookLM Verification note (Phase 5), merged:
  - Opposing position: from Verification note (steelmanned by NotebookLM) + Phase 5.6 steelman check
  - Weakest link: from `CROSS_EXAMINATION_NOTES` Phase 5.6 step 4
  - Overall confidence: from `CROSS_EXAMINATION_NOTES` Phase 5.6 step 5
  - Citation mismatches: all ✗ entries from Citation Verification Log
  - Unverified sources: all [UNVERIFIED] entries from Citation Verification Log
  - Research gaps: from Verification note + Phase 5.6 step 2 gaps
  - Currency flags: from Verification note currency section
  - Temporal applicability: summary of all `⚠ Post-date`, `⚠ Version mismatch`, and `⚠ Commentary may be outdated` flags from `CROSS_EXAMINATION_NOTES` step 0; include any retroactivity findings
- **PRIMARY_SOURCES / SECONDARY_SOURCES / TIER3_SOURCES** — cited sources only, classified by tier from Evidence Registry, with hyperlinks. Omit tier section if empty.

**Research Log is not included in the report.**

### Step 3 — Open

```bash
open ./legal-research-[topic-slug]-[YYYY-MM-DD].html        # macOS
# xdg-open ./legal-research-[topic-slug]-[YYYY-MM-DD].html  # Linux
```

### Step 4 — Confirm to user

```
Report saved: ./legal-research-[topic-slug]-[YYYY-MM-DD].html
Notebook ID:  <id>  (kept for future reference)

Node coverage summary:
  Node 1: ✓  Node 2: ✓  Node 3: ✓  Node 4: ⚠ Thin — disclosed in Verification Notes
Confidence: [High / Medium / Low]
```

### Autonomous state write

```bash
python3 "$SKILL_ROOT/references/scripts/workspace.py" mark-complete "$WORKSPACE" 6 done
```

---

## Reference Files

| File | Load when |
|------|-----------|
| `$SKILL_ROOT/references/analysis-prompts.md` | Phase 5 — framework selection, node-aware prompt sequence; Phase 5.5 — consolidated CitationVerification prompt |
| `$SKILL_ROOT/references/source-priority.md` | Phase 3 — designing research queries by jurisdiction |
| `$SKILL_ROOT/references/output-templates.md` | Phase 6 — report assembly: HTML template, source tier classification, content patterns |
| `$SKILL_ROOT/references/citation-styles.md` | Phase 6 — formatting inline citations by jurisdiction |
| `$SKILL_ROOT/references/verification-protocol.md` | Phase 5.6 — Claude cross-examination protocol |
