# Empirical studies — what is publishable, and the evidence for each

Five separable studies came out of this work. Each is listed with its claim, the evidence
that supports it, the files that reproduce it, and — importantly — what it does **not**
support, since every one of these is a negative or methodological result and overclaiming
would be the fastest way to lose it in review.

Authorship, venue and framing are yours to decide. This file records what the data will
carry.

---

## Study 1 — Generative models produce molecules that cannot exist

**Claim.** A protein-conditioned generative model, evaluated only on docking score and a
synthetic-accessibility heuristic, produced 73 molecules of which **none** survive a
standard pre-synthesis filter. The failure is categorical, not marginal.

**Evidence.**
- **0 of 73 have an aromatic ring.** Reference drugs: 2 of 2 do.
- 63 of 73 in the reported shortlist carry a genotoxic or unstable group; mean 1.9 each.
- 15 are **self-reactive** — functional groups that destroy each other in the same molecule.
- The three structures actually sent to chemists all carry a triazane, an epoxide and (in
  two) a free aldehyde. Roughly a year of failed synthesis followed.
- Same filter on 902,833 purchasable compounds: **57-76% pass**. Generated: 0.0%.

**Reproduce.** `src/audit_molecules.py data/raw/source-cross_docked_kras.xlsx`
→ `results/audit-output.txt`

**Does not support.** That generative chemistry cannot work — only that this model, with
this objective, did not. Selection used docking thresholds only (DiffDock confidence >= -1.5, GNINA
minimised affinity <= -5.0 kcal/mol); no stability or reactivity criterion was applied.

**Why it is worth publishing.** The failure mode is invisible to every metric the field
routinely reports. A paper that says "we shipped three impossible molecules to a lab and
here is exactly why the metrics did not catch it" is more useful than another benchmark.

---

## Study 2 — Every filter must be calibrated against known-good molecules

**The strongest methodological result here.** Five independent filters, each standard
practice, each wrong in the same direction until checked against molecules with known
answers.

| filter | failure | detected by |
|---|---|---|
| BRENK catalogue | rejects Sotorasib and Adagrasib (acrylamide warhead) | 2-drug check |
| DiffDock + GNINA | cannot rank three known drugs; 4 kcal/mol run-to-run noise | cognate control |
| ADMET-AI thresholds | textbook cutoffs reject 199/200, including both approved drugs | 3-drug check |
| AiZynthFinder | returns clean routes for molecules that cannot exist | negative controls |
| our own reality gate | rejected MRTX-1133 (`triple_bond`); nitro over-match rejected Venetoclax | **14-drug panel** |

**The finding that generalises:** panel size matters. Three references missed five broken
catalogue rules. Fourteen caught them all. ~202,000 of 384,171 rejections in the production
run came from rules that reject marketed drugs.

**Evidence.** `results/catalogue_exemptions.json`, DISCOVERIES sections 2, 5, 6, 7b.
`src/gate_service.py` `/validate` runs the panel check on startup — that is how the
MRTX-1133 failure surfaced after two days of unnoticed operation.

**Does not support.** That these tools are bad. BRENK is a fine lead-likeness filter; it is
not an existence test. The error is using a preference filter as a gate.

---

## Study 3 — Blind docking fails on induced-fit pockets; site-directed does not

**Claim.** On KRAS, where the switch-II pocket does not exist until a ligand opens it,
blind docking cannot rank and site-directed docking can.

| | DiffDock + GNINA | Vina, site-directed |
|---|---|---|
| cognate redock | fails quality threshold | **0.67 A** (G12C), **0.88 A** (G12D) |
| spread across 3 known drugs | 0.4 kcal/mol | 2.96 (G12C), 4.84 (G12D) |
| run-to-run variance | **4.0 kcal/mol** | 0 (seeded) |
| per ligand | 41 s (T4 GPU) | 3.5-5 s (laptop CPU) |

Two identical DiffDock runs, same receptor, same settings, one session apart: Sotorasib
moved from -3.80 to -7.78. Noise ten times the signal.

**Mechanism.** Each liganded structure's pocket is shaped by *its* ligand — 8AFB by
BI-0474, 6OIM by Sotorasib, 6UT0 by Adagrasib. Cross-docking measures pocket mismatch, not
binding. Blind search also discards a site you already know.

**Evidence.** `runs/` holds both DiffDock notebooks with outputs;
`targets/g12c/validate/`, `targets/g12d/validate/` hold the site-directed validations.

**Does not support.** That DiffDock is unsound generally — it is designed for targets where
the site is unknown, which is not this case.

---

## Study 4 — No purchasable compound competes with clinical KRAS G12D inhibitors

**A properly controlled negative result**, which is rare enough to be worth publishing on
its own.

**Design.** 902,833 ZINC compounds (MW 500-700) → gate → 518,662 → two arms of ~10,000:
one ranked by similarity to three G12D references, one **drawn at random from the same
pool**. Receptor 7RPZ, validated at 0.88 A cognate redock before any screening.

| arm | scored | best | p1 | p10 | median | >AM-2383 | >MRTX-1133 |
|---|---|---|---|---|---|---|---|
| similarity | 9,913 | -12.83 | -11.07 | -10.00 | -8.68 | 1 | 0 |
| random | 9,726 | -12.06 | -10.68 | -9.69 | -8.25 | 0 | 0 |

**19,639 compounds. One beats AM-2383 by 0.12 kcal/mol — inside the method's error. None
beat MRTX-1133.**

**Second result from the same run:** the similarity heuristic beats random on median
(+0.43), p10 (+0.31) and best (+0.77), and produced the only hit. Selection heuristics are
almost never validated; this one now is.

**Contrast that makes it interpretable.** The identical pipeline on G12C returned 82
compounds beating Adagrasib. Same library, same gate, same method, both validated. The
difference is the target.

**Evidence.** `data/screens/screen_g12d_{sim,random}.json`,
`data/shortlists/top200_g12d_{final,random}.json`, `targets/g12d/validate/`.

**Does not support.** That no purchasable G12D binder exists. 19,639 of 518,662 gated
compounds were searched, selected two ways. The honest claim is bounded by the library and
the selection.

---

## Study 5 — Retrosynthesis cannot distinguish makeable from impossible

**Claim.** Route-planning tools answer "if this existed, what would assemble it" and never
"can this exist", so they cannot be used as a synthesis-feasibility gate.

| molecule | precursors in stock | steps | reality |
|---|---|---|---|
| Sotorasib | 83% | 5 | marketed |
| BI-0474 | 80% | 6 | clinical |
| **Hit 41** | **80%** | **6** | **cannot exist** |
| Adagrasib | 71% | 6 | marketed |

Approved 71-83%, impossible 67-80%. **Not separated.** A triazane bearing an epoxide and an
aldehyde returns a cleaner route than a marketed drug.

**Consequence.** Stage ordering is not optional: the chemical reality gate must run first.
`src/route_check.py` enforces it and refuses ungated input.

**Also.** AiZynthFinder's `is_solved` boolean is unusable — it returns False for Sotorasib
because one intermediate is absent from the stock catalogue. Use stock fraction and step
count as graded evidence.

**Evidence.** `results/routes.json`, `data/raw/route_validation.json`.

**Corrects an earlier claim of ours.** This work initially identified stage 04
(retrosynthesis) as the missing piece that cost the year. It was not. Stage 03 (reality
gate) was. Adding retrosynthesis alone would have produced confident routes for all three
impossible molecules.

---

## Cross-cutting: what the whole thing argues

Every stage of a computational discovery pipeline should carry a **validation gate against
molecules with known answers**, and the pipeline should refuse to proceed when one fails.
Of six such gates built here, **five failed on first attempt.** The 2025 campaign had none,
which is a sufficient explanation for its outcome without invoking anything about the lab.

Full runbook: `../PIPELINE.md`. Full narrative with all numbers: `../DISCOVERIES.md`.

---

## Data availability

| what | where | size |
|---|---|---|
| ZINC library, MW 500-700 | `data/raw/library_K.smi` | 66 MB |
| gate survivors + every rejection with reason | `data/gated/` | 78 MB |
| all docking results with poses | `data/screens/` | 492 MB |
| ranked shortlists | `data/shortlists/` | 1.4 MB |
| receptors, boxes, crystal refs, validations | `targets/` | 1.4 MB |
| DiffDock notebooks with outputs | `runs/` | 228 KB |
| every pipeline script | `src/` | 132 KB |

Reproducing any study needs only `src/` plus the named data directory.

---

## Study 6 — Rescoring cannot rank a shortlist that is flat in the primary score

**Claim.** When a virtual screen's shortlist spans less than the primary scoring function's
own error, no rescoring method recovers a meaningful ranking — and two independent methods,
of different physical type, both fail. The shortlist is not merely hard to order; it
carries no ordering information to recover.

### Evidence

Target KRAS G12V (9YMQ), site-directed Vina shortlist, top 200 of 9,913 screened.

| quantity | value |
|---|---|
| Vina score spread across all 200 | **1.80 kcal/mol** (−12.66 … −10.86) |
| Vina's own documented error | ~2.5 kcal/mol |
| MM-GBSA spread across the same 200 | **87.28 kcal/mol** (−45.56 … +41.72) |
| Spearman rho, Vina vs MM-GBSA (n=200) | **+0.106** (p = 0.13) |
| Spearman rho, Vina vs Vinardo (same shortlist) | **+0.259** |
| Top-10 overlap between the two rankings | **2 of 10** |
| Compounds MM-GBSA calls binders | 166 / 200 |

Two rescoring functions of different type — Vinardo, an empirical function, and MM-GBSA,
molecular mechanics with GB implicit solvent — independently fail to agree with the
docking ranking. Vinardo additionally **failed its own controls**, ranking MRTX-1133 last
of three, which disqualified it as an arbiter on this target.

The disagreement is not subtle. One method reports the compounds as indistinguishable
(1.80 kcal/mol apart), the other as differing by 87 kcal/mol. Which ten compounds you
order depends almost entirely on which method you believe.

**MM-GBSA controls (the gate that licenses the number):** cognate AM-2383 **−33.22**,
RP03514 **−33.02**, G12D-selective MRTX-1133 **−5.70** kcal/mol. The method places the
wrong-variant drug last unprompted, and **cannot** separate two close analogues 0.2
kcal/mol apart. Both facts belong in the paper; the second bounds what the first licenses.

**A pre-registered premise, confirmed.** `PAPER-2-prospective-gates.md` was written before
this run finished and predicted no meaningful rank correlation *on the grounds that* the
Vina spread lies inside Vina's error. The measured spread (1.80 kcal/mol) and the measured
rho (+0.106) confirm **the premise**. The prediction itself concerns *measured* activity
and remains untested — no compound has been assayed.

**Interim estimates were noise, and the record shows it.** rho by sample size:
0.239 (n=50) → 0.347 (n=60) → 0.196 (n=80) → **0.106 (n=200)**. The apparent significance
at n=60 (p = 0.007) was a sampling artefact. Reporting it as a trend would have been wrong,
and the interim values are kept here deliberately as evidence of how unstable small-n
correlations are in this setting.

**Reproduce.** `results/mmgbsa_g12v.json`, `results/rescoring_verdict_g12v.json`,
`results/rescore_g12v.json`. 200 compounds, 8 workers, 286 s each, 14.3 h wall.

### Methodological contribution — a failure mode worth naming

The first MM-GBSA implementation scored a **re-embedded conformer** rather than the docked
pose, so ligand and receptor sat in unrelated coordinate frames. The crystallographic
cognate ligand scored **+23.44 kcal/mol** — non-binding, and impossible for a ligand
resolved in the structure. Scoring the docked pose gives **−33.22**.

The bug was caught only because a control gate demanded the cognate score as a binder. An
earlier version of that gate *counted* results instead of checking the ranking its own
docstring promised, and let the broken run proceed for 37 minutes. **A gate that does not
check what it claims to check is indistinguishable from no gate.**

### Does not support

- That MM-GBSA is unreliable in general. It ordered the controls correctly here. It failed
  to rank a set that contains no rank signal.
- That these 200 compounds are inactive. Nothing was measured. They are unrankable *by
  these methods*, which is a different claim.
- That rescoring is not worth doing. It is the check that revealed the shortlist was flat.
  A negative result from a cheap method is why the expensive method was not run.
- Any conclusion about compounds outside this shortlist, or about other targets.

### Why it is worth publishing

The field routinely reports rescoring correlations without reporting the **spread of the
primary score**. If the shortlist is flat, rho is bounded near zero before any rescoring
begins, and a low correlation will be read as a failure of the rescoring method rather
than a property of the input. The practical rule this yields is one line: **check that
your shortlist spans more than your scoring function's error before you pay to rescore it.**

---

## Study 7 — Docking exhaustiveness buys geometry, not ranking

**Claim.** Increasing docking search effort improves *pose* accuracy substantially while
leaving *score ranking* nearly unchanged. Virtual screening, which consumes rank, is
therefore safe at low exhaustiveness; method validation and pose-dependent rescoring, which
consume geometry, are not.

**Evidence.** 50 compounds stratified across a G12V shortlist, docked at exhaustiveness
4 / 16 / 64 / 128 with an identical embedding seed at every level, so the only variable is
the search (200 docks).

| level | median | mean d vs ex128 | max d | rho vs ex128 | top-10 kept | median cost |
|---|---|---|---|---|---|---|
| ex4 | -10.94 | **+0.08** | +1.49 | **0.821** | **8/10** | 24 s |
| ex16 | -10.96 | +0.02 | +0.76 | 0.950 | 9/10 | 94 s |
| ex64 | -11.00 | -0.01 | +0.06 | 0.977 | 10/10 | 347 s |
| ex128 | -10.98 | 0.00 | 0.00 | 1.000 | 10/10 | 747 s |

A 31x increase in compute moves the median score by 0.08 kcal/mol — two orders of
magnitude inside Vina's ~2.5 kcal/mol error. Only 2 of 50 compounds shift by more than
1 kcal/mol.

**The complementary observation, from the same target family.** On KRAS G12R (9XB7) the
cognate ligand's score moved only -9.28 -> -9.80 between ex16 and ex128, while its
redocked pose moved **7.19 A -> 0.99 A**, turning a failed validation gate into a passed
one. Same parameter, same protein family: negligible effect on score, decisive effect on
geometry.

**Reproduce.** `python src/exhaustiveness_test.py data/shortlists/top200_g12v.json
--receptor targets/g12v/rec.pdbqt --box targets/g12v/box.txt -n 50 --levels 4,16,64,128`
-> `results/exhaustiveness_g12v.json`, `results/exhaustiveness_verdict_g12v.json`.

**Does not support.** That exhaustiveness never matters to ranking — measured on a
shortlist spanning only 1.8 kcal/mol, where compounds are near-tied by construction; a
wider-ranging set may behave differently. Nor that ex4 is sufficient generally: 8/10
retention means marginal compounds are not stably ordered. Nor anything about targets
outside KRAS.

**Why it is worth publishing.** Screening exhaustiveness is usually chosen by folklore and
rarely reported with a sensitivity analysis. The practical rule is one line: **spend search
effort where geometry is consumed (validation, pose-based rescoring), not where only rank
is consumed (screening).** For this project it was worth 31x on the screening budget.
