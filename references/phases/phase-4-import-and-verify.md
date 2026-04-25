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

Write the URLs from the Evidence Registry to a temporary file, one URL per line, then
run the URL checker script.  **Do NOT use bash arrays (`arr=(...)`, `${arr[@]}`);
do NOT use `python3 -c "..."` with inline `#` comments — both cause tool errors.**

```bash
SKILL_WORKSPACE="$WORKSPACE" SKILL_NB_ID="$NB_ID" python3 - << 'PYEOF'
import json, os, pathlib
workspace = os.environ["SKILL_WORKSPACE"]
nb_id = os.environ["SKILL_NB_ID"]
state = json.loads(pathlib.Path(workspace + "/state.json").read_text())
reg = state.get("evidence_registry", [])
if isinstance(reg, str):
    reg = json.loads(reg)
urls = [e["url"] for e in (reg if isinstance(reg, list) else []) if e.get("url")]
out = f"/tmp/spot_check_urls_{nb_id}.txt"
pathlib.Path(out).write_text("\n".join(urls))
print(f"Wrote {len(urls)} URLs to {out}")
PYEOF

python3 "$SKILL_ROOT/references/scripts/check_urls.py" \
  "/tmp/spot_check_urls_${NB_ID}.txt" \
  --timeout 10 \
  --output "/tmp/spot_check_results_${NB_ID}.json"
```

Review `/tmp/spot_check_results_$NB_ID.json`.  Sources with `"ok": false` should be
flagged with `queryable_status: "not_queryable"` in the Evidence Registry before
proceeding.
