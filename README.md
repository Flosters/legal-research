# notebooklm-legal-research-hybrid

Hybrid agentic reincarnation of `notebooklm-legal-research-rhino`. Same quality
layers (verifiable checklist, evidence registry, crawlability checks, primary-source
import, citation verification, cross-examination) — but runs end-to-end autonomously
by dispatching fresh-context subagents for each phase.

## Installation

```bash
npx skills add <your-github-username>/notebooklm-legal-research-hybrid
```

Requires the [`notebooklm` CLI](https://github.com/your-github-username/notebooklm) authenticated.

## Layout

- `SKILL.md` — thin orchestrator
- `references/phases/` — one file per subagent
- `references/scripts/` — reusable Python helpers
- `references/schemas/` — JSON schema for workspace state
- `tests/` — pytest structural + integration tests
- `research-workspaces/` — per-session state (gitignored)

## Usage

```
/notebooklm-legal-research-hybrid new <your query>
/notebooklm-legal-research-hybrid resume /path/to/state.json
```

## How it differs from notebooklm-legal-research-rhino

| Aspect | rhino | hybrid |
|---|---|---|
| Orchestrator size | ~1040 lines | ≤300 lines |
| Mid-run user prompts | 3 checkpoint halts | 0 |
| Phase execution | single long session | 7 fresh-context subagents |
| State handoff | in-memory registry + JSON checkpoint | `state.json` (schema-validated) |
| Reference-file loading | most loaded upfront | loaded per-subagent on demand |

Every quality layer — verifiable checklist, evidence registry, crawlability
checks, primary-source import, citation verification, cross-examination — is
preserved verbatim. See `tests/test_phase_fidelity.py` for the enforcement.

## Rollback

The original `notebooklm-legal-research-rhino` skill is untouched. If the hybrid
misbehaves, use:

```
/notebooklm-legal-research-rhino <query>
```

## Test invariants

- `tests/test_phase_fidelity.py` — every line from every original phase section
  must appear in a hybrid phase file. Fails the build on accidental content loss.
- `tests/test_no_halt_directives.py` — hybrid skill must have zero halt blocks.
- `tests/test_orchestrator_structure.py` — SKILL.md must stay ≤300 lines and
  must not contain phase content.
