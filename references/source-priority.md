# Source Priority Guide

Always search Tier 1 first, then Tier 2, then Tier 3. Never skip Tier 1 for a jurisdiction that has official databases available.

## Tier 1 — Free, Official (Government & Court Databases)

### United States
- **Federal statutes**: congress.gov, uscode.house.gov, govinfo.gov
- **Federal regulations**: regulations.gov, ecfr.gov (eCFR)
- **Federal case law**: supremecourt.gov, courtlistener.com, pacer.gov (PACER)
- **State law**: each state legislature's official site (e.g., leginfo.legislature.ca.gov for California)
- **General US legal**: law.cornell.edu (LII — Legal Information Institute)

### United Kingdom
- **Legislation**: legislation.gov.uk
- **Case law**: bailii.org (BAILII), judiciary.gov.uk
- **Parliament**: parliament.uk

### European Union
- **Legislation & treaties**: eur-lex.europa.eu
- **Court of Justice**: curia.europa.eu
- **GDPR & data**: edpb.europa.eu

### Canada
- **Federal statutes & regulations**: laws-lois.justice.gc.ca
- **Supreme Court**: scc-csc.ca
- **Multi-jurisdictional**: canlii.org (CanLII — free, comprehensive)

### Australia
- **Federal legislation**: legislation.gov.au
- **High Court**: hcourt.gov.au
- **Multi-jurisdictional**: austlii.edu.au (AustLII)

### Argentina
- **Legislation**: infoleg.gob.ar (InfoLeg), argentina.gob.ar/normativa
- **Supreme Court (CSJN)**: csjn.gov.ar
- **Legal information system**: saij.gob.ar (SAIJ)
- **Official gazette**: boletinoficial.gob.ar

#### Argentine URL Resolution Patterns

When importing Argentine Tier 1 sources, apply these substitutions before running the crawlability pre-check:

| Source type | If the discovered URL contains… | Replace with… |
|---|---|---|
| CSJN decision | `csjn.gov.ar/jurisprudencia/` HTML page | Direct PDF: `csjn.gov.ar/data/pdf/fallos/[vol]-[folio].pdf`. Find the Fallos citation (e.g. Fallos 332:111) and construct `332-111.pdf`. If the Fallos citation is unknown, run a web search for `site:csjn.gov.ar "[party name]" fallos pdf`. |
| SAIJ norma | `saij.gob.ar/norma/` or `saij.gob.ar/legislacion/` | Equivalent InfoLeg URL: `infoleg.gob.ar/infolegInternet/anexos/[range]/[id]/norma.htm`. If the ID is unknown, run a web search for `site:infoleg.gob.ar "[Ley NNNNN]"` to locate it. |
| SAIJ timeout | `saij.gob.ar` returns timeout or 5xx | Do not retry SAIJ. Run a web search for `site:infoleg.gob.ar "[Ley NNNNN]"` to find the static InfoLEG equivalent. |
| Boletín Oficial | `boletinoficial.gob.ar/detalleAviso/` | Same URL — but verify `Content-Type: text/html` with body ≥ 2000 bytes (see B2). |
| CSJN Acordada | `csjn.gov.ar/acordada` HTML page | Look for a linked PDF at `csjn.gov.ar/acordadas/[year]/acord[N]-[year].pdf`. If none, try `saij.gob.ar`. |
| NGO / advocacy site | `padec.org.ar/` or similar civil society pages | Do not import. Find the legislation the NGO references at `infoleg.gob.ar` and import the official text. |
| Decreto / DNU | Any Argentine executive decree or DNU | Try `infoleg.gob.ar` first. If ID is unknown, run `site:infoleg.gob.ar "decreto NNN/YYYY"` or `site:infoleg.gob.ar "DNU NNN/YYYY"`. |

**Amendment instruments for Argentina:** Modifying instruments include Decretos, DNU (Decreto de Necesidad y Urgencia), and amending legislation (leyes modificatorias). To check whether a statute has been amended, search `site:infoleg.gob.ar "[Ley NNNNN] modificación"` or check the "Normas que modifican" section on the InfoLEG page for the original statute.

### Latin America (General)
- **OAS / SICE**: sice.oas.org (trade & commercial law)
- **National congresses**: search "[country] congreso legislación oficial" for the official legislative portal
- **Mercosur**: mercosur.int

### International
- **UN Treaty Collection**: treaties.un.org
- **ICJ**: icj-cij.org
- **ILO**: ilo.org/natlex (national labor law database)
- **WTO**: wto.org/dispute settlement
- **ICSID (investment arbitration)**: icsid.worldbank.org
- **UNCITRAL**: uncitral.un.org

---

## Tier 2 — Academic & Institutional Repositories

- **Google Scholar** (scholar.google.com) — case law + academic articles; broad jurisdiction coverage
- **SSRN** (ssrn.com) — preprints and working papers; excellent for cutting-edge doctrine
- **HeinOnline** (heinonline.org) — comprehensive law journal archive; use public-access links where available
- **Law school repositories**:
  - Harvard: hls.harvard.edu, dash.harvard.edu
  - Yale: library.law.yale.edu
  - Stanford: law.stanford.edu
  - Columbia: law.columbia.edu
  - Georgetown: law.georgetown.edu
- **Free Law Project / CourtListener**: free.law, courtlistener.com — US federal & state case law, PACER mirror

---

## Tier 3 — Specialized Analysis

Use for doctrinal context, practical commentary, and current developments. Never cite as primary authority.

- Major law firm client alerts and practice guides (search "[firm name] + [topic] + alert")
- Legal journals and law reviews (findable via Google Scholar "cite" links)
- Bar association publications: americanbar.org, ibanet.org
- Practice-specific organizations: relevant regulatory bodies' publications
- Legal blogs with identified author credentials (e.g., SCOTUSblog for US Supreme Court)

---

## Source Currency and Temporal Applicability Rules

### 1 — Establish the legally relevant date first

Before assessing any source's currency, confirm `LEGALLY_RELEVANT_DATE` from Phase 1. Every temporal check below is relative to this date, not to today's date — unless the research is purely advisory, in which case today applies.

### 2 — Primary sources: statutes and regulations

- Always identify **two dates**: (a) the publication/gazette date and (b) the enforcement/entry-into-force date. These are often different. In civil law jurisdictions a *vacatio legis* period between publication and entry into force is common (days to months).
- The legally operative date is the **enforcement date**, not the publication date. A law published before `LEGALLY_RELEVANT_DATE` but with an enforcement date after it was not yet in force at the relevant time.
- Check for **amendments**: confirm whether the version found is the version in force at `LEGALLY_RELEVANT_DATE`. If the statute has been amended since, identify whether the amendment predates or postdates `LEGALLY_RELEVANT_DATE`.
- Check for **retroactivity provisions**: if a later law or amendment postdates `LEGALLY_RELEVANT_DATE` but contains explicit retroactivity language, note this — the later source may still govern past facts.
- Use **official gazette sources** (e.g., boletinoficial.gob.ar for Argentina, govinfo.gov for US, legislation.gov.uk for UK) to confirm publication and enforcement dates. Commercial reprints may omit this information or reflect a consolidated version without noting the consolidation date.

### 3 — Primary sources: case law

- Check if the case is **still good law**: look for subsequent history (affirmed, reversed, overruled, distinguished). Use Shepard's/KeyCite if available; otherwise search by case name + "subsequently" or "appeal" manually.
- Confirm the **decision date**. If the decision postdates `LEGALLY_RELEVANT_DATE`, the case may be cited as persuasive or predictive authority, but it was not the controlling rule at the time of the facts. Note this distinction explicitly.
- For cases that interpret statutes, confirm that the **statute version the court applied** matches the version in force at `LEGALLY_RELEVANT_DATE`. A court interpreting an amended statute may reach a different conclusion than one interpreting the pre-amendment version.

### 4 — Secondary and tertiary sources: smart currency flagging

Do **not** flag secondary sources as outdated based on age alone. Age is a proxy; what matters is whether the underlying law has changed since the source was written. Apply this logic:

- **Law has not materially changed** since the secondary source was published → source is current regardless of age. A foundational treatise chapter from 10 years ago remains valid if the statute it analyzes is unchanged.
- **Law has been amended, replaced, or reinterpreted** since the secondary source was published → flag as `⚠ Commentary may be outdated — [describe what changed and when]`. Do not discard; flag it so the reader can assess whether the doctrinal analysis still holds.
- **Law is unsettled or developing** (active legislative reform, conflicting decisions, pending ruling) → flag as `⚠ Area in flux — commentary may not reflect current state`. Note the specific development creating uncertainty.
- **Source relies on a case that has since been overruled** → flag as `⚠ Cited authority overruled — [case name, date]`. The secondary source's analysis built on that case may no longer be sound.

### 5 — Source version integrity

When importing sources, prefer **point-in-time versions** of statutes and regulations where available (versions as of a specific date from official codification databases). If only a consolidated/current version is available, note in the Evidence Registry that the version reflects the law as of the import date, which may differ from `LEGALLY_RELEVANT_DATE`.

If a statute version mismatch is suspected, search explicitly for the historical version: e.g., `"[statute name] texto vigente [year]"` or `"[statute name] as amended through [year]"` depending on the jurisdiction.
