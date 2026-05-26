"""Cross-check citations in the Evidence Registry against the citation log.

Usage:
    python3 cross_check_citations.py <state.json> <citation_log.txt> [output_path]

If output_path is omitted, writes to <workspace>/final_citation_log.txt
(derived from the directory containing state.json).
Prints a summary to stdout. Exits 0 on success, 1 on error.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path


VALID_IMPORT_STATUSES = {"imported", "failed", "pending", "skipped"}
VALID_QUERYABLE_STATUSES = {"queryable", "not_queryable", "pending", "unknown"}


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: cross_check_citations.py <state.json> <citation_log.txt> [output_path]", file=sys.stderr)
        sys.exit(1)

    state_path = Path(sys.argv[1])
    log_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else state_path.parent / "final_citation_log.txt"

    with open(state_path) as f:
        state = json.load(f)
    with open(log_path) as f:
        log_content = f.read()

    # evidence_registry lives in evidence_registry.json next to state.json;
    # fall back to state.json for old workspaces that stored it inline.
    reg_file = state_path.parent / "evidence_registry.json"
    if reg_file.exists():
        evidence_registry = json.loads(reg_file.read_text())
    else:
        evidence_registry = state.get("evidence_registry", [])
        if isinstance(evidence_registry, str):
            try:
                evidence_registry = json.loads(evidence_registry)
            except json.JSONDecodeError:
                evidence_registry = []

    lines = [
        "# Citation Cross-Check Report",
        f"# State: {state_path}",
        f"# Log: {log_path}",
        "",
    ]

    mismatches = []
    unverified = []
    for entry in (evidence_registry if isinstance(evidence_registry, list) else []):
        url = entry.get("url", "")
        title = entry.get("title", "")
        import_status = entry.get("import_status", "pending")
        queryable_status = entry.get("queryable_status", "pending")

        if import_status not in VALID_IMPORT_STATUSES:
            mismatches.append(f"Invalid import_status '{import_status}' for: {title}")
        if queryable_status not in VALID_QUERYABLE_STATUSES:
            mismatches.append(f"Invalid queryable_status '{queryable_status}' for: {title}")

        if url and url not in log_content:
            unverified.append(f"[UNVERIFIED] {title} — {url}")

    if mismatches:
        lines.append("## Status Mismatches")
        lines.extend(mismatches)
        lines.append("")

    if unverified:
        lines.append("## Unverified Sources")
        lines.extend(unverified)
        lines.append("")

    lines.append(f"## Summary")
    lines.append(f"Registry entries: {len(evidence_registry)}")
    lines.append(f"Mismatches: {len(mismatches)}")
    lines.append(f"Unverified: {len(unverified)}")

    report = "\n".join(lines)
    output_path.write_text(report)
    print(report)
    print(f"\nReport written to: {output_path}")


if __name__ == "__main__":
    main()
