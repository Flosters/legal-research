# notebooklm-legal-research-hybrid

Hybrid agentic reincarnation of `notebooklm-legal-research-rhino`. Same quality
layers; autonomous end-to-end; subagent-per-phase. See
`/Users/agustinsilvazambrano/docs/plans/2026-04-22-notebooklm-legal-research-hybrid-migration.md`.

## Layout

- `SKILL.md` — thin orchestrator
- `references/phases/` — one file per subagent
- `references/scripts/` — reusable Python helpers
- `references/schemas/` — JSON schema for workspace state
- `tests/` — pytest structural + integration tests
- `research-workspaces/` — per-session state (gitignored)
