---
phase_id: "4.1-spot-check-runner"
covers: ["4.1"]
subagent_type: general-purpose
inputs_from_dispatcher: ["source_id", "title", "source_type", "central_issue", "cited_articles", "nb_id", "report_language", "skill_root"]
outputs_to_dispatcher: ["source_id", "queryable_status", "flags"]
estimated_runtime_minutes: 2-8
---

# Phase 4.1 Spot-Check Runner — Single Source Queryability

> **Sub-subagent contract:** You are a spot-check runner dispatched by Subagent C for Phase 4.1.
> `$NB_ID` is the MAIN research notebook (not a temp notebook — `ask` calls are read-only).
> Your job:
> 1. Run the general queryability check for your assigned source.
> 2. If `$SOURCE_TYPE` is a statute with cited articles, run the article-level probe.
> 3. If `$SOURCE_TYPE` is a court decision, run both the general check and the holding check.
> 4. Apply fallback escalation if the source is not queryable (see below).
> 5. Return `{"source_id": "$SOURCE_ID", "queryable_status": "...", "flags": [...]}` to Subagent C.

---

## Phase 4.1 — Queryability Spot-Check (Primary Sources Only)

After import, confirm each Tier 1 primary source is actually queryable — not just registered as a source ID. This is the step that catches the silent-empty-body failure mode: `notebooklm source add` returns a source ID for JS-rendered pages even when the content body is empty and unsearchable.

Run one targeted query per primary source using the source's name and the central legal issue as the query. Do **not** run this for Tier 2/3 sources — the cost in API calls is not justified for secondary materials.

```bash
# For each Tier 1 source in the Evidence Registry, run:
notebooklm ask "What does [Source Title] say about [central legal issue in 5 words]?" -n "$NB_ID"
# Write in REPORT_LANGUAGE — not the jurisdiction language
```

**Interpret the response:**

| Response pattern | Meaning | Action |
|---|---|---|
| Response cites the source by name and quotes specific text | Source is queryable ✓ | Mark `Queryable ✓` in Evidence Registry |
| Response says "I don't have information about X" or gives only generic answer without citing the source | Source indexed but empty | Apply fallback escalation (see below) |
| Response times out | Network issue | Retry once; if second timeout, mark `[SPOT-CHECK TIMEOUT]` and proceed |

**Article-level probe (required for long statutes with specific cited articles):** After the generic queryability check passes for a statute, run a second targeted query for each article that appears in the research checklist or has been identified as a key citation in any Tier 2/3 source:

```bash
# For each cited article in a long statute, run:
notebooklm ask "Reproduce the text of Article [N] of [Statute Name]." -n "$NB_ID"
# Write in REPORT_LANGUAGE
```

**Interpret the response:**

| Response | Meaning | Action |
|---|---|---|
| Response reproduces or closely paraphrases the article text | Article is indexed ✓ | Mark `Article [N] indexed ✓` in Evidence Registry |
| Response says "I don't have information about that article" or gives a generic answer | Article not indexed | Mark `[ARTICLE NOT INDEXED]` in Evidence Registry for that article; apply the long-statute sub-import rule (Phase 3.7 Step A) to import the missing section |
| Second sub-import also fails article probe | Section not crawlable | Every citation to that article receives `[SECONDARY ONLY]` in Phase 5.5; disclose in Verification Notes |

**Two-part spot-check for court decisions:** For any source that is a court decision (not a statute), run two queries — not one:

1. **General check:**
```bash
notebooklm ask "What does [Case Name] say about [central legal issue in 5 words]?" -n "$NB_ID"
```

2. **Holding/operative conclusion check:**
```bash
notebooklm ask "What is the holding / operative conclusion of [Case Name]?" -n "$NB_ID"
# Use the jurisdiction's term: "holding" (common law); "parte dispositiva" or "dispositivo" (Spanish civil law); "dispositif" (French); "ratio decidendi" (Latin/academic)
```

If the holding check returns only factual summary with no legal conclusion, or says "I don't have information", mark the source `[TRUNCATED — HOLDING MISSING]`. A truncated source **cannot** receive `✓ Verified` for any holding-derived proposition in Phase 5.5. Apply the B3 fallback escalation to find a fuller version.

**Fallback escalation for non-queryable sources:**

A source that imported but is not queryable most likely has an empty index body. Apply Phase 3.7 B1 URL resolution rules to find a crawlable alternative URL, then re-import:

```bash
# Remove the empty source
notebooklm source delete <source_id> -n "$NB_ID" -y

# Import the resolved alternative URL
notebooklm source add "<resolved-alternative-url>" -n "$NB_ID"

# Re-run the spot-check query for this source
notebooklm ask "What does [Source Title] say about [issue]?" -n "$NB_ID"
```

If the re-import also fails the spot-check, mark the source `[NOT QUERYABLE — DISCLOSED]` in the Evidence Registry. This status means:
- The source **will not** yield `✓ Verified` or `~ Paraphrase — Consistent` citations in Phase 5.5
- Every citation to it will be `[SECONDARY ONLY]` at best
- The Verification Notes section must disclose it explicitly

**Update the Evidence Registry** with the spot-check outcome column:

| #  | Title | URL | Tier | Node(s) | Batch | Pub. Date | Enforcement Date | Import | Queryable |
|----|-------|-----|------|---------|-------|-----------|-----------------|--------|-----------|
| 1  | Ley 20.744 | infoleg.gob.ar/... | T1 | 2 | Q1 | 1976-05-13 | 1976-05-13 | ✓ | Queryable ✓ |
| 2  | Halabi c/ PEN | csjn.gov.ar/...pdf | T1 | 1 | 3.7 | 2009-02-24 | 2009-02-24 | ✓ | Queryable ✓ |
| 3  | Acordada 32/2014 | csjn.gov.ar/...pdf | T1 | 1 | 3.7 | 2014-06-03 | 2014-06-03 | ✓ | NOT QUERYABLE — DISCLOSED |

## Return to Subagent C

Return to Subagent C in your ≤200-word summary:

```json
{
  "source_id": "<SOURCE_ID>",
  "title": "<TITLE>",
  "queryable_status": "Queryable ✓ | [NOT QUERYABLE — DISCLOSED] | [SPOT-CHECK TIMEOUT] | [TRUNCATED — HOLDING MISSING]",
  "flags": ["Article 5 indexed ✓", "Article 12 NOT INDEXED", ...]
}
```
