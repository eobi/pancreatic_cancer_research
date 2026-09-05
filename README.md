# KRAS G12C screening pipeline

**[DISCOVERIES.md](DISCOVERIES.md)** — what we found, with the numbers.
**[PIPELINE.md](PIPELINE.md)** — every phase, its command, and the gate it must pass.
**[papers/STUDIES.md](papers/STUDIES.md)** — the five publishable studies, their evidence,
and what each does *not* support.

## Layout

    src/          every pipeline script, plus the Kaggle notebook and status helpers
    data/raw/     ZINC library, the 2025 cross-docking sheet, validation sets
    data/gated/   gate survivors and every rejection with its reason
    data/screens/ all docking results, with poses
    data/shortlists/  ranked shortlists and the G12D lead
    targets/      receptors, boxes, crystal references, validation runs (g12c, g12d)
    results/      audit output, ADMET report, routes, catalogue exemptions
    runs/         DiffDock notebooks with outputs, and FINDINGS.md
    papers/       what is publishable
    logs/         run logs
    bin/vina      AutoDock Vina 1.2.7, native arm64

Rebuilt around two rules the 2025 campaign lacked:

1. Nothing reaches a chemist without passing a chemical-reality gate.
2. No scoring function is trusted until it reproduces a known crystal pose.

## State

Validated on KRAS G12C / 8AFB: cognate redock **0.67 A**, controls separated by
**2.96 kcal/mol**. A 2,000-compound screen has run — 1,987 scored, **82 beat Adagrasib**,
2 beat the cognate crystal ligand. All purchasable, no synthesis route to solve.

Next step is ADMET on `top200.json`, gating rather than annotating.

## Flow

    library.smi                    fetch_zinc.py    (ZINC tranches, resumable)
        |
        |  prepare_ligands.py      ~15,000 mol/s on an M1 Pro, streaming
        v
    ligands.json                   chemically real, drug-like, MW-windowed
        |
        |  select_ligands.py       similarity to known binders + diversity cap
        v
    selected.json
        |
        |  run_screen.py           Vina into the validated box, 3.5 s/ligand
        v
    screen_results.json  ->  top200.json
        |
        |  adapt_results.py        into the results.json shape connector.py consumes
        v
    results.json

## Validate before you screen

    python dock_site.py validate

Redocks the crystal ligand and reports RMSD to its known pose. Under 2.0 A means the box
and scoring function work on this receptor. **Run this for every new target.** It is the
check that was missing in 2025.

## Reproduce the post-mortem

    python audit_molecules.py source-cross_docked_kras.xlsx

## Setup

    pip install rdkit meeko gemmi scipy numpy openpyxl
    # bin/vina is already the native arm64 binary

## Three things that will bite you

**The covalent exemption.** BRENK flags acrylamide as `Michael_acceptor_1`, rejecting
Sotorasib and Adagrasib — the warhead *is* the mechanism. Pass `--covalent` for KRAS G12C.

**RMSD against a PDB ligand.** No bond orders, so `CalcRMS` maps atoms arbitrarily and
returns a large meaningless number. Assign bond orders from SMILES first.

**Cognate controls only.** Judging 8AFB with Sotorasib (whose structure is 6OIM) measures
cross-docking, not binding.

Full list in [DISCOVERIES.md](DISCOVERIES.md#5-traps-found-along-the-way).
