---
name: legal-research
description: Comprehensive AI-powered legal research for lawyers, law students, and paralegals. Performs deep, jurisdiction-specific research entirely within the agent — finding, verifying, and synthesizing primary and secondary sources into a structured, verified legal memo. Trigger on /legal-research command or when the user asks to research a legal topic, find case law, analyze statutes, investigate legal doctrine, or answer questions requiring sourced legal analysis. Always asks for jurisdiction if not stated. Responds in the language of the query. Applies mandatory anti-hallucination cross-examination before delivering results. Never sends the user to external tools — all research is performed autonomously via web search.
---

# Legal Research

Perform deep, sourced legal research and deliver a verified, structured analysis. All research is done autonomously — no external tools required from the user.

## Workflow Overview

Two-gate hybrid: clarification → plan confirmation (Gate 1) → research → source review (Gate 2) → synthesis → cross-examination → final output.

---

## Execution Constraints

- **Run synchronously.** Never use Monitor, ScheduleWakeup, or background polling loops. All phases complete inline before returning.
- **Suppress phase narration.** Do not write "Now starting Phase X", "Moving to Phase Y", or similar transition headers between internal phases. Visible output is limited to: (1) Gate 1 plan + confirmation prompt, (2) Gate 2 source table + confirmation prompt, and (3) the final memo. No running commentary between phases.
- **Source failure handling — apply immediately on any HTTP error:**
  - 403 / 404: try the official government/institutional alternative URL from the same tier before marking failed; document both the failed URL and the replacement in the Research Log.
  - Paywall blocked: mark `[PAYWALL BLOCKED]`, skip — do not retry or infer content.
  - YouTube / video-only URLs: mark `[NON-CRAWLABLE: MEDIA]`, skip — these contain no citable text.
  - All tier-equivalent alternatives exhausted: mark `[CRAWL FAILED]` and note in Research Log.
- **Pending legislation:** Any bill, senate project, or legislative proposal not yet enacted (e.g., Argentine S-XXXX/YYYY, US House/Senate bills pre-enactment) must be presented as *pending legislation — not in force*. Never cite as positive law without confirming promulgation.
- **Claim provenance:** If a claim's only primary source is removed after verification fails, re-qualify the claim as "per secondary sources only" or remove it entirely. Never leave a claim cited to a lost or invalid primary instrument.

---

## Gate 1 — Scope & Plan

**Extract from the query:**
- Legal question / topic
- Jurisdiction — ask if not stated or not clearly inferable
- Area of law — infer if possible; confirm only if genuinely ambiguous
- Procedural posture (litigation, transactional, advisory, academic) — infer when possible

**Ask only what's missing.** One consolidated question covering all gaps. Never ask more than 3 clarifying questions total. If jurisdiction is the only gap, ask only that.

**Present a research plan and ask for confirmation before proceeding:**
```
Research question: [precise restatement]
Jurisdiction: [confirmed]
Area of law: [identified]
Source tiers planned: Official databases → Academic repositories → Specialized analysis
Output: Structured legal memo (IRAC/CRAC) with verified citations
```

Ask: "Confirm to proceed, or adjust scope?"

---

## Research Phase

Follow this sequence after Gate 1 confirmation. Load `references/source-priority.md` for the full database list by jurisdiction.

1. **Secondary sources first** — legal encyclopedias, treatises, law review articles, practice guides. These map doctrine and vocabulary before primary law.
2. **Primary authorities** — constitutions, statutes, regulations, case law. Prioritize mandatory authority over persuasive. Read full judgment texts; never rely on headnotes or summaries to identify *ratio decidendi* vs *obiter dicta*.
3. **Search strategy** — start broad, progressively narrow. Use Boolean logic where search engines support it. Tier 1 (official/free) sources first, then Tier 2 (academic), then Tier 3 (specialized analysis).
4. **Source assessment** — for each source, determine: authority type, relevance, currency, and verifiability. Flag any source that cannot be independently confirmed as `[UNVERIFIED]`.

---

## Gate 2 — Source Review

Present all found sources as a table before synthesizing:

| # | Source | Type | Relevance | Status |
|---|--------|------|-----------|--------|
| 1 | [Title](url) | Primary — Case | Key precedent on X | ✓ Verified |
| 2 | [Title](url) | Secondary — Article | Background doctrine | ✓ Verified |
| 3 | [Title](url) | Primary — Statute | Governing provision | [UNVERIFIED] |

Ask: "Proceed with these sources, or remove/add any before I synthesize?"

---

## Phase 2.5 — Deep Source Verification

Run this phase after Gate 2 confirmation and before synthesis. It ensures all applicable primary sources are fully read and that secondary source citations are faithful to the primary text.

### Part A — Full-Text Retrieval

For every primary source (case, statute, regulation, constitutional provision) confirmed in Gate 2 as applicable:

1. Fetch the **full text** via web search or direct URL — not a summary, headnote, or abstract.
2. If full text is unavailable, mark the source `[FULL TEXT UNAVAILABLE]` and note what partial version was used.
3. Extract and store verbatim the key provisions or holdings relevant to the research question, with exact location references (e.g. "Art. 5, §3, para. 2" or "slip op. at 14").

### Part B — Secondary Citation Cross-Referencing

For every secondary source (article, treatise, commentary, doctrine) that quotes or paraphrases a primary source:

1. Extract each quoted or attributed passage.
2. Search it against the full text retrieved in Part A.
3. Classify the result:
   - **`[TEXT VERIFIED]`** — the quoted passage appears verbatim or near-verbatim in the primary; cite with exact location.
   - **`[PARAPHRASE — CONSISTENT]`** — the passage is a paraphrase but accurately represents the primary text; note the actual wording.
   - **`[CITATION MISMATCH]`** — the quoted passage does not appear in the primary text, or the primary text says something materially different; disclose both the secondary's claim and what the primary actually says.
4. Only passages classified as `[TEXT VERIFIED]` or `[PARAPHRASE — CONSISTENT]` may be cited in the final report. `[CITATION MISMATCH]` findings must be disclosed in Verification Notes.

---

## Synthesis Phase

After Gate 2 confirmation:

1. **Structure** using IRAC or CRAC — load `references/output-templates.md` for full templates. Choose based on jurisdiction and context:
   - US / Canada / Latin America: IRAC or CRAC
   - UK / Commonwealth: CRAC or CREAC
   - Academic / pure advisory: IRAC

2. **Citations** — load `references/citation-styles.md` to auto-detect style by jurisdiction. Fall back to raw hyperlinks with title and date if style is ambiguous.

3. **Canons of construction** — apply where statutory interpretation is at issue (plain meaning, purposivist, contextual, *in pari materia*, etc.).

---

## Verification Phase (mandatory — never skip)

Before presenting final output, apply the AI Cross-Examination Protocol. Load `references/verification-protocol.md` for the full framework.

**Minimum checks always required:**
1. Verify every cited case/statute exists and says what you claim — do not cite from memory
2. Steelman the opposing position — identify how opposing counsel would attack the analysis
3. Check internal consistency — would the analysis hold if reformatted as an elements chart?
4. Identify and disclose the weakest link in the reasoning chain
5. Any source still marked `[UNVERIFIED]` must be disclosed in the output with a note

---

## Final Output

Respond in the **language of the query** unless the user specifies otherwise.

```
# Legal Research: [Topic]
**Jurisdiction:** | **Date:** | **Area of law:**

## Research Question
[Precise restatement]

## Sources Consulted
[Verified source table — Tier 1 first, then Tier 2, Tier 3]

## Legal Analysis
[Full IRAC / CRAC / CREAC memo]

## Verification Notes
[Weakest link, UNVERIFIED disclosures, CITATION MISMATCH disclosures, opposing position summary]

## Research Log
[Databases searched, queries run]
```

---

## Reference Files

| File | Load when |
|------|-----------|
| `references/source-priority.md` | Selecting which sources to search, in what order, by jurisdiction |
| `references/citation-styles.md` | Formatting citations for any jurisdiction |
| `references/verification-protocol.md` | Running the AI Cross-Examination Protocol |
| `references/output-templates.md` | Structuring IRAC / CRAC / CREAC analysis |
