---
phase_id: "3.7"
covers: ["3.7"]
subagent_type: general-purpose
inputs_from_state: ["scope","evidence_registry","nb_id","research_checklist"]
outputs_to_state: ["evidence_registry","completed_phases","next_phase"]
next_phase_on_success: "4"
estimated_runtime_minutes: 10-30
---

# Phase 3.7 — Mandatory Primary Source Import

> **Subagent contract:** fresh context; read state.json; execute B1/B2/B3 for every
> cited primary source; update evidence_registry entries in-place; mark phase
> 3.7 complete with next_phase=4; return ≤200-word summary (N identified, M imported,
> K failed, source-priority patterns used).

## Phase 3.7 — Mandatory Primary Source Import

This phase ensures the notebook contains the actual text of the primary sources that secondary and tertiary sources cite. Without this, citation verification in Phase 5.5 can only confirm that a secondary source described a case consistently with another secondary source — not that the description matches the original decision or statute. This phase is **mandatory**, not optional.

### Step A — Identify cited primary sources

From the Evidence Registry, scan all Tier 2 and Tier 3 entries. For each, identify the primary sources they cite that are relevant to the research question. Typical targets:

- **Cases** (court decisions) cited in academic articles, commentary, or law firm analyses — e.g., "UK Supreme Court, Donoghue v Stevenson [1932] AC 562"; "CSJN, Halabi c/ PEN, Fallos 332:111 (Argentina)"
- **Statutes and regulations** cited in secondary sources — e.g., "42 U.S.C. § 1983 (US)"; "Ley 24.240 Art. 52 (Argentina)"; "Consumer Rights Act 2015, s.9 (UK)"
- **Constitutional provisions** cited — e.g., "U.S. Const. amend. XIV"; "Art. 43 Constitución Nacional (Argentina)"

For each identified primary source, note:
1. The official citation (court, year, Fallos number / statute number / official gazette reference)
2. The jurisdiction's authoritative publication URL (use `$SKILL_ROOT/references/source-priority.md` to find the correct official source for the jurisdiction)

**Do not skip a primary source because it looks familiar or "obvious" — every cited primary source requires explicit import so its text can be used for verification.**

**Long statute rule:** When a statute with more than approximately 100 articles is identified for import (e.g., a civil code, consumer protection code, aeronautical code, tax code), do not assume a single URL covers the entire text. Before importing:
1. List every article of that statute cited across all Tier 2/3 sources in the Evidence Registry.
2. Identify which chapter or section each cited article belongs to.
3. If the articles span multiple chapters and the import URL corresponds to only one chapter, schedule a separate import for each additional section as an independent Tier 1 entry. Label each with the article range it covers: e.g., `Civil Code — Arts. 1094–1095 (Consumer contracts)`.

This rule catches the failure mode where an import is recorded as "Queryable ✓" at the statute level but the specific articles the analysis depends on were never indexed.

**Doctrine-anchor rule:** For each checklist node whose acceptance criterion requires binding primary authority, identify the specific court decisions or statutory instruments that are the known source of that doctrine — not just what appeared in the deep-research results, but what is actually the foundational authority. Every such source is a mandatory import target regardless of whether it appears in any T2/T3 Evidence Registry entry.

For each:
1. Find the official URL for the decision or instrument using `$SKILL_ROOT/references/source-priority.md` (check the jurisdiction's apex court and official gazette entries).
2. Apply the B1 URL resolution rules — most apex court decision pages are JS-rendered; resolve to a direct PDF.
3. Add the source to the Phase 3.7 import queue with a note: `[Doctrine anchor — Node N]`.

If the official URL cannot be resolved after applying B1 and the fallback escalation in B3, mark the entry `[IMPORT FAILED — DOCTRINE ANCHOR]` in the Evidence Registry and flag the corresponding checklist node as `⚠ Doctrine unanchored — all citations to this authority will be [SECONDARY ONLY]`.

**Amendment instrument scan:** For each statute or regulation identified for import, run a targeted search for modifying instruments issued between the statute's publication date and `LEGALLY_RELEVANT_DATE`. The instrument type varies by jurisdiction:

- **Argentina:** Decretos, DNU (Decreto de Necesidad y Urgencia), leyes modificatorias — search `site:infoleg.gob.ar "[Ley NNNNN] modificación"`
- **United States:** Executive orders, agency final rules in the Federal Register — search `site:govinfo.gov "[Act name] amendment [year range]"`
- **United Kingdom:** Statutory instruments, orders in council — search `site:legislation.gov.uk "[Act name] amendment"`
- **Other jurisdictions:** Consult `$SKILL_ROOT/references/source-priority.md` for the jurisdiction's official gazette and amendment search patterns.

If a modifying instrument is found and predates `LEGALLY_RELEVANT_DATE`, import it as a separate Tier 1 entry and flag the original statute in the Evidence Registry as `⚠ Amended — see [instrument name/number]`. This flag will surface in Phase 5.6 step 0 for temporal applicability review.

### Step B — URL Resolution + Crawlability Check + Import

For each identified primary source, **resolve the URL and verify it is crawlable before importing**. NotebookLM's indexer silently indexes empty bodies for JS-rendered pages — a successful `source add` does NOT guarantee queryable content.

#### B1 — Jurisdiction URL Resolution Rules (apply before any import)

Official court and legislative websites frequently render pages in JavaScript or serve only metadata. These "JS shells" return a source ID on import but index an empty body. Before importing any Tier 1 source, check whether its URL is from a site known to have this pattern and resolve it to a directly crawlable equivalent.

**General rule:** If a discovered URL is a court or legislative site that renders in JS, find the direct PDF or static HTML version. Use `$SKILL_ROOT/references/source-priority.md` — each jurisdiction's section lists its official sources and URL resolution patterns.

**Common patterns across all jurisdictions:**

| Source type | Pattern | Resolution |
|---|---|---|
| Apex court decision | JS-rendered HTML page at official court domain | Look for a direct PDF link on the same domain (most apex courts publish PDFs). If no PDF link is visible, run a web search: `site:[court-domain] "[party name]" [year] pdf`. |
| Official gazette page | Gazette entry URL returns small HTML body | Verify `Content-Type: text/html` with body ≥ 2000 bytes (see B2). If too small, search the gazette's document store for a PDF version. |
| Legal aggregator | URL is from a national law-indexing service rather than the primary official source | Find the primary official URL using `$SKILL_ROOT/references/source-priority.md`. Prefer the official legislative portal over any aggregator. |
| NGO / advocacy site | URL belongs to a civil society or advocacy organization | Do not import. Find the primary legislation at the official legislative portal and import that instead. |

For jurisdiction-specific URL patterns and fallback domains, see `$SKILL_ROOT/references/source-priority.md` under each jurisdiction's heading.

**Unknown URL fallback:** If the official URL for a Tier 1 source cannot be determined by inspection or from source-priority.md, run a targeted web search before marking the source unimportable:

```bash
# Pattern: site:[official-domain] "[law name or number]"
# Examples:
#   site:infoleg.gob.ar "Ley 26.451"          ← Argentine statute
#   site:legislation.gov.uk "Consumer Rights Act 2015"  ← UK statute
#   site:govinfo.gov "15 U.S.C. 45"           ← US statute
#   site:curia.europa.eu "C-281/98"            ← EU case
```

If the web search returns a matching official URL, use that URL and proceed to B2. If no official URL is found after the web search, apply the B3 fallback escalation ladder. Only mark a source `[NOT CRAWLABLE]` after exhausting both this web-search step and B3.

Apply these rules to every Tier 1 URL before proceeding to B2.

#### B2 — Crawlability Pre-Check

For each resolved URL, run:

```bash
# Check Content-Type and body size without downloading the full page
RESPONSE=$(curl -sI --max-time 10 "<resolved-url>" 2>&1)
CONTENT_TYPE=$(echo "$RESPONSE" | grep -i "content-type:" | head -1)
echo "URL: <resolved-url>"
echo "Content-Type: $CONTENT_TYPE"

# For HTML pages, also check body length (JS shells return < 500 bytes of real text)
if echo "$CONTENT_TYPE" | grep -qi "text/html"; then
  BODY_LEN=$(curl -sL --max-time 15 "<resolved-url>" 2>/dev/null | wc -c)
  echo "Body length: $BODY_LEN bytes"
  if [ "$BODY_LEN" -lt 2000 ]; then
    echo "⚠ LIKELY EMPTY SHELL — body too small. Apply URL resolution rules or mark [NOT CRAWLABLE]."
  fi
fi
```

**Interpret results:**
- `Content-Type: application/pdf` → safe to import directly, PDF content is fully indexed
- `Content-Type: text/html` + body ≥ 2000 bytes → likely safe; proceed
- `Content-Type: text/html` + body < 2000 bytes → JS-rendered shell; apply URL resolution rules or mark `[NOT CRAWLABLE]`
- HTTP 4xx / 5xx → mark `[URL UNREACHABLE]` and try fallback (see B3)

#### B3 — Import with Fallback Escalation

For each URL that passed B2 (or was resolved in B1):

```bash
notebooklm source add "<resolved-url>" -n "$NB_ID"
```

**Fallback escalation ladder** (apply when B2 flags a problem or import returns an error):

1. **Try the PDF version** — for court decisions and statutes, the PDF link is the most reliable. Use B1 resolution rules to find it.
2. **Try an alternative authoritative domain** — e.g., if `saij.gob.ar` fails, try `infoleg.gob.ar`; if `csjn.gov.ar` fails, try a Google Scholar mirror of the decision.
3. **Try a secondary source that quotes the primary verbatim** — e.g., if the CSJN PDF is unavailable, import a law review article that reproduces the relevant holding verbatim.
4. **Mark `[NOT CRAWLABLE]`** — if all three alternatives fail, mark the source in the Evidence Registry as `[NOT CRAWLABLE]`. This status propagates to Phase 4.1 (spot-check skipped) and Phase 5.5 (citation status will be `[SECONDARY ONLY]` at best). Disclose in Verification Notes.

For authoritative sources and preferred URL formats by jurisdiction, see `$SKILL_ROOT/references/source-priority.md`.

**Failure handling:** If a primary source URL is `[URL UNREACHABLE]` or `[NOT CRAWLABLE]` after exhausting the escalation ladder:
1. Mark it in the Evidence Registry with the appropriate status tag
2. Proceed — any citation to this source in Phase 5.5 will be tagged `[SECONDARY ONLY]` and cannot receive verified status

### Step C — Update the Evidence Registry

For each successfully imported primary source:
- Add it as a new Tier 1 entry in the Evidence Registry (or update an existing entry from `[IMPORT FAILED]` to `Imported ✓`)
- Tag it to the checklist node(s) it supports
- Note: these sources were **explicitly imported for citation verification**, not only from deep research

For each failed import:
- Mark the entry `[PRIMARY IMPORT FAILED]` in the Evidence Registry
- This status will propagate to the Citation Verification Log in Phase 5.5

Notify the user:
> "Identified [N] primary sources cited by secondary materials. Imported [M] successfully. [K] failed — these citations will be flagged as unverifiable in the report. Proceeding to source import."

