# legal-research-py Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden the legal-research-py skill so the workflow runs uninterrupted and fails loudly on real errors rather than silently.

**Architecture:** Six independent, self-contained tasks. Each touches one file (or two — a script and its test). No task depends on another; they can be done in any order. Tasks 1–3 are TDD; Tasks 4–5 are doc-only edits; Task 6 stages untracked scripts that are already complete.

**Tech Stack:** Python 3 stdlib + certifi, pytest, notebooklm CLI. All tests run with `pytest tests/ -v -m "not live"`.

---

## Context

All paths below are relative to the skill root: `~/.claude/skills/legal-research/`.

Run the full test suite before starting to establish a baseline:

```bash
cd ~/.claude/skills/legal-research
python3 -m pytest tests/ -v -m "not live"
```

Expected: all existing tests pass (some pre-existing failures are known and out of scope).

---

## Task 1: Add `Bash(jq *)` to setup.py permissions

SKILL.md Phase 2 shells out `jq -r .scope.topic` inline. Without `Bash(jq *)` in the settings, Claude Code prompts for permission mid-Phase 2 — right after the user confirmed scope — breaking the autonomous run.

**Files:**
- Modify: `tests/test_setup.py:9-14`
- Modify: `setup.py:20-25`

### Step 1: Update the expected permissions list in the test

In `tests/test_setup.py`, the `REQUIRED_PERMISSIONS` list at line 9 is the source of truth for what `test_adds_all_required_permissions`, `test_idempotent`, and `test_returns_added_count` all assert. Add the new entry there:

```python
REQUIRED_PERMISSIONS = [
    "Bash(notebooklm *)",
    "Bash(python3 *)",
    "Bash(open *)",
    "Bash(jq *)",
    "Agent(*)",
]
```

### Step 2: Run tests to confirm they fail

```bash
python3 -m pytest tests/test_setup.py -v -m "not live"
```

Expected: `test_adds_all_required_permissions`, `test_idempotent`, and `test_returns_added_count` FAIL because `setup.py` doesn't have `Bash(jq *)` yet.

### Step 3: Add `Bash(jq *)` to setup.py

In `setup.py`, the `REQUIRED_PERMISSIONS` list at line 20:

```python
REQUIRED_PERMISSIONS = [
    "Bash(notebooklm *)",
    "Bash(python3 *)",
    "Bash(open *)",
    "Bash(jq *)",
    "Agent(*)",
]
```

### Step 4: Run tests to confirm they pass

```bash
python3 -m pytest tests/test_setup.py -v -m "not live"
```

Expected: all setup tests PASS.

### Step 5: Commit

```bash
git add setup.py tests/test_setup.py
git commit -m "feat: add Bash(jq *) to required permissions — prevents mid-Phase-2 prompt"
```

---

## Task 2: Fix `run_research.py` error handling

Two bugs:
1. `run_cmd` ignores non-zero exit codes — failures are silent, research proceeds with empty data.
2. The polling condition string-matches `"in_progress"/"pending"` in raw output — an error response containing either word is misidentified as "still running" and the query loops until the 60-attempt cap.

**Files:**
- Create: `tests/test_run_research.py`
- Modify: `references/scripts/run_research.py`

### Step 1: Create the test file

Create `tests/test_run_research.py`:

```python
"""Tests for run_research.py helper functions."""
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPT = Path(__file__).parent.parent / "references/scripts/run_research.py"


def _load():
    spec = importlib.util.spec_from_file_location("run_research", str(SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── run_cmd ──────────────────────────────────────────────────────────────────

def test_run_cmd_returns_stdout_on_success():
    mod = _load()
    fake = MagicMock(returncode=0, stdout="hello\n", stderr="")
    with patch("subprocess.run", return_value=fake):
        result = mod.run_cmd("echo hello")
    assert result == "hello"


def test_run_cmd_raises_on_nonzero_exit():
    mod = _load()
    fake = MagicMock(returncode=1, stdout="", stderr="something went wrong")
    with patch("subprocess.run", return_value=fake):
        try:
            mod.run_cmd("false")
            assert False, "Expected RuntimeError"
        except RuntimeError as exc:
            assert "something went wrong" in str(exc)


def test_run_cmd_check_false_does_not_raise():
    mod = _load()
    fake = MagicMock(returncode=1, stdout="partial output", stderr="err")
    with patch("subprocess.run", return_value=fake):
        result = mod.run_cmd("false", check=False)
    assert result == "partial output"


# ── is_still_pending ─────────────────────────────────────────────────────────

def test_is_still_pending_true_when_status_in_progress():
    mod = _load()
    payload = json.dumps({"status": "in_progress", "tasks": []})
    assert mod.is_still_pending(payload) is True


def test_is_still_pending_true_when_status_pending():
    mod = _load()
    payload = json.dumps({"status": "pending"})
    assert mod.is_still_pending(payload) is True


def test_is_still_pending_false_when_status_completed():
    mod = _load()
    payload = json.dumps({"status": "completed", "tasks": [{"sources": []}]})
    assert mod.is_still_pending(payload) is False


def test_is_still_pending_false_when_status_done():
    mod = _load()
    payload = json.dumps({"status": "done"})
    assert mod.is_still_pending(payload) is False


def test_is_still_pending_falls_back_to_string_match_on_bad_json():
    mod = _load()
    assert mod.is_still_pending("Research is in_progress...") is True
    assert mod.is_still_pending("All done.") is False


def test_is_still_pending_treats_error_response_as_not_pending():
    """An error JSON with no status/in_progress should NOT be treated as pending."""
    mod = _load()
    payload = json.dumps({"error": "notebook not found", "code": 404})
    assert mod.is_still_pending(payload) is False
```

### Step 2: Run tests to confirm they fail

```bash
python3 -m pytest tests/test_run_research.py -v
```

Expected: all tests FAIL — `run_cmd` doesn't have a `check` parameter yet and `is_still_pending` doesn't exist.

### Step 3: Rewrite `run_research.py`

Replace the entire file content with the version below. The logic is identical to the original; only `run_cmd` and polling are fixed, and `is_still_pending` is extracted as a testable function:

```python
import json
import subprocess
import sys
import time
from pathlib import Path


def run_cmd(cmd: str, check: bool = True) -> str:
    """Run a shell command. Returns stripped stdout. Raises RuntimeError on non-zero exit unless check=False."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed (exit {result.returncode}): {cmd}\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def is_still_pending(status_out: str) -> bool:
    """Return True if the notebooklm research status indicates work is still in progress."""
    try:
        data = json.loads(status_out)
        status = data.get("status", "")
        return status in ("in_progress", "pending", "running")
    except (json.JSONDecodeError, AttributeError, TypeError):
        # Unparseable output: fall back to substring match
        low = status_out.lower()
        return "in_progress" in low or ("pending" in low and "error" not in low)


def main():
    if len(sys.argv) < 2:
        print("Usage: run_research.py <workspace_dir>")
        sys.exit(1)

    workspace = Path(sys.argv[1])
    state_file = workspace / "state.json"

    with open(state_file) as f:
        state = json.load(f)

    nb_id = state.get("nb_id")
    queries = state.get("scope", {}).get("research_queries", [])

    print(f"Starting research for {len(queries)} queries...")

    temp_notebooks = []

    # 1. Create temp notebooks
    for i, q in enumerate(queries):
        query_id = q.get("query_id", i + 1)
        print(f"Creating temp notebook for Query {query_id}...")
        try:
            out = run_cmd(f"notebooklm create 'research-temp-q{query_id}-{nb_id}' --json")
            d = json.loads(out)
            t_nb_id = d.get("id") or d.get("notebook_id") or d.get("notebook", {}).get("id", "")
            temp_notebooks.append((query_id, t_nb_id, q.get("query", "")))
            time.sleep(2)
        except Exception as e:
            print(f"ERROR creating notebook for Query {query_id}: {e}", file=sys.stderr)
            raise

    try:
        # 2. Launch research in all temp notebooks
        for q_id, t_nb_id, q_text in temp_notebooks:
            print(f"Starting research for Query {q_id} in {t_nb_id}...")
            q_text_esc = q_text.replace("'", "'\\''")
            run_cmd(f"notebooklm source add-research '{q_text_esc}' --mode deep -n '{t_nb_id}'")

        # 3. Poll for completion (5-minute cap: 60 × 5s)
        pending = list(temp_notebooks)
        print("Polling for research completion...")
        attempts = 0
        while pending and attempts < 60:
            time.sleep(5)
            attempts += 1
            still_pending = []
            for item in pending:
                q_id, t_nb_id, q_text = item
                status_out = run_cmd(
                    f"notebooklm research status --json -n '{t_nb_id}'",
                    check=False,
                )
                if is_still_pending(status_out):
                    still_pending.append(item)
                else:
                    print(f"Query {q_id} completed.")
                    with open(f"/tmp/research_q{q_id}_{nb_id}.json", "w") as f:
                        f.write(status_out)
            pending = still_pending

        if pending:
            ids = [str(q_id) for q_id, _, _ in pending]
            raise RuntimeError(f"Research timed out after 5 minutes for queries: {', '.join(ids)}")

    finally:
        # 4. Cleanup temp notebooks (best-effort — don't fail the run if delete fails)
        for q_id, t_nb_id, q_text in temp_notebooks:
            print(f"Deleting temp notebook {t_nb_id}...")
            run_cmd(f"notebooklm delete -n '{t_nb_id}' -y", check=False)

    print("Research phase complete.")


if __name__ == "__main__":
    main()
```

### Step 4: Run tests to confirm they pass

```bash
python3 -m pytest tests/test_run_research.py -v
```

Expected: all 10 tests PASS.

### Step 5: Commit

```bash
git add references/scripts/run_research.py tests/test_run_research.py
git commit -m "fix: run_research raises on command failure; polling parses JSON status"
```

---

## Task 3: Add `--fail-threshold` to `check_urls.py`

Phase 4 Step 3 is advisory: the script always exits 0 and the subagent is supposed to read the JSON. In practice a subagent with a compressed context can silently pass the gate. Adding `--fail-threshold` makes the gate assertive — the subagent's `FAIL-FAST RULE` triggers automatically.

**Files:**
- Modify: `tests/test_check_urls.py`
- Modify: `references/scripts/check_urls.py`

### Step 1: Add three new tests to `tests/test_check_urls.py`

Append to the end of the existing file:

```python
def test_fail_threshold_exits_nonzero_when_exceeded():
    """With --fail-threshold 0, any failure triggers exit 1 (fail_pct > 0)."""
    r, _ = _run(
        ["http://definitely-does-not-exist-zzz.invalid"],
        ["--timeout", "2", "--fail-threshold", "0"],
    )
    assert r.returncode == 1


def test_fail_threshold_exits_zero_when_empty_url_list():
    """No URLs → 0% fail rate → exit 0 even with threshold=0."""
    r, _ = _run([], ["--fail-threshold", "0"])
    assert r.returncode == 0


def test_fail_threshold_not_set_preserves_exit_zero():
    """Omitting --fail-threshold keeps the existing always-exit-0 behaviour."""
    r, _ = _run(
        ["http://definitely-does-not-exist-zzz.invalid"],
        ["--timeout", "2"],
    )
    assert r.returncode == 0
```

### Step 2: Run new tests to confirm they fail

```bash
python3 -m pytest tests/test_check_urls.py::test_fail_threshold_exits_nonzero_when_exceeded \
                  tests/test_check_urls.py::test_fail_threshold_exits_zero_when_empty_url_list \
                  tests/test_check_urls.py::test_fail_threshold_not_set_preserves_exit_zero \
                  -v --timeout 10
```

Expected: first two FAIL (no `--fail-threshold` argument exists yet); third PASS (already passes since default is exit 0).

### Step 3: Add `--fail-threshold` to `check_urls.py`

In `references/scripts/check_urls.py`, make three changes:

**1. Update the docstring** (line 7) to mention the new flag:

```python
"""URL accessibility checker for Phase 4 spot-checks.

Usage:
    python3 check_urls.py <urls_file> [--timeout 10] [--output /tmp/url_check.json]
                          [--fail-threshold N]

Reads one URL per line from <urls_file>, sends HEAD requests, and reports HTTP
status codes.  Writes a JSON summary to --output (default: /tmp/url_check_results.json).
Exits 0 by default.  With --fail-threshold N, exits 1 if the percentage of failed
URLs exceeds N (0 = fail if any URL fails; 99 = fail only if almost all fail).
"""
```

**2. Add the argument to the parser** after the `--output` line (currently line 38):

```python
    ap.add_argument(
        "--fail-threshold",
        type=int,
        default=None,
        metavar="N",
        help="Exit 1 if fail%% > N (0–100). Omit to always exit 0.",
    )
```

**3. Add the threshold check** at the end of `main()`, replacing the final `print(...)` line:

```python
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count
    print(f"\n{ok_count}/{len(results)} URLs accessible. Results: {out_path}")

    if args.fail_threshold is not None and results:
        fail_pct = (fail_count / len(results)) * 100
        if fail_pct > args.fail_threshold:
            print(
                f"FAIL: {fail_count}/{len(results)} URLs failed ({fail_pct:.0f}% > threshold {args.fail_threshold}%)",
                file=sys.stderr,
            )
            sys.exit(1)
```

The complete updated `main()` looks like:

```python
def main() -> None:
    ap = argparse.ArgumentParser(description="Check URL accessibility")
    ap.add_argument("urls_file", help="Text file with one URL per line")
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--output", default="/tmp/url_check_results.json")
    ap.add_argument(
        "--fail-threshold",
        type=int,
        default=None,
        metavar="N",
        help="Exit 1 if fail%% > N (0–100). Omit to always exit 0.",
    )
    args = ap.parse_args()

    urls_path = Path(args.urls_file)
    if not urls_path.exists():
        print(f"ERROR: {urls_path} not found", file=sys.stderr)
        sys.exit(1)

    urls = [u.strip() for u in urls_path.read_text().splitlines() if u.strip() and not u.startswith("#")]
    results = []
    for url in urls:
        r = check_url(url, args.timeout)
        status_str = r.get("error", str(r["status"]))
        flag = "OK" if r["ok"] else "FAIL"
        print(f"{flag} {status_str:>6}  {url}")
        results.append(r)

    out_path = Path(args.output)
    out_path.write_text(json.dumps(results, indent=2))

    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count
    print(f"\n{ok_count}/{len(results)} URLs accessible. Results: {out_path}")

    if args.fail_threshold is not None and results:
        fail_pct = (fail_count / len(results)) * 100
        if fail_pct > args.fail_threshold:
            print(
                f"FAIL: {fail_count}/{len(results)} URLs failed ({fail_pct:.0f}% > threshold {args.fail_threshold}%)",
                file=sys.stderr,
            )
            sys.exit(1)
```

### Step 4: Run all check_urls tests

```bash
python3 -m pytest tests/test_check_urls.py -v --timeout 15
```

Expected: all tests PASS including the three new ones.

### Step 5: Update Phase 4 step 3 in the phase file to pass `--fail-threshold`

In `references/phases/phase-4-import-and-verify.md`, update the Step 3 script block. Find:

```
python3 "$SKILL_ROOT/references/scripts/check_urls.py" \
  "/tmp/spot_check_urls_${NB_ID}.txt" \
  --timeout 10 \
  --output "/tmp/spot_check_results_${NB_ID}.json"
```

Replace with:

```
python3 "$SKILL_ROOT/references/scripts/check_urls.py" \
  "/tmp/spot_check_urls_${NB_ID}.txt" \
  --timeout 10 \
  --fail-threshold 50 \
  --output "/tmp/spot_check_results_${NB_ID}.json"
```

This makes the gate assertive: if more than half the sources are unreachable the subagent's `FAIL-FAST RULE` triggers automatically.

### Step 6: Commit

```bash
git add references/scripts/check_urls.py tests/test_check_urls.py \
        references/phases/phase-4-import-and-verify.md
git commit -m "feat: add --fail-threshold to check_urls; phase 4 uses threshold 50"
```

---

## Task 4: Phase 4 Step 3 — reuse the URL file from Step 1

Step 1 and Step 3 of Phase 4 both call `extract_urls.py` to produce a URL list from the same evidence registry. Step 3 should reuse the Step 1 output.

**Files:**
- Modify: `references/phases/phase-4-import-and-verify.md`

> **Note:** If you completed Task 3 Step 5 above, Task 3 already modified this file. Apply this edit on top.

### Step 1: Edit Step 3 in phase-4-import-and-verify.md

Find the Step 3 block (currently calling extract_urls.py a second time):

```bash
python3 "$SKILL_ROOT/references/scripts/extract_urls.py" "$WORKSPACE" "$NB_ID" --output "/tmp/spot_check_urls_${NB_ID}.txt"

python3 "$SKILL_ROOT/references/scripts/check_urls.py" \
```

Replace with (drop the extract_urls.py call, reuse the Step 1 file):

```bash
python3 "$SKILL_ROOT/references/scripts/check_urls.py" \
  "/tmp/urls_${NB_ID}.txt" \
  --timeout 10 \
  --fail-threshold 50 \
  --output "/tmp/spot_check_results_${NB_ID}.json"
```

Also update the line just above the code block (the prose describing what will happen) from any reference to "extract URLs" / "temporary file" to simply:

> Run the URL checker against the URL list already written in Step 1:

### Step 2: Commit

```bash
git add references/phases/phase-4-import-and-verify.md
git commit -m "refactor: phase 4 step 3 reuses url list from step 1, no redundant extract"
```

> **Note:** If you committed the `--fail-threshold` change in Task 3 Step 6 and this file was already staged, you may have already committed this. If so, skip this commit.

---

## Task 5: Remove phantom "3.7" from SKILL.md dispatch table comment

The working-tree changes to phase-3-research-curation.md advance state from `3.6` directly to `4`, eliminating phase 3.7. The SKILL.md comment still lists it, which will confuse subagents reading the dispatch table.

**Files:**
- Modify: `SKILL.md`

### Step 1: Edit the comment in SKILL.md

Find the line (currently after the dispatch table):

```
Dispatch table phase IDs: 3-curation, 3.7, 4-indexing, 5, 5.5, 5.6, 6.
```

Replace with:

```
Dispatch table phase IDs: 3-curation, 4-indexing, 5, 5.5, 5.6, 6.
```

### Step 2: Commit

```bash
git add SKILL.md
git commit -m "docs: remove phantom 3.7 from dispatch table comment — phase skipped in refactor"
```

---

## Task 6: Commit untracked scripts

`run_research.py` (after Task 2 edits) and `extract_urls.py` are both untracked. They are load-bearing for Phases 3 and 4 respectively. Without them the repo cannot be cloned and used.

Also commit any files in `docs/` that are untracked (the `docs/plans/` directory including this plan file).

**Files:**
- Add: `references/scripts/extract_urls.py`
- Add: `references/scripts/run_research.py` (already handled in Task 2 commit if done)
- Add: `docs/` (new directory + any plan files)

### Step 1: Check what's untracked

```bash
git status --short
```

Expected to see `??` entries for `references/scripts/extract_urls.py`, `references/scripts/run_research.py` (if not yet committed in Task 2), and `docs/`.

### Step 2: Stage and commit

If `run_research.py` was already committed in Task 2, omit it here:

```bash
git add references/scripts/extract_urls.py docs/
git commit -m "chore: commit extract_urls.py and docs/ — were untracked after refactor"
```

If `run_research.py` was NOT committed yet (Task 2 skipped or reordered):

```bash
git add references/scripts/extract_urls.py references/scripts/run_research.py docs/
git commit -m "chore: commit extract_urls, run_research, docs/ — untracked after refactor"
```

---

## Final verification

Run the full test suite to confirm nothing regressed:

```bash
python3 -m pytest tests/ -v -m "not live"
```

Then verify the settings permissions are correct end-to-end:

```bash
python3 ~/.claude/skills/legal-research/setup.py --check
```

Expected: `Permissions OK.`

If it exits 1, run:

```bash
python3 ~/.claude/skills/legal-research/setup.py
```

Then restart Claude Code.
