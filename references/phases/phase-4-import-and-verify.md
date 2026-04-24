# Phase 4 — Import & Verify

> **GATE 1: URL Resolution.** 
> Use `source-priority.md` to resolve official URLs for all cited primary sources.
> **DO NOT PROCEED to Step 2 until you have written the resolved URLs to state.json.**
> **DEPENDENCY REQUIREMENT:** Step 2 must read the file `/tmp/urls_${NB_ID}.txt` which you must generate using the URLs resolved in this step. Step 2 cannot be executed if this file is empty.

### Step 2: Batch Import
```bash
python3 "$SKILL_ROOT/references/scripts/batch-import.py" "$NB_ID" "/tmp/urls_${NB_ID}.txt"
```

> **GATE 2: Import Check.**
> **DO NOT PROCEED to Step 3 until batch-import completes.**

### Step 3: Spot Check
Execute spot checks for queryability (replace sub-subagents with script).
