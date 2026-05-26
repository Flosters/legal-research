# Notebook Source Deduplication Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Prevent the main NotebookLM notebook from accumulating duplicate and uncurated sources by isolating all research writes to temp notebooks, making batch import idempotent, hardening Phase 3 agent instructions, and adding an orchestrator guard before Phase 4.

**Architecture:** Four independent tasks in dependency order. Tasks 1 and 2 are TDD (script changes + new tests). Tasks 3 and 4 are documentation edits (no new code). The main notebook must remain empty until Phase 4 batch-import runs — that invariant is enforced by all four tasks working together.

**Tech Stack:** Python 3 stdlib, argparse, pytest, `notebooklm` CLI (`source list --json`, `source add-research`, `delete`). All tests run with `pytest tests/ -v -m "not live"` from the skill root.

---

## Context

All paths are relative to the skill root: `~/.claude/skills/legal-research/`.

The `notebooklm source list -n "$NB_ID" --json` command returns a JSON array of source objects, each with a `"url"` field (empty string for non-URL sources like uploaded files).

Run the baseline before starting:

```bash
cd ~/.claude/skills/legal-research
python3 -m pytest tests/ -q -m "not live"
```

There are 15 pre-existing failures in `test_phase_fidelity.py` and `test_setup.py` — these are out of scope and must remain unchanged after our work.

---

## Task 1: Extend `run_research.py` with a gap-query mode (Fix 1)

**Problem:** Phase 3.6 gap searches run `notebooklm source add-research -n "$NB_ID"` directly against the main notebook. They should go through a temp notebook like the 5 main queries do.

**Solution:** Add a `--gap-query / --nb-id / --out` CLI mode to `run_research.py` that creates a temp notebook, runs the query, saves the result JSON, and deletes the temp notebook — never touching the main notebook.

**Files:**
- Modify: `references/scripts/run_research.py`
- Modify: `tests/test_run_research.py`

---

### Step 1: Write the failing tests

Append to `tests/test_run_research.py`:

```python
import argparse
import tempfile
from pathlib import Path


# ── run_gap_query ─────────────────────────────────────────────────────────────

def test_run_gap_query_creates_temp_notebook_with_query():
    """Temp notebook is created, add-research called on it (not main nb), then deleted."""
    mod = _load()
    calls = []

    def fake_run_cmd(cmd, check=True):
        calls.append(cmd)
        if "create" in cmd:
            return '{"id": "temp-nb-123"}'
        if "research status" in cmd:
            return '{"status": "done"}'
        return ""

    with patch.object(mod, "run_cmd", side_effect=fake_run_cmd), \
         patch.object(mod, "time") as mock_time:
        mock_time.sleep = lambda _: None
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out_path = f.name
        mod.run_gap_query("OFAC sanctions list", "main-nb-456", out_path)

    add_research_calls = [c for c in calls if "add-research" in c]
    assert len(add_research_calls) == 1
    assert "temp-nb-123" in add_research_calls[0]
    assert "main-nb-456" not in add_research_calls[0]


def test_run_gap_query_saves_status_to_out_path():
    """Status JSON is written to the --out path."""
    mod = _load()

    def fake_run_cmd(cmd, check=True):
        if "create" in cmd:
            return '{"id": "temp-nb-abc"}'
        if "research status" in cmd:
            return '{"status": "done", "sources": [{"url": "https://ofac.treasury.gov"}]}'
        return ""

    with patch.object(mod, "run_cmd", side_effect=fake_run_cmd), \
         patch.object(mod, "time") as mock_time:
        mock_time.sleep = lambda _: None
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out_path = f.name
        mod.run_gap_query("sanctions", "main-nb-456", out_path)

    content = Path(out_path).read_text()
    assert "ofac.treasury.gov" in content


def test_run_gap_query_deletes_temp_notebook_on_success():
    """Temp notebook is deleted after successful completion."""
    mod = _load()
    calls = []

    def fake_run_cmd(cmd, check=True):
        calls.append(cmd)
        if "create" in cmd:
            return '{"id": "temp-nb-xyz"}'
        if "research status" in cmd:
            return '{"status": "done"}'
        return ""

    with patch.object(mod, "run_cmd", side_effect=fake_run_cmd), \
         patch.object(mod, "time") as mock_time:
        mock_time.sleep = lambda _: None
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out_path = f.name
        mod.run_gap_query("sanctions", "main-nb-456", out_path)

    delete_calls = [c for c in calls if "delete" in c and "temp-nb-xyz" in c]
    assert len(delete_calls) == 1


def test_run_gap_query_deletes_temp_notebook_on_error():
    """Temp notebook is deleted even when add-research raises."""
    mod = _load()
    calls = []

    def fake_run_cmd(cmd, check=True):
        calls.append(cmd)
        if "create" in cmd:
            return '{"id": "temp-nb-err"}'
        if "add-research" in cmd and check:
            raise RuntimeError("network error")
        return ""

    with patch.object(mod, "run_cmd", side_effect=fake_run_cmd), \
         patch.object(mod, "time") as mock_time:
        mock_time.sleep = lambda _: None
        try:
            mod.run_gap_query("sanctions", "main-nb-456", "/tmp/out.json")
        except RuntimeError:
            pass

    delete_calls = [c for c in calls if "delete" in c and "temp-nb-err" in c]
    assert len(delete_calls) == 1


# ── main — gap mode ───────────────────────────────────────────────────────────

def test_main_invokes_gap_mode_with_flags(tmp_path):
    """main() calls run_gap_query when --gap-query flag is present."""
    mod = _load()
    out_file = tmp_path / "gap.json"
    invoked = []

    def fake_gap(query, nb_id, out_path):
        invoked.append((query, nb_id, out_path))

    with patch.object(mod, "run_gap_query", side_effect=fake_gap), \
         patch("sys.argv", ["run_research.py",
                            "--gap-query", "EU sanctions list",
                            "--nb-id", "nb-999",
                            "--out", str(out_file)]):
        mod.main()

    assert len(invoked) == 1
    assert invoked[0] == ("EU sanctions list", "nb-999", str(out_file))


def test_main_workspace_mode_still_works(tmp_path):
    """main() still reads workspace queries and creates temp notebooks when no --gap-query."""
    mod = _load()
    state = {
        "nb_id": "main-nb-001",
        "scope": {"research_queries": [{"query_id": 1, "query": "OFAC SDN list"}]}
    }
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "state.json").write_text(__import__("json").dumps(state))

    calls = []
    def fake_run_cmd(cmd, check=True):
        calls.append(cmd)
        if "create" in cmd:
            return '{"id": "temp-nb-ws"}'
        if "research status" in cmd:
            return '{"status": "done"}'
        return ""

    with patch.object(mod, "run_cmd", side_effect=fake_run_cmd), \
         patch.object(mod, "time") as mock_time, \
         patch("sys.argv", ["run_research.py", str(ws)]):
        mock_time.sleep = lambda _: None
        mod.main()

    create_calls = [c for c in calls if "create" in c and "research-temp-q" in c]
    assert len(create_calls) == 1
```

**Step 2: Run the tests to verify they fail**

```bash
cd ~/.claude/skills/legal-research
python3 -m pytest tests/test_run_research.py -v -k "gap" 2>&1 | tail -20
```

Expected: all 6 new tests FAIL with `AttributeError: module 'run_research' has no attribute 'run_gap_query'` (or similar).

---

### Step 3: Implement `run_gap_query` and update `main()` in `run_research.py`

Replace the entire file `references/scripts/run_research.py` with:

```python
import argparse
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
        low = status_out.lower()
        return "in_progress" in low or ("pending" in low and "error" not in low)


def run_gap_query(query: str, nb_id: str, out_path: str) -> None:
    """Run a single gap query through a temp notebook; never touches the main notebook."""
    gap_nb_id = ""
    try:
        out = run_cmd(f"notebooklm create 'research-temp-gap-{nb_id}' --json")
        d = json.loads(out)
        gap_nb_id = d.get("id") or d.get("notebook_id") or d.get("notebook", {}).get("id", "")
        time.sleep(2)

        q_esc = query.replace("'", "'\\''")
        run_cmd(f"notebooklm source add-research '{q_esc}' --mode deep -n '{gap_nb_id}'")

        attempts = 0
        while attempts < 60:
            time.sleep(5)
            attempts += 1
            status_out = run_cmd(
                f"notebooklm research status --json -n '{gap_nb_id}'", check=False
            )
            if not is_still_pending(status_out):
                Path(out_path).write_text(status_out)
                print("Gap query completed.")
                return

        raise RuntimeError("Gap query timed out after 5 minutes")
    finally:
        if gap_nb_id:
            run_cmd(f"notebooklm delete -n '{gap_nb_id}' -y", check=False)


def main():
    parser = argparse.ArgumentParser(description="Run NotebookLM research queries.")
    parser.add_argument("workspace", nargs="?", help="Workspace directory (normal mode)")
    parser.add_argument("--gap-query", help="Single query text (gap mode)")
    parser.add_argument("--nb-id", help="Main notebook ID (gap mode only)")
    parser.add_argument("--out", help="Output JSON path (gap mode only)")
    args = parser.parse_args()

    if args.gap_query:
        if not args.nb_id or not args.out:
            print("--nb-id and --out are required with --gap-query", file=sys.stderr)
            sys.exit(1)
        run_gap_query(args.gap_query, args.nb_id, args.out)
        return

    if not args.workspace:
        print("Usage: run_research.py <workspace_dir>", file=sys.stderr)
        sys.exit(1)

    workspace = Path(args.workspace)
    state_file = workspace / "state.json"

    with open(state_file) as f:
        state = json.load(f)

    nb_id = state.get("nb_id")
    queries = state.get("scope", {}).get("research_queries", [])

    print(f"Starting research for {len(queries)} queries...")

    temp_notebooks = []

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
        for q_id, t_nb_id, q_text in temp_notebooks:
            print(f"Starting research for Query {q_id} in {t_nb_id}...")
            q_text_esc = q_text.replace("'", "'\\''")
            run_cmd(f"notebooklm source add-research '{q_text_esc}' --mode deep -n '{t_nb_id}'")

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
        for q_id, t_nb_id, q_text in temp_notebooks:
            print(f"Deleting temp notebook {t_nb_id}...")
            run_cmd(f"notebooklm delete -n '{t_nb_id}' -y", check=False)

    print("Research phase complete.")


if __name__ == "__main__":
    main()
```

**Step 4: Run the tests and verify they pass**

```bash
cd ~/.claude/skills/legal-research
python3 -m pytest tests/test_run_research.py -v 2>&1 | tail -20
```

Expected: all tests PASS (including the 8 pre-existing ones plus the 6 new ones).

**Step 5: Commit**

```bash
cd ~/.claude/skills/legal-research
git add references/scripts/run_research.py tests/test_run_research.py
git commit -m "feat: add gap-query mode to run_research.py so gap searches use temp notebooks"
```

---

## Task 2: Make `batch-import.py` idempotent (Fix 2)

**Problem:** `batch-import.py` adds all curated URLs unconditionally. On retry or resume, it duplicates whatever was already imported.

**Solution:** Before crawling, fetch existing source URLs from the notebook and skip any that are already present.

**Files:**
- Modify: `references/scripts/batch-import.py`
- Create: `tests/test_batch_import.py`

---

### Step 1: Write the failing tests

Create `tests/test_batch_import.py`:

```python
"""Tests for batch-import.py idempotent import logic."""
import importlib.util
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPT = Path(__file__).parent.parent / "references/scripts/batch-import.py"


def _load():
    spec = importlib.util.spec_from_file_location("batch_import", str(SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── get_existing_urls ─────────────────────────────────────────────────────────

def test_get_existing_urls_returns_set_of_urls():
    mod = _load()
    sources = [
        {"url": "https://ofac.treasury.gov/sanctions-list"},
        {"url": "https://eur-lex.europa.eu/regulation"},
    ]
    fake = MagicMock(returncode=0, stdout=json.dumps(sources))
    with patch("subprocess.run", return_value=fake):
        result = mod.get_existing_urls("nb-123")
    assert result == {
        "https://ofac.treasury.gov/sanctions-list",
        "https://eur-lex.europa.eu/regulation",
    }


def test_get_existing_urls_ignores_entries_without_url():
    mod = _load()
    sources = [{"url": "https://ofac.treasury.gov"}, {"title": "Uploaded PDF", "url": ""}]
    fake = MagicMock(returncode=0, stdout=json.dumps(sources))
    with patch("subprocess.run", return_value=fake):
        result = mod.get_existing_urls("nb-123")
    assert result == {"https://ofac.treasury.gov"}


def test_get_existing_urls_returns_empty_set_on_cli_error():
    mod = _load()
    fake = MagicMock(returncode=1, stdout="", stderr="not found")
    with patch("subprocess.run", return_value=fake):
        result = mod.get_existing_urls("nb-123")
    assert result == set()


def test_get_existing_urls_returns_empty_set_on_bad_json():
    mod = _load()
    fake = MagicMock(returncode=0, stdout="not-json")
    with patch("subprocess.run", return_value=fake):
        result = mod.get_existing_urls("nb-123")
    assert result == set()


def test_get_existing_urls_returns_empty_set_on_exception():
    mod = _load()
    with patch("subprocess.run", side_effect=Exception("timeout")):
        result = mod.get_existing_urls("nb-123")
    assert result == set()


# ── main — skip existing ──────────────────────────────────────────────────────

def test_main_skips_already_imported_urls(tmp_path):
    """URLs already in the notebook are not re-imported."""
    import asyncio
    mod = _load()

    already_in_nb = {"https://ofac.treasury.gov/already-there"}
    new_url = "https://eur-lex.europa.eu/new-source"

    with patch.object(mod, "get_existing_urls", return_value=already_in_nb), \
         patch.object(mod, "is_crawlable", return_value=(True, "html (5000 bytes)")):

        client_mock = MagicMock()
        client_mock.__aenter__ = lambda s: asyncio.coroutine(lambda: client_mock)()
        client_mock.__aexit__ = lambda s, *a: asyncio.coroutine(lambda: None)()
        client_mock.sources.add_url = asyncio.coroutine(lambda nb, url: None)

        with patch("notebooklm.NotebookLMClient.from_storage",
                   return_value=asyncio.coroutine(lambda: client_mock)()):
            result = asyncio.run(mod.main(
                "nb-test",
                ["https://ofac.treasury.gov/already-there", new_url]
            ))

    assert "https://ofac.treasury.gov/already-there" not in result["imported"]
    assert new_url in result["imported"] or new_url in [s["url"] for s in result.get("skipped", [])]
```

**Step 2: Run the tests to verify they fail**

```bash
cd ~/.claude/skills/legal-research
python3 -m pytest tests/test_batch_import.py -v 2>&1 | tail -20
```

Expected: all tests FAIL with `AttributeError: module 'batch_import' has no attribute 'get_existing_urls'`.

---

### Step 3: Add `get_existing_urls` and wire it into `main()` in `batch-import.py`

Replace `references/scripts/batch-import.py` with:

```python
#!/usr/bin/env python3
"""Batch-import URLs into a NotebookLM notebook using the async Python API.
Usage: python3 batch-import.py <notebook_id> <url_list_file>
"""
import asyncio, json, subprocess, sys
from pathlib import Path
from notebooklm import NotebookLMClient
from notebooklm.exceptions import RateLimitError

CONCURRENCY = 5
RATE_LIMIT_BACKOFF = 30
MIN_BODY_BYTES = 2000


def get_existing_urls(nb_id: str) -> set:
    """Return the set of URLs already in the notebook. Returns empty set on any error."""
    try:
        result = subprocess.run(
            ["notebooklm", "source", "list", "-n", nb_id, "--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return set()
        sources = json.loads(result.stdout)
        if isinstance(sources, list):
            return {s.get("url", "") for s in sources if s.get("url")}
        return set()
    except Exception:
        return set()


def is_crawlable(url: str) -> tuple[bool, str]:
    """Return (ok, reason). Checks Content-Type and body size for HTML pages."""
    try:
        head = subprocess.run(
            ["curl", "-sI", "--max-time", "10", url],
            capture_output=True, text=True, timeout=15
        )
        lines = head.stdout.splitlines()
        if not lines:
            return False, "empty-response"
        import re
        status_match = re.search(r"HTTP/[0-9.]+\s+([45]\d\d)", lines[0])
        if status_match:
            return False, f"http-error: {status_match.group(1)}"

        ct_line = next((l for l in lines if "content-type" in l.lower()), "")
        if "application/pdf" in ct_line.lower():
            return True, "pdf"
        if "text/html" in ct_line.lower():
            body = subprocess.run(
                ["curl", "-sL", "--max-time", "15", url],
                capture_output=True, timeout=20
            )
            size = len(body.stdout)
            if size < MIN_BODY_BYTES:
                return False, f"html-shell ({size} bytes)"
            return True, f"html ({size} bytes)"
        return True, f"other ({ct_line.strip()})"
    except Exception as e:
        return False, f"check-error: {e}"


async def main(nb_id, urls):
    imported, failed, skipped = [], [], []

    existing = get_existing_urls(nb_id)
    if existing:
        print(f"SKIP-EXISTING  {len(existing)} URLs already in notebook", flush=True)

    deduped = []
    for url in urls:
        if url in existing:
            skipped.append({"url": url, "reason": "already-in-notebook"})
            print(f"SKIP-DUP  {url}  [already-in-notebook]", flush=True)
        else:
            deduped.append(url)

    crawlable = []
    for url in deduped:
        ok, reason = is_crawlable(url)
        if ok:
            crawlable.append(url)
            print(f"CRAWL-OK  {url}  [{reason}]", flush=True)
        else:
            skipped.append({"url": url, "reason": reason})
            print(f"SKIP      {url}  [{reason}] — apply URL resolution rules from Phase 3.7 B1", flush=True)

    sem = asyncio.Semaphore(CONCURRENCY)
    async with await NotebookLMClient.from_storage() as client:
        async def add_one(url):
            async with sem:
                try:
                    await client.sources.add_url(nb_id, url)
                    imported.append(url)
                    print(f"OK  {url}", flush=True)
                except RateLimitError as e:
                    retry = getattr(e, "retry_after", None) or RATE_LIMIT_BACKOFF
                    print(f"429 {url} — backing off {retry}s", flush=True)
                    await asyncio.sleep(retry)
                    try:
                        await client.sources.add_url(nb_id, url)
                        imported.append(url)
                        print(f"OK  {url} (retry)", flush=True)
                    except Exception as e2:
                        failed.append({"url": url, "error": str(e2)})
                        print(f"ERR {url}: {e2}", flush=True)
                except Exception as e:
                    failed.append({"url": url, "error": str(e)})
                    print(f"ERR {url}: {e}", flush=True)
        await asyncio.gather(*[add_one(u) for u in crawlable])
    return {"imported": imported, "failed": failed, "skipped": skipped}


if __name__ == "__main__":
    nb_id = sys.argv[1]
    urls = [u.strip() for u in Path(sys.argv[2]).read_text().splitlines() if u.strip()]
    result = asyncio.run(main(nb_id, urls))
    print(json.dumps(result))
```

**Step 4: Run the tests and verify they pass**

```bash
cd ~/.claude/skills/legal-research
python3 -m pytest tests/test_batch_import.py -v 2>&1 | tail -20
```

Expected: all tests PASS.

**Step 5: Run the full suite and confirm pre-existing failure count is unchanged**

```bash
cd ~/.claude/skills/legal-research
python3 -m pytest tests/ -q -m "not live" 2>&1 | tail -5
```

Expected: same 15 failures as baseline; our new tests all pass.

**Step 6: Commit**

```bash
cd ~/.claude/skills/legal-research
git add references/scripts/batch-import.py tests/test_batch_import.py
git commit -m "feat: make batch-import.py idempotent by skipping already-imported URLs"
```

---

## Task 3: Add explicit prohibition to Phase 3 instructions (Fix 4)

**Problem:** The ABORT RULE bans unlisted commands in the abstract, but `add-research` appears later in the file (Phase 3.6), so agents rationalize they can use it on the main notebook too.

**Solution:** Name the forbidden pattern explicitly, by notebook ID.

**Files:**
- Modify: `references/phases/phase-3-research-curation.md`

---

### Step 1: Add the prohibition to the ABORT RULE block

Find this block in `references/phases/phase-3-research-curation.md` (lines ~17–24):

```markdown
> **ABORT RULE — read this before executing any step:**
> - You are allowed to run ONLY commands listed explicitly in this file.
> - If `run_research.py` exits non-zero, return `error: run_research.py failed: <stderr>` immediately. Do NOT check for files. Do NOT run `notebooklm` commands manually. Do NOT try to poll, retry, or diagnose.
> - NEVER copy from `.claude/projects/*/tool-results/` paths — those files are ephemeral session internals.
> - NEVER run `nslookup`, `curl`, `for`, `until`, `case`, `sleep`, or `cp` directly. All multi-step logic must go through the provided Python scripts.
> - If any script exits non-zero: return `error: <script name> failed` to the orchestrator and stop.
```

Replace with (adding the new prohibition line after the first bullet):

```markdown
> **ABORT RULE — read this before executing any step:**
> - You are allowed to run ONLY commands listed explicitly in this file.
> - **FORBIDDEN:** `notebooklm source add-research ... -n "$NB_ID"` — never call `add-research` against the main notebook ID (`$NB_ID`) in Phase 3. The main notebook must remain empty until Phase 4. The ONLY permitted way to run research queries — including gap searches — is `python3 "$SKILL_ROOT/references/scripts/run_research.py"`. Violating this will silently corrupt the notebook with hundreds of uncurated duplicates.
> - If `run_research.py` exits non-zero, return `error: run_research.py failed: <stderr>` immediately. Do NOT check for files. Do NOT run `notebooklm` commands manually. Do NOT try to poll, retry, or diagnose.
> - NEVER copy from `.claude/projects/*/tool-results/` paths — those files are ephemeral session internals.
> - NEVER run `nslookup`, `curl`, `for`, `until`, `case`, `sleep`, or `cp` directly. All multi-step logic must go through the provided Python scripts.
> - If any script exits non-zero: return `error: <script name> failed` to the orchestrator and stop.
```

### Step 2: Update the Phase 3.6 gap search command

Find the gap search bash block (around line 100–103):

```bash
notebooklm source add-research "[targeted query for the gap — in jurisdiction language]" --mode deep -n "$NB_ID"
notebooklm research status --json -n "$NB_ID" > /tmp/research_gap_$NB_ID.json
```

Replace with:

```bash
python3 "$SKILL_ROOT/references/scripts/run_research.py" \
  --gap-query "[targeted query for the gap — in jurisdiction language]" \
  --nb-id "$NB_ID" \
  --out "/tmp/research_gap_$NB_ID.json"
```

### Step 3: Verify the file looks right

```bash
grep -n "FORBIDDEN\|gap-query\|add-research" \
  ~/.claude/skills/legal-research/references/phases/phase-3-research-curation.md
```

Expected output:
```
19:> - **FORBIDDEN:** `notebooklm source add-research ... -n "$NB_ID"` — never call...
101:python3 "$SKILL_ROOT/references/scripts/run_research.py" \
102:  --gap-query "[targeted query for the gap — in jurisdiction language]" \
```

### Step 4: Commit

```bash
cd ~/.claude/skills/legal-research
git add references/phases/phase-3-research-curation.md
git commit -m "docs: forbid add-research on main notebook in Phase 3; route gap searches through run_research.py"
```

---

## Task 4: Add orchestrator guard after Phase 3 (Fix 5)

**Problem:** Even with Fix 1 and Fix 4, agent deviation could still write sources to the main notebook. There is no check between Subagent A returning and Subagent B being dispatched.

**Solution:** After Subagent A's summary is printed, assert the main notebook has 0 sources before dispatching Subagent B. Halt with a clear error if the count is > 0.

**Files:**
- Modify: `SKILL.md`

---

### Step 1: Locate the dispatch loop in SKILL.md

Find the section after the Subagent Dispatch Protocol (around line 168–173):

```markdown
Wait for the subagent summary. Print it verbatim to the user. Then:

```bash
NEXT=$(jq -r .next_phase "$WORKSPACE/state.json")
# Loop: look up NEXT in Dispatch Table, dispatch next subagent, or exit on done.
```
```

### Step 2: Add the guard block

Replace that section with:

```markdown
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

```bash
NEXT=$(jq -r .next_phase "$WORKSPACE/state.json")
# Loop: look up NEXT in Dispatch Table, dispatch next subagent, or exit on done.
```
```

### Step 3: Verify the guard appears in the right place

```bash
grep -n "SOURCE_COUNT\|guard failed\|Phase 3 guard" \
  ~/.claude/skills/legal-research/SKILL.md
```

Expected: lines pointing to the new guard block between the Subagent Dispatch Protocol and the dispatch loop.

### Step 4: Commit

```bash
cd ~/.claude/skills/legal-research
git add SKILL.md
git commit -m "docs: add orchestrator guard asserting notebook is empty after Phase 3 before dispatching Phase 4"
```

---

## Final verification

Run the full test suite one last time:

```bash
cd ~/.claude/skills/legal-research
python3 -m pytest tests/ -q -m "not live" 2>&1 | tail -8
```

Expected: same 15 pre-existing failures; all new tests pass. No regressions.
