# Analysis Prompts — NotebookLM Legal Research (Rhino Edition)

> **Language rules (three independent concerns — read before sending any prompt):**
> 1. **Report language = query language.** The report is written in the language the user queried in. Jurisdiction does NOT determine report language. Record explicitly as `REPORT_LANGUAGE`.
> 2. **Phase 3 research queries = jurisdiction language.** Write deep-research queries in the jurisdiction's primary language (Spanish for Argentina, Portuguese for Brazil, French for France, etc.) to retrieve sources in the correct language. Independent of report language.
> 3. **Phase 5+ analysis prompts = report language.** Every prompt sent to NotebookLM — Source Overview (Phase 4.5), IRAC/CRAC prompts (Phase 5), and the consolidated CitationVerification prompt (Phase 5.5) — must be sent in `REPORT_LANGUAGE`. NotebookLM responds in the language of the question; prompt language directly controls the language of every analysis note and the final report. An English query → English prompts, even if all sources are in Spanish.

---

## Framework Selection

| Context | Framework |
|---------|-----------|
| US litigation memo / brief | IRAC |
| US transactional / advisory | CRAC |
| UK / Commonwealth | CRAC or CREAC |
| Academic / law review | IRAC |
| Multi-issue analysis | IRAC per issue (nested) |
| Regulatory / compliance | CREAC |
| Latin America | IRAC or CRAC |

---

## Phase 4.5 — Source Overview Prompt

Send **in `REPORT_LANGUAGE`**. Note title: `SourceOverview`.

```
For each source in this notebook, provide a simple metadata list. Format as a numbered list with one line per source:
[Source Title] | Publication Date: [Date] | Enforcement Date: [Date or "same" or "unknown"]
Do not include any summaries, legal analysis, or descriptions. Just the title and the two dates.
```

---

## Standard Sequence (5 Prompts)

Send all prompts in `REPORT_LANGUAGE`. Each builds on the previous via NotebookLM's conversation history. Use `--save-as-note` on every prompt.

If a prompt response is truncated, follow up with:
`"Continue the [Section] analysis — you were cut off after [last point made]."`

If a response lacks citations, follow up with:
`"Please add specific source citations to each point in the [Section] section."`

**Context management:** After each prompt response arrives, note the title it was saved under, then release the full response from Claude's context. Phases 5.5 and 6 retrieve notes on-demand via `notebooklm note get` — do not hold all responses in context simultaneously.

---

### Prompt 1 — Issue Identification

**Note title:** `Issue`

```
Based on the sources in this notebook, identify and state the precise legal question or
questions raised. For each issue:
- State the legal question in one sentence
- Identify the jurisdiction and area of law
- Note whether this is a question of fact, law, or mixed
- Flag any threshold jurisdictional or procedural issues that must be resolved first

If there are multiple issues, number and list each one separately.
```

---

### Prompt 2 — Rule Synthesis (Node-Anchored)

**Note title:** `Rule`

When sending this prompt, insert the relevant checklist nodes from Phase 1 so NotebookLM focuses on the right sources. Replace the bracketed section with actual node descriptions.

```
Based on the sources in this notebook and the issues defined in the "[PREVIOUS_NOTE_TITLE]" note, synthesize the governing legal rules that apply. Structure your answer around these research dimensions:
[INSERT: "  — [Node N description]: [which sources are expected to address this]" for each node]

For each rule:
- State the black-letter rule and cite the specific source (case name, statute, article number, etc.)
- Distinguish mandatory authority from persuasive authority
- Note any split of authority, conflicting interpretations, or recent changes in the law
- For multi-element rules, list each element separately

Cite every rule to a specific source in the notebook. Do not state rules from general
knowledge — only from the imported sources.
```

**Example (product liability — US jurisdiction):**
```
Based on the sources in this notebook, synthesize the governing legal rules that apply to
the issue(s) identified. Structure your answer around these research dimensions:
  — Binding primary authority (leading cases and statutes establishing the product liability standard)
  — Statutory and regulatory framework (applicable federal and state statutes, agency regulations)
  — Doctrine and academic analysis (leading treatises on the elements of the claim)

For each rule: [rest of prompt as above]
```

---

### Prompt 3 — Application

**Note title:** `Application`

```
Based on the legal rules synthesized in the "[PREVIOUS_NOTE_TITLE]" note, apply those rules to the facts of the research question.
Work through each rule element by element:
- State the relevant fact
- Apply the rule element to that fact
- Cite the specific source that supports the application
- Identify where the analysis is strong and where it is weak or disputed
- Address the strongest counterargument for each element

Do not skip unfavorable facts. If a fact cuts against the conclusion, say so explicitly
and explain how it affects the analysis.
```

---

### Prompt 4 — Conclusion

**Note title:** `Conclusion`

```
Based on the analysis in the "[PREVIOUS_NOTE_TITLE]" note, state your conclusion for each issue analyzed:
- Provide a direct answer to the legal question
- State your confidence level: High / Medium / Low
- Briefly explain what drives the confidence level (e.g., clear binding authority,
  unresolved circuit split, sparse case law)
- Note any conditions or changes in facts that would alter the conclusion
- If there are multiple issues, state how they interact and give an overall conclusion
```

---

### Prompt 5 — Verification (Mandatory)

**Note title:** `Verification`

```
Before this research is finalized, perform a quality check on the analysis:

1. Citation uncertainty: List any sources you cited in the analysis that you are uncertain
   about — cases you could not fully verify, statutes that may have been amended, or
   secondary sources of questionable authority. For each, explain the uncertainty.

2. Research gaps: Identify any legal questions raised by the analysis that the sources in
   this notebook do not adequately address. What would a thorough lawyer look for next?

3. Opposing position: Steelman the opposing argument. What is the strongest case against
   the conclusion reached? Which sources would opposing counsel rely on?

4. Weakest link: Name the single most vulnerable point in the analysis — the assumption,
   inference, or citation that opposing counsel would attack first.

5. Temporal applicability and currency:
   a. For each statute, regulation, or decree cited: confirm its publication date and
      entry-into-force date. Was it in force at the legally relevant date for this research?
      If a law entered into force after the legally relevant date, flag it explicitly.
   b. For each case cited: confirm the decision date. If it post-dates the legally relevant
      date, note that it may be persuasive or predictive authority rather than the
      controlling rule at the time of the facts.
   c. For each secondary or tertiary source (articles, treatises, commentary): check whether
      the primary sources it analyzes have been materially amended, overruled, or superseded
      since the secondary source was published. If so, flag the secondary source as
      potentially outdated — not discarded, but requiring reader attention. Do not flag a
      secondary source as outdated merely because of age; flag it only if the underlying law
      has actually changed.
   d. Identify any law or regulation where the publication date and the enforcement date
      differ. Note the gap and confirm which date is legally operative for this research.
```

---

## Multi-Issue Variant (MANDATORY FOR >1 ISSUE)

For research questions with two or more distinct legal issues, you MUST process them sequentially to prevent prompt timeouts. Send Prompts 1–4 once per issue using note titles like `Issue-1-Issue`, `Issue-1-Rule`, `Issue-1-Application`, `Issue-1-Conclusion`. NEVER combine prompts (e.g., Application and Conclusion) into a single `ask` call for efficiency. Each step must be its own completely separate note. For Issue Identification, do not use a single combined prompt; run Prompt 1 independently per issue.

Crucially, you must replace `[PREVIOUS_NOTE_TITLE]` in each prompt with the precise title of the preceding note (e.g., for `Issue-1-Application`, the previous note is `Issue-1-Rule`).

Once all issues are complete, send the Synthesis prompt, then Prompt 5 (Verification).

**Synthesis prompt** (note title: `Synthesis`):
```
Based on the conclusions reached in the preceding issue-specific conclusion notes, synthesize the overall outcome:
- How do the issues interact? Does the resolution of one affect another?
- What is the overall legal position?
- What is the recommended course of action, if any?
- What are the priority next steps for further research or legal action?
```

Then send Prompt 5 (Verification) as the final prompt.

---

## Phase 5.5 — Focused CitationVerification Prompt

Build this prompt dynamically by first extracting a checklist of up to 4 citations from the generated notes. Send **in `REPORT_LANGUAGE`** as a single `notebooklm ask` call. Note title: `CitationVerification`. If there are more than 4 citations, split them into multiple batches and use titles like `CitationVerification-1`.

This focused prompt replaces the open-ended verification to prevent NotebookLM from falling into a "thinking" reasoning limit. NotebookLM performs cross-referencing against its source store for the specific citations requested; Claude receives one structured response to parse.

**Core rule before sending:** Citation verification must be performed against **primary source texts only**. The purpose of this phase is to confirm that what the analysis attributes to a case, statute, or regulation actually appears in that primary source. Checking whether a secondary source describes a primary source consistently with another secondary source is *not* citation verification — it is circular.

```
Verify the following specific citations against the primary sources in this notebook:
[INSERT FOCUSED LIST OF CITATIONS HERE IN THIS FORMAT: 
1. Source: [Name], Proposition: [Attributed claim]
2. Source: [Name], Proposition: [Attributed claim]
...]

For every citation in the checklist above, verify whether the quoted or attributed passage
appears in the primary source document itself (the actual court decision, the actual
statute text, the actual regulatory text).

PRIMARY SOURCE VERIFICATION RULE:
If the analysis cites case X for proposition P, find the text of case X in this notebook
and verify P against it. Do NOT verify P by checking whether a secondary source (article,
commentary, treatise, official digest) describes case X consistently with P. The secondary source's
description of a case is not the case. EXCEPTION: You MAY verify case X without finding its original text IF AND ONLY IF you verify it against *another* Tier 1 primary source in this notebook (like a recent case) that quotes or restates it.

Return a numbered list in this exact format for every citation found:

Citation [n]:
- Source: [source name as cited in the analysis — use the jurisdiction's citation format, e.g., common law: "Donoghue v Stevenson [1932] AC 562 (UK)"; US: "Brown v. Board of Education, 347 U.S. 483 (1954)"; civil law: "CSJN, Halabi c/ PEN, Fallos 332:111 (Argentina)"]
- Proposition: [the claim made about this source in the analysis]
- Status: [TEXT VERIFIED | PARAPHRASE — CONSISTENT | CITATION MISMATCH | PRIMARY NOT IN NOTEBOOK | SOURCE NOT IN NOTEBOOK]
- Verified Against: [state the exact source title you checked — must be the primary source text, not a secondary description of it]
- Verbatim passage: "[exact passage from the PRIMARY source — only if TEXT VERIFIED or PARAPHRASE — CONSISTENT]"
- Location: [article / section / paragraph / recital / opinion section / considerando / page — only if available; use the jurisdiction's term for the reasoning and operative sections of judgments]
- Note: [if CITATION MISMATCH: what the primary source actually says; if PRIMARY NOT IN NOTEBOOK: name the secondary source that describes it and note it could not be cross-checked; if SOURCE NOT IN NOTEBOOK: state so]

Status definitions:
- TEXT VERIFIED: the verbatim or near-verbatim passage was found in the primary source text in this notebook.
- PARAPHRASE — CONSISTENT: the proposition is a fair paraphrase of the primary source text in this notebook.
- CITATION MISMATCH: the primary source text is in this notebook but does not support the attributed proposition, or the attributed text does not appear in it.
- PRIMARY NOT IN NOTEBOOK: the cited source is a primary source (case, statute, regulation, constitutional provision) and its text is NOT in this notebook. Do not upgrade this to TEXT VERIFIED or PARAPHRASE — CONSISTENT based on a secondary source's description. Secondary source descriptions are not primary source text.
- SOURCE NOT IN NOTEBOOK: neither the primary source nor any secondary source describing it is present in this notebook.

Rules:
- Do not skip any citation. Cover every source referenced in Rule and Application.
- Never use a secondary source (article, commentary, treatise, official digest, law firm analysis) as a
  substitute for the primary source when verifying a citation to a case, statute, or
  regulation. If a secondary source says "Halabi held X", that does not verify that
  Halabi held X — find the Halabi decision text and check there (or another primary source quoting Halabi).
- If uncertain whether a passage is accurate, mark it CITATION MISMATCH rather than guessing.
- If a source is in the notebook but does not address the cited point at all, mark it CITATION MISMATCH and note "source does not address this proposition."
- For every statute, regulation, or executive instrument (decree, executive order, statutory instrument, ordonnance, etc. — use the jurisdiction's term): include its publication date and enforcement/entry-into-force date in the Note field, even if the citation is otherwise TEXT VERIFIED. If these dates are unavailable from the source text, write "dates not determinable from source."
```

**Result classification (used when building the Citation Verification Log in Claude):**

| Status returned | Log entry status | Verified Against |
|----------------|-----------------|-----------------|
| `TEXT VERIFIED` | `✓ Verified` | Must be primary source text |
| `PARAPHRASE — CONSISTENT` | `~ Paraphrase — Consistent` | Must be primary source text |
| `CITATION MISMATCH` | `✗ Citation Mismatch` | Primary source text (text did not match) |
| `PRIMARY NOT IN NOTEBOOK` | `[SECONDARY ONLY]` | Secondary source only — primary not in notebook |
| `SOURCE NOT IN NOTEBOOK` | `[UNVERIFIED]` | Not in notebook |

Only citations with status `✓ Verified` or `~ Paraphrase — Consistent` (both verified against the primary source text) may appear as block-quotes in the final report. `[SECONDARY ONLY]` citations must be disclosed in Verification Notes with a clear statement that the primary source was not available for direct verification. `✗ Citation Mismatch` and `[UNVERIFIED]` must also be disclosed. Do not silently remove any of these.
