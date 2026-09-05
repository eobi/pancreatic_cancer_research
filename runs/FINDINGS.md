# Kaggle GPU tier — validation result, 2026-08-31

**Conclusion: DiffDock + GNINA blind docking cannot rank ligands on KRAS G12C / 8AFB.
Do not use it to order a shortlist for this target.**

The infrastructure works. The scoring does not discriminate.

## What was proven to work

Kaggle T4 x2 (P100 fails — torch 2.10+cu128 dropped Pascal sm_60). DiffDock v1.1
(= DiffDock-L) at ~41 s/ligand. GNINA 1.3.3, `Affinity:` regex from the original
`docking.py` parses unmodified. Checkpointing, resume, and the chemical gate all live.
Setup ~10 min/session; `/kaggle/working` does not persist.

## What failed

Two identical runs (same receptor, same code, `SAMPLES_PER_COMPLEX=10`,
`INFERENCE_STEPS=20`), one session apart:

| ligand    | run 1  | run 2  | delta |
|-----------|--------|--------|-------|
| Adagrasib | -9.85  | -8.16  | 1.7   |
| Sotorasib | -3.80  | -7.78  | 4.0   |
| BI-0474   | —      | -8.07  | —     |

Three findings, any one of which is disqualifying:

1. **The cognate control fails.** BI-0474 is co-crystallised in 8AFB (ligand LXD).
   DiffDock should reproduce its pose trivially. It returns confidence -3.52, well
   below the -1.6 threshold, so `Good Docking Quality = False`.
2. **No discrimination.** The three known drugs span 0.4 kcal/mol (-8.16, -8.07, -7.78).
3. **Noise exceeds signal by 10x.** Sotorasib moved 4.0 kcal/mol between identical runs.
   DiffDock samples poses stochastically; 10 samples is not enough to stabilise the best.

Implication for the 2025 campaign: its rankings were substantially noise. That is a
second, independent reason the shortlist sent to the chemists was unreliable — on top of
the chemistry (see ../audit-output.txt).

## Why blind docking is wrong for this target

The G12C switch-II pocket is induced-fit: it does not exist in apo KRAS, it is carved
open by whichever inhibitor bound it. Each PDB's pocket is therefore shaped by ITS ligand:

    8AFB = BI-0474 (LXD)    6OIM = Sotorasib    6UT0 = Adagrasib

Docking a drug into a non-cognate structure is a cross-docking problem, and scores
degrade for reasons unrelated to binding. Sotorasib occupies a cryptic groove the
BI-0474 pocket does not present; Adagrasib happens to tolerate the shape.

Blind docking also discards information you already have. The site is known from three
crystal structures. Searching the whole protein surface for it pays variance for nothing.

## Next approach

Site-directed docking with smina, box defined from the LXD coordinates in 8AFB.
Deterministic given a seed, exploits the known pocket, ~1000x faster, and builds
natively on Apple Silicon — so the screen runs on the laptop.

Validate before screening: redock all three controls into the box and require that
BI-0474 lands near its crystal pose and that the three separate. That validation is
exactly what the 2025 campaign never did.

Keep the notebook. DiffDock earns its place on targets where the site is genuinely
unknown; it is the wrong tool for one with three liganded structures.

## Files

    kaggle_run_2026-08-31_two-controls.ipynb   run 1 (Adagrasib, Sotorasib)
    kaggle_run_2026-08-31_controls.ipynb       run 2 (+ BI-0474 cognate)

---

# Site-directed docking — validation PASSES, 2026-08-31

**AutoDock Vina 1.2.7 into a box built from the crystal ligand reproduces the cognate
pose and separates the controls. This replaces DiffDock for KRAS G12C.**

Receptor 8AFB protein-only (altloc A), box from LXD coordinates:
centre (14.63, -10.07, 21.50), size 24.0 x 18.8 x 22.0 A. Exhaustiveness 16, seed 42.

| ligand    | score (kcal/mol) | RMSD to crystal |
|-----------|------------------|-----------------|
| BI-0474   | **-12.26**       | **0.67 A**      |
| Adagrasib | -10.83           | -               |
| Sotorasib | -9.30            | -               |

The cognate ligand ranks first AND its top-scoring pose returns to within 0.67 A of the
crystal structure. Standard criterion is under 2.0 A.

## Against blind docking on the same receptor

|                          | DiffDock + GNINA | Vina site-directed |
|--------------------------|------------------|--------------------|
| cognate redock           | fails quality    | 0.67 A, ranks 1st  |
| control spread           | 0.4 kcal/mol     | 2.96 kcal/mol      |
| run-to-run variance      | 4.0 kcal/mol     | 0 (seeded)         |
| time per ligand          | 41 s (T4 GPU)    | ~13 s (M1 Pro CPU) |
| hardware                 | Kaggle GPU       | the laptop         |

Deterministic, better separated, three times faster, and no GPU. The whole screen can
run locally.

## Trap: RMSD needs bond orders

First attempt reported 8.42 A and looked like a failure. A ligand read from PDB has no
bond orders, so `rdMolAlign.CalcRMS` cannot match it to the docked molecule and maps
atoms arbitrarily. The give-away was that the docked centroid sat 0.34 A from the
crystal centroid with all 42 atoms inside the box — geometrically on top of it.
`AllChem.AssignBondOrdersFromTemplate` against the SMILES first gives the true 0.67 A.
`dock_site.py` now does this; do not compare a docked pose to a raw PDB ligand.

## Next

Screen a purchasable library:

    python prepare_ligands.py library.smi -o ligands.json --covalent
    python dock_site.py screen ligands.json -o screen_results.json

At ~13 s/ligand single-threaded, parallelise across cores for a real library.
