# Paper 2 — Prospective test: does gating at every stage change the outcome?

**Status:** hypothesis and protocol fixed; **the experiment has not been run.** Written now,
before the data exists, so the predictions are on record and cannot be adjusted afterwards.
**This is the paper that reaches the A-list tier — and only if the wet-lab arm is done.**

**Author:** Obi Ebuka David
**Affiliation:** *decide before submission* (see Paper 1).

---

## Title (working)

**Known-answer gating at every stage of computational drug discovery: a prospective test
against laboratory measurement**

Alternatives:
- *Refusing to believe a tool until it reproduces a known answer: prospective validation
  on KRAS in pancreatic cancer*
- *From 500,000 compounds to five, each carrying a number that means something*

---

## Hypothesis

**H1 (primary, prospective).** A pipeline in which every stage must reproduce a known
answer before its output is used will select compounds whose **measured** activity is
materially better than compounds selected by the same pipeline with the gates disabled.

Stated so it can fail: for compounds ordered and assayed,

> **gated selection yields a higher hit rate at a pre-specified activity threshold than
> ungated selection from the same library and the same docking scores.**

**H2 (calibration).** The fidelity ladder is monotone: predictions from higher rungs
(MM-GBSA, then MD pose stability, then FEP) correlate more strongly with measured affinity
than docking score alone.

**H3 (falsification target for our own method).** Where a rescoring function cannot
separate close analogues in silico, it will not separate them in vitro either. Stated
explicitly because we already have in-silico evidence pointing this way and must not
quietly drop it if the assay disagrees.

### Pre-specified predictions — fix these before ordering

1. **Gated > ungated** hit rate at the activity threshold, in a head-to-head arm.
2. **Ladder monotonicity:** Spearman rho(measured, prediction) rises from docking → MM-GBSA
   → MD-stable subset.
3. **Prediction of our own null:** because Vina scores across the G12V top-200 span only
   **1.4 kcal/mol** — inside Vina's own ~2.5 kcal/mol error — we predict **no meaningful
   rank correlation with measured activity within that shortlist.** A shortlist this flat
   should not be rank-orderable by any method. If measured activity *does* track the
   ranking, H1's mechanism is wrong and we say so.

### What would falsify the whole paper

- Gated and ungated arms give indistinguishable hit rates.
- Higher ladder rungs do not correlate better with measurement than docking.
- No ordered compound shows activity, leaving nothing to correlate. (A real outcome, given
  the screening results below — and it must be reported, not buried.)

---

## Why this is the A-list paper and Paper 1 is not

Paper 1 is retrospective and negative: it explains why a past campaign failed. Valuable,
but its ceiling is set by having no forward measurement.

This paper inverts that. **The gates make predictions before the assay runs, and the assay
adjudicates.** That converts the work from "here is why the old approach failed" into "here
is a system, prospectively tested, and here is the failure analysis showing why it was
needed." Prior art on individual components stops mattering once the claim is a
prospectively validated end-to-end result — which is exactly the gap Paper 1's prior-art
table exposes.

It is also the only version in which a **negative** result is still publishable: a
pre-registered prediction that fails is a finding, whereas an unregistered one is a
disappointment.

---

## What already exists

**Pipeline, built and gated.** Eleven phases, each with a known-answer gate. Nine of the
eleven gates were added because a tool had already failed silently (documented in Paper 1).

**Method validation.** Cognate redock **0.67 Å** (G12C), **0.88 Å** (G12D) — under the
2.0 Å criterion. Control spread 2.96 and 4.84 kcal/mol.

**Selection heuristic validated against a random control arm.** Similarity-based selection
median **−8.68** vs random **−8.24** kcal/mol. The heuristic is measured, not assumed.

**Screens, by disease prevalence in pancreatic ductal adenocarcinoma:**

| variant | % of PDAC | compounds screened | result |
|---|---|---|---|
| G12D | 39% | 19,639 | essentially nothing |
| G12V | 29% | 9,913 | 2 past the cognate ligand |
| G12R | 15% | **pending** | — |
| G12C | 1.7% | 2,000 | 82 hits — *wrong variant for this disease* |

Coverage **68%**; G12R takes it to **83%**.

**Rung 2 (MM-GBSA), built and gated.** Controls on G12V: cognate AM-2383 **−33.22**,
RP03514 **−33.02**, G12D-selective MRTX-1133 **−5.70** kcal/mol. The method correctly
places the wrong-variant drug last without being told which variant it is looking at, and
**cannot** separate two close analogues 0.2 kcal/mol apart. Both facts go in the paper.

**Independent rescoring disagrees with docking.** Vinardo rho = **0.259** and failed its
own controls on this target. This is why H3 exists.

---

## What is missing — the entire experimental arm

1. **Order 5–10 compounds.** Catalogue compounds: synthesis already solved, delivered with
   purity data. This sidesteps the failure mode of Paper 1 entirely.
2. **Ungated control arm.** Compounds selected from the same library by docking score
   alone, gates disabled. Without this arm there is no comparison and no paper.
3. **Assay.** Binding or cell-based potency against the relevant KRAS variant, with the
   activity threshold **fixed in advance**.
4. **Phase 10, lab capture.** Ingest NMR, LC-MS, purity and assay readouts onto the
   molecule record that predicted them. Currently NOT BUILT, and nothing here is
   verifiable without it.
5. **Rung 3, MD pose stability** on the ordered set — needed for H2's middle point.

**Critical-path note.** Compound delivery takes weeks. Ordering is the rate-limiting step
for this paper, not compute.

---

## Figures (planned)

1. **The funnel with its gates**, annotated with what each gate rejected and why.
2. **Gated vs ungated arms:** measured activity distributions, the head-to-head for H1.
3. **Ladder monotonicity:** rho(measured, predicted) by rung, for H2.
4. **The honest negative:** Vina score spread (1.4 kcal/mol) against measured activity,
   testing prediction 3.
5. **Coverage by variant frequency** — why G12C results were the wrong answer to the
   pancreatic question.

---

## What this paper will **not** claim, however the data falls

- That the pipeline finds a drug. It selects candidates for measurement; nothing here is a
  therapeutic claim.
- That the gates are complete. They catch the failures documented in Paper 1. Others exist.
- That in-silico rungs replace an assay. The ladder narrows 10,000 compounds to five worth
  measuring — it does not remove the measurement.
- Anything about efficacy in disease. No animal or patient data is in scope.

---

## Target venues

| venue | condition |
|---|---|
| Nature Machine Intelligence | if H1 holds with a clean head-to-head arm |
| Nature Communications | if H1 holds, or a well-powered pre-registered null |
| JACS Au | chemistry-facing framing |
| J. Chem. Inf. Model. | fallback if the experimental arm stays small |

The tier depends almost entirely on whether the ungated control arm is run. Without it
this is a case report; with it, it is a controlled prospective test.

---

## Protocol integrity

Because this file predates the data: **do not edit the hypotheses or the pre-specified
predictions after ordering compounds.** Amendments go in a dated appendix below, with the
reason. This costs nothing now and is the difference between a prediction and a
post-hoc explanation.

### Amendments
*(none — hypotheses and predictions unchanged)*

---

## Results recorded against the pre-registration

**2026-09-05 — in-silico premise of prediction 3 confirmed; the prediction itself untested.**

Prediction 3 was: *because the G12V top-200 Vina scores span only 1.4 kcal/mol, we predict
no meaningful rank correlation with measured activity.*

Completed: MM-GBSA on all 200 (8 workers, 286 s each, 14.3 h wall).

| quantity | predicted | measured |
|---|---|---|
| Vina spread across the shortlist | ~1.4 kcal/mol | **1.80 kcal/mol** |
| rank correlation, Vina vs an independent method | near zero | **rho = +0.106** (p = 0.13, n = 200) |

**What this does and does not establish.** It confirms the *premise* — the shortlist is
flat in the primary score, and a second independent method (MM-GBSA, molecular mechanics)
agrees with a third (Vinardo, empirical, rho = 0.259) that no ranking is recoverable in
silico. **Prediction 3 concerns measured activity and remains untested**; no compound has
been assayed. This entry must not be read as the prediction having been met.

**Consequence for the experimental design.** Compounds ordered from the G12V shortlist
cannot be described as top-ranked, because the three available methods do not agree on a
rank (top-10 overlap between Vina and MM-GBSA: **2 of 10**). Either order the intersection
as an explicitly unranked diversity set, or draw the ordered set from a target whose
shortlist is not flat. G12R was validated on 2026-09-05 (cognate redock 0.99 A) and is the
better source.
