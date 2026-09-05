# Digitising pancreatic cancer drug discovery, end to end

A validated pipeline from target structure to an orderable compound, and the plan for
extending it through the chemical and biological validation that normally happens in a lab.

**[DISCOVERIES.md](DISCOVERIES.md)** — what we found, with the numbers.
**[PIPELINE.md](PIPELINE.md)** — every phase, its command, and the gate it must pass.
**[SIMULATION_LADDER.md](SIMULATION_LADDER.md)** — the fidelity ladder, and what each rung costs.
**[papers/STUDIES.md](papers/STUDIES.md)** — five publishable studies and what each does *not* support.

---

## Why this exists

A 2025 campaign generated molecules for pancreatic cancer. MD Anderson asked for
laboratory validation. Chemical synthesis then stalled for over a year — cost, a
relocation, impure reagents.

The post-mortem found the delay was not only logistical. **Of 3,631 generated molecules,
0 pass a standard pre-synthesis filter.** 3,626 have no aromatic ring; 57–76% of
purchasable compounds pass the same filter. The three structures actually sent to chemists
carry a triazane, an epoxide and, in two cases, a free aldehyde — functional groups that
destroy each other in the same molecule. A year was spent trying to make things that
cannot exist.

So the goal is not a better generator. It is to move every step that can be computed
*before* a compound reaches a bench, and to make each step prove itself against a known
answer first.

## Two rules the 2025 campaign lacked

1. **Nothing reaches a chemist without passing a chemical-reality gate.**
2. **No scoring function is trusted until it reproduces a known crystal pose.**

The second rule generalises into the method that runs through everything here: every
filter is calibrated against molecules whose answer is already known. Five separate
filters were broken *in the same direction* until checked this way — each silently
rejecting the approved drugs it should have ranked first. A 14-drug panel caught what
3 reference compounds missed.

---

## Where the work stands

### Targets screened

KRAS variant frequencies in pancreatic ductal adenocarcinoma drive the priority.
G12C — the variant with marketed drugs — is a **lung** variant and barely present here.

| variant | % of PDAC | structure | screened | outcome |
|---|---|---|---|---|
| G12D | 39% | 9HFK | 19,639 | essentially nothing |
| G12V | 29% | 9YMQ | 9,913 | 2 past the cognate ligand |
| G12R | 15% | 9XB7 (1.36 A) | validated, screen queued | cognate redock **0.99 A** (needs high exhaustiveness) |
| G12C | 1.7% | 8AFB | 2,000 | 82 hits, wrong variant for PDAC |

Screened coverage is **68%** of pancreatic KRAS. G12R is now validated and queued; screening it takes coverage to **83%**.

### Fidelity ladder — from a docking score to a computed binding free energy

| rung | method | error vs experiment | cost | status |
|---|---|---|---|---|
| 1 | Docking (Vina, site-directed) | ~2.5 kcal/mol | 5 s | **built** |
| 2 | MM-GBSA rescoring | ~1.5–2.0 kcal/mol | ~5 min | **built** |
| 3 | MD pose stability (RMSD/RMSF) | kills false positives | 5–12 h | next, runs on an M1 Pro |
| 4 | FEP / TI binding free energy | **~1.0 kcal/mol** | 1–3 days | needs a real GPU |
| 5 | PBPK exposure | plasma and tissue exposure | minutes | not built |
| 6 | Pathway / QSP (KRAS→RAF→MEK→ERK) | downstream signalling | minutes | not built |

**Rung 4 is what changes the argument.** At ~1 kcal/mol a computed number starts
predicting a measured one — the difference between "this might bind" and "we calculate
this binds 10× tighter than the reference."

### Chemical process — beyond "does a route exist"

| capability | question | status |
|---|---|---|
| Retrosynthesis | does a route exist | **built** |
| Chemoselectivity + conditions | will each step work *on this molecule* | **built** |
| Forward reaction prediction | what product does this step actually give | stub — needs a model |
| Yield prediction | will the route deliver material | not built |

Retrosynthesis alone reproduces the 2025 failure with more confidence attached: it gave an
impossible molecule an 80% in-stock precursor fraction, **better than Adagrasib's 71%**. A
valid disconnection is not a working reaction.

---

## The plan

**Now — order compounds.** The only step that produces a real measurement, and the long
pole because shipping takes weeks. These are catalogue compounds: synthesis is already
solved and they arrive with purity data. This is the fast path to what MD Anderson asked
for, and it does not depend on solving retrosynthesis.

**Next — G12R (9XB7).** The last untested common variant, and the last chance for
catalogue screening to yield a strong lead before the honest conclusion becomes "ZINC does
not contain a good starting point for pancreatic KRAS."

**Then — rung 3, MD pose stability.** Runs on a laptop. Removes docking false positives
that survive rescoring, which matters given how weakly the rescoring functions agree here.

**Then — Phase 10, lab capture.** Orders placed from inside the system, and NMR, LC-MS,
purity and assay readouts ingested back onto the molecule record that predicted them.
Marked NOT BUILT, and it *matters more than anything above it*: every phase improves only
if measured outcomes return. Potency, cell response and exposure prediction cannot be
built at all until they have assay data to calibrate against.

**Separately — retrosynthesis for generated molecules.** The composition-of-matter IP path
and the longer road. Both belong in the system; only one is on the critical path to a
measurement.

---

## What each phase does, and what it caught

Eleven phases. Each has a **gate** — a check against a known answer that must pass before
anything downstream is believed. The gates are the point: nine of the eleven were added
because something upstream had already failed silently.

### Phase 0 — Target intake
Pick the variant by **disease prevalence**, then find a structure for it.
**Gate:** the structure must contain a co-crystallised drug-like ligand.

*What it caught:* G12C was chosen first only because 8AFB had a cognate ligand — and G12C
is **1.7%** of pancreatic cancer. It is the lung variant. 82 hits were found against a
target that barely occurs in this disease. Prevalence drives the choice now, and a
structure without a cognate ligand is rejected outright, because phase 2 cannot run
without one.

### Phase 1 — Receptor prep
Strip waters and ions, keep the pocket, define the box around the crystal ligand.

*Why it matters here:* KRAS has an induced-fit switch-II pocket that only exists when a
ligand holds it open. An apo structure has no pocket to dock into.

### Phase 2 — Method validation ← the gate missing in 2025
Redock the crystal ligand and measure RMSD to its known pose.
**Gate: cognate redock RMSD < 2.0 Å.** Measured **0.67 Å** (G12C), **0.88 Å** (G12D).

Also record the **control spread** — how far apart the known binders score: 2.96 kcal/mol
on G12C, 4.84 on G12D. A spread near zero means the function cannot rank at all.

*What it caught:* the original DiffDock + GNINA setup showed **4.0 kcal/mol run-to-run
variance on the same molecule** (Sotorasib scored −3.80 and −7.78 on repeat runs). It was
not ranking, it was sampling noise. Replaced with site-directed Vina.

### Phase 3 — Library acquisition
Download purchasable compounds from ZINC, resumable and polite.
**Gate:** the mass range must bracket the target's known drugs.

*What it caught:* ZINC tranche letters are **mass bins** — I = 425–450, J = 450–500,
K = 500–953. MRTX-1133 is 600 Da. The first library pulled was centred on 437 Da and had
to be thrown away. Also: `files.docking.org` returns 503 under parallel requests and
writes the HTML error page into your `.smi` file, and 403s urllib's default User-Agent
while allowing curl's. Both corrupt a library without announcing it.

### Phase 4 — Chemical reality gate ← the phase that would have saved the year
Can this molecule exist? Aromatic rings, unstable groups, self-reactive pairs, PAINS/BRENK.
**Gate: a PANEL of known drugs must survive it** — not two or three.

*What it caught:* **five separate catalogue rules were broken in the same direction.**
BRENK flags acrylamide as a Michael acceptor, rejecting Sotorasib and Adagrasib — the
warhead *is* the mechanism. A nitroso pattern also matched nitro groups, rejecting
Venetoclax. And the gate rejected **MRTX-1133** on the alkyne in its structure. A 14-drug
panel found all of them; a 3-drug check had missed them. Streaming is required — a 22M
compound list exhausts 16 GB otherwise.

### Phase 5 — Selection
Similarity to known binders, with a diversity cap so the shortlist is not one scaffold.

*Validated against a random control arm:* similarity-selected median **−8.68** vs random
**−8.24** kcal/mol. The heuristic earns its place; it is not assumed.

### Phase 6 — Docking screen
Site-directed Vina into the validated box. One Vina per ligand at one core each —
**4× faster** than one Vina on ten cores, because Vina's search threads poorly.
Checkpointed every 25 and resumable.

*Result:* G12D essentially nothing across 19,639. G12V 2 past the cognate across 9,913.

### Phase 7 — ADMET
Absorption, distribution, metabolism, excretion, toxicity — as a **filter**, not a column.
**Gate: the approved controls must pass.** Re-checked on every invocation; the script
exits if one fails.

*What it caught:* textbook cutoffs (DILI < 0.70, hERG < 0.70) rejected **199 of 200
compounds, including Sotorasib and Adagrasib**. Every approved control failed them. Those
two endpoints are now informational, with the thresholds derived from a 14-drug panel
rather than a textbook.

### Phase 8 — Route and buyability
Retrosynthesis (AiZynthFinder) for molecules nobody has made; vendor and price lookup for
ones you can buy. **Gate: chemical reality first** — the script refuses ungated input.

*What it caught:* retrosynthesis gave an impossible molecule an **80% in-stock precursor
fraction, better than Adagrasib's 71%**. It cannot judge stability: a triazane that
decomposes on formation still has a valid formal disconnection. Running this stage alone
reproduces the 2025 failure with more confidence attached.

Now extended by `route_forward.py`, which asks the question retrosynthesis structurally
cannot: **will each step work on this molecule?** It checks chemoselectivity (the reagent
cannot tell three identical sites apart) and condition compatibility (an epoxide does not
survive the acid that removes a Boc). Calibrated: generated molecules need a median of
**4** interventions where a purchasable compound needs **1**.

### Phase 9 — Order dossier
Join survivors back to ZINC IDs, vendor, price and availability. The output a human
approves before money is spent.

### Rung 2 — MM-GBSA rescoring
An independent physics-based check on the docking ranking, scoring the **docked pose**.
**Gate: the cognate ligand must score as a binder, and the known drugs must order sensibly.**

*What it caught — my own bug:* the first version re-embedded each ligand from SMILES, so
it sat in an arbitrary frame near the origin while the protein sat elsewhere. The
"complex" was two things floating apart. The crystallographic ligand scored **+23.44
kcal/mol** — impossible. Scoring the docked pose gives **−33.22**. The gate initially only
*counted* results instead of checking the ranking it promised, so the broken run proceeded
and burned 37 minutes. Both are fixed and commented.

### Phase 10 — Lab capture — NOT BUILT
Orders placed from inside the system; NMR, LC-MS, purity and assay readouts ingested back
onto the molecule record that predicted them.

**This matters more than anything above it.** Every phase improves only if measured
outcomes return. Without it the pipeline never learns, and the phases that need real assay
data — potency, cell response, exposure — cannot be built at all.

---

## The pattern across all of it

Nine of eleven gates exist because a tool gave a confident, plausible, wrong answer.
None of them threw an error. A filter that rejects the drugs it should rank first still
returns a tidy sorted list, and a scoring function with 4 kcal/mol of noise still prints
numbers to two decimal places.

The only defence that worked was running every stage against molecules whose answer was
already known, and refusing to believe the stage until it reproduced them.

---

## Layout

    src/          every pipeline script, plus the Kaggle notebook and status helpers
    data/raw/     the 2025 cross-docking sheet, validation sets
    data/gated/   gate survivors and every rejection with its reason
    data/screens/ docking results
    data/shortlists/  ranked shortlists per variant
    targets/      receptors, boxes, crystal references, validation runs
    results/      audit output, ADMET, routes, rescoring, forward-chemistry
    runs/         DiffDock notebooks with outputs, and FINDINGS.md
    papers/       what is publishable
    bin/vina      AutoDock Vina 1.2.7, native arm64

Pose archives, the ZINC library and the retrosynthesis models are excluded for size;
`run_screen.py` and `fetch_zinc.py` regenerate them.

## Flow

    library.smi                    fetch_zinc.py       ZINC tranches, resumable
        |
        |  prepare_ligands.py      ~15,000 mol/s, streaming
        v
    ligands.json                   chemically real, drug-like, MW-windowed
        |
        |  select_ligands.py       similarity to known binders + diversity cap
        v
    selected.json
        |
        |  run_screen.py           Vina into the validated box
        v
    screen_results.json  ->  top200.json
        |
        |  admet_gate.py           gating, not annotating
        |  mmgbsa.py               rung 2, scores the docked pose
        |  route_forward.py        selectivity and condition conflicts
        v
    order dossier

## Validate before you screen

    python src/dock_site.py validate

Redocks the crystal ligand and reports RMSD to its known pose. Under 2.0 Å means the box
and scoring function work on this receptor. **Run this for every new target.** It is the
check that was missing in 2025.

## Reproduce the post-mortem

    python src/audit_molecules.py data/raw/source-cross_docked_kras.xlsx

## Setup

    pip install rdkit meeko gemmi scipy numpy openpyxl
    # bin/vina is already the native arm64 binary

---

## Four things that will bite you

**The covalent exemption.** BRENK flags acrylamide as `Michael_acceptor_1`, rejecting
Sotorasib and Adagrasib — the warhead *is* the mechanism. Pass `--covalent` for G12C.

**RMSD against a PDB ligand.** No bond orders, so `CalcRMS` maps atoms arbitrarily and
returns a large meaningless number. Assign bond orders from SMILES first. A pose 0.34 Å
from the crystal centroid first reported as 8.42 Å.

**Cognate controls only.** Judging 8AFB with Sotorasib (whose structure is 6OIM) measures
cross-docking, not binding.

**Score the docked pose, not a fresh conformer.** MM-GBSA on a re-embedded conformer put
the crystallographic ligand at **+23 kcal/mol** — the protein and ligand were floating
apart. Scoring the pose gives −33.

Full list in [DISCOVERIES.md](DISCOVERIES.md#8-traps-found-along-the-way).
