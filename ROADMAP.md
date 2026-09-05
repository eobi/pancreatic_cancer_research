# Where we are and what runs next

Updated 2026-09-05. The single organising fact: **every step that can be computed has been
computed, and nothing has yet been measured.** The pipeline is validated end to end in
silico; no compound has been touched by a lab. That gap sets every priority below.

---

## Where we are

### Built and gated (11 phases + 2 ladder rungs)

| stage | state | evidence |
|---|---|---|
| 0 Target intake | done, 4 targets | prevalence-driven; cognate ligand required |
| 1 Receptor prep | done | box from crystal ligand + 10 A |
| 2 Method validation | done | G12C 0.67 A, G12D 0.88 A, G12V 1.55 A, G12R 0.99 A |
| 3 Library | done | 518,662 gated ligands, target-independent |
| 4 Chemical reality gate | done | 14-drug panel; caught 5 broken filters |
| 5 Selection | done | validated vs random arm (-8.68 vs -8.24) |
| 6 Docking screen | 3 of 4 targets | ex4 justified by Study 7 |
| 7 ADMET | done | controls self-check on every run |
| 8 Route + buyability | done | + forward chemoselectivity layer |
| 9 Order dossier | built, **not used** | no order placed |
| Rung 2 MM-GBSA | done | 200 compounds, controls gated |
| **10 Lab capture** | **NOT BUILT** | the blocking gap |

### Screens, by disease prevalence

| variant | % PDAC | screened | outcome |
|---|---|---|---|
| G12D | 39% | 19,639 | essentially nothing |
| G12V | 29% | 9,913 | 2 past cognate; shortlist unrankable |
| **G12R** | **15%** | **queued** | validated 0.99 A, ready |
| G12C | 1.7% | 2,000 | 82 hits — wrong variant for this disease |

Coverage **68%** now, **83%** once G12R runs.

### What the experiments established

1. 0 of 73 generated molecules pass a filter 57-76% of purchasable compounds pass.
2. Five independent filters failed in the same direction, each rejecting approved drugs.
3. Retrosynthesis scored an impossible molecule above a marketed drug (80% vs 71%).
4. Blind docking could not rank (4.0 kcal/mol variance); site-directed can.
5. No purchasable compound competes with clinical inhibitors, over 68% of PDAC KRAS.
6. Two independent rescoring methods cannot rank a shortlist flat in the primary score
   (rho 0.259 and 0.106) — the input carries no ordering.
7. Exhaustiveness buys geometry, not ranking: ex4 vs ex128 drifts 0.08 kcal/mol at 1/31 cost.

All seven are written up in `papers/STUDIES.md` with reproduction commands.

---

## Where we are going

Two papers, and they need different things.

**Paper 1 (retrospective) — writable now.** Merges studies 1, 2, 5 with 3, 4, 6, 7 as
supporting material. Ceiling is Nature Communications; it is a negative result with a
real-world anchor.

**Paper 2 (prospective) — blocked on the lab.** Pre-registered, hypotheses fixed before
data. This is the A-list paper, and its tier depends almost entirely on running an
**ungated control arm** alongside the gated one.

---

## What runs next, in order

### 1. G12R screen — running now
Cores are free, target validated, ex4 justified by Study 7 (31x cheaper than the
alternative, at 0.08 kcal/mol cost). Takes coverage 68% -> 83%. **~14 h.**

### 2. Order compounds — the critical path
Weeks of lead time, and everything downstream waits on it. Two decisions first:

- **Which compounds.** The G12V shortlist is *not rank-orderable* (study 6): Vina and
  MM-GBSA share only 2 of their top 10. Either order that intersection as an explicitly
  unranked diversity set, or draw from G12R once it lands. Do not describe any G12V
  selection as "top-ranked" in a paper.
- **The ungated control arm.** Compounds selected by docking score alone, gates disabled.
  Without it Paper 2 is a case report rather than a controlled test. This must be
  specified *before* ordering.

### 3. Phase 10 — lab capture
Orders placed from inside the system; NMR, LC-MS, purity and assay readouts ingested onto
the molecule record that predicted them. Nothing in Paper 2 is verifiable without it, and
no phase improves until measured outcomes return.

### 4. Rung 3 — MD pose stability
Runs on this laptop, 5-12 h per compound. Removes docking false positives that survive
rescoring. Needed for Paper 2's H2 (ladder monotonicity). Do it on the ordered set only.

### 5. Write Paper 1
Independent of all the above. Needs the prior-art citations verified — they are currently
from recall, not a literature search.

---

## What is NOT next, and why

- **More rescoring on G12V.** Three methods agree the shortlist is flat. More compute will
  not produce an ordering that is not there.
- **Rung 4 (FEP).** ~1 kcal/mol and the rung that would change the argument, but 1-3 days
  per compound on a real GPU. Worth it only for compounds that are actually being ordered.
- **Retraining the generator.** Needs a GPU and a regenerated Kaggle token, and it
  addresses study 1's failure — which is a known result. Not on the critical path.
