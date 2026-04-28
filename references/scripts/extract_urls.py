#!/usr/bin/env python3
"""Extract URLs from evidence_registry.json for batch import or spot check.

Usage: extract_urls.py <workspace_dir> <nb_id> [--output /tmp/urls.txt]

Writes one URL per line to the output file (defaults to /tmp/urls_<nb_id>.txt).
Prints the count of URLs written.
"""
import sys, json, pathlib, argparse


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace")
    ap.add_argument("nb_id")
    ap.add_argument("--output", default=None)
    args = ap.parse_args()

    reg_path = pathlib.Path(args.workspace) / "evidence_registry.json"
    if not reg_path.exists():
        print(f"ERROR: {reg_path} not found", file=sys.stderr)
        sys.exit(1)

    reg = json.loads(reg_path.read_text())
    urls = [e["url"] for e in (reg if isinstance(reg, list) else []) if e.get("url")]

    output = args.output or f"/tmp/urls_{args.nb_id}.txt"
    pathlib.Path(output).write_text("\n".join(urls))
    print(f"Wrote {len(urls)} URLs to {output}")


if __name__ == "__main__":
    main()
