#!/usr/bin/env python3
"""Merge and deduplicate sources from one or more research result JSON files.

Usage: curate_sources.py <file1.json> [file2.json ...] > curated_sources.json

Each input file is the output of `notebooklm research status --json`.
Sources are deduplicated by exact URL (case-insensitive). All tiers are kept;
tier assignment is handled downstream in Phase 3.5.
"""
import sys, json


def load_sources(path: str) -> list:
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception as e:
        print(f"WARNING: could not read {path}: {e}", file=sys.stderr)
        return []

    sources = []
    # Support both top-level 'sources' and nested under 'tasks[*].sources'
    for task in data.get("tasks", []):
        for s in task.get("sources", []):
            if s.get("url"):
                sources.append(s)
    for s in data.get("sources", []):
        if s.get("url"):
            sources.append(s)
    return sources


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: curate_sources.py <file1.json> [file2.json ...]", file=sys.stderr)
        sys.exit(1)

    all_sources: list = []
    for path in sys.argv[1:]:
        all_sources.extend(load_sources(path))

    # Deduplicate by normalised URL (strip trailing slash, lowercase scheme+host)
    seen: set = set()
    unique: list = []
    for s in all_sources:
        key = s["url"].rstrip("/").lower()
        if key not in seen:
            seen.add(key)
            unique.append(s)

    print(json.dumps(unique, ensure_ascii=False, indent=2))
    print(f"Merged {len(all_sources)} sources → {len(unique)} after deduplication",
          file=sys.stderr)


if __name__ == "__main__":
    main()
