# Output Templates — NotebookLM Legal Research

## Source Tier Classification

Claude classifies each source from the notebook into a tier based on its URL domain and title before assembling the Sources Consulted table. Only sources cited in the analysis are included.

| Tier | Label | Indicators |
|------|-------|------------|
| 1 | Primary Authorities | Official government sites, court databases, legislative portals, constitutional texts, official gazette publications |
| 2 | Secondary — Doctrine & Academic | Law review journals, university repositories, academic publishers, treatises, legal encyclopedias |
| 3 | Tier 3 — Law Firm & Specialized Commentary | Law firm blogs, bar association publications, specialized legal news, practice guides |

**Source type labels** (use in the Type column):

Primary tier: `Case — [Court name]`, `Statute`, `Constitution`, `Regulation`, `Treaty`, `Decree`, `Administrative Resolution`

Secondary tier: `Law Review Article`, `Treatise`, `Legal Encyclopedia`, `Academic Commentary`

Tier 3: `Law Firm Analysis`, `Bar Association Guide`, `Practice Guide`, `Legal News`

---

## Report Structure

1. Page header (topic + confidential label)
2. Cover (navy banner with gold accent)
3. Metadata table (jurisdiction, area, posture, date, language, source count, confidence)
4. Research Question
5. Legal Analysis (IRAC / CRAC / CREAC with verbatim block-quotes)
6. Verification Notes
7. Sources Consulted (Primary / Secondary / Tier 3 — with hyperlinks)
8. Disclaimer
9. Page footer

**Research Log is not included in the report.**

---

## HTML Template

Write the complete file below, replacing every `<!-- PLACEHOLDER -->` with actual content from Phases 5 and 5.5. Save as `./legal-research-[topic-slug]-[YYYY-MM-DD].html`.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title><!-- DOC_TITLE --></title>
<style>
  :root {
    --ink: #0F172A;
    --accent: #0D9488;
    --muted: #64748B;
    --border: #E2E8F0;
    --surface: #F8FAFC;
    --green: #059669; --amber: #B45309; --red: #DC2626; --ugray: #94A3B8;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: system-ui, -apple-system, 'Helvetica Neue', sans-serif;
    font-size: 11pt;
    color: #1E293B;
    max-width: 860px;
    margin: 0 auto;
    padding: 40px 48px;
    line-height: 1.65;
    background: #fff;
  }
  /* Page header */
  .page-header {
    display: flex;
    justify-content: space-between;
    font-size: 8.5pt;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px;
    margin-bottom: 32px;
  }
  .page-header .right { color: var(--muted); }
  /* Cover */
  .cover {
    background: var(--ink);
    padding: 28px 36px 0;
    margin-bottom: 0;
  }
  .cover-inner {
    padding-bottom: 28px;
  }
  .cover-bar {
    height: 3px;
    background: var(--accent);
    margin-bottom: 28px;
  }
  .cover-label {
    color: var(--accent);
    font-weight: 500;
    font-size: 8pt;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 12px;
  }
  .cover-title {
    color: #fff;
    font-weight: 700;
    font-size: 19pt;
    line-height: 1.25;
  }
  /* Metadata table */
  .meta-table {
    width: 100%;
    border-collapse: collapse;
    background: var(--surface);
    margin-bottom: 36px;
    border: 1px solid var(--border);
    border-top: none;
  }
  .meta-table td {
    padding: 9px 18px;
    font-size: 9.5pt;
    vertical-align: top;
    width: 50%;
    border-bottom: 1px solid var(--border);
  }
  .meta-table .label { font-weight: 600; color: var(--accent); }
  /* Headings */
  h1 {
    font-size: 9.5pt;
    color: var(--ink);
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border-bottom: 2px solid var(--accent);
    padding-bottom: 6px;
    margin: 36px 0 16px;
  }
  h2 {
    font-size: 13pt;
    color: var(--ink);
    font-weight: 700;
    margin: 26px 0 10px;
  }
  h3 {
    font-size: 9pt;
    color: var(--muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 18px 0 8px;
  }
  /* Body text */
  p {
    text-align: justify;
    margin-bottom: 10px;
  }
  /* Block quote */
  blockquote {
    border-left: 3px solid var(--accent);
    margin: 14px 0 16px 16px;
    padding: 10px 18px;
    background: var(--surface);
  }
  blockquote p { font-style: italic; color: #475569; margin-bottom: 4px; }
  blockquote .attribution {
    display: block;
    font-style: normal;
    color: var(--muted);
    font-size: 9pt;
    margin-top: 6px;
  }
  /* Sources table */
  .sources-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 24px;
    font-size: 9.5pt;
  }
  .sources-table th {
    background: var(--ink);
    color: #fff;
    font-weight: 600;
    padding: 9px 12px;
    text-align: left;
    font-size: 8.5pt;
    letter-spacing: 0.04em;
  }
  .sources-table td {
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
  }
  .sources-table tr:nth-child(even) td { background: var(--surface); }
  .sources-table a { color: var(--accent); text-decoration: underline; }
  .col-num    { width: 4%; text-align: center; font-weight: bold; }
  .col-source { width: 58%; }
  .col-type   { width: 22%; }
  .col-status { width: 16%; }
  .status-verified   { color: var(--green); font-weight: 500; }
  .status-paraphrase { color: var(--amber); }
  .status-mismatch   { color: var(--red); }
  .status-unverified { color: var(--ugray); }
  /* Page footer */
  .page-footer {
    display: flex;
    justify-content: space-between;
    font-size: 7.5pt;
    color: var(--muted);
    border-top: 1px solid var(--border);
    padding-top: 10px;
    margin-top: 56px;
  }
  @media print {
    body { max-width: 100%; padding: 20px; }
  }
</style>
</head>
<body>

<!-- PAGE HEADER -->
<div class="page-header">
  <span>Legal Research: <!-- SHORT_TOPIC --></span>
  <span class="right">CONFIDENTIAL — <!-- DATE_LABEL --></span>
</div>

<!-- COVER -->
<div class="cover">
  <div class="cover-inner">
    <div class="cover-label">LEGAL RESEARCH MEMORANDUM</div>
    <div class="cover-title"><!-- DOC_TITLE --></div>
  </div>
  <div class="cover-bar"></div>
</div>

<!-- METADATA -->
<table class="meta-table">
  <tr>
    <td><span class="label">Jurisdiction:</span> <!-- JURISDICTION --></td>
    <td><span class="label">Date:</span> <!-- DATE --></td>
  </tr>
  <tr>
    <td><span class="label">Area of Law:</span> <!-- AREA_OF_LAW --></td>
    <td><span class="label">Language:</span> <!-- LANGUAGE --></td>
  </tr>
  <tr>
    <td><span class="label">Posture:</span> <!-- POSTURE --></td>
    <td><span class="label">Sources:</span> <!-- SOURCE_COUNT --></td>
  </tr>
  <tr>
    <td><span class="label">Legally relevant date:</span> <!-- LEGALLY_RELEVANT_DATE --></td>
    <td><span class="label">Confidence:</span> <!-- CONFIDENCE --></td>
  </tr>
</table>

<!-- RESEARCH QUESTION -->
<h1>Research Question</h1>
<p><!-- RESEARCH_QUESTION --></p>

<!-- LEGAL ANALYSIS -->
<h1>Legal Analysis</h1>
<!-- ANALYSIS_CONTENT: insert h2 / h3 / p / blockquote elements per the patterns below -->

<!-- VERIFICATION NOTES -->
<h1>Verification Notes</h1>
<p><strong>Opposing position:</strong> <!-- OPPOSING_POSITION --></p>
<p><strong>Weakest link:</strong> <!-- WEAKEST_LINK --></p>
<p><strong>Overall confidence:</strong> <!-- OVERALL_CONFIDENCE --></p>
<p><strong>Citation mismatches:</strong> <!-- CITATION_MISMATCHES --></p>
<p><strong>Unverified sources:</strong> <!-- UNVERIFIED_SOURCES --></p>
<p><strong>Research gaps:</strong> <!-- RESEARCH_GAPS --></p>
<p><strong>Currency flags:</strong> <!-- CURRENCY_FLAGS --></p>
<p><strong>Temporal applicability:</strong> <!-- TEMPORAL_APPLICABILITY --></p>
<!-- TEMPORAL_APPLICABILITY: list all ⚠ Post-date, ⚠ Version mismatch, and ⚠ Commentary may be outdated flags from Phase 5.6 step 0; include retroactivity findings; "None" if all sources confirmed applicable -->

<!-- SOURCES CONSULTED -->
<h1>Sources Consulted</h1>
<p><em>Only sources cited in the legal analysis are listed. Verification status reflects citation checks performed against notebook sources.</em></p>

<!-- PRIMARY AUTHORITIES (omit entire block if no primary sources) -->
<h2>Primary Authorities</h2>
<table class="sources-table">
  <tr>
    <th class="col-num">#</th>
    <th class="col-source">Source</th>
    <th class="col-type">Type</th>
    <th class="col-status">Status</th>
  </tr>
  <!-- ROW PATTERN: <tr><td class="col-num">1</td><td class="col-source"><a href="URL">Title</a></td><td class="col-type">Case — [Court]</td><td class="col-status status-verified">✓ Verified</td></tr> -->
</table>

<!-- SECONDARY — DOCTRINE & ACADEMIC (omit entire block if none) -->
<h2>Secondary — Doctrine &amp; Academic</h2>
<table class="sources-table">
  <tr>
    <th class="col-num">#</th>
    <th class="col-source">Source</th>
    <th class="col-type">Type</th>
    <th class="col-status">Status</th>
  </tr>
  <!-- rows -->
</table>

<!-- TIER 3 — LAW FIRM & SPECIALIZED COMMENTARY (omit entire block if none) -->
<h2>Tier 3 — Law Firm &amp; Specialized Commentary</h2>
<table class="sources-table">
  <tr>
    <th class="col-num">#</th>
    <th class="col-source">Source</th>
    <th class="col-type">Type</th>
    <th class="col-status">Status</th>
  </tr>
  <!-- rows -->
</table>

<!-- DISCLAIMER -->
<h1>Disclaimer</h1>
<p><em>This document was prepared with AI assistance (Claude + Google NotebookLM) and is provided for informational and research purposes only. It does not constitute legal advice and should not be relied upon as such. AI-generated research may contain errors, omissions, or outdated information. All citations and legal propositions should be independently verified by a qualified legal professional before use in any legal proceeding, transaction, or advisory context. Citation verification was performed by querying source texts within the NotebookLM notebook; sources marked [UNVERIFIED] or ✗ Citation Mismatch require independent confirmation.</em></p>

<!-- PAGE FOOTER -->
<div class="page-footer">
  <span>Prepared with AI-assisted research | All citations must be independently verified before professional reliance</span>
</div>

</body>
</html>
```

---

## Legal Analysis Content Patterns

Use these HTML snippets when building the `ANALYSIS_CONTENT` section. Add `<blockquote>` only for `✓ Verified` and `~ Paraphrase — Consistent` citations from the Phase 5.5 running list.

### IRAC Pattern

```html
<h2>Issue 1 — [Heading]</h2>

<h3>Issue</h3>
<p>[State the precise legal question in one sentence.]</p>

<h3>Rule</h3>
<p><strong>[Source]:</strong> [Rule statement — element 1.]</p>
<blockquote>
  <p>"[Verbatim passage from CitationCheck]"</p>
  <span class="attribution">— [Source], [location]</span>
</blockquote>
<p><strong>[Source]:</strong> [Rule statement — element 2.]</p>
<!-- No blockquote if status is ✗ or [UNVERIFIED] -->

<h3>Application</h3>
<p><strong>Element 1:</strong> [fact] → [result] <em>— [Source] ✓</em></p>
<blockquote>
  <p>"[Verbatim passage]"</p>
  <span class="attribution">— [Source], [location]</span>
</blockquote>
<p><strong>Element 2:</strong> [fact] → [result] <em>— [Source] ~</em></p>
<blockquote>
  <p>"[Verbatim passage]"</p>
  <span class="attribution">— [Source], [location] (paraphrase — consistent)</span>
</blockquote>

<h3>Conclusion</h3>
<p>[Direct answer. Confidence: High/Medium/Low — reason.]</p>
```

### CRAC Pattern

```html
<h2>Issue 1 — [Heading]</h2>

<h3>Conclusion (preliminary)</h3>
<p>[One-sentence conclusion.]</p>

<h3>Rule</h3>
<p><strong>[Source]:</strong> [Rule element.]</p>
<blockquote>
  <p>"[Verbatim passage]"</p>
  <span class="attribution">— [Source], [location]</span>
</blockquote>

<h3>Application</h3>
<p><strong>Element:</strong> [fact] → [result] <em>— [Source] ✓</em></p>
<blockquote>
  <p>"[Verbatim passage]"</p>
  <span class="attribution">— [Source], [location]</span>
</blockquote>

<h3>Conclusion (confirmed)</h3>
<p>[Restate conclusion. Confidence: High/Medium/Low. Caveats.]</p>
```

### CREAC Pattern

```html
<h2>Issue 1 — [Heading]</h2>

<h3>Conclusion (preliminary)</h3>
<p>[One-sentence conclusion.]</p>

<h3>Rule</h3>
<p><strong>[Source]:</strong> [Black-letter rule.]</p>
<blockquote>
  <p>"[Verbatim passage]"</p>
  <span class="attribution">— [Source], [location]</span>
</blockquote>

<h3>Explanation</h3>
<p><em>[Source]</em> held that [explanation]. ✓</p>
<blockquote>
  <p>"[Verbatim passage]"</p>
  <span class="attribution">— [Source], [location]</span>
</blockquote>

<h3>Application</h3>
<p><strong>Element:</strong> [fact] → [result] <em>— [Source] ✓</em></p>
<blockquote>
  <p>"[Verbatim passage]"</p>
  <span class="attribution">— [Source], [location]</span>
</blockquote>

<h3>Conclusion (confirmed)</h3>
<p>[Restate. Confidence level. Caveats.]</p>
```

### Multi-Issue

Repeat the selected pattern for each issue, then add:

```html
<h2>Synthesis</h2>
<p>[How issues interact. Overall conclusion. Recommended next steps.]</p>
```
