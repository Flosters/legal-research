---
phase_id: "5.5"
covers: ["5.5"]
subagent_type: general-purpose
inputs_from_state: ["evidence_registry","analysis_notes","nb_id","scope"]
outputs_to_state: ["citation_log","completed_phases","next_phase"]
next_phase_on_success: "5.6"
estimated_runtime_minutes: 5-15
loads_reference: "$SKILL_ROOT/references/analysis-prompts.md"
---

# Phase 5.5 — Focused Citation Verification

> **Subagent contract:** build the focused checklist (max 4 citations per batch),
> send verification prompt, parse structured response, run the mandatory registry
> cross-check (tier + queryable verification), apply downgrades, write citation_log
> to state.json.

## Phase 5.5 — Focused Citation Verification Checklist (Rhino)

This phase replaces the open-ended verification prompt that sometimes caused NotebookLM to return a "thinking" reasoning fragment. Instead of asking NotebookLM to extract the citations, Claude will first extract a targeted citation checklist from the notes, and then send a focused verification prompt.

### Step A — Extract Citations

Retrieve only the notes that contain citable sources. Issue and Conclusion do not contain citations — only Rule and Application do:
```bash
notebooklm note get "Rule" -n "$NB_ID"
notebooklm note get "Application" -n "$NB_ID"
```

For multi-issue research, retrieve the per-issue variants: `Issue-1-Rule`, `Issue-1-Application`, `Issue-2-Rule`, `Issue-2-Application`, etc.

Read the notes and build a **focused checklist of up to 4 key citations** (every case name, statute, regulation, constitutional provision, decree, or attributed proposition). Sending more than 4 citations at once can trigger NotebookLM's extended reasoning mode, which breaks the structured response format. If there are more than 4 citations to verify, you MUST split them into multiple batches of 4 and send separate verification prompts for each batch.

### Step B — Send Verification Prompt

Construct the focused verification prompt by inserting your checklist into the Phase 5.5 prompt template from `$SKILL_ROOT/references/analysis-prompts.md`. 
Send the prompt **in `REPORT_LANGUAGE`** (the same language used for all Phase 5 prompts):

```bash
# Example syntax:
notebooklm ask "<FOCUSED_VERIFICATION_PROMPT>" --save-as-note --note-title "CitationVerification" -n "$NB_ID"
```

Where `<FOCUSED_VERIFICATION_PROMPT>` is your dynamic prompt.

After the note is saved, retrieve it:
```bash
notebooklm note list --json -n "$NB_ID"
# Identify the CitationVerification note ID, then:
notebooklm note get <citationverification-note-id> -n "$NB_ID"
```

Parse the structured response and build the **Citation Verification Log** — a compact list of every citation with its status. Format:

```
Citation [n]:
  Source: [source name as cited]
  Proposition: [claim made in the analysis]
  Status: [✓ Verified | ~ Paraphrase — Consistent | ✗ Citation Mismatch | [UNVERIFIED] | [SECONDARY ONLY]]
  Verified Against: [Primary source text | Secondary source only — cannot fully verify]
  Verbatim passage: "[exact passage, if ✓ or ~]"
  Location: [article/section/page, if available]
  Note: [only for ✗, [UNVERIFIED], or [SECONDARY ONLY] — what was found, what is missing, or why unverified]
```

**Status meaning (strict definitions):**
- `✓ Verified` — the verbatim or near-verbatim passage was found in the **primary source text** in the notebook (the actual statute, regulation, or court decision). `Verified Against` must read "Primary source text."
- `~ Paraphrase — Consistent` — the proposition is a fair paraphrase of the **primary source text** in the notebook. `Verified Against` must read "Primary source text."
- `✗ Citation Mismatch` — the primary source text is in the notebook but what the analysis attributes to it does not match what the primary source actually says. `Verified Against` reads "Primary source text — text does not match."
- `[SECONDARY ONLY]` — the primary source text is **not queryable** in the notebook. This covers three cases: (a) the source was never imported; (b) the import failed with an error; (c) the source imported but indexed as an empty body (JS-rendered page — detected in Phase 4.1 spot-check and marked `[NOT QUERYABLE — DISCLOSED]` in the Evidence Registry). In all three cases, the proposition was only confirmed against a secondary source's description. `Verified Against` reads "Secondary source only — primary not queryable in notebook." Every citation with this status must be disclosed in Verification Notes.
- `[UNVERIFIED]` — the cited source (primary or secondary) is not present in the notebook at all.

**Critical rule:** A citation to a primary source (case, statute, regulation, constitution) is only `✓ Verified` or `~ Paraphrase` if the **primary source text itself** was checked. If the primary source is not in the notebook and only secondary sources (articles, treatises, official digests) describe it, the correct status is `[SECONDARY ONLY]`, never `~ Paraphrase — Consistent`. 
**EXCEPTION:** If a primary source is heavily quoted or restated within *another* Tier 1 primary source that IS in the notebook (e.g., a recent CSJN ruling quoting an older CSJN case), you MAY accept the citation as verified without fetching the older case. State in `Verified Against` that it was "Primary source text quoting primary source." Official digests (e.g. CSJN Jurisprudence Digest) do NOT qualify for this exception, they are secondary sources.

**Handling sources not in the notebook (or text gaps):**
If NotebookLM reports a cited primary source as not present in the notebook, or that its text is cut off or incomplete (a "text gap"), add or supplement it and re-query:
```bash
notebooklm source add "<url>" -n "$NB_ID"
# Poll until ready (status not 'processing'):
python3 -c "
import subprocess, json, time, sys
nb_id = sys.argv[1]; url = sys.argv[2]; deadline = time.time() + 300
while time.time() < deadline:
    out = subprocess.check_output(['notebooklm', 'source', 'list', '--json', '-n', nb_id])
    sources = json.loads(out)
    sources = sources.get('sources', sources) if isinstance(sources, dict) else sources
    match = next((s for s in sources if url in s.get('url','') or url in s.get('title','')), None)
    if match and match.get('status') not in ('processing', ''):
        print(match.get('status')); sys.exit(0)
    time.sleep(15)
print('timeout'); sys.exit(1)
" "$NB_ID" "<url>"
```
If the source cannot be imported or fixed, mark the citation `[UNVERIFIED]` in the Citation Verification Log.

**If Phase 4.1 already marked the source `[NOT QUERYABLE — DISCLOSED]`:** Do not attempt to re-import here — Phase 4.1 already exhausted the fallback escalation ladder for this source. Mark the citation `[SECONDARY ONLY]` immediately without retrying.

**However**, if a source simply failed to surface and was NOT marked `[NOT QUERYABLE — DISCLOSED]` in Phase 4.1, you MUST RE-IMPORT a better version (e.g., InfoLEG raw text, full HTML text) rather than accepting a `[SECONDARY ONLY]` failure.

**Mandatory registry cross-check (run before finalizing the Citation Verification Log):** NotebookLM does not internally enforce the primary-source-only rule. It will accept a T3 legal news article or a secondary digest quoting from a decision as sufficient to return `PARAPHRASE — CONSISTENT` — without flagging that the verification was against a secondary source. After building the initial log from NotebookLM's responses, run this cross-check on every entry with status `✓ Verified` or `~ Paraphrase — Consistent`:

1. Find the source named in `Verified Against` in the Evidence Registry.
2. Confirm it is tagged **Tier 1** in the Evidence Registry.
3. Confirm it is marked **Queryable ✓** in the Phase 4.1 column.

If either condition fails, downgrade the status to `[SECONDARY ONLY]` and log the downgrade:
```
Downgraded: [citation name]
  Was: ~ Paraphrase — Consistent
  Reason: NotebookLM verified against [source name] (Evidence Registry Tier [N], [Queryable / NOT QUERYABLE]) — not a queryable primary source
  New status: [SECONDARY ONLY]
```

This cross-check is the structural control that catches false status elevations. The manual inspection of the `Verified Against` field described above is necessary but not sufficient — this registry comparison is the enforcement step.

The Citation Verification Log feeds three places in Phase 6: the Sources Consulted verification status column, the inline block-quotes in the Legal Analysis section, and the Verification Notes section.

**Phase 6 reporting rules derived from this log:**
- Only `✓ Verified` and `~ Paraphrase — Consistent` (both with `Verified Against: Primary source text`) may appear as block-quotes in the final report.
- `[SECONDARY ONLY]` citations must be disclosed in Verification Notes with this exact language: *"Citation verified only against secondary source — primary source text was not available in the notebook. This citation reflects the secondary source's description of [primary source name], not the original text."*
- `✗ Citation Mismatch` and `[UNVERIFIED]` must also be disclosed in Verification Notes.

### Autonomous state write

```bash
python3 "$SKILL_ROOT/references/scripts/workspace.py" mark-complete "$WORKSPACE" 5.5 5.6
```
