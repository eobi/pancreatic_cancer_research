# Known-answer gating at every stage of a computational screening pipeline: a pre-registered prospective test

**Obi Ebuka David**
Autogon Inc.
Correspondence: davidobi023@gmail.com

**Pre-registration v1 — 2026-09-05.** Target: Nature Machine Intelligence / Nature
Communications / JACS Au.
*All references verified against publisher records on 2026-09-05; see `REFERENCES.md`.*

> **Status: the experimental arm has not been run.** Hypotheses, predictions, analysis plan
> and stopping rules below are fixed **before** any compound has been ordered or assayed.
> They must not be edited afterwards; amendments belong in the dated appendix (§9), with
> reasons. This document is the record that the predictions preceded the data.

---

## Abstract

Computational screening pipelines chain together scoring, filtering and prioritisation
tools, each individually validated, and consume each stage's output on the assumption that
the tool works. In a companion retrospective study we documented five independent tools in
such a stack failing **silently and directionally** — returning confident, well-formed
output that was wrong, and wrong against the molecules known to be correct — with a
downstream cost of approximately one year of unproductive synthesis. We rebuilt the
pipeline so that every stage must reproduce a panel of known answers before its output is
used, and report here the pre-registered protocol for testing whether that discipline
changes the **measured** outcome. The primary hypothesis is that gated selection yields a
higher hit rate at a pre-specified activity threshold than ungated selection from the same
library and the same docking scores. Secondary hypotheses concern monotonicity of a
fidelity ladder (docking → MM-GBSA → molecular-dynamics pose stability) against measured
affinity. We additionally pre-register a prediction **against our own method**: because the
shortlist for one target spans less than the docking function's own error, we predict no
recoverable rank correlation with measured activity for that target. Registering that
prediction is what makes a null result informative rather than a disappointment. We state
in advance what would falsify each hypothesis, and commit to reporting the outcome
regardless of direction.

---

## 1. Why a pre-registration

The retrospective audit that motivates this work (companion paper) reaches a negative
conclusion: the tools failed, the molecules could not be made, and the metrics did not
show it. Negative conclusions of that kind are cheap to reach after the fact and easy to
over-fit to. The natural objection — that we selected the analyses which made the failure
legible — cannot be answered retrospectively.

It can be answered prospectively. This document fixes the hypotheses, the comparison arms,
the activity threshold and the analysis before any measurement exists. If the gated arm
does not outperform the ungated arm, that is reported as a failure of the central claim.

There is a second reason, specific to this project's subject matter. Our own methods failed
twice during development in exactly the manner the companion paper describes: an MM-GBSA
implementation scored a crystallographic ligand at **+23.44 kcal/mol** — physically
impossible for a ligand resolved in the structure — and the control gate that should have
caught it *counted* results rather than checking the ranking its documentation promised. A
project whose thesis is that computational tools fail silently is obliged to constrain its
own degrees of freedom in advance.

---

## 2. Hypotheses

### H1 — Primary

**Gated selection outperforms ungated selection.** For compounds drawn from the same gated
library, scored by the same docking function, selection that additionally passes every
known-answer gate yields a higher hit rate at a pre-specified activity threshold than
selection by docking score alone.

*Falsified if:* the two arms give hit rates whose difference is not distinguishable from
zero at the pre-specified n.

### H2 — Fidelity ladder monotonicity

**Higher rungs correlate better with measurement.** Spearman ρ between predicted and
measured affinity increases along docking → MM-GBSA → MD-stable subset.

*Falsified if:* ρ does not increase, or decreases, along the ladder.

### H3 — Our own null, registered in advance

**A shortlist flat in the primary score is not rank-orderable, in silico or in vitro.**
For KRAS G12V, the top-200 Vina scores span **1.80 kcal/mol**, inside Vina's own ~2.5
kcal/mol error (ref. 6). Two independent rescoring functions already fail to recover an
ordering: Spearman ρ = **+0.106** (MM-GBSA, n = 200) and **+0.259** (Vinardo), sharing only
**2 of 10** top-ranked compounds. We therefore predict **no meaningful rank correlation
between any of these scores and measured activity within the G12V shortlist**.

*Falsified if:* measured activity tracks any of the three rankings within that shortlist.
If it does, the mechanism proposed in H1 is wrong and we will say so.

---

## 3. Design

### 3.1 Arms

| arm | selection rule | n |
|---|---|---|
| **Gated** | passes every known-answer gate (§3.2), then top-ranked | 5–10 |
| **Ungated control** | same library, docking score alone, all gates disabled | 5–10 |

**The ungated arm is not optional.** Without it this is a case series, not a controlled
test, and H1 is untestable. Compounds are ordered from catalogue suppliers, so synthesis
is not a variable: both arms arrive with vendor purity data.

### 3.2 The gates being tested

1. **Method validation** — cognate redock RMSD < 2.0 Å.
2. **Chemical reality** — 14-drug panel must survive the filter.
3. **ADMET** — approved controls must pass; re-checked every invocation.
4. **Route ordering** — stability gate before retrosynthesis.
5. **Rescoring** — cognate ligand must score as a binder, controls must order sensibly.

### 3.3 Pre-specified analysis

- Primary: difference in hit rate between arms, Fisher's exact test, α = 0.05.
- Secondary: Spearman ρ per ladder rung, reported with n.
- **Activity threshold fixed before unblinding.** To be entered in §9 with a date, before
  compounds ship.
- All compounds assayed are reported, including failures and compounds that do not
  dissolve, degrade, or fail QC.

### 3.4 Stopping and reporting rules

- No compound is added to or removed from either arm after ordering.
- If fewer than 3 compounds per arm return usable data, H1 is reported as **untested**,
  not as negative.
- Outcome is reported regardless of direction.

---

## 4. What already exists

**Pipeline.** Eleven gated phases; nine gates exist because a tool had already failed
silently (companion paper).

**Method validation, four targets.** Cognate redock RMSD: **0.67 Å** (G12C, 8AFB),
**0.88 Å** (G12D, 9HFK), **1.55 Å** (G12V, 9YMQ), **0.99 Å** (G12R, 9XB7) — all under the
2.0 Å criterion, using AutoDock Vina 1.2.7 (ref. 6).

**Selection heuristic, validated against a random arm.** Similarity-based selection median
**−8.68** vs random **−8.24** kcal/mol.

**Screens.** From 518,662 gated purchasable compounds: G12D n = 19,639, G12V n = 9,913,
covering **81% of codon-12-mutant PDAC** (ref. 8; ≈68% of all PDAC). G12R in progress,
bringing coverage to **98% of codon-12-mutant PDAC** (≈83% of all PDAC). Neither completed
screen produced a compound competitive with the clinical inhibitors (refs. 7, 9, 10).

**Rung 2 (MM-GBSA), gated.** Controls on G12V: cognate AM-2383 **−33.22**, RP03514
**−33.02**, G12D-selective MRTX1133 **−5.70** kcal/mol. The method places the wrong-variant
drug last unprompted, and **cannot** separate two close analogues 0.2 kcal/mol apart. Both
facts are reported; the second bounds what the first licenses.

**Search-effort sensitivity.** Screening exhaustiveness 4 versus 128: mean score drift
**+0.08 kcal/mol**, ρ = 0.821, 8/10 of the top 10 retained, at 1/31 the cost. Screening
consumes rank and tolerates shallow search; validation consumes geometry and does not — on
G12R the same parameter change moved a cognate pose **7.19 Å → 0.99 Å** while moving its
score only −9.28 → −9.80.

---

## 5. What is missing

1. **Compounds ordered.** Weeks of lead time; the rate-limiting step for this paper.
2. **The ungated control arm**, specified and funded.
3. **An assay** — binding or cell-based, against the relevant variant, threshold fixed in
   advance.
4. **Phase 10, lab capture** — ingestion of NMR, LC-MS, purity and assay readouts onto the
   molecule record that predicted them. **Not built.** Nothing here is verifiable without
   it.
5. **Rung 3, MD pose stability** on the ordered set, for H2's middle point.

---

## 6. Which compounds, and an honest constraint

The G12V shortlist **cannot be described as top-ranked**. Three scoring methods do not agree
on an order within it (H3), sharing 2 of 10 top compounds. Two options remain, and the
choice must be recorded before ordering:

- **(a)** Order the intersection of the rankings as an explicitly **unranked diversity
  set**, described as such throughout.
- **(b)** Draw the ordered set from **G12R**, whose screen is in progress and whose
  shortlist may not be flat.

Option (b) is preferred if the G12R score distribution spans more than the docking
function's error. That is a property of data not yet in hand, and the decision rule — not
the decision — is what is registered here.

---

## 7. Limitations known in advance

- **Small n.** 5–10 compounds per arm detects only a large effect. A null result will be
  reported as underpowered, not as evidence of no effect.
- **One target family.** All results are KRAS in PDAC.
- **Gates validate methods, not predictions.** Every gate checks that a tool reproduces
  known answers. None establishes that a prediction about a novel compound is correct.
- **Catalogue compounds are not novel chemical matter.** This tests selection, not
  invention. No composition-of-matter claim arises.
- **Assay choice constrains interpretation.** A binding assay tests binding; cell activity
  additionally requires permeability and target engagement.

---

## 8. Data and code availability

`github.com/eobi/pancreatic_cancer_research` — code, gated libraries, screening results,
rescoring outputs, and all validation records **including failed validations**. The G12R
validation that failed at 7.19 Å is retained alongside the one that passed at 0.99 Å.

---

## 9. Amendments and pre-specified values

*Entries are dated and append-only. Hypotheses in §2 are frozen.*

- **2026-09-05** — Document created. Hypotheses H1–H3 fixed. No compound ordered.
- **PENDING** — Activity threshold for H1, to be entered **before compounds ship**.
- **PENDING** — Compound-source decision under §6, with the G12R score spread that
  justified it.

### Results recorded against this pre-registration

**2026-09-05 — H3 premise confirmed; H3 itself untested.** MM-GBSA completed on all 200
G12V compounds (8 workers, 286 s each, 14.3 h).

| quantity | predicted | measured |
|---|---|---|
| Vina spread across shortlist | ~1.4 kcal/mol | **1.80 kcal/mol** |
| rank correlation with an independent method | near zero | **ρ = +0.106** (p = 0.13, n = 200) |

This confirms the **premise** of H3 — the shortlist is flat, and a second independent
method agrees with a third that no ordering is recoverable in silico. **H3 concerns
measured activity and remains untested.** No compound has been assayed. This entry is not
to be read as H3 having been met.

---

## 10. References

*Verified 2026-09-05; full list in `papers/REFERENCES.md`.*

6. Eberhardt, J., Santos-Martins, D., Tillack, A. F. & Forli, S. AutoDock Vina 1.2.0.
   *J. Chem. Inf. Model.* **61**, 3891–3898 (2021). doi:10.1021/acs.jcim.1c00203
7. Wang, X. et al. Identification of MRTX1133, a Noncovalent, Potent, and Selective
   KRAS^G12D Inhibitor. *J. Med. Chem.* **65**, 3123–3133 (2022).
   doi:10.1021/acs.jmedchem.1c01688
8. Ardalan, B., Ciner, A., Baca, Y. et al. Distinct Molecular and Clinical Features of
   Specific Variants of KRAS Codon 12 in Pancreatic Adenocarcinoma. *Clin. Cancer Res.*
   **31**, 1082–1090 (2025). doi:10.1158/1078-0432.CCR-24-3149
9. Canon, J. et al. The clinical KRAS(G12C) inhibitor AMG 510 drives anti-tumour immunity.
   *Nature* **575**, 217–223 (2019). doi:10.1038/s41586-019-1694-1
10. Hallin, J. et al. The KRAS^G12C Inhibitor MRTX849. *Cancer Discov.* **10**, 54–71
    (2020). doi:10.1158/2159-8290.CD-19-1167

*(Numbering follows `REFERENCES.md` so the two manuscripts share one bibliography.)*
