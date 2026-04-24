# Phase 5 — Analysis & Verification

### Step 1: Draft Analysis
Execute IRAC sequence via `notebooklm ask`.

> **GATE 1: Analysis Complete.**
> **DO NOT PROCEED to Step 2 until all 5 notes (Issue, Rule, Application, Conclusion, Verification) have been successfully saved.**

### Step 2: Citation Verification
> **DEPENDENCY REQUIREMENT:** You must extract the citations strictly from the "Rule" and "Application" notes saved in Step 1. If those notes do not exist yet, you cannot perform this step.
Retrieve "Rule" and "Application" notes. 
Execute `notebooklm ask` with FOCUSED_VERIFICATION_PROMPT.

### Step 3: Mandatory Registry Cross-Check
Execute the validation script:
```bash
python3 "$SKILL_ROOT/references/scripts/cross_check_citations.py" "$WORKSPACE/state.json" /tmp/citation_log.txt > "$WORKSPACE/final_citation_log.txt"
```
