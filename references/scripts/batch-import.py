#!/usr/bin/env python3
"""Batch-import URLs into a NotebookLM notebook using the async Python API.
Usage: python3 batch-import.py <notebook_id> <url_list_file>
"""
import asyncio, json, sys, subprocess
from pathlib import Path
from notebooklm import NotebookLMClient
from notebooklm.exceptions import RateLimitError

CONCURRENCY = 5
RATE_LIMIT_BACKOFF = 30
MIN_BODY_BYTES = 2000  # HTML bodies below this are likely JS-rendered shells

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
    # Pre-filter: check crawlability synchronously before async import
    crawlable = []
    for url in urls:
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
