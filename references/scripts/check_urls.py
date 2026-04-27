"""URL accessibility checker for Phase 4 spot-checks.

Usage:
    python3 check_urls.py <urls_file> [--timeout 10] [--output /tmp/url_check.json]

Reads one URL per line from <urls_file>, sends HEAD requests, and reports HTTP
status codes.  Writes a JSON summary to --output (default: /tmp/url_check_results.json).
Exits 0 always — callers read the JSON to decide next steps.
"""
from __future__ import annotations
import argparse
import json
import ssl
import sys
import urllib.request
import urllib.error
from pathlib import Path
import certifi


def check_url(url: str, timeout: int) -> dict:
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "Mozilla/5.0 (compatible; legal-research-bot/1.0)")
        ctx = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return {"url": url, "status": resp.status, "ok": resp.status < 400}
    except urllib.error.HTTPError as exc:
        return {"url": url, "status": exc.code, "ok": exc.code < 400}
    except Exception as exc:
        return {"url": url, "status": 0, "error": str(exc), "ok": False}


def main() -> None:
    ap = argparse.ArgumentParser(description="Check URL accessibility")
    ap.add_argument("urls_file", help="Text file with one URL per line")
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--output", default="/tmp/url_check_results.json")
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
    print(f"\n{ok_count}/{len(results)} URLs accessible. Results: {out_path}")


if __name__ == "__main__":
    main()
