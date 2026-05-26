# Phase 4 — Import & Verify

> **Environment variables available:** `WORKSPACE`, `SKILL_ROOT`, `NB_ID`
>
> **ABORT RULE — read this before executing any step:**
> - You are allowed to run ONLY the `python3` commands listed explicitly in this file.
> - If any script exits non-zero: return `error: <script name> failed: <stderr>` immediately. Stop. Do NOT debug, introspect, or retry.
> - NEVER copy from `.claude/projects/*/tool-results/` paths.
> - NEVER run `nslookup`, `curl`, `for`, `until`, `case`, `sleep`, or `cp` directly.
> - Do NOT use `inspect.signature()`, `python3 -c`, or any interactive introspection.

---

### Step 1: Extract URLs from Evidence Registry

Read the evidence registry from `$WORKSPACE/evidence_registry.json` (not from state.json).
Extract all source URLs by running:

```bash
python3 "$SKILL_ROOT/references/scripts/extract_urls.py" "$WORKSPACE" "$NB_ID" --output "/tmp/urls_${NB_ID}.txt"
```

Then consult `$SKILL_ROOT/references/source-priority.md`. For any Tier 1 sources where
the URL is a redirect or non-canonical form, update the URL in `/tmp/urls_${NB_ID}.txt`
to the official canonical form documented in source-priority.md.

Verify `/tmp/urls_${NB_ID}.txt` is non-empty before proceeding. If it is empty, return
`error: evidence_registry.json has no URLs`.

---

### Step 2: Batch Import

```bash
python3 "$SKILL_ROOT/references/scripts/batch-import.py" "$NB_ID" "/tmp/urls_${NB_ID}.txt" 2>&1 | tail -30
```

> **GATE: DO NOT PROCEED to Step 3 until batch-import exits with code 0.**
> If batch-import fails, return `error: batch-import failed` to the orchestrator.

---

### Step 3: Spot Check

Run the URL checker against the URL list already written in Step 1:

```bash
python3 "$SKILL_ROOT/references/scripts/check_urls.py" \
  "/tmp/urls_${NB_ID}.txt" \
  --timeout 10 \
  --fail-threshold 50 \
  --output "/tmp/spot_check_results_${NB_ID}.json"
```

Review `/tmp/spot_check_results_${NB_ID}.json`. For each source with `"ok": false`,
update `queryable_status` to `"not_queryable"` in `$WORKSPACE/evidence_registry.json`.

---

### Step 4: Advance state

```bash
python3 "$SKILL_ROOT/references/scripts/workspace.py" mark-complete "$WORKSPACE" 4 5
```
