## Phase 1 — Gate 1: Scope + Verifiable Checklist

### 1A — Extract scope

From the query, extract:
- Legal question / topic
- Jurisdiction — **ask if not stated or not clearly inferable**
- Area of law — infer if possible; confirm only if genuinely ambiguous
- Procedural posture (litigation, transactional, advisory, academic) — infer when possible
- Report language — detect from the query itself. Record as `REPORT_LANGUAGE`. Ask only if the user writes in one language but seems to want the report in another.
- **Legally relevant date** — the date as of which the legal analysis must be assessed. This determines which version of a statute, regulation, or case law was in force, and anchors the temporal applicability of all sources. Infer from context if possible; record as `LEGALLY_RELEVANT_DATE`.
  - Litigation: typically the date of the alleged breach, injury, or triggering event
  - Transactional: typically the date of execution, signing, or closing
  - Advisory / compliance: today's date by default
  - Academic: not usually applicable — omit if purely doctrinal
  - **Ask if not clearly inferable.** Do not assume today's date for litigation or transactional matters.

Ask only what's missing. One consolidated question. Never ask more than 3 clarifying questions.

### 1B — Build the Verifiable Checklist

Before defining research queries, decompose the legal question into **3–8 researchable nodes**, each with an explicit acceptance criterion. This is the Rhino discipline that prevents research drift.

Each node must be:
- **Specific** — not "research employment law" but "find binding authority establishing the rule on dismissal without cause in [jurisdiction]"
- **Acceptance-checked** — state what satisfies the node (e.g., "2+ primary authorities found, full text accessible, holdings directly address the question")
- **Non-overlapping** — nodes should cover distinct dimensions (primary authority, doctrine/academic, procedural, comparative, recent developments, etc.)

**Example checklist structure:**
```
Legal Question: [precise restatement]
Legally relevant date: [LEGALLY_RELEVANT_DATE]
├── Node 1: [Primary authority — binding rule]
│   └── Accepted when: 2+ binding primary sources found, holdings on point,
│       sources confirmed in force at LEGALLY_RELEVANT_DATE
├── Node 2: [Statutory / regulatory framework]
│   └── Accepted when: governing statute/regulation identified, version in force
│       at LEGALLY_RELEVANT_DATE confirmed, publication and enforcement dates noted
├── Node 3: [Doctrine and academic analysis]
│   └── Accepted when: leading doctrinal treatment found, rule elements mapped,
│       flagged if primary sources have changed since publication
└── Node 4: [Temporal applicability / currency]
    └── Accepted when: entry-into-force dates confirmed for all primary sources,
        amendment history checked, secondary sources cross-checked against
        whether underlying law has changed since their publication date
```

Record this checklist as `RESEARCH_CHECKLIST`. It is your research anchor — every source, every query, every section of the final report maps to a specific node.

### 1C — Map queries to nodes

Determine how many deep research queries are needed (3–5). Default to 3. Each query must be anchored to one or more checklist nodes.

- **3 queries** — single issue, well-defined jurisdiction, established doctrine
- **4 queries** — two sub-issues, or fast-moving area needing a dedicated currency/developments angle
- **5 queries** — multi-issue, multi-jurisdictional, or highly specialized with distinct coverage requirements

For each query, record: the angle, the query string (to be written in jurisdiction language in Phase 3), and which node(s) it addresses.

Record the list as `RESEARCH_QUERIES` — used verbatim in Phase 3.

### 1D — Present the plan and request confirmation

```
Research question: [precise restatement]
Jurisdiction: [confirmed]
Area of law: [identified]
Legally relevant date: [LEGALLY_RELEVANT_DATE — e.g., 2023-08-15, or "today (advisory)"]
Report language: [REPORT_LANGUAGE — e.g., English, Spanish]
Research method: NotebookLM deep web research + IRAC/CRAC analysis + Rhino evidence discipline
Output: Legal memo (.html)
NotebookLM notebook: will be kept for future reference

Verifiable checklist ([N] nodes):
  Node 1: [description] — Accepted when: [criterion]
  Node 2: [description] — Accepted when: [criterion]
  ...

Research queries ([N] total — each runs ~5–10 min sequentially, ~[N×5]–[N×10] min total):
  Query 1 → [node(s)]: [angle]
  Query 2 → [node(s)]: [angle]
  Query 3 → [node(s)]: [angle]
  Query 4 → [node(s)]: [angle]   ← only if N ≥ 4
  Query 5 → [node(s)]: [angle]   ← only if N = 5

Estimated total time (all phases): ~40–80 min (3 queries) | ~55–110 min (5 queries)
Checkpoints at phases 3.6, 4.5, and 5 allow pausing and resuming in a fresh session.

⚠ Deep research runs sequentially. To reduce wait time, remove a query before confirming.
```

Ask: "Confirm to proceed, or adjust scope?"
