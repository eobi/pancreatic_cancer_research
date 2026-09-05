# Adversarial review of both manuscripts

Written against the standard a hostile Reviewer 2 would apply, not a friendly one.
Each item states the objection, how damaging it is, and what fixes it.

---

## PAPER 1

### C1. The "five independent failures" claim will be collapsed by any reviewer. FATAL if unaddressed.

Three of the five are the same mechanism wearing different hats:

| reported failure | actual mechanism |
|---|---|
| BRENK rejects acrylamide (sotorasib, adagrasib) | over-broad SMARTS alert |
| Nitroso pattern rejects venetoclax | over-broad SMARTS alert |
| Stability rule rejects MRTX1133 | over-broad SMARTS alert |
| ADMET rejects 199/200 | threshold not fitted to this chemotype |
| Retrosynthesis ranks impossible above marketed | tool answers a different question |

That is **three mechanisms across five instances**, not five independent tool failures.
Claiming five invites the reviewer to do the collapsing for you, in public, and to conclude
the paper oversells.

**Fix.** Restructure around the three mechanisms. Report five instances as evidence that
each mechanism recurs. The argument gets stronger, because recurrence across independent
implementations is the actual finding.

### C2. n = 1 campaign, no control campaign. SERIOUS.

We cannot separate "the vetting tools failed" from "this particular generator was bad."
A generator with a stability term might have produced molecules that pass. The paper
implies the tools are at fault; the design cannot establish that.

**Fix.** State it as a limitation in the abstract, not only in §4. Reframe the claim from
"the tools failed" to "the tools did not catch a failure they are widely assumed to catch."
That is defensible with n = 1.

### C3. The year of failed synthesis is asserted, not documented. SERIOUS.

It is the ground-truth anchor and the paper's main novelty claim rests on it. There is no
lab notebook, no chemist's report, no purchase record, no failed-reaction log in the
repository. A reviewer will ask. "Approximately one year" with no artefact is anecdote.

**Fix.** Either produce documentation (synthesis attempts, dates, who attempted them) or
downgrade the claim to what can be evidenced, and say plainly that the synthesis record is
not available. Do not leave it load-bearing and unsupported.

### C4. The 0/73 result uses our own filter. Circularity risk. SERIOUS.

We built the gate, then reported that generated molecules fail it. A reviewer will ask
whether the filter was constructed, consciously or not, to separate these sets.

**Fix.** Report the result using **unmodified** published catalogues (BRENK, PAINS as
shipped in RDKit) as the primary number, with our exemptions as a secondary analysis. If
the unmodified catalogue also gives 0/73, the circularity objection dies. If it does
not, we must say so.

### C5. No positive result anywhere in the paper. MODERATE.

Every finding is a failure, including ours. Reviewers ask "so what should I do?" The
14-drug panel is the answer but is currently one short subsection.

**Fix.** Promote the panel intervention to a first-class result with its own figure, and
quantify what it costs (one function call) against what it catches (all instances).

### C6. §2.5 self-criticism is right but is framed as confession. MODERATE.

"Our method produced +23.44 kcal/mol" reads as incompetence unless framed as method.

**Fix.** Frame as a **positive control that worked**. The gate caught our error; that is
the intervention demonstrating its own value on the authors. Same facts, correct frame.

### C7. No figures. MODERATE, easily fixed.

A paper of this type needs the pipeline, the failure matrix and the panel curve as figures.

### C8. "A clinical partner" is vague. MINOR but reviewers notice.

Either name them with permission or state that the collaborator is anonymised at their
request.

---

## PAPER 2

### C9. This is a protocol, not a paper, and most target venues do not publish protocols. FATAL to the stated venue list.

Nature Communications and JACS Au do not publish empty pre-registrations. The correct
vehicle is a **Registered Report** (Stage 1 peer review before data collection), offered by
Royal Society Open Science, PLOS ONE, BMC Biology, Nature Human Behaviour and others, or
deposition on OSF with the full paper submitted later.

**Fix.** Rewrite the venue section honestly. Register the protocol on OSF now, submit the
completed study later, or submit as a Stage 1 Registered Report to a venue that accepts them.

### C10. No power calculation. n = 5 to 10 per arm is drastically underpowered. FATAL for Stage 1 review.

Fisher's exact test with 10 per arm detects only enormous effects. If the true hit rates
were 40% gated versus 10% ungated, power at n = 10 per arm is roughly 30%. The study would
more likely than not miss a real threefold effect.

**Fix.** Compute power explicitly, state the minimum detectable effect, and either raise n
or state honestly that the study is a pilot powered only for a very large effect.

### C11. H2 is not testable at this n. SERIOUS.

Spearman correlation across 5 to 10 compounds is noise. We already showed in this project
that rho moved 0.239 to 0.347 to 0.196 to 0.106 between n = 50 and n = 200.

**Fix.** Drop H2 or restate it as exploratory and not inferential.

### C12. The activity threshold is PENDING. FATAL if it stays that way.

The primary outcome depends on it. A pre-registration with an unspecified primary endpoint
provides no protection at all.

**Fix.** Fix a number, with justification, before anything ships.

### C13. No blinding, no randomisation, no assay-order control. MODERATE.

Plate position and run order are known confounders in binding assays.

**Fix.** Specify that arm identity is masked to whoever runs the assay, and that compounds
are randomised across plate positions.

### C14. "Hit rate" is undefined. MODERATE.

Binding? Cell activity? At what concentration? Undefined outcome, undefined test.

---

## Cross-cutting

### C15. Both papers claim more novelty than the prior art leaves. MODERATE.

Capuzzi et al. already report that 87 FDA-approved drugs carry PAINS alerts and already
caution against blind filtering. Our BRENK finding is a rediscovery in a new context, not a
new observation. Say so explicitly; a reviewer who finds it first will not be gentle.

### C16. Style: em dashes throughout, an AI tell. Replace all.

### C17. Every quantitative claim needs an n and a test. Several currently lack them.
