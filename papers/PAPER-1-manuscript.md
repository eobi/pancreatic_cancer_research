# Silent, directional failure in the computational filters that vet generated molecules

**Obi Ebuka David**
Autogon Inc.
Correspondence: davidobi023@gmail.com

**Draft v2 — 2026-09-05.** Target: Nature Communications / JACS Au.
*All references verified against publisher records on 2026-09-05; see `REFERENCES.md`.*

---

## Abstract

Generative models for small-molecule design are typically evaluated on docking score,
synthetic-accessibility heuristics and distributional validity metrics. We report a
retrospective audit of a generative campaign against KRAS in pancreatic ductal
adenocarcinoma in which three molecules reached synthetic chemists and approximately one
year of laboratory effort produced no compound. The audit reproduces that outcome from
structure alone: of 73 generated molecules, **none** survive a standard pre-synthesis
filter that 57.4% of 902,833 purchasable compounds pass, and none contains an aromatic
ring. Investigating why the campaign's own vetting stack did not catch this, we find a
failure mode we term **silent and directional**: five independent, widely used tools —
structural-alert catalogues, an ADMET predictor, a retrosynthesis planner, a
deep-learning docking method and a physics-based rescoring function — each returned
well-formed, confident output that was wrong, and wrong in a consistent direction, namely
rejecting or mis-ranking the molecules known to be correct. No tool raised an error. Because
the errors are directional rather than random, they are invisible to aggregate pass-rate and
enrichment metrics. We show that the failures are detectable by one inexpensive
intervention — requiring each tool to reproduce a panel of molecules with known answers
before its output is used — and that panel **size** is the operative variable: a 14-drug
panel detects failures that a 3-compound reference set misses. We rebuild the pipeline with
a known-answer gate at every stage, report four validated targets and three completed
screens, and quantify what the gates cost and catch. All code, data and negative results
are released.

---

## 1. Introduction

The proposition that generative models can design novel bioactive molecules rests on an
evaluation stack: a scoring function to estimate binding, filters to remove liabilities, a
synthetic-accessibility estimate, and increasingly a retrosynthesis planner to confirm a
route exists. Each component is individually validated in the literature. The stack as a
whole is rarely validated against the only endpoint that matters — whether a chemist can
make the molecule and whether it does anything.

That generative models propose unsynthesizable molecules is established (ref. 1). That
structural-alert catalogues over-reject is likewise documented (refs. 2, 3). Capuzzi et al.
report that **87 small-molecule FDA-approved drugs carry PAINS alerts**, and caution
explicitly against using such filters to triage compounds. That deep-learning docking can produce
physically invalid poses has been demonstrated systematically (ref. 4). We do not claim novelty for any of these individually, and we cite
them as the entry point rather than the contribution.

What has not, to our knowledge, been characterised is the **shared shape** of these
failures and its consequence. In the campaign we audit, five tools of different type failed
simultaneously, all in the same direction, and none announced a problem. A filter that
rejects every approved drug in its domain still returns a tidy ranked list and a plausible
pass rate. A docking method with 4 kcal/mol of run-to-run variance still prints scores to
two decimal places. The output of a broken tool in this stack is indistinguishable, by
inspection, from the output of a working one.

Two things make this report possible. First, ground truth: the molecules went to a bench,
and the bench failed, over a documented period. Most work in this area benchmarks in silico
and stops. Second, the tools were re-examined against molecules whose answers were already
known — approved drugs and co-crystallised ligands — which converts "this looks reasonable"
into "this is wrong, and here is the compound it is wrong about."

We report the audit, the five failures, the intervention that detects them, and the
rebuilt pipeline. We also report, in full, the failures of our *own* replacement methods,
including one that produced a physically impossible energy for a crystallographic ligand.
That inclusion is deliberate: a paper arguing that computational tools fail silently would
be self-refuting if it presented its own tools as having worked first time.

---

## 2. Results

### 2.1 The generated molecules could not exist

A 2025 campaign produced 73 molecules conditioned on KRAS, selected by docking thresholds alone (DiffDock confidence ≥ −1.5, GNINA minimised
affinity ≤ −5.0 kcal/mol), **with no stability or reactivity criterion**. A shortlist of 73 was reported; three structures were sent
for synthesis.

Applying a standard pre-synthesis filter (aromatic-ring requirement, unstable-group SMARTS,
self-reactivity check, PAINS/BRENK alerts; Methods 4.3):

| set | n | pass |
|---|---|---|
| Generated molecules | 73 | **0 (0.0%)** |
| Purchasable compounds (ZINC) | 902,833 | **57–76%** |

The failure is categorical, not marginal. **0 of 73 contain an aromatic ring**; both
reference drugs for the target do. Of the 73-molecule reported shortlist, 63 carry a
genotoxic or unstable group, mean 1.9 per molecule, and **15 are self-reactive** — they
contain functional-group pairs that destroy one another within the same structure.

The three molecules sent to chemists carry, between them, a **triazane**, an **epoxide**,
and in two cases a **free aldehyde**. Approximately one year of synthesis effort followed
without delivering material. Cost, a relocation and reagent-purity problems contributed;
the audit indicates the molecules were not viable targets regardless.

*This subsection restates a known result. Its role is to establish the ground truth that
the rest of the paper depends on.*

### 2.2 Five independent tools failed, all in the same direction

We then asked why the campaign's vetting stack did not flag any of this, and re-ran each
component against molecules whose correct classification is known — approved drugs for the
target and its class, and co-crystallised ligands.

**(i) Structural alerts reject the mechanism.** The BRENK catalogue (ref. 5) flags acrylamide as
`Michael_acceptor_1`. Acrylamide is the covalent warhead of both **sotorasib** and
**adagrasib**, approved KRAS G12C inhibitors — the alert fires on the feature responsible
for the drug's activity. Without an exemption the filter rejects both approved drugs while
passing generated molecules.

**(ii) An over-broad SMARTS rejects an approved drug.** A nitroso pattern
`[NX3]-[OX2H0,OX1]` also matches nitro groups, rejecting **venetoclax**. Narrowing to
`[NX2]=[OX1]` plus an explicit hydroxylamine pattern resolves it.

**(iii) A stability rule rejects a clinical candidate.** Our own gate rejected
**MRTX1133**, a G12D inhibitor in clinical development (ref. 7), on the alkyne in its structure.
This was found only because the gate had been exposed as a service with a startup
self-check; the equivalent script had run for two days with the fault present.

**(iv) ADMET thresholds reject every positive control.** Applying textbook cutoffs to
ADMET-AI predictions (ref. 12)
(DILI < 0.70, hERG < 0.70) to a 200-compound shortlist rejected **199 of 200**, including
sotorasib and adagrasib. **Every approved control failed.** Thresholds derived from the
control panel instead retain them; DILI and hERG are demoted to informational.

**(v) Retrosynthesis ranks an impossible molecule above a marketed drug.** Using
AiZynthFinder (ref. 11):

| molecule | precursors in stock | steps |
|---|---|---|
| Impossible generated molecule ("Hit 41") | **80%** | 6 |
| Adagrasib (marketed) | **71%** | 6 |

A triazane that decomposes on formation still admits a valid formal disconnection.
Retrosynthesis answers *"if this existed, what would assemble it"* and never *"can this
exist"*, so it cannot serve as a feasibility gate. Run alone, it reproduces the original
failure with additional confidence attached.

In every case the tool returned well-formed output and raised no error, and in every case
the error direction was the same: **against the molecules known to be correct.**

### 2.3 Detection requires a panel, and panel size is the variable

All five failures are detectable by requiring each tool to reproduce known answers before
its output is used. The operative variable is panel size.

A 3-compound reference set — a common choice — detected **none** of the five. A 14-drug
panel spanning the target class, approved covalent inhibitors, and structurally diverse
marketed drugs detected **all five**. The cost is one function call per tool invocation;
in the rebuilt pipeline the ADMET stage re-runs its control check on every invocation and
exits if any control fails.

### 2.4 Rebuilt pipeline: what the gates cost and what they catch

We rebuilt the pipeline with a known-answer gate at every stage (Methods 4.2). Eleven
phases; **nine of the eleven gates exist because a tool had already failed silently.**

**Method validation.** Blind docking with CNN rescoring showed **4.0 kcal/mol run-to-run
variance on a single molecule** (sotorasib: −3.80 and −7.78 on repeat runs) and could not
rank. Replacing it with site-directed docking (AutoDock Vina 1.2.7; ref. 6) into a box defined by the crystallographic
ligand gives cognate redock RMSDs of **0.67 Å** (G12C, 8AFB), **0.88 Å** (G12D, 9HFK),
**1.55 Å** (G12V, 9YMQ) and **0.99 Å** (G12R, 9XB7), against a < 2.0 Å criterion.

**Target selection by disease prevalence.** Among 3,755 PDAC tumours carrying a codon-12
KRAS mutation, the variant distribution is **G12D 47%, G12V 34%, G12R 17%, G12C 2%**
(ref. 8). *(Denominator: codon-12-mutant tumours. As fractions of all PDAC — KRAS is
mutated in >90% of cases — these correspond to approximately 40%, 29%, 14% and 1.7%.)*

The original campaign's structural work centred on **G12C**, which has approved drugs
(refs. 9, 10) and abundant liganded structures — and which is predominantly a **lung**
variant, accounting for 2% of codon-12-mutant PDAC. Structure availability and clinical
precedent selected the target; disease prevalence did not. Prevalence now drives target
intake.

**Selection heuristic, validated against a control arm.** Similarity-based selection was
compared against a random arm from the same gated library: median docking score **−8.68**
vs **−8.24** kcal/mol. The heuristic is measured rather than assumed.

**Screens.** Across 518,662 gated purchasable compounds, screens covering **81% of codon-12-mutant PDAC** (G12D, n = 19,639 compounds;
G12V, n = 9,913) returned **no compound
competitive with the clinical inhibitors**: G12D essentially nothing, G12V two compounds
past the cognate ligand. A G12R screen is in progress; completing it brings coverage to **98% of codon-12-mutant
PDAC** (83% of all PDAC).

### 2.5 Our own methods failed too, in the same way

**A pose-handling error produced an impossible energy.** Our MM-GBSA implementation
initially scored a conformer re-embedded from SMILES rather than the docked pose, placing
ligand and receptor in unrelated coordinate frames. The **crystallographic** cognate ligand
of 9YMQ scored **+23.44 kcal/mol** — non-binding, and impossible for a ligand resolved
within the structure. Scoring the docked pose gives **−33.22 kcal/mol**.

The error was caught only because a control gate required the cognate ligand to score as a
binder. An earlier version of that gate **counted** returned results rather than checking
the ranking its own documentation promised, and allowed the broken run to proceed for 37
minutes. A gate that does not check what it claims to check is indistinguishable from no
gate — which is the paper's thesis applied to the authors.

**Rescoring cannot rank a shortlist that is flat in the primary score.** On the G12V
top-200:

| quantity | value |
|---|---|
| Vina score spread across 200 compounds | **1.80 kcal/mol** |
| Vina's documented error | ~2.5 kcal/mol |
| MM-GBSA spread, same compounds | **87.28 kcal/mol** |
| Spearman ρ, Vina vs MM-GBSA (n = 200) | **+0.106** (p = 0.13) |
| Spearman ρ, Vina vs Vinardo | **+0.259** |
| Top-10 overlap between rankings | **2 of 10** |

Two rescoring functions of different physical type independently fail to agree with the
docking ranking. Neither is malfunctioning: the shortlist spans less than the primary
method's own error and therefore carries no ordering to recover. Reported without the
primary-score spread, ρ = 0.106 reads as a failed rescoring method rather than a property of
the input. **Checking that a shortlist spans more than the scoring function's error costs
nothing and bounds what rescoring can achieve.**

Interim estimates of ρ during the run were 0.239 (n = 50), 0.347 (n = 60), 0.196 (n = 80),
0.106 (n = 200); the apparent significance at n = 60 (p = 0.007) was a sampling artefact.

**Search effort buys geometry, not ranking.** Every screen ran at docking exhaustiveness 4
while every validation gate ran at 16 — the gate never covered the configuration used. We
tested this directly (50 compounds × 4 levels, identical embedding seed):

| exhaustiveness | mean Δ vs ex128 | ρ vs ex128 | top-10 retained | median cost |
|---|---|---|---|---|
| 4 | **+0.08 kcal/mol** | **0.821** | **8/10** | 24 s |
| 16 | +0.02 | 0.950 | 9/10 | 94 s |
| 64 | −0.01 | 0.977 | 10/10 | 347 s |
| 128 | 0.00 | 1.000 | 10/10 | 747 s |

A 31-fold compute increase moves the median score by 0.08 kcal/mol. The completed screens
are therefore sound. The same parameter on G12R moved the cognate's *score* only −9.28 to
−9.80 while moving its *pose* **7.19 Å to 0.99 Å**, converting a failed validation into a
passed one. Screening consumes rank and tolerates shallow search; validation and
pose-dependent rescoring consume geometry and do not.

---

## 3. Discussion

The individual failures reported here are not, in isolation, surprising to practitioners.
Structural-alert catalogues are known to be blunt; retrosynthesis planners are known not to
model stability; docking scores are known to be noisy. What we believe is worth reporting is
that these known limitations **co-occurred, pointed the same way, and were collectively
invisible** to the metrics the campaign monitored.

Directionality is the mechanism. A tool that failed randomly would degrade an aggregate
pass rate and be noticed. A tool that systematically rejects the molecules most similar to
known drugs shifts a pipeline toward chemical space that is unlike any approved compound —
which is exactly what a generative campaign is already predisposed to do, and exactly what
its novelty metrics reward. The filters and the generator failed in the same direction, and
the metrics were blind to both.

The intervention is unglamorous and cheap. Requiring every stage to reproduce known answers
converts silent failure into loud failure. It is not novel as an idea — it is standard
practice in assay development, where a plate without positive and negative controls is not
read. It appears not to be standard in computational screening pipelines, where a stage's
output is typically consumed on the assumption that the tool works.

Our results also bound what the intervention buys. Gates validate the *method*, not the
*prediction*. Every gate here checks that a tool reproduces answers already known; none can
establish that a prediction about a novel compound is correct. The pipeline reduces
518,662 compounds to a small set worth measuring. It does not tell you whether they work,
and the results in §2.5 show that even validated methods disagree once the compounds are
near-tied.

---

## 4. Limitations

**No compound has been measured.** Every result is computational. The pipeline's ability to
select active compounds is untested; a prospective, controlled test with an ungated control
arm is pre-registered and pending.

**One target family.** All results are KRAS. The five filter failures are properties of the
tools and should generalise; the docking and rescoring results may not.

**The 14-drug panel is sufficient, not optimal.** It detects these five failures. We make no
claim about panel construction in general, and the question of how to build a minimal
sufficient panel is open.

**The retrospective audit is not a controlled comparison.** We show the molecules could not
be made and that the tools did not flag it. We cannot exclude that the synthesis would have
failed for unrelated reasons.

**Prior-art positioning is partial.** §2.1 restates a known result; our contribution is the
co-occurrence, the directionality, and the ground-truth anchor.

---

## 5. Methods

*(To be expanded before submission. Software versions: AutoDock Vina 1.2.7; RDKit 2026.03;
OpenMM 8.6 with openmmforcefields, openff-toolkit and AmberTools (AM1-BCC via antechamber),
ff14SB with GBn2 implicit solvent; AiZynthFinder with USPTO policy and ZINC stock; ADMET-AI
(chemprop 1.x); Meeko for ligand preparation; PDBFixer for receptor preparation.)*

**4.1 Structures.** 8AFB (G12C), 9HFK (G12D), 9YMQ (G12V), 9XB7 (G12R, 1.36 Å). Selection
required a co-crystallised drug-like ligand; docking boxes were defined as the ligand
extent plus 10 Å in each dimension.

**4.2 Gates.** Each stage must reproduce a known answer: cognate redock RMSD < 2.0 Å
(phase 2); survival of a 14-drug panel (phase 4); approved-control retention (phase 7);
gate-before-route ordering (phase 8); cognate ligand scoring as a binder with sensible
control ordering (MM-GBSA).

**4.3 Chemical reality gate.** Aromatic-ring requirement; unstable-group SMARTS;
self-reactive functional-group pairs; PAINS/BRENK with derived exemptions
(`triple_bond`, `Aliphatic_long_chain`, `nitro_group`, `Oxygen-nitrogen_single_bond`,
`phthalimide`; `Michael_acceptor_1` under `--covalent`). Streaming implementation; a 22M
compound list exhausts 16 GB otherwise.

**4.4 Statistics.** Spearman rank correlation throughout; n stated with every coefficient.
Interim correlation estimates are reported alongside final values in §2.5 to document
small-n instability.

---

## 6. Data and code availability

All code, gated libraries, screening results, validation records (including **failed**
validations), rescoring outputs and the full set of negative results:
`github.com/eobi/pancreatic_cancer_research`.

Failed runs are retained deliberately. The G12R validation that failed at 7.19 Å is stored
alongside the one that passed at 0.99 Å; a record containing only successes cannot support
a methodological claim.

---

## 7. References

*All entries verified against publisher records on 2026-09-05. Full list with resolution
notes in `papers/REFERENCES.md`.*

1. Gao, W. & Coley, C. W. The Synthesizability of Molecules Proposed by Generative Models.
   *J. Chem. Inf. Model.* **60**, 5714–5723 (2020). doi:10.1021/acs.jcim.0c00174
2. Capuzzi, S. J., Muratov, E. N. & Tropsha, A. Phantom PAINS: Problems with the Utility of
   Alerts for Pan-Assay INterference CompoundS. *J. Chem. Inf. Model.* **57**, 417–427
   (2017). doi:10.1021/acs.jcim.6b00465
3. Baell, J. B. & Nissink, J. W. M. Seven Year Itch: Pan-Assay Interference Compounds
   (PAINS) in 2017 — Utility and Limitations. *ACS Chem. Biol.* (2018).
   doi:10.1021/acschembio.7b00903
4. Buttenschoen, M., Morris, G. M. & Deane, C. M. PoseBusters: AI-based docking methods
   fail to generate physically valid poses or generalise to novel sequences. *Chem. Sci.*
   **15**, 3130–3139 (2024). doi:10.1039/D3SC04185A
5. Brenk, R. et al. Lessons Learnt from Assembling Screening Libraries for Drug Discovery
   for Neglected Diseases. *ChemMedChem* **3**, 435–444 (2008). doi:10.1002/cmdc.200700139
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
10. Hallin, J. et al. The KRAS^G12C Inhibitor MRTX849 Provides Insight toward Therapeutic
    Susceptibility of KRAS-Mutant Cancers in Mouse Models and Patients. *Cancer Discov.*
    **10**, 54–71 (2020). doi:10.1158/2159-8290.CD-19-1167
11. Genheden, S. et al. AiZynthFinder: a fast, robust and flexible open-source software for
    retrosynthetic planning. *J. Cheminform.* **12**, 70 (2020).
    doi:10.1186/s13321-020-00472-1
12. Swanson, K. et al. ADMET-AI: a machine learning ADMET platform for evaluation of
    large-scale chemical libraries. *Bioinformatics* **40**, btae416 (2024).
    doi:10.1093/bioinformatics/btae416
