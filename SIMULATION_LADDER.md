# Digitising the chemical and biological processes — the fidelity ladder

Correcting my own earlier framing. I described in vitro / in vivo as binary: wet or nothing.
It is not. Between a docking score and a measured IC50 there is a ladder of physics-based
methods of increasing fidelity and cost. **We have built only the bottom rung.**

Your 2025 `notes.txt` already listed the right targets — RMSD, RMSF, SASA, MM-PBSA/GBSA.
That instinct was correct and was never acted on.

---

## Part 1 — Biological process: from hypothesis to computed binding free energy

| rung | method | error vs experiment | cost per compound | status |
|---|---|---|---|---|
| 1 | Docking score (Vina) | ~2.5 kcal/mol | **5 s** | **built** |
| 2 | MM-GBSA rescoring | ~1.5-2.0 kcal/mol | ~5 min | **built** (`mmgbsa.py`) |
| 3 | MD pose stability (RMSD/RMSF, 10-50 ns) | qualitative — kills false positives | 5-12 h | not built |
| 4 | Relative binding free energy (FEP/TI) | **~1.0 kcal/mol** | 1-3 days | not built |
| 5 | PBPK exposure (PK-Sim / OSP) | plasma & tissue exposure | minutes | not built |
| 6 | Pathway / QSP (KRAS→RAF→MEK→ERK) | downstream signalling inhibition | minutes | not built |

**Rung 4 is the one that changes the argument.** FEP at ~1 kcal/mol is the point where a
computed number starts predicting a measured one. It is the difference between "this might
bind" and "we calculate this binds ~10x tighter than the reference."

### Why this is not just more docking

Rung 1 asks *does this shape fit*. Rungs 2-4 compute **free energy** — the actual
thermodynamic quantity an IC50 reflects. Rung 3 additionally asks *does the pose survive
physics*, which removes a large class of docking false positives: poses that score well
and fall apart in 2 ns of simulation.

Our own data shows why this matters. The G12D lead beats AM-2383 by 0.12 kcal/mol, which
is **noise** at rung 1. At rung 4 that same comparison would be meaningful.

### The funnel this creates

    10,000  Vina docking          5 s each      ~14 h    (built)
       200  MM-GBSA rescoring     3 min each    ~10 h
        20  MD pose stability     8 h each      GPU box
         5  FEP binding free E    2 d each      GPU box
         5  PBPK + pathway        minutes
    -----
         5  compounds ordered, each with a computed binding free energy

**That is the digitised biological process.** Not a replacement for the assay — a way to
arrive at the assay with five compounds instead of five hundred, each carrying a number
that means something.

### Hardware honesty

Rungs 1-2 run on your laptop. Rung 3 is 5-12 h per compound on an M1 Pro via OpenMM/Metal —
feasible for ~20 compounds over a few days. **Rung 4 needs a real GPU.** FEP is 10-20x MD
cost; on a rented A100 it is hours rather than days. This is where Kaggle or a rented box
finally earns its place, and where regenerating that Kaggle token becomes worth doing.

---

## Part 2 — Chemical process: beyond route search

We built retrosynthesis (does a route exist). That is one of six things worth simulating.

| capability | question answered | tooling | status |
|---|---|---|---|
| Retrosynthesis | does a route exist, from what | AiZynthFinder | **built** |
| Forward reaction prediction | does each proposed step give the intended product | Molecular Transformer / IBM RXN | stub (`route_forward.predict_step`) — needs GPU/API |
| Condition recommendation | solvent, temperature, catalyst, time | rule-based, 8 reaction classes | **built** (`route_forward.py`) |
| Yield prediction | will the route actually deliver material | yield models | not built |
| Stability / degradation | does it survive storage, plasma, pH | RDKit alerts + per-condition compatibility | **built** (`route_forward.py`) |
| Physicochemical | pKa, logD, solubility at pH | RDKit + ML predictors | partial |

**Forward prediction is the important gap.** Retrosynthesis proposes a disconnection;
forward prediction checks the reaction actually runs that way. Together they are a closed
loop — propose, verify — and that pairing is much closer to "digitised synthesis" than
route search alone.

This also partly repairs the finding in DISCOVERIES section 6: retrosynthesis cannot judge
whether the *product* can exist, but forward prediction plus stability modelling can flag
when a proposed product would decompose under its own reaction conditions.

---

## Part 3 — What still cannot be digitised, honestly

| | why |
|---|---|
| **Cellular potency on your chemistry** | needs your assay data to train on; literature models mis-rank novel scaffolds |
| **Animal PK/PD, toxicity** | PBPK designs a smaller study; regulators do not accept it as a replacement |
| **Anything a regulator must accept** | FDA Modernization Act 2.0 opened the door in principle, not in practice |

The ladder does not remove the wet lab. It reduces it from "test hundreds and hope" to
"test five, each with a computed free energy and a predicted exposure." That is the prize,
and it is large.

---

## Build order

**Phase A — laptop, immediate.** MM-GBSA rescoring (rung 2) on the top 200 of each screen.
Biggest fidelity gain per unit effort. `openmm` + `openmmforcefields` + `mdtraj`, all
installable now.

**Phase B — laptop, days.** MD pose stability (rung 3) on the top 20. Produces exactly the
RMSD/RMSF/SASA your 2025 notes asked for, and kills docking false positives before anyone
spends money.

**Phase C — GPU box.** FEP (rung 4) on the top 5. This is the number worth putting in front
of a clinical partner.

**Phase D — laptop, hours.** PBPK (rung 5) and KRAS pathway simulation (rung 6) via
`tellurium`/`libroadrunner`. Cheap, and turns a binding number into a predicted biological
effect.

**Phase E — parallel.** Forward reaction prediction to close the synthesis loop.

Phases A, B and D are buildable on hardware you already own. Only C needs rented compute.
