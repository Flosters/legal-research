---
phase_id: "5"
covers: ["5"]
subagent_type: general-purpose
inputs_from_state: ["scope","evidence_registry","research_checklist","nb_id"]
outputs_to_state: ["analysis_notes","completed_phases","next_phase"]
next_phase_on_success: "5.5"
estimated_runtime_minutes: 15-30
loads_reference: "$SKILL_ROOT/references/analysis-prompts.md"
---

# Phase 5 — Analysis via NotebookLM Chat (IRAC sequence)

> **Subagent contract:** send the 5-prompt IRAC sequence (or Multi-Issue Variant if
> Phase 1 identified ≥2 issues). All prompts in REPORT_LANGUAGE. Use node-aware
> prompting with the checklist from state.json. Save note titles to state.json
> `analysis_notes` (do NOT store response bodies — they stay in the notebook).
> Replace Checkpoint 3 halt with autonomous state write.

## Phase 5 — Analysis via NotebookLM Chat

Load `$SKILL_ROOT/references/analysis-prompts.md` for the framework selection table and the full prompt sequence.

**Language:** Send ALL prompts in `REPORT_LANGUAGE`. This applies to every prompt in Phase 5, Phase 5.5, and Phase 5.6 — regardless of jurisdiction language or the language of the imported sources. The user's query language is the controlling variable.

**Multi-issue MUST split:** If Phase 1 identified two or more distinct legal issues, you MUST use the Multi-Issue Variant from `$SKILL_ROOT/references/analysis-prompts.md`. Send prompts 1–4 sequentially once per issue (note titles: `Issue-1-Issue`, `Issue-1-Rule`, `Issue-1-Application`, etc.), then the Synthesis prompt, then prompt 5 (Verification). **NEVER combine prompts for efficiency**; each stage MUST be completely separate. For example, never combine Application and Conclusion into a single prompt. Furthermore, do not use a single combined Issue Identification prompt for all issues; you must run Prompt 1 independently per issue (e.g., `Issue-1-Issue`, `Issue-2-Issue`). When sending Prompts 2-4, you must replace the `[PREVIOUS_NOTE_TITLE]` placeholder in the prompt with the exact title of the preceding note (e.g., replace with `Issue-1-Rule` when sending the Application prompt).

**Node-aware prompting:** When sending prompts, reference the relevant checklist nodes explicitly. For example, the Rule prompt should name the nodes that cover primary authority and statutory framework so NotebookLM focuses on the right sources. See `$SKILL_ROOT/references/analysis-prompts.md` for node-aware prompt variants.

Send each prompt via:
```bash
notebooklm ask "<prompt>" --save-as-note --note-title "<Section>" -n "$NB_ID"
```

**Standard sequence (5 prompts):**

1. `--note-title "Issue"` — issue identification
2. `--note-title "Rule"` — governing law synthesis (node-anchored, replaces `[PREVIOUS_NOTE_TITLE]` with `Issue`)
3. `--note-title "Application"` — element-by-element application (replaces `[PREVIOUS_NOTE_TITLE]` with `Rule`)
4. `--note-title "Conclusion"` — conclusion with confidence level (replaces `[PREVIOUS_NOTE_TITLE]` with `Application`)
5. `--note-title "Verification"` — self-reported uncertainty, gaps, opposing position, currency flags

**Context management:** After each prompt response arrives, note the title it was saved under, then release the full response from Claude's context. Phases 5.5 and 6 retrieve notes on-demand via `notebooklm note get` — do not hold all responses in context simultaneously.

**If an `ask` call returns `Chat request timed out`:** retry once with a shorter prompt. If it times out twice, split into two follow-up messages in the same conversation.


### Autonomous state write (replaces Checkpoint 3 halt)

```bash
python3 "$SKILL_ROOT/references/scripts/workspace.py" mark-complete "$WORKSPACE" 5 5.5
```
