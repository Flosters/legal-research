---
phase_id: "5.6"
covers: ["5.6"]
subagent_type: general-purpose
inputs_from_state: ["evidence_registry","citation_log","scope","research_checklist"]
outputs_to_state: ["cross_exam","completed_phases","next_phase"]
next_phase_on_success: "6"
estimated_runtime_minutes: 3-8
loads_reference: "$SKILL_ROOT/references/verification-protocol.md"
---

# Phase 5.6 — Claude Cross-Examination

> **Subagent contract:** pure reasoning — no notebooklm calls. Runs every check in
> verification-protocol.md (temporal applicability, reasoning ladder, internal
> consistency, steelman, weakest link, confidence calibration) against the data
> in state.json. Writes cross_exam to state.json.

## Phase 5.6 — Claude Cross-Examination (Rhino + legal-research)

After receiving the NotebookLM Verification note and completing the Citation Verification Log, apply a Claude-side cross-examination. This is independent of NotebookLM's self-assessment and adds a second layer of scrutiny before report assembly.

Load `$SKILL_ROOT/references/verification-protocol.md` for the full AI Cross-Examination Protocol.

Working from the date-enriched Evidence Registry and the Citation Verification Log (not from raw note content), run the following checks:

**0. Temporal applicability check:** For each Tier 1 source in the Evidence Registry, verify it was in force at `LEGALLY_RELEVANT_DATE`:

- **Statutes and regulations:** Compare the enforcement/entry-into-force date against `LEGALLY_RELEVANT_DATE`. If the enforcement date is *after* `LEGALLY_RELEVANT_DATE`, the source was not yet in force and must be flagged `⚠ Post-date — may not apply`. Note: check separately whether retroactivity provisions apply before excluding the source from analysis.
- **Cases:** Confirm the decision date is on or before `LEGALLY_RELEVANT_DATE`. A ruling issued after the relevant date may be cited as persuasive or predictive authority but not as the controlling rule at the time of the facts.
- **Publication date vs. enforcement date gap:** For any source where these differ, explicitly note the gap and confirm which date is legally operative. In civil law jurisdictions this gap (vacatio legis) can be weeks to months.
- **Amendment history:** For statutes and regulations, check whether the version in the notebook is the version that was in force at `LEGALLY_RELEVANT_DATE`. If it appears to be a later-amended version, flag it as `⚠ Version mismatch — confirm applicable version`.
- **Retroactivity:** If any source post-dates `LEGALLY_RELEVANT_DATE`, check whether it contains explicit retroactivity provisions. If it does, note this — the source may still govern.
- **Tier 2 and Tier 3 currency:** For each secondary or tertiary source, check whether any of the primary sources it discusses have been amended, overruled, or superseded since its publication date. If the underlying law has materially changed, flag the source as `⚠ Commentary may be outdated — primary source amended [date]`. Do not discard it; flag it so the reader can assess whether the doctrinal analysis still holds.

**1. Reasoning ladder check:** For each checklist node, verify there is a chain: controlling authority (confirmed in force at `LEGALLY_RELEVANT_DATE`) → rule element → application to facts. If any rung is missing, flag it.

**2. Internal consistency check:** Mentally convert the IRAC/CRAC structure into an elements chart. Does each element have: a rule source (✓ or ~ in Citation Log, and temporally applicable) + a corresponding fact application? If an element appears in the Rule note but has no Application entry, flag the gap.

**3. Steelman check:** Using the Verification note's opposing position summary, assess: does the analysis address the strongest counter-argument? If not, note it as a gap to disclose in the final report.

**4. Weakest link identification:** Name the single most vulnerable point in the analysis chain — the citation most likely to be challenged, the most unsettled doctrinal area, or the largest factual gap. Temporal applicability issues identified in step 0 should be considered candidates for weakest link.

**5. Confidence calibration:** Assign a confidence tier based on the Citation Verification Log and temporal applicability results:
- **High (>80%):** All key citations ✓ Verified and confirmed in force at `LEGALLY_RELEVANT_DATE`, reasoning ladder complete, no significant gaps
- **Medium (50–80%):** Most citations verified and applicable; minor temporal flags (e.g., one `⚠ Commentary may be outdated`) or ~ Paraphrase entries; doctrine partially settled
- **Low (<50%):** One or more key citations [UNVERIFIED], ✗ Citation Mismatch, or `⚠ Post-date — may not apply`; version mismatch unresolved; doctrine unsettled; material facts missing

Record the outputs of this check as `CROSS_EXAMINATION_NOTES`. These feed directly into the Verification Notes section of the final report.

### Autonomous state write

```bash
python3 "$SKILL_ROOT/references/scripts/workspace.py" mark-complete "$WORKSPACE" 5.6 6
```
