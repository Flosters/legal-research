#!/usr/bin/env python3
"""Wrong-jurisdiction filter for NotebookLM source lists.
Usage: echo '<json_array>' | python3 jurisdiction-filter.py <Jurisdiction>
       e.g.: echo '[{"url":"...","title":"..."}]' | python3 jurisdiction-filter.py Argentina
Reads a JSON array of source objects from stdin, writes filtered array to stdout.
Drops sources whose URL netloc ends with a foreign ccTLD or whose title contains
a foreign-country keyword. Prints drop reasons to stderr.
"""
import sys, json
from urllib.parse import urlparse

JURISDICTION_TLDS = {
    "Argentina": [".ar", ".com.ar", ".gov.ar", ".edu.ar", ".org.ar", ".net.ar"],
    "Brazil":    [".br", ".com.br", ".gov.br", ".edu.br", ".org.br", ".net.br"],
    "Mexico":    [".mx", ".com.mx", ".gob.mx", ".edu.mx", ".org.mx"],
    "Chile":     [".cl", ".com.cl", ".gob.cl", ".edu.cl"],
    "Colombia":  [".com.co", ".gov.co", ".edu.co"],
    "Uruguay":   [".uy", ".com.uy", ".gub.uy", ".edu.uy"],
    "Paraguay":  [".py", ".com.py", ".gov.py"],
    "Bolivia":   [".bo", ".com.bo", ".gob.bo"],
    "Peru":      [".pe", ".com.pe", ".gob.pe", ".edu.pe"],
    "Venezuela": [".ve", ".com.ve", ".gob.ve"],
    "Ecuador":   [".ec", ".com.ec", ".gob.ec"],
    "France":    [".fr", ".gouv.fr"],
    "Spain":     [".es", ".gob.es"],
    "Portugal":  [".pt", ".gov.pt"],
    "Germany":   [".de"],
    "Italy":     [".it", ".gov.it"],
    "UK":        [".uk", ".co.uk", ".gov.uk", ".ac.uk"],
}
WRONG_TITLE_KEYWORDS = {
    "Argentina": ["brasil", "brazil", "brasileiro", "méxico", "mexico", "chile", "colombia"],
    "Brazil":    ["argentina", "argentino", "méxico", "mexico", "chile", "colombia"],
}

def is_wrong_jurisdiction(url, title, target):
    target_tlds = set(JURISDICTION_TLDS.get(target, []))
    other_tlds = set()
    for jur, tlds in JURISDICTION_TLDS.items():
        if jur != target:
            other_tlds.update(tlds)
    other_tlds -= target_tlds
    try:
        netloc = urlparse(url).netloc.lower().split(":")[0]
    except Exception:
        netloc = ""
    # Longest-first so ".com.br" matches before ".br"
    for tld in sorted(other_tlds, key=len, reverse=True):
        if netloc.endswith(tld):
            return True, f"foreign TLD '{tld}' in netloc '{netloc}'"
    for kw in WRONG_TITLE_KEYWORDS.get(target, []):
        if kw in title.lower():
            return True, f"foreign keyword '{kw}' in title"
    return False, ""

if __name__ == "__main__":
    target = sys.argv[1]   # e.g. "Argentina"
    sources = json.load(sys.stdin)
    kept, dropped = [], []
    for s in sources:
        drop, reason = is_wrong_jurisdiction(s.get("url", ""), s.get("title", ""), target)
        if drop:
            dropped.append({**s, "_drop_reason": reason})
        else:
            kept.append(s)
    print(f"Wrong-jurisdiction filter: kept {len(kept)}, dropped {len(dropped)}", file=sys.stderr)
    for d in dropped:
        print(f"  DROPPED: {d.get('title','?')} — {d['_drop_reason']}", file=sys.stderr)
    json.dump(kept, sys.stdout, ensure_ascii=False)
