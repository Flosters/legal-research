# legal-research-py

A Claude Code skill for autonomous, multi-jurisdiction legal research. It produces
verifiable, citation-backed legal reports by orchestrating a sequence of fresh-context
subagents — each handling one phase of the research workflow in its own context window.

## Install

```bash
npx skills add Flosters/legal-research2
```

Or clone manually and place the directory in `~/.claude/skills/`.

---

## What it does

Given a legal question, the skill:

1. Extracts the research scope — jurisdiction, area of law, legal posture, language
2. Designs a verifiable checklist of legal nodes (issues) and N targeted research queries
3. Creates a dedicated NotebookLM notebook for the research session
4. Runs N deep-research queries in **parallel** (one sub-subagent per query, each with its own temp notebook — eliminates the `research status` race condition)
5. Curates sources against a jurisdiction-aware priority ladder, deduplicates, and builds an Evidence Registry
6. Imports primary sources (T1) with crawlability checks and fallback URL resolution
7. Spot-checks every T1 source for actual queryability in parallel (one sub-subagent per source)
8. Runs an IRAC-structured analysis sequence via NotebookLM chat
9. Verifies every citation against the notebook — marks each as `✓ Verified`, `~ Paraphrase — Consistent`, or `[SECONDARY ONLY]`
10. Cross-examines weak propositions via adversarial prompting
11. Assembles and writes an HTML report

All phases are stateless across subagents — state passes through a schema-validated `state.json` file in the workspace directory.

---

## Workflow

```
User query
    │
    ▼
Phase 1 — Scope extraction + checklist + query design  (orchestrator, inline)
Phase 2 — Notebook creation                            (orchestrator, inline)
    │
    ▼  state.json written → autonomous from here
    │
Phase 3   — Parallel deep research (Subagent A)
              └─ N query runners dispatched simultaneously (sub-subagents)
Phase 3.5 — Source curation + Evidence Registry (Subagent A, continued)
Phase 3.6 — Node coverage check (Subagent A, continued)
Phase 3.7 — Primary source import with crawlability checks (Subagent B)
Phase 4   — Batch source import (Subagent C)
Phase 4.1 — Parallel queryability spot-check (Subagent C)
              └─ M spot-check runners dispatched simultaneously (sub-subagents)
Phase 4.5 — Source overview note + date enrichment (Subagent C, continued)
Phase 5   — IRAC analysis via NotebookLM chat (Subagent D)
Phase 5.5 — Citation verification (Subagent E)
Phase 5.6 — Cross-examination (Subagent F)
Phase 6   — Report assembly → HTML output (Subagent G)
```

The orchestrator (`SKILL.md`) is a thin router — it never loads phase logic. Each
subagent reads only its own phase file from `references/phases/`.

---

## Requirements

### Python

- Python **3.10 or later**

### notebooklm-py CLI

The skill drives Google NotebookLM via the [notebooklm-py](https://github.com/tenglin2/notebooklm) unofficial Python library (CLI: `notebooklm`).

```bash
pip install notebooklm-py
# or
uv add notebooklm-py
```

Version **0.3.4+** required (the version shipping with this skill).

### Google authentication

```bash
notebooklm login
notebooklm status   # must show "Authenticated as: ..."
```

The login flow opens a browser window and stores a session token locally. The skill checks authentication at startup and aborts if not authenticated.

### Claude Code

The skill runs inside [Claude Code](https://claude.ai/code) (CLI or desktop app). It uses the Agent tool to dispatch subagents and sub-subagents — this requires Claude Code's multi-agent execution environment.

### Python dependencies (for workspace scripts)

The workspace scripts (`references/scripts/`) require:

```bash
pip install -r requirements.txt
# or individually:
pip install certifi notebooklm-py
```

`certifi` provides a cross-platform CA certificate bundle so HTTPS URLs are
verified correctly on macOS, Linux, and Windows alike.

---

## Setup

```bash
# 1. Install notebooklm-py
pip install notebooklm-py

# 2. Authenticate
notebooklm login

# 3. Install the skill (if not already installed via npx skills)
# Place this directory at ~/.claude/skills/legal-research/
```

### Permissions (one-time)

The skill runs subagents that call `notebooklm` and `python3`. Claude Code needs
permission to run these commands without prompting mid-workflow.

Run once after installing the skill:

```bash
python3 ~/.claude/skills/legal-research/setup.py
```

Then **restart Claude Code**. You only need to do this once — subsequent runs are
fully automatic.

What it adds to `~/.claude/settings.json`:
- `Bash(notebooklm *)` — drives the NotebookLM CLI
- `Bash(python3 *)` — runs workspace and analysis scripts
- `Bash(open *)` — opens the HTML report on completion
- `Agent(*)` — allows the orchestrator to dispatch phase subagents

```bash
# 4. Verify
notebooklm status
python3 -m pytest ~/.claude/skills/legal-research/tests/ -v -m "not live"
```

---

## Usage

**New research session:**
```
/legal-research-py What is the severance pay entitlement for unjustified dismissal under Argentine labour law?
```

**Resume an interrupted session:**
```
/legal-research-py resume /path/to/research-workspaces/<slug>/state.json
```

The skill asks **one** confirmation question (scope review) and then runs fully autonomously. The HTML report is written to the workspace parent directory on completion.

---

## Output

- **HTML report** — structured legal memorandum with citations, verification status, and node coverage summary
- **Evidence Registry** — every source with tier, import status, queryability status, and article-level index results
- **state.json** — full workspace state; used for resume and audit

---

## Workspace layout

```
research-workspaces/
└── <slug>-<date>/
    └── state.json      ← schema-validated, updated after each phase
```

---

## Phases reference

| File | Handled by | Est. runtime |
|---|---|---|
| `references/phases/phase-3-research-curation.md` | Subagent A | 25–80 min |
| `references/phases/phase-4-import-and-verify.md` | Subagent B | 20–50 min |
| `references/phases/phase-5-analysis-and-verification.md` | Subagent D | 35–75 min |
| `references/phases/phase-6-report.md` | Subagent F | 15–35 min |

Total wall-clock: **~2–4 hours** depending on jurisdiction complexity and number of sources.

---

## How it differs from notebooklm-legal-research-rhino

| Aspect | rhino | hybrid (py) |
|---|---|---|
| Orchestrator size | ~1040 lines | ≤300 lines |
| Mid-run user prompts | 3 checkpoint halts | 0 |
| Phase execution | single long session | 4 fresh-context subagents |
| Phase 3 research | N queries × ~12 min serial | max(N queries) ≈ ~12–15 min parallel |
| Phase 4.1 spot-check | M sources × ~2 min serial | max(M sources) ≈ ~2–4 min parallel |
| State handoff | in-memory + JSON checkpoint | `state.json` (schema-validated) |
| Reference loading | most loaded upfront | per-subagent, on demand |

The original `notebooklm-legal-research-rhino` skill is untouched. If the hybrid misbehaves:
```
/notebooklm-legal-research-rhino <query>
```

---

## Tests

```bash
cd ~/.claude/skills/legal-research
python3 -m pytest -v -m "not live"   # 36 tests, ~2s
```

Key invariants enforced by the test suite:

- **Fidelity** (`test_phase_fidelity.py`) — every line from every original phase section must appear in a hybrid phase file. Catches accidental content loss during edits.
- **No halt directives** (`test_no_halt_directives.py`) — the hybrid must contain zero checkpoint-halt blocks. Autonomy is a hard constraint.
- **Orchestrator structure** (`test_orchestrator_structure.py`) — `SKILL.md` must stay ≤300 lines and must not contain phase content inline.

---

## License

MIT — see [LICENSE](LICENSE).
