---
name: legal-research-py
description: >
  Agentic legal research workflow. Runs end-to-end through 6 phases: scope extraction,
  notebook creation, research curation, source import, analysis, and report generation.
  Requires notebooklm CLI, authenticated. Trigger with /legal-research or on any
  deep legal research request.
---

# NotebookLM Legal Research

This skill is a **router**, not a workflow. Every substantive phase runs in a fresh
subagent with its own context window. The orchestrator only does two things:

1. Extract scope + checklist + queries from the user (Phase 1), create the notebook
   (Phase 2), and initialise the workspace.
2. Dispatch seven subagents in sequence, each reading and writing `state.json`.

All per-phase rules, fallback ladders, and jurisdiction logic live in
`references/phases/*.md`. The orchestrator never loads them.

---

## Language Rules

| Concern | Rule |
|---|---|
| Report language (`REPORT_LANGUAGE`) | Language of the user's query. Phase subagents inherit via state.json. |
| Phase 3 research queries | Jurisdiction's primary language. Set by orchestrator in Phase 1; stored in `research_queries[*].query`. |
| Phase 5/5.5/5.6 prompts | `REPORT_LANGUAGE` — enforced by every phase subagent. |

---

## Resume Handler

**If the invocation begins with `resume <path-to-state.json>`:**

1. `state = load <path>`
2. Validate against `references/schemas/state.schema.json`.
3. Print restoration summary (slug, topic, jurisdiction, completed_phases, next_phase).
4. Jump directly to the Dispatch Table entry for `state.next_phase`.

No user pause. No re-execution of completed phases.

**If the invocation begins with `new <query>` or a plain user query**, proceed to Phase 1.

---

## Prerequisites

**Step 1 — Check permissions are configured:**

```bash
python3 "$SKILL_ROOT/references/../setup.py" --check
```

If this exits non-zero, tell the user:
> "Run `python3 ~/.claude/skills/legal-research/setup.py` in your terminal, then restart Claude Code, then try again."
Then abort — do not proceed.

**Step 2 — Check NotebookLM authentication:**

```bash
notebooklm status  # must show "Authenticated as: ..."
```

If not authenticated, prompt the user once to run `notebooklm login`, then abort.

---

## Phase 1 — Scope + Checklist (inline)

Load `references/scope-prompt.md` for the full Phase 1 logic (scope extraction, verifiable checklist design, research-query design). Ask at most one consolidated clarification question; never more than three clarifying questions total.

Produce a JSON object with this shape and write it to `/tmp/scope-$$.json`:

```json
{
  "topic": "...",
  "jurisdiction": "...",
  "area_of_law": "...",
  "posture": "litigation|transactional|advisory|academic",
  "report_language": "es|en|pt|fr|...",
  "legally_relevant_date": "YYYY-MM-DD or 'today' or 'not applicable'",
  "research_checklist": [ {"node_id": 1, "name": "...", "criterion": "..."}, ... ],
  "research_queries":   [ {"query_id": 1, "angle": "...", "query": "...", "nodes": [1]}, ... ]
}
```

Present the checklist + query plan to the user as a compact summary and ask ONE confirmation question: *"Confirm to proceed, or adjust scope?"*

On confirmation:

```bash
WORKSPACE=$(python3 "$SKILL_ROOT/references/scripts/scope_to_state.py" \
              "$SKILL_ROOT/research-workspaces" /tmp/scope-$$.json)
echo "Workspace: $WORKSPACE"
```

**This is the last synchronous user prompt.** Everything after this point runs autonomously.

---

## Phase 2 — Notebook Creation (inline)

```bash
TITLE="Legal Research: $(jq -r .scope.topic "$WORKSPACE/state.json") — \
$(jq -r .scope.jurisdiction "$WORKSPACE/state.json") — $(date +%F)"
NB_ID=$(notebooklm create "$TITLE" --json | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id') or d.get('notebook_id') or d.get('notebook',{}).get('id',''))")
python3 "$SKILL_ROOT/references/scripts/workspace.py" update "$WORKSPACE" \
  --set nb_id="$NB_ID" --set notebook_title="$TITLE" \
  --mark-complete 2 --next-phase 3
```

---

## Dispatch Table

| next_phase in state.json | Phase skill to load | Subagent label |
|---|---|---|
| `3` / `3.5` / `3.6` | `references/phases/phase-3-research-curation.md` | A |
| `4`                 | `references/phases/phase-4-import-and-verify.md` | B |
| `5`                 | `references/phases/phase-5-analysis-and-verification.md` | D |
| `6`                 | `references/phases/phase-6-report.md` | F |
| `done`              | — (print report path + node coverage; exit) — **do NOT run `open` — Phase 6 subagent already opened the report** |

Dispatch table phase IDs: 3-curation, 4-indexing, 5, 5.5, 5.6, 6.

---

## Subagent Dispatch Protocol

For each entry in the Dispatch Table matching `state.next_phase`, dispatch a subagent via the Agent tool with `model="sonnet"` and this exact prompt template:

```
You are Subagent <LABEL> for the legal-research skill.

Load ONLY these files:
  - <absolute path to phase skill>
  - <absolute path to any loads_reference entries in its frontmatter>
  - $WORKSPACE/state.json

Environment variables to use verbatim in shell commands:
  WORKSPACE=<absolute path>
  SKILL_ROOT=<absolute path to ~/.claude/skills/legal-research>
  NB_ID=<from state.json>
  REPORT_LANGUAGE=<from state.json scope>
  LEGALLY_RELEVANT_DATE=<from state.json scope>
  JURISDICTION=<from state.json scope>
  EVIDENCE_REGISTRY=$WORKSPACE/evidence_registry.json

The evidence_registry is stored at $WORKSPACE/evidence_registry.json as a standalone
file — it is NOT embedded in state.json. Read it directly from that path whenever you
need source data. Do not look for evidence_registry inside state.json.

YOUR SCOPE IS THIS PHASE ONLY. Execute every step in the phase skill, in order.
On exit, call mark-complete and return a ≤200-word summary to the orchestrator.
After returning your summary, you are done — do not attempt to read, start, or
infer what the next phase requires. The orchestrator dispatches each phase separately.
Do not load other phase files.
**Start immediately.** YOUR FIRST ACTION is to run the first bash command in Stage 1
of the phase file. Do not summarise, plan, or ask questions first. Execute, then report.

If any step fails after the documented fallback ladder, write `error: <reason>` to
state.json and return the error — do not prompt the user, do not retry indefinitely.
```

Wait for the subagent summary. Print it verbatim to the user. Then:

**If Subagent A (Phase 3) just completed** — before dispatching Subagent B (Phase 4), run this guard:

```bash
SOURCE_COUNT=$(notebooklm source list -n "$NB_ID" --json 2>/dev/null \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d) if isinstance(d,list) else 0)" \
  2>/dev/null || echo "0")
```

If `SOURCE_COUNT` is greater than 0, **stop** and tell the user:

> "Phase 3 guard failed: the main notebook already contains $SOURCE_COUNT sources after Phase 3. Expected 0 — Subagent A wrote directly to the main notebook instead of using temp notebooks. Do not proceed to Phase 4. To investigate, inspect the workspace at `$WORKSPACE/state.json`. To restart Phase 3 cleanly, delete the notebook sources and resume with `/legal-research resume $WORKSPACE/state.json` after setting `next_phase` back to `3`."

Do **not** dispatch Subagent B if this guard fails.

Before dispatching each subagent, re-read `state.json`. If the phase you are about to dispatch is already listed in `completed_phases`, a zombie agent ran it — **do not dispatch**. Resume the loop from the actual `next_phase` value instead.

```bash
# Before each dispatch: re-read state and guard against zombie advance.
COMPLETED=$(jq -r '.completed_phases[]' "$WORKSPACE/state.json" 2>/dev/null)
NEXT=$(jq -r .next_phase "$WORKSPACE/state.json")
# If NEXT is already in completed_phases, a zombie ran it — do not dispatch again.
# Skip to the actual next_phase and resume from there.
# Loop: look up NEXT in Dispatch Table, dispatch subagent (if not already done), or exit on done.
```

---

## Error Handling

- **Subagent returns `error:`**: stop the loop, show the error + state.json path, tell the user how to resume: `/legal-research-py resume <state.json path>`.
- **Schema validation failure**: the workspace helper raises; treat as fatal; surface to user.
- **notebooklm CLI not authenticated mid-run**: subagent aborts; user is given resume instructions.

No silent continuation past failure.

---

## Reference Files

| File | Loaded by |
|---|---|
| `references/scope-prompt.md` | Orchestrator (Phase 1 only) |
| `references/schemas/state.schema.json` | Every workspace.py call |
| `references/scripts/workspace.py` | Orchestrator + every subagent |
| `references/scripts/scope_to_state.py` | Orchestrator (Phase 1 only) |
| `references/scripts/jurisdiction-filter.py` | Subagent A |
| `references/scripts/batch-import.py` | Subagent C |
| `references/source-priority.md` | Subagents A + B |
| `references/analysis-prompts.md` | Subagents D + E |
| `references/verification-protocol.md` | Subagent F |
| `references/output-templates.md` | Subagent G |
| `references/citation-styles.md` | Subagent G |
