---
title: "Gates, not columns: a pre-registered prospective test of known-answer gating in computational compound selection"
author: "Obi Ebuka David (Autogon Inc.)"
date: "2026-09-05"
---

# Gates, not columns

## A pre-registered prospective test of known-answer gating in computational compound selection

**Obi Ebuka David**, Autogon Inc. Correspondence: davidobi023@gmail.com

**Stage 1 protocol, v2, 2026-09-05.** References verified against publisher records
(`REFERENCES.md`).

> **The experimental arm has not been run.** Hypotheses, predictions, power analysis,
> outcome definitions and stopping rules below are fixed before any compound has been
> ordered or assayed. They are not to be edited afterwards. Amendments belong in the dated,
> append-only log (§9), with reasons.

---

## Abstract

A companion self-audit (ref. 14) found that a generative drug-discovery campaign failed at
the bench for reasons its own output file had already recorded: a column named
`Epoxide Ring Present` reads True for all three molecules sent to synthetic chemists.
Prediction was not the weak link. The predictions were computed, written down, and given no
authority to stop anything. We rebuilt the pipeline so that every stage must reproduce a
panel of known answers before its output is used, and we report here the protocol for
testing whether that architectural change alters a **measured** outcome. The primary
hypothesis is that gated selection produces a higher hit rate than ungated selection from
the same library and the same docking scores. We report an exact power analysis showing
that the originally intended 5 to 10 compounds per arm is inadequate for a confirmatory
test (power 0.12 to 0.47 against plausible effects) and that **20 per arm** is the minimum
for 80 percent power against a 50 versus 10 percent difference. We additionally pre-register
a prediction against our own method: for one target the shortlist spans less than the
docking function's own error, and we predict no recoverable rank correlation with measured
activity there. Registering that prediction is what makes a null result informative rather
than disappointing.

---

## 1. Why this is a pre-registration

The companion audit reaches a negative conclusion about work we ourselves produced. Negative
conclusions about one's own past work are easy to reach selectively, and the obvious
objection, that we chose the analyses which made the failure legible, cannot be answered
after the fact.

It can be answered in advance. This document fixes hypotheses, arms, outcome definition,
threshold and analysis before any measurement exists. If the gated arm does not outperform
the ungated arm, that is reported as a failure of the central claim.

There is a second reason, specific to the subject matter. Our own replacement methods failed
twice during development in precisely the manner the audit describes. An MM-GBSA
implementation scored a crystallographic ligand at **+23.44 kcal/mol**, physically impossible
for a ligand resolved in the structure, and the control gate that should have caught it
counted results rather than checking the ranking its documentation promised. A project whose
thesis is that computational pipelines must constrain themselves is obliged to constrain
itself in advance.

---

## 2. Hypotheses

### H1, primary, confirmatory

**Gated selection outperforms ungated selection.** Among compounds drawn from the same gated
library and scored by the same docking function, those additionally passing every
known-answer gate (§3.2) show a higher hit rate at the threshold defined in §3.4 than those
selected by docking score alone.

*Falsified if* the difference in hit rate is not significant at one-sided α = 0.05 at the
enrolled n.

### H2, exploratory, not confirmatory

**Higher ladder rungs track measurement better.** Spearman ρ between predicted and measured
affinity increases along docking, then MM-GBSA, then MD-stable subset.

**Declared exploratory on statistical grounds.** At any n we can realistically fund, a
Spearman coefficient is uninterpretable. This project has already observed ρ move 0.239,
0.347, 0.196, 0.106 across n = 50 to 200 on a single dataset. H2 will be reported as an
observation with its n, and will not be tested.

### H3, registered against our own method

**A shortlist flat in the primary score is not rank-orderable, in silico or in vitro.** For
KRAS G12V the top-200 Vina scores span **1.80 kcal/mol**, inside Vina's ~2.5 kcal/mol error
(ref. 6). Two independent rescoring functions already fail to recover an ordering:
ρ = **+0.106** (MM-GBSA, n = 200) and **+0.259** (Vinardo), sharing 2 of 10 top compounds. We
predict **no meaningful rank correlation between any of these scores and measured activity
within the G12V shortlist**.

*Falsified if* measured activity tracks any of the three rankings there. If it does, the
mechanism proposed for H1 is wrong and we will report that.

---

## 3. Design

### 3.1 Arms

| arm | selection rule |
|---|---|
| **Gated** | passes every known-answer gate, then top-ranked by docking |
| **Ungated control** | same library, same docking scores, all gates disabled |

The ungated arm is not optional. Without it this is a case series and H1 is untestable. All
compounds are catalogue purchases, so synthesis is not a variable and both arms arrive with
vendor purity data.

### 3.2 The gates under test

1. Method validation, cognate redock RMSD < 2.0 Å.
2. Chemical reality, a 14-compound calibration panel must survive the filter.
3. ADMET, approved controls must pass; re-checked on every invocation.
4. Ordering, stability gate before retrosynthesis.
5. Rescoring, cognate ligand must score as a binder with sensible control ordering.

### 3.3 Power analysis

Exact power of Fisher's exact test, one-sided α = 0.05, enumerating all outcomes.

**Table 1. Power by arm size and assumed effect.**

| n per arm | 30% vs 10% | 40% vs 10% | 50% vs 10% | 60% vs 5% |
|---|---|---|---|---|
| 5 | 0.02 | 0.05 | 0.12 | 0.28 |
| 10 | 0.14 | 0.29 | 0.47 | 0.80 |
| 15 | 0.26 | 0.46 | 0.67 | 0.94 |
| **20** | 0.34 | 0.62 | **0.84** | 0.99 |
| 30 | 0.49 | **0.80** | 0.95 | 1.00 |
| 50 | 0.75 | 0.96 | 1.00 | 1.00 |

**Consequences, stated plainly.**

- The originally intended **5 to 10 compounds per arm is not adequate** for a confirmatory
  test. At 10 per arm the study would miss a real fourfold effect roughly seven times in ten.
- **20 per arm** is the minimum for a confirmatory H1 against a 50 versus 10 percent effect
  (power 0.84).
- **30 per arm** is required for a fourfold effect (power 0.80).
- If funding permits fewer than 20 per arm, the study proceeds **as a declared pilot**, H1 is
  reported as untested rather than negative, and the observed rates inform a later powered
  study. This decision is recorded in §9 before ordering.

### 3.4 Outcome definition

**Primary outcome.** A compound is a hit if it produces ≥ 50 percent inhibition at 10 µM in
the primary binding assay, in at least two of three technical replicates.

The threshold, concentration and replicate rule are fixed here. A pre-registration with an
unspecified primary endpoint provides no protection, so no element of this definition may
move after compounds ship.

**Assay.** Biochemical binding against the relevant KRAS variant, run by a contract research
organisation. Cell-based activity, if run, is secondary and exploratory, because it
additionally requires permeability and target engagement.

### 3.5 Bias control

- **Masking.** Arm identity is withheld from the personnel running the assay. Compounds are
  supplied as coded identifiers.
- **Randomisation.** Compounds are randomised across plate positions to break the confound
  between arm and plate location.
- **Order.** Run order is randomised and recorded.

### 3.6 Stopping and reporting rules

- No compound is added to or removed from either arm after ordering.
- If fewer than 3 compounds per arm return usable data, H1 is reported as **untested**.
- Compounds failing QC, solubility or stability are reported, not silently dropped.
- The outcome is reported regardless of direction.

---

## 4. What already exists

**Pipeline.** Eleven gated phases. Nine gates exist because a tool had already failed
silently (ref. 14).

**Method validation, four targets.** Cognate redock RMSD 0.67 Å (G12C, 8AFB), 0.88 Å (G12D,
9HFK), 1.55 Å (G12V, 9YMQ), 0.99 Å (G12R, 9XB7), all under the 2.0 Å criterion, using
AutoDock Vina 1.2.7 (ref. 6).

**Selection heuristic, validated against a random arm.** Similarity-based selection median
−8.68 versus random −8.24 kcal/mol.

**Screens.** From 518,662 gated purchasable compounds: G12D n = 19,639 and G12V n = 9,913,
covering 81 percent of codon-12-mutant PDAC (ref. 8). Neither produced a compound competitive
with the clinical inhibitors (refs. 7, 9, 10). G12R in progress, taking coverage to 98
percent of codon-12-mutant tumours.

**Rung 2, MM-GBSA, gated.** G12V controls: cognate AM-2383 −33.22, RP03514 −33.02,
G12D-selective MRTX1133 −5.70 kcal/mol. The method places the wrong-variant drug last
unprompted and cannot separate two close analogues 0.2 kcal/mol apart. Both facts are
reported; the second bounds what the first licenses.

---

## 5. What is missing

1. Compounds ordered. Weeks of lead time, and the rate-limiting step.
2. The ungated control arm, specified and funded at the n selected in §3.3.
3. The assay contracted.
4. **Phase 10, laboratory capture.** Ingestion of purity, LC-MS, NMR and assay readouts onto
   the molecule record that predicted them. Not built. Nothing here is verifiable without it.
5. Rung 3, MD pose stability, for H2's middle point.

---

## 6. Compound source, decision rule fixed in advance

The G12V shortlist **cannot be described as top-ranked**: three scoring methods disagree on
its order, sharing 2 of 10 top compounds (H3). Two options remain, and the rule, not the
choice, is registered here.

- **(a)** Order the intersection of the rankings as an explicitly **unranked diversity set**,
  described as such throughout.
- **(b)** Draw from **G12R**, whose screen is in progress.

**Rule.** Option (b) is taken if and only if the G12R top-200 Vina scores span more than
2.5 kcal/mol, that is, more than the docking function's own error. Otherwise option (a).
The observed spread and the resulting decision are recorded in §9 before ordering.

---

## 7. Limitations known in advance

- **Power.** See §3.3. Below 20 per arm this is a pilot and will say so.
- **One target family.** All results are KRAS in pancreatic cancer.
- **Gates validate methods, not predictions.** Every gate checks that a tool reproduces known
  answers. None establishes that a prediction about a novel compound is correct.
- **Catalogue compounds are not novel chemical matter.** This tests selection, not invention.
- **Assay scope.** A binding assay tests binding.
- **Self-interest.** We designed the gates being tested. The protocol is fixed in advance and
  the data will be released for exactly this reason.

---

## 8. Data and code availability

`github.com/eobi/pancreatic_cancer_research`, including all failed validations.

---

## 9. Amendments and pre-specified values

*Append-only. Hypotheses in §2 and the outcome definition in §3.4 are frozen.*

- **2026-09-05** Document created. H1 to H3 fixed. Outcome definition fixed at ≥ 50 percent
  inhibition at 10 µM, 2 of 3 replicates. Power analysis computed. No compound ordered.
- **PENDING** n per arm, with the funding decision and whether the study is confirmatory or a
  declared pilot.
- **PENDING** Compound source under §6, with the observed G12R spread.

### Results recorded against this pre-registration

**2026-09-05. H3 premise confirmed, H3 itself untested.** MM-GBSA completed on all 200 G12V
compounds.

| quantity | predicted | measured |
|---|---|---|
| Vina spread across shortlist | ~1.4 kcal/mol | **1.80 kcal/mol** |
| rank correlation with an independent method | near zero | **ρ = +0.106** (p = 0.13, n = 200) |

This confirms the **premise** of H3. **H3 concerns measured activity and remains untested.**
No compound has been assayed. This entry is not to be read as H3 having been met.

---

## 10. References

Numbering follows `REFERENCES.md` so both manuscripts share one bibliography.

6. Eberhardt, J., Santos-Martins, D., Tillack, A. F. & Forli, S. AutoDock Vina 1.2.0. *J. Chem. Inf. Model.* **61**, 3891–3898 (2021). doi:10.1021/acs.jcim.1c00203
7. Wang, X. et al. Identification of MRTX1133, a Noncovalent, Potent, and Selective KRAS^G12D^ Inhibitor. *J. Med. Chem.* **65**, 3123–3133 (2022). doi:10.1021/acs.jmedchem.1c01688
8. Ardalan, B., Ciner, A., Baca, Y. et al. Distinct Molecular and Clinical Features of Specific Variants of KRAS Codon 12 in Pancreatic Adenocarcinoma. *Clin. Cancer Res.* **31**, 1082–1090 (2025). doi:10.1158/1078-0432.CCR-24-3149
9. Canon, J. et al. The clinical KRAS(G12C) inhibitor AMG 510 drives anti-tumour immunity. *Nature* **575**, 217–223 (2019). doi:10.1038/s41586-019-1694-1
10. Hallin, J. et al. The KRAS^G12C^ Inhibitor MRTX849. *Cancer Discov.* **10**, 54–71 (2020). doi:10.1158/2159-8290.CD-19-1167
14. Obi, E. D. Computed, recorded, ignored: a self-audit of a generative drug-discovery campaign whose failure was visible in its own output. Companion manuscript (2026).
