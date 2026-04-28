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
