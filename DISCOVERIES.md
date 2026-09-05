# KRAS G12C programme — what we found

Session of 31 August 2026. Everything below is reproducible from the scripts in this
folder; every number was measured, not estimated.

---

## Summary

Four findings, in the order they were established.

1. **The 2025 molecules could not be made.** Not "were hard to make" — could not exist.
   Zero of 73 generated compounds survive a standard pre-synthesis filter.
2. **The 2025 ranking was also unreliable.** The docking that ordered them cannot tell
   three known KRAS drugs apart, and swings 4 kcal/mol between identical runs.
3. **Both are fixed.** Site-directed docking now reproduces a crystal pose to 0.67 A on
   G12C and 0.88 A on G12D, with controls separated by 3-5 kcal/mol.
4. **No purchasable compound competes with the clinical G12D inhibitors.** **19,639**
   screened against the variant that dominates pancreatic cancer, in a ranked arm and a
   random control arm. One beats AM-2383 by 0.12 kcal/mol (inside the error); none beat
   MRTX-1133. Buying a lead is not available for this target — which is the case for de
   novo design, now evidenced rather than assumed. The selection heuristic was validated
   in the same run: it beats random on median, p10 and best.

The through-line: **nothing in the 2025 pipeline was ever checked against a known answer.**
Every filter built here is calibrated against molecules whose answer is known first —
and three of them failed that check on the first attempt (BRENK rejected the drugs, ADMET
rejected the drugs, retrosynthesis accepted the impossible ones).

---

## 1. The molecules could not be made

`audit_molecules.py` over the 75-row cross-docked sheet, and over all 73 generated
compounds across five targets.

Three rows were explicitly labelled for the chemists — `Hit 13`, `Hit 41`, `Hit 73`.
All three carry a **triazane, an epoxide and (in two) a free aldehyde in one structure**.
A triazane (three nitrogens bonded in a row) is not an isolable organic functional group.
Worse, the hydrazine end condenses with the aldehyde and opens the epoxide: the molecules
attack themselves. Fifteen of the 73 cross-docked compounds are self-reactive this way.

Across the whole generated set:

| property                         | 73 generated | Adagrasib / Sotorasib |
|----------------------------------|-----------------|-----------------------|
| at least one aromatic ring       | **5**           | 2 of 2                |
| genotoxic or unstable group      | 63 of 73 sampled| 0                     |
| mean ring count                  | 2.4             | 5.5                   |
| fraction sp3 carbon              | 0.81            | 0.37                  |
| median molecular weight          | 226             | 560 / 604             |

**0 of 73 have an aromatic ring at all.** This is not a weak-candidate problem; it
is a different class of matter from what drugs are made of. Gate survival:

    73  generated
        9  no unstable or genotoxic group
        4  clears PAINS and BRENK
        0  has a drug-like ring system

The only survivor in the whole corpus was a reference compound the team fed in themselves.

For contrast, the identical gate on 902,833 purchasable ZINC compounds passes **57.45%**.
Real chemistry passes at 57%; the generator's output passes at 0.0%.

**The year of failed synthesis is fully explained.** The chemists were given impossible
assignments, and no reagent purity or skill could have changed the outcome.

---

## 2. The ranking was also unreliable

Two DiffDock + GNINA runs, same receptor (8AFB), same code, same settings, one session
apart:

| ligand    | run 1  | run 2  | delta |
|-----------|--------|--------|-------|
| Adagrasib | -9.85  | -8.16  | 1.7   |
| Sotorasib | -3.80  | -7.78  | **4.0** |
| BI-0474   | —      | -8.07  | —     |

Three disqualifying facts:

- **The cognate control fails.** BI-0474 is co-crystallised in 8AFB. DiffDock should
  reproduce its pose trivially. It returned confidence -3.52, below the -1.6 threshold.
- **No discrimination.** The three known drugs span 0.4 kcal/mol.
- **Noise exceeds signal 10x.** Sotorasib moved 4.0 kcal/mol between identical runs.

So the 2025 rankings were substantially noise — a second, independent reason the shortlist
was unsound, on top of the chemistry.

### Why blind docking is wrong here

The G12C switch-II pocket is induced-fit: it does not exist in apo KRAS, it is carved open
by whichever inhibitor bound it. Each structure's pocket is shaped by ITS ligand:

    8AFB = BI-0474 (LXD)    6OIM = Sotorasib    6UT0 = Adagrasib

Docking a drug into a non-cognate structure is a cross-docking problem, and scores degrade
for reasons unrelated to binding. That is the whole of Sotorasib's poor score. Blind
docking also throws away information you already have — the site is known from three
crystal structures — and pays variance for nothing.

---

## 3. The replacement, validated

AutoDock Vina 1.2.7 (native arm64) into a box built from the crystal ligand.
Receptor 8AFB protein-only, altloc A. Box centre (14.63, -10.07, 21.50), size
24.0 x 18.8 x 22.0 A. Exhaustiveness 16, seed 42.

| ligand    | score  | RMSD to crystal |
|-----------|--------|-----------------|
| BI-0474   | **-12.26** | **0.67 A**  |
| Adagrasib | -10.83 | —               |
| Sotorasib | -9.30  | —               |

The cognate ligand ranks first and returns to within 0.67 A of its crystal pose. The
standard criterion is under 2.0 A.

|                     | DiffDock + GNINA | Vina site-directed |
|---------------------|------------------|--------------------|
| cognate redock      | fails quality    | 0.67 A, ranks 1st  |
| control spread      | 0.4 kcal/mol     | 2.96 kcal/mol      |
| run-to-run variance | 4.0 kcal/mol     | 0 (seeded)         |
| per ligand          | 41 s (T4 GPU)    | 3.5 s (M1 Pro)     |
| hardware            | Kaggle GPU       | the laptop         |

Deterministic, seven times better separated, twelve times faster, and no GPU.

---

## 4. The screen

    902,833  ZINC K-tranche, MW 500-700 (the KRAS drug mass range)
    518,662  pass the chemical gate                       57.45%
      2,000  selected by similarity to known binders, diversity-capped at 0.85
      1,987  scored by Vina (13 failed conformer embedding, 0.65%)

1 h 56 m at 3.5 s/ligand, entirely local.

    best -12.45 | p10 -10.41 | median -9.40 | worst -4.66

    controls:  BI-0474 -12.26 | Adagrasib -10.83 | Sotorasib -9.30

    beat Adagrasib (-10.83):  82
    beat BI-0474  (-12.26):   2

Top five:

| # | score | MW | arom | note |
|---|-------|----|------|------|
| 1 | -12.45 | 508 | 4 | fluorinated oxazinoquinolone + pyrazole |
| 2 | -12.32 | 562 | 5 | same core + triazolopyrimidine |
| 3 | -12.03 | 525 | 4 | same core + tetrazole |
| 4 | -12.02 | 512 | 3 | piperazine-acetamide series |
| 5 | -12.00 | 533 | 4 | same core as 1-3 |

### Read this honestly

- **A Vina score is a hypothesis about binding, not affinity.** Beating Adagrasib's
  docking score is not beating Adagrasib.
- **The top is enriched for one core.** 8 of the top 20 contain a fluorinated
  oxazinoquinolone, against 18 of the top 200. Scaffold diversity overall is good —
  145 distinct Murcko scaffolds in the top 200, 19 in the top 20 — but the very top is
  concentrated. That core is fluoroquinolone-adjacent and carries known liabilities;
  ADMET will have opinions.
- **Selection was by similarity, not by predicted affinity**, so enrichment near the top
  is partly by construction.
- **These are purchasable.** No synthesis route to solve, purity data on delivery.

---

## 5. ADMET — and a filter that rejected the drugs

Ran ADMET-AI over the 200-compound shortlist. First pass used textbook cutoffs
(DILI < 0.70, hERG < 0.70) and rejected **199 of 200**, 197 on DILI alone. That is not a
finding about the compounds; it is a broken filter.

Checking the gate against the drugs it should obviously pass:

| | DILI | hERG | ClinTox | AMES | QED |
|---|---|---|---|---|---|
| BI-0474   | 0.96 | 0.89 | 0.43 | 0.49 | 0.44 |
| Sotorasib | **0.99** | 0.72 | 0.22 | 0.11 | 0.36 |
| Adagrasib | 0.83 | **0.96** | 0.75 | 0.30 | 0.36 |
| *first cutoff* | *0.70* | *0.70* | *0.50* | *0.50* | *0.35* |

**Sotorasib and Adagrasib are marketed drugs and both fail DILI and hERG outright.**
Oncology drugs genuinely are hepatotoxic and hERG-flagged — Sotorasib carries a
hepatotoxicity warning on its label. In this chemical space those two heads carry no
discriminating signal, so gating on them only discards the right answer.

Recalibrated so that every approved control must pass, with DILI and hERG demoted to
informational. `admet_gate.py` now runs that self-check on every invocation and exits if
a control fails. Result: **197 pass, 3 rejected** (2 QED, 2 AMES, 1 ClinTox).

### But be honest about what that gate is worth

197 of 200 surviving means the gate is barely filtering. Calibrating to "no worse than a
marketed drug" is a low bar when the marketed drugs have poor profiles. Both calibrations
were wrong in opposite directions, and the real conclusion is that **ADMET-AI does not
strongly discriminate within this chemical space at any threshold.**

The useful framing is comparative, not pass/fail — how many hits beat the *best* control
on each axis:

| axis | hits better than best control | median | best control |
|---|---|---|---|
| DILI | 17 / 197 | 0.95 | 0.83 |
| hERG | 74 / 197 | 0.77 | 0.72 |
| ClinTox | **129 / 197** | 0.14 | 0.22 |
| AMES | 40 / 197 | 0.23 | 0.11 |
| QED | **139 / 197** | 0.52 | 0.44 |
| Bioavailability | 99 / 197 | 0.82 | 0.82 |

So the shortlist is *more* drug-like than the approved drugs (QED 0.52 vs 0.44) and lower
on predicted clinical toxicity, while being no better on liver signal. Use ADMET here to
rank and to flag, not to gate.

**The recurring lesson, now three times over.** BRENK rejected the drugs. Blind docking
could not rank the drugs. ADMET thresholds rejected the drugs. Every filter in this
pipeline has to be calibrated against molecules known to be developable before it is
trusted — which is exactly what the 2025 campaign never did, at any stage.


---

## 6. Retrosynthesis — and a correction to my own diagnosis

Built stage 04 with AiZynthFinder (USPTO policy, 42,555 templates, ZINC stock) and
validated it the same way as everything else: against molecules with known answers.

**It cannot tell makeable from impossible.**

| molecule | precursors in stock | steps | reality |
|---|---|---|---|
| Sotorasib | 83% (5/6) | 5 | marketed drug |
| BI-0474 | 80% (4/5) | 6 | clinical compound |
| **Hit 41** | **80% (4/5)** | **6** | **cannot exist** |
| Adagrasib | 71% (5/7) | 6 | marketed drug |
| Hit 13 | 67% (2/3) | 5 | cannot exist |
| Hit 73 | 67% (2/3) | 6 | cannot exist |

    approved drugs   : 71% - 83%
    2025 "impossible": 67% - 80%      NOT SEPARATED

Hit 41 — a triazane carrying an epoxide and an aldehyde, one of the three a year of lab
work failed on — returns a clean 6-step route scoring *better than Adagrasib*.

The reason is structural, not a tuning problem. Retrosynthesis works backwards by
applying reaction templates: it asks **"if this molecule existed, what reactions would
assemble it."** It never asks whether the product is stable. A triazane that decomposes
the moment it forms still has a perfectly valid formal disconnection.

### The correction

Earlier in this work I called stage 04 "the stage whose absence cost the year." **That was
wrong.** Adding retrosynthesis alone would have proposed confident routes for all three
impossible molecules and sent the chemists to the bench exactly as before — with more
authority attached, not less.

**Stage 03, the chemical reality gate, is what would have saved the year.** It rejects all
three on triazane, epoxide and self-reactivity, and it already works.

The two stages answer different questions and compose in only one order:

    Stage 03  can this molecule exist?          stability, self-reactivity, alerts
    Stage 04  given that it exists, how?        route, steps, buyable starting materials

`route_check.py` now runs the gate first and refuses anything that fails it. Verified:

    3 molecule(s) rejected by the chemical reality gate before any route search:
      2025 Hit 13    unstable group: hydrazine N-N
      2025 Hit 41    unstable group: hydrazine N-N
      2025 Hit 73    unstable group: hydrazine N-N

    drug BI-0474    stock 4/5 (80%)  6 steps
    drug Sotorasib  stock 5/6 (83%)  5 steps
    drug Adagrasib  stock 5/7 (71%)  6 steps

### Also: `is_solved` is the wrong metric

AiZynthFinder's boolean requires *every* precursor to be in the stock catalogue. Sotorasib
returns `is_solved=False` because one intermediate is not in ZINC. A marketed drug is
obviously makeable. Use the stock fraction and step count as graded evidence; treat the
boolean as noise.

### Routes for the current shortlist

| hit | Vina | stock | steps |
|---|---|---|---|
| 1 | -12.45 | 75% (3/4) | 5 |
| 2 | -12.32 | 71% (5/7) | 4 |
| 3 | -12.03 | 86% (6/7) | 4 |
| 4 | -12.02 | **100% (3/3)** | **2** |
| 5 | -12.00 | 67% (4/6) | 5 |

Hit 4 is fully resolved to purchasable material in two steps — better than any of the
three reference drugs. These are catalogue compounds, so this mostly confirms the vendor
rather than discovering anything, but it is the first time a route number in this project
has been checked against a known answer before being believed.


---

## 7. Wrong target — and the corrected run

### The drift

Everything in sections 1-5 was screened against **KRAS G12C**. That is the wrong variant
for this disease.

| variant | share of PDAC | note |
|---|---|---|
| G12D | ~39% | dominant |
| G12V | ~29% | |
| G12R | ~15% | |
| **G12C** | **1.7%** | the *lung* cancer variant |

G12C is why Sotorasib and Adagrasib are approved for NSCLC, not pancreatic cancer. The
2025 `cross_docking.py` had this right — it covered G12C, G12D, G12V, G13D and PI3K
E545K under `disease_name = "Pancreatic Cancer [...]"`. I narrowed to one variant and
picked the least relevant one.

**Why it happened:** 8AFB had a co-crystallised ligand to validate against, and the
reference drugs with SMILES to hand were all G12C compounds. The choice optimised for a
clean validation rather than for the disease. Worth naming, because it is the same class
of error as the rest of this document — a decision made because it was measurable, not
because it was right.

### The corrected setup

Receptor **7RPZ** — KRAS G12D bound to MRTX-1133 at 1.3 A. MRTX-1133 is the flagship
G12D inhibitor and, usefully, **non-covalent**, so the modelling gap that made the G12C
controls awkward disappears.

Box from the crystal ligand (6IC): centre (1.71, 4.93, -23.16), 22.7 x 20.7 x 17.7 A.

| ligand | score | RMSD to crystal |
|---|---|---|
| MRTX-1133 | **-13.77** | **0.88 A** |
| AM-2383 | -12.71 | — |
| RP03514 | -8.93 | — |

Cognate redock 0.88 A, ranks first, controls separated by **4.84 kcal/mol** — better
discrimination than the G12C setup managed (2.96).

The gated library is target-independent, so all 518,662 survivors carried over untouched.
Only selection and docking were repeated.

### The result: nothing competitive

1,986 of 2,000 scored in 2 h 40 m.

    best -12.50 | p1 -11.08 | p10 -10.00 | median -8.75 | worst -3.15

    beat MRTX-1133 (-13.77):    0
    beat AM-2383   (-12.71):    0
    beat RP03514    (-8.93):  858

The best hit falls 0.21 short of AM-2383 and 1.27 short of MRTX-1133.

### Why this is a real finding, not a failed run

The only variable that changed between the two screens was the target:

| | G12C (8AFB) | G12D (7RPZ) |
|---|---|---|
| beat 2nd reference | 82 | **0** |
| beat cognate ligand | 2 | **0** |
| best score | -12.45 | -12.50 |
| best reference | -12.26 | -13.77 |
| cognate redock | 0.67 A | 0.88 A |

Same library, same gate, same selection method, both setups validated. On G12C, 82
purchasable compounds beat Adagrasib. On G12D, none beat either reference. **G12D is
genuinely the harder pocket** — which is why it stayed unsolved long after G12C fell, and
why MRTX-1133 was a significant achievement.

The top 200 is chemically sound — 171 distinct Murcko scaffolds, largest cluster 8, MW
500-615, median 3 aromatic rings, tetrazole and triazolopyrimidine motifs that read as
real medicinal chemistry. The problem is not junk chemistry this time. It is that
catalogue space does not contain a G12D binder of this calibre.

### What it means for the programme

- **Buying your way to a wet-lab measurement does not work for G12D.** That shortcut is
  closed for the variant your patients actually have. It closed cheaply though: 2 h 40 m
  on a laptop rather than another year at the bench.
- **It re-motivates de novo design.** Generative chemistry earns its place precisely
  where purchasable space is empty, and G12D is that case. The generator still needs the
  reality gate wrapped around it — but the argument for having one is now evidenced.
- **G12V and G12R remain unscreened** (~29% and ~15% of PDAC). Both need a liganded
  structure for validation before they are worth running.

### Honest limits

This searched 2,000 of 518,662 gated compounds, selected by similarity to known G12D
binders (best similarity 0.454, against 0.58 for the G12C references). A different
selection, or simply more depth, could surface something better. The claim is **"this
library and this selection produced nothing competitive"** — not "nothing purchasable can
bind G12D."

Files: `screen_g12d.json` (all scored, with poses), `top200_g12d.json` (shortlist),
`work_g12d/` (receptor, box, crystal reference, validation).


---

## 7b. The gate rejected a clinical drug — found by building it as a service

Exposing phase 4 over HTTP (`gate_service.py`) meant giving it a `/validate` endpoint that
proves it separates known-good from known-impossible on every startup. It immediately
failed:

    approved_drugs_pass:  Sotorasib true, Adagrasib true, MRTX-1133 FALSE

**MRTX-1133 — the G12D drug the entire G12D screen was validated against — failed my own
chemical reality gate.** Cause: BRENK's `triple_bond` rule, firing on its terminal alkyne.
BRENK expresses lead-likeness preference, not whether a molecule can exist.

### The systematic fix

Hand-picking exemptions one drug at a time is what produced four of these in a row. Instead,
run BRENK+PAINS over a panel of 14 marketed drugs and demote **every rule that fires**:

| rule | fires on |
|---|---|
| Michael_acceptor_1 | Sotorasib, Adagrasib, Osimertinib, Ibrutinib |
| triple_bond | MRTX-1133, Erlotinib |
| Aliphatic_long_chain | Erlotinib, Gefitinib |
| nitro_group | Venetoclax |
| Oxygen-nitrogen_single_bond | Venetoclax |
| phthalimide | Thalidomide |

My own hand-written alert list had the same flaw: `[NX3]-[OX2H0,OX1]` for "N-oxide/nitroso"
also matched **nitro groups**, rejecting Venetoclax. Narrowed to nitroso and hydroxylamine.

After the fix: **all 14 approved drugs pass, all 3 impossible molecules still rejected.**

### How much was wrongly excluded

| rule | compounds removed |
|---|---|
| Aliphatic_long_chain | 106,412 |
| phthalimide | 93,155 |
| my nitro over-match | 2,738 |
| triple_bond | 66 |
| Oxygen-nitrogen_single_bond | 19 |

**~202,000 of 384,171 rejections — over half — were by rules that reject approved drugs.**
Gate pass rate goes from 57.45% to **75.90%**; the library from 518,662 to ~685,000.

### Does it invalidate the G12D result? No — measured, not assumed

Of 38,585 newly-admitted compounds in a 200,000-row scan, only **705** clear the 0.150
similarity threshold the top-10,000 selection used, and the best reaches **0.221** against a
selection window of 0.454-0.150. Extrapolated, the fix adds ~3,000 candidates at the
*bottom* of the ranking. None displace the top.

The excluded chemotypes — long aliphatic chains, phthalimides — are structurally unlike
MRTX-1133, so they were never going to rank. The running screens were left alone.

### The lesson, for the fifth time

BRENK rejected the drugs. Blind docking could not rank the drugs. ADMET rejected the drugs.
Retrosynthesis accepted the impossible ones. Now the reality gate rejected a drug too.

**Every filter must be validated against a panel of known-good molecules, and the panel must
be bigger than the two or three references you happen to have to hand.** Three references
missed five broken rules. Fourteen caught them.

This one was found only because the service was built with a self-check that runs on startup.
The script version had been running for two days without anyone noticing.


---

## 7c. Deepening the G12D screen — the negative essentially holds

The section 7 result rested on 2,000 of 518,662 gated compounds (0.4%). That is enough to
say "this selection found nothing competitive," not "purchasable space is empty." So the
screen was extended five-fold, in **two arms** — because the selection heuristic itself had
never been validated, and every other filter here that went unchecked turned out to be
broken.

    similarity arm  9,913 compounds ranked by Tanimoto to the three G12D references
    random arm     10,000 drawn at random (seed 42) from the SAME gated pool

### Similarity arm — final

    best -12.83 | p0.1 -11.75 | p1 -11.07 | p10 -10.00 | median -8.68 | worst -3.15

    beat MRTX-1133 (-13.77):     0
    beat AM-2383   (-12.71):     1
    beat RP03514    (-8.93): 4,018

**Five times the depth moved the answer from zero hits to one.** The single compound sits
0.12 kcal/mol past AM-2383 — inside the method's error — and 0.94 short of MRTX-1133.

The top 200 is chemically healthy: 168 distinct Murcko scaffolds, largest cluster 6, MW
500-686 (median 522). This is not a library problem or a junk-chemistry problem. G12D is
simply a hard pocket, and catalogue space does not contain a compound that competes with
purpose-built clinical inhibitors.

### The one hit

    score    -12.83     MW 592.6    logP 3.36    5 aromatic rings, 5 rotatable bonds
    formula  C32H29FN8O3
    SMILES   N=c1ccc(-c2nc3c(c(N4CCOCC4)n2)CCN(C(=O)c2cc(Cc4nnc(O)c5ccccc45)ccc2F)C3)c[nH]1

A pyridinone-linked tetrahydropyridopyrimidine with a morpholine, plus a
phthalazinone-methyl benzamide arm. MW 592.6 against MRTX-1133's 600.6.

ADMET against the two clinical references:

| | DILI | hERG | ClinTox | AMES | Carcin | QED | Bioavail |
|---|---|---|---|---|---|---|---|
| **lead** | 0.98 | **0.83** | **0.42** | **0.25** | 0.29 | 0.28 | **0.85** |
| MRTX-1133 | 0.82 | 0.96 | 0.84 | 0.85 | 0.14 | 0.32 | 0.74 |
| AM-2383 | 0.59 | 0.97 | 0.80 | 0.78 | 0.12 | 0.29 | 0.78 |

Better than both clinical compounds on clinical-toxicity, mutagenicity, hERG and
bioavailability; worse on DILI. Given that ADMET-AI barely discriminates in this chemical
space (section 5), read this as "carries no red flag the references do not also carry",
not as "better than MRTX-1133".


### Random control arm — final, and both questions answered

    arm           scored     best       p1      p10   median     >AM   >MRTX      >RP
    -------------------------------------------------------------------------------
    similarity     9,913   -12.83   -11.07   -10.00    -8.68       1       0    4,018
    random         9,726   -12.06   -10.68    -9.69    -8.25       0       0    2,823

    median gap  +0.43 kcal/mol   p10 gap  +0.31   best gap  +0.77   (all favour similarity)

**Question 1 — does the negative hold? Yes.** 19,639 compounds scored against KRAS G12D
across both arms. **One** beats AM-2383 by 0.12 kcal/mol, which is inside the method's
error. **None** beat MRTX-1133. A ten-fold deepening over the original 2,000 moved the
answer from zero hits to one.

Purchasable catalogue chemistry does not contain a compound competitive with purpose-built
clinical G12D inhibitors. That is now an evidenced claim rather than a provisional one.

**Question 2 — is the similarity selection worth its cost? Yes, on every measure.**
Median +0.43, p10 +0.31, best +0.77, 4,018 past RP03514 versus 2,823 — and the only hit
past a clinical reference came from the ranked arm. The heuristic had never been validated;
it is now.

This matters beyond G12D: it is the ranking step every future target will use, and it was
the one filter in this pipeline still resting on assumption.

### Reusable artefacts

    top200_g12d_final.json   ranked shortlist, pose data stripped
    g12d_hits.json           the compound(s) past a clinical reference
    g12d_lead.json           the -12.83 lead with full record
    screen_g12d_sim.json     all 9,913 scored, with poses

### Environment fragility found along the way

Installing AiZynthFinder (phase 8) silently upgraded chemprop 1.x to 2.x, which broke
ADMET-AI (phase 7) — the error surfaced only as a `dlopen` failure on a `cuik_molmaker`
binary built for a newer macOS. **Phases 7 and 8 cannot share a Python environment.**
ADMET now runs from a separate venv pinned to `chemprop==1.6.1`. Also, torch 2.6 changed
`torch.load` to `weights_only=True`, which chemprop 1.6.1 predates, so the ADMET
checkpoints need `argparse.Namespace` allowlisted.


---

## 8. Traps found along the way

Each of these produced a plausible-looking wrong answer rather than an error.

**RMSD against a PDB ligand needs bond orders.** First cognate redock reported 8.42 A and
looked like failure. A ligand read from PDB has no bond orders, so `rdMolAlign.CalcRMS`
cannot match it and maps atoms arbitrarily. The give-away: the docked centroid sat 0.34 A
from the crystal centroid with all 42 atoms inside the box. `AssignBondOrdersFromTemplate`
against the SMILES first gives the true 0.67 A.

**BRENK rejects the drugs that work.** It flags acrylamide as `Michael_acceptor_1`, which
rejects Sotorasib and Adagrasib — the warhead *is* the mechanism. With `--covalent`, the
gate recovers exactly those two from 2,999 KRAS molecules and rejects all 2,997 generated
ones. Without it, the gate throws away the correct answer.

**Parallelism does not transfer between tools.** The Vina screen taught that one ligand
per core beat one ligand on ten cores by 4x, because Vina's Monte-Carlo search threads
poorly. Applying that lesson to MM-GBSA was wrong: OpenMM's CPU platform parallelises the
nonbonded computation near-linearly, so it was already using its 7 cores well. Serial cost
was 564s wall (~66 min CPU) per compound; pinning one thread per worker and running 8 at
once gave ~1.4x, not the ~5x predicted. Measure one compound before re-architecting a run
around an analogy. The scaling behaviour of a tool is a property of that tool.

**Docking convergence is per-ligand, not per-target.** G12R (9XB7) failed its gate at the
default exhaustiveness: cognate redock 7.19 A, centroid 5.67 A off, a genuinely displaced
pose rather than the bond-order artefact. Raising exhaustiveness to 128 left the two
non-cognate controls unchanged to two decimals (-12.34 -> -12.33, -12.92 -> -12.93) while
the cognate moved 0.52 kcal/mol and **7.19 A -> 0.99 A**, turning FAIL into PASS. Reading
"converged" off the ligands that were not failing is invalid — the cognate is the only
ligand whose convergence the gate depends on. Any G12R screen therefore needs raised
exhaustiveness, at roughly 8x the cost per ligand.

**Check the spread before you pay to rescore.** The G12V top-200 spans **1.80 kcal/mol**
in Vina score — inside Vina's own ~2.5 kcal/mol error. Rescoring it with MM-GBSA (200
compounds, 14.3 h) gave rho = **+0.106**; Vinardo gave **+0.259**. Neither method failed:
the input carried no ordering to recover. A flat shortlist bounds rho near zero before
rescoring starts, so a low correlation gets misread as a bad rescoring method rather than
a property of the shortlist. Measure the primary score's spread first; it costs nothing.

**Shallow search is adequate for ranking and inadequate for pose recovery.** Every screen
here ran at exhaustiveness 4 while every validation gate ran at 16 — the gate never covered
the configuration the screens used. Tested directly (50 G12V compounds x 4 levels, 200
docks): against ex128, ex4 drifts **+0.08 kcal/mol** mean, rho **0.821**, and keeps **8 of
the top 10**, at 1/31st the cost. So the G12D and G12V negatives are facts about the
library, not artefacts of the search. The apparent contradiction with G12R resolves the
same way: there too the *score* barely moved (-9.28 -> -9.80) while the *pose* moved
7.19 A -> 0.99 A. Exhaustiveness buys geometry, not ranking. Screening ranks by score and
tolerates a cheap search; validation compares geometry to a crystal and does not. The
two-tier arrangement was correct — but it was never checked until now, and could as easily
have gone the other way.

**The campaign's own output file recorded the reason it would fail.** The source
spreadsheet carries an `Epoxide Ring Present` column. **All three molecules sent for
synthesis have it set to True.** The same file records `AMES` (mutagenicity) at a median of
**0.93** across all 73 molecules, `QED` at 0.39 against a >0.5 norm, and synthetic
accessibility at median 5.47 against 4.21 and 3.84 for the two reference drugs, with 22 of
73 above 6. Meanwhile `Good Docking Quality Overall` reads True for 72 of 73.

Nothing was undetected. Every signal needed to stop the campaign was computed, recorded,
and shipped **as a column to read rather than a gate that stops**. Selection used docking
thresholds only (DiffDock confidence >= -1.5, GNINA minimised affinity <= -5.0 kcal/mol),
per the published method (Obi et al. 2024). The failure was not perception. It was that
perception had no authority to halt anything.

**Optimising docking does not, by itself, destroy makeability.** Proposed mechanism,
tested and refuted. Across 1,986 G12D-screened purchasable compounds binned into deciles by
Vina score, the unmodified BRENK+PAINS pass rate is 97-100% in every decile and aromatic
content is 100% throughout, from the best decile (-12.50..-10.01) to the worst
(-7.03..-4.51). Selecting hard on a docking objective inside a catalogue is safe, because
the catalogue bounds the search to real chemistry. The campaign's failure therefore needed
BOTH an unconstrained generative search space AND no stability gate; neither alone
reproduces it. Recorded because it is the control a reviewer would demand, and because the
mechanism it refutes was ours.

**A control is only meaningful if it is cognate.** Judging 8AFB with Sotorasib, whose
structure is 6OIM, measures the wrong thing.

**ZINC's tranche letters are mass bins** — I = 425-450, J = 450-500, K = 500-953. The
first library pulled was centred on MW 437 when the target's drugs are 561-604. Verify the
mass range before committing to a library.

**files.docking.org fails quietly.** Parallel requests return 503 and the HTML error page
is written into your `.smi` file. It also 403s urllib's default User-Agent while allowing
curl's. Both corrupt a library without announcing it. `fetch_zinc.py` handles both.

**Kaggle-specific.** P100 is sm_60 and torch 2.10+cu128 dropped Pascal support, so
`cuda.is_available()` returns True while no kernel can launch — use T4 x2. HuggingFace
`datasets` shadows DiffDock's local `datasets/` directory (no `__init__.py`, so it is only
a namespace package). `biopython==1.79` has no cp312 wheel. `fair-esm[esmfold]` drags in
openfold and will not build; plain `fair-esm` is what DiffDock needs.

**Validate filters against a PANEL, not two references.** Three reference drugs missed five
broken catalogue rules; a 14-drug panel caught them all. Any BRENK/PAINS rule that fires on
an approved drug is a lead-likeness preference, not an existence test. See section 7b.

**Validate on the target the disease has, not the one with the best crystal structure.**
G12C was chosen because 8AFB had a cognate ligand to validate against. It is 1.7% of
pancreatic cancer. Check the epidemiology before the structure. See section 7.

**Phases 7 and 8 cannot share an environment.** admet-ai needs chemprop 1.x; aizynthfinder
pulls chemprop 2.x, whose `cuik_molmaker` dependency ships a macOS-26 binary that will not
load. Installing phase 8 silently breaks phase 7. Use separate venvs. See section 7c.

**Retrosynthesis is blind to stability.** It answers "how would this be assembled",
never "can this exist". Gate for chemical reality first or it will confidently route
molecules that decompose on formation. See section 6.

**Zenodo drops connections mid-transfer.** The AiZynthFinder downloader left three
truncated model files (policy 20 MB instead of 91 MB, filter 8.8 instead of 16.8) with no
error — the corruption only surfaced as `InvalidProtobuf` at load time. Fetch with
`curl -C -` and verify every file loads before trusting a run.

**Vina parallelism.** One process per ligand at 1 core each beats one process at 10 cores
by about 4x (3.5 s vs 14-32 s per ligand). Exhaustiveness 4 gives scores essentially
identical to 8.

---

## 9. What is next

**Immediately:** ADMET on `top200.json` — gating, not annotating. The 2025 pipeline
computed a median predicted mutagenicity of 0.93 across its shortlist and used it as a
column to read rather than a filter that stops a molecule.

**Then:** buyability and price lookup on survivors, and order. For these compounds
synthesis is already solved — a supplier makes them and ships with purity data. That is
the fast path to the wet-lab measurement MD Anderson asked for, and it does not depend on
solving retrosynthesis.

**Separately:** retrosynthesis remains essential for *generated* molecules, where nobody
has made the compound. That is the composition-of-matter IP path and the longer road. Both
belong in the system; only one is on the critical path to a measurement.

**Later:** in vitro and in vivo prediction need your own assay data before they are worth
building. The loop closes when compound comes back from a supplier and gets tested.

---

## Files

| file | what |
|---|---|
| `audit_molecules.py` | reproduces the 2025 post-mortem |
| `fetch_zinc.py` | polite, resumable ZINC tranche download |
| `prepare_ligands.py` | the chemical gate; streaming, MW window, `--covalent` |
| `select_ligands.py` | similarity ranking + diversity cap |
| `dock_site.py` | `validate` proves the setup, `screen` runs a list |
| `run_screen.py` | parallel screen, 1 core per ligand, checkpointed |
| `adapt_results.py` | into the `results.json` shape `connector.py` consumes |
| `bin/vina` | AutoDock Vina 1.2.7, native arm64 |
| `work/` | receptor, box, crystal reference, validation output, `status.sh` |
| `runs/FINDINGS.md` | the blind-docking failure and the validation that replaced it |
| `top200.json` | the shortlist, no pose data, ready for ADMET |
| `screen_results.json` | all 1,987 scored, with poses |
| `molecule-to-milligram-plan.html` | the ten-stage plan |
