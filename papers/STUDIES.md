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
synthetic-accessibility heuristic, produced 3,631 molecules of which **none** survive a
standard pre-synthesis filter. The failure is categorical, not marginal.

**Evidence.**
- 3,626 of 3,631 have **no aromatic ring**. Reference drugs: 2 of 2.
- 63 of 73 in the reported shortlist carry a genotoxic or unstable group; mean 1.9 each.
- 15 are **self-reactive** — functional groups that destroy each other in the same molecule.
- The three structures actually sent to chemists all carry a triazane, an epoxide and (in
  two) a free aldehyde. Roughly a year of failed synthesis followed.
- Same filter on 902,833 purchasable compounds: **57-76% pass**. Generated: 0.0%.

**Reproduce.** `src/audit_molecules.py data/raw/source-cross_docked_kras.xlsx`
→ `results/audit-output.txt`

**Does not support.** That generative chemistry cannot work — only that this model, with
this objective, did not. The objective weighted docking 0.65 and synthetic accessibility
0.20, with no stability term at all.

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
