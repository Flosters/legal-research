# AI Cross-Examination Protocol

Apply this protocol to all AI-generated legal analysis before presenting final output. Treat every claim as coming from an "untested expert witness" whose work must be interrogated before it enters any work product.

---

## Phase 1 — Prepare

Before generating analysis, set strict parameters:
- Narrow, jurisdiction-specific questions only
- Clear procedural posture (litigation / transactional / advisory / academic)
- Explicit instruction to flag uncertainty rather than fill gaps

---

## Phase 2 — Interrogate (5 Pillars)

Run all five pillars on every substantive legal claim.

### Pillar 1: Establish the Basis (Reasoning Ladder)
Do not accept smooth, confident paragraphs. Build a step-by-step reasoning ladder:
- What is each legal element?
- What is the controlling authority for each element?
- Why does that authority apply to these specific facts?

If any rung of the ladder is missing or assumed, flag it.

### Pillar 2: Probe the Limits (Uncertainties)
Counter the AI's tendency to fill gaps with plausible-sounding content:
- What facts are missing that would change the conclusion?
- Where is the doctrine unsettled or in flux?
- What is the weakest link in the reasoning chain?
- Explicitly state: "I am uncertain about [X]" in the output where applicable.

### Pillar 3: Steelman the Opposition
Prevent confirmation bias by arguing the other side:
- How would opposing counsel attack this analysis?
- What is the strongest counter-argument?
- Which cited authority could be distinguished, and on what grounds?

Include a brief opposing position summary in every final output.

### Pillar 4: Test Internal Consistency (Office Impeachment)
Reformat the core analysis in a different structure to expose brittle reasoning:
- Convert the IRAC/CRAC memo into an elements chart: does it still hold?
- If an element disappears or contradicts when reformatted, the original analysis is unreliable — revise before proceeding.

### Pillar 5: Demand a Verification Pathway
For every cited case, statute, or regulation, produce a verification checklist:
- Does this authority exist? (Searched and confirmed, or marked [UNVERIFIED])
- Does it say what you claim? (Quote the exact passage, not a paraphrase)
- Is it still good law? (Check for subsequent history; note if citator unavailable)
- If unsure whether a case exists: label it **[UNVERIFIED]** and propose a traditional research path instead of guessing

### Pillar 6: Secondary-to-Primary Citation Fidelity
For every secondary source (article, treatise, doctrine, commentary) that quotes or attributes a passage to a primary source:
- Retrieve the full text of the cited primary source (not a summary or headnote).
- Search the quoted or attributed passage against the full text.
- If the passage is found verbatim or near-verbatim: mark `[TEXT VERIFIED]` with its exact location in the primary.
- If the passage is a paraphrase that accurately reflects the primary: mark `[PARAPHRASE — CONSISTENT]` and note the actual wording.
- If the passage cannot be found, or the primary says something materially different: mark `[CITATION MISMATCH]` — record both what the secondary claimed and what the primary text actually says. Disclose this in Verification Notes. Do not cite the secondary's characterization as established law.

This pillar is the primary enforcement mechanism for Phase 2.5 of the research workflow.

---

## Phase 3 — Verify

Independent confirmation of every citation:
1. Search for the case/statute by exact name and citation
2. Confirm the holding or provision matches your description
3. Check subsequent history (has it been reversed, overruled, distinguished?)
4. Any source that cannot be confirmed must be disclosed as **[UNVERIFIED]** in the final output — never silently remove it, never present it as confirmed

---

## Output of Verification Phase

Add a **Verification Notes** section to the final output containing:
- Summary of the steelmanned opposing position
- Disclosure of any **[UNVERIFIED]** sources with explanation
- The weakest link in the analysis chain, explicitly named
- Confidence level: High / Medium / Low — with brief justification

**High**: All sources independently confirmed, reasoning ladder complete, no significant gaps
**Medium**: Most sources confirmed; minor gaps or uncertainties noted
**Low**: One or more key sources unverified, doctrine unsettled, or facts insufficient for definitive conclusion

---

## Professional Liability Reminder

Incorporate into every output at Low or Medium confidence:
> ⚠️ This analysis is AI-assisted. All citations and holdings must be independently verified against primary sources before reliance in any professional context. AI tools can hallucinate case names, misquote holdings, and misapply jurisdictional rules.
