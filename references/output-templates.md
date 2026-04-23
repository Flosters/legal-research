# Output Templates

## Template Selection Guide

| Context | Preferred Framework |
|---|---|
| US litigation memo / brief | IRAC |
| US transactional / advisory | CRAC |
| UK / Commonwealth | CRAC or CREAC |
| Academic / law review | IRAC |
| Multi-issue analysis | IRAC per issue (nested) |
| Regulatory / compliance | CREAC |

---

## IRAC — Issue, Rule, Application, Conclusion

Best for: single-issue analysis, US litigation, law school exams.

```
## [Issue Heading]

**Issue**
[State the precise legal question raised by the facts. One sentence.]

**Rule**
[State the governing legal rule. Include the source: statute, case, regulation.
For multi-element rules, list each element:
  1. Element one
  2. Element two
  3. Element three]

**Application**
[Apply the rule to the specific facts. Work through each element:
- Element 1: [fact] → [result] because [authority]
- Element 2: [fact] → [result] because [authority]
Analyze the strongest counterarguments here. Do not skip unfavorable facts.]

**Conclusion**
[State the outcome. Be direct. Note any uncertainty.]
```

---

## CRAC — Conclusion, Rule, Application, Conclusion

Best for: US transactional / advisory memos, UK legal writing, reader-first format.

```
## [Issue Heading]

**Conclusion (preliminary)**
[State your conclusion upfront in one sentence.]

**Rule**
[State the governing legal rule with source citations.]

**Application**
[Apply the rule to the facts, working through each element.
Address counterarguments within the application section.]

**Conclusion (confirmed)**
[Restate the conclusion, now supported by the analysis.
Note confidence level and any conditions that could change the outcome.]
```

---

## CREAC — Conclusion, Rule, Explanation, Application, Conclusion

Best for: complex doctrinal issues, regulatory analysis, Commonwealth jurisdictions.

```
## [Issue Heading]

**Conclusion (preliminary)**
[State conclusion in one sentence.]

**Rule**
[State the black-letter rule with citations.]

**Explanation**
[Explain how courts/authorities have applied this rule.
Discuss leading cases, split authorities, and the policy rationale.
This section fleshes out the rule before application.]

**Application**
[Apply the explained rule to the specific facts.
Reference the cases discussed in Explanation to show how this case fits or is distinguished.]

**Conclusion (confirmed)**
[Restate conclusion with confidence level and caveats.]
```

---

## Multi-Issue Structure

For research questions involving more than one legal issue, use nested IRAC:

```
# Legal Research: [Topic]

## Overview
[Brief summary of all issues and overall conclusion — 2-3 sentences]

---

## Issue 1: [Heading]
[Full IRAC / CRAC / CREAC]

---

## Issue 2: [Heading]
[Full IRAC / CRAC / CREAC]

---

## Issue 3: [Heading]
[Full IRAC / CRAC / CREAC]

---

## Synthesis
[How the issues interact. Overall recommendation or conclusion.]
```

---

## Full Research Memo Template

```markdown
# Legal Research: [Topic]

**Jurisdiction:** [Jurisdiction]
**Date:** [YYYY-MM-DD]
**Area of law:** [Area]
**Prepared for:** [Lawyer / Law student / Paralegal]

---

## Research Question
[Precise restatement of the legal question]

---

## Sources Consulted

| # | Source | Type | Authority | Status |
|---|--------|------|-----------|--------|
| 1 | [Title](url) | Primary — Case | Binding | ✓ Verified |
| 2 | [Title](url) | Primary — Statute | Binding | ✓ Verified |
| 3 | [Title](url) | Secondary — Article | Persuasive | ✓ Verified |

---

## Legal Analysis

[IRAC / CRAC / CREAC — use nested structure for multi-issue]

---

## Verification Notes

**Opposing position:** [Summary of steelmanned counter-argument]

**Weakest link:** [Name the most vulnerable part of the analysis]

**Confidence level:** High / Medium / Low — [brief justification]

**Unverified sources:** [List any [UNVERIFIED] items with explanation, or "None"]

---

## Research Log

| Database | Queries run | Notes |
|----------|-------------|-------|
| [Source] | "[query 1]", "[query 2]" | [any relevant note] |
```
