"""
MM-GBSA rescoring — rung 2 of the fidelity ladder.

Docking scores are empirical functions with fitted weights. MM-GBSA computes an
interaction energy from a molecular-mechanics force field with implicit (GB) solvent.
Different kind of method, roughly 1.5-2.0 kcal/mol error against ~2.5 for docking.

    ΔG_bind ≈ E(complex) − E(receptor) − E(ligand)      each after minimisation

This is single-snapshot MM-GBSA, not an MD ensemble average — the cheap, standard
variant. It corrects the grosser docking errors; it is not FEP.

    python src/mmgbsa.py data/shortlists/top200_g12v.json \
        --receptor targets/g12v/receptor_protein.pdb \
        --controls targets/g12v/controls.json -o results/mmgbsa_g12v.json

CONTROL GATE: the known drugs must rank sensibly or the run is reported as
untrustworthy. Vinardo failed exactly this check on G12V, ranking MRTX-1133 last of
three. A method that cannot order the clinical compounds cannot order yours.
"""
import argparse, json, os, sys, time, warnings
import multiprocessing as mp
from pathlib import Path

# Must be set before OpenMM creates a Platform. One thread per process: the pool
# gets its parallelism from running many compounds at once, not from splitting one.
os.environ.setdefault("OPENMM_CPU_THREADS", "1")

warnings.filterwarnings("ignore")


def prepare_receptor(pdb_in, pdb_out):
    """Add missing heavy atoms and hydrogens. Amber ff14SB needs explicit H, and a
    PDB stripped of hydrogens (or missing side-chain atoms) fails template matching
    with 'No template found for residue'."""
    from pdbfixer import PDBFixer
    from openmm.app import PDBFile
    fixer = PDBFixer(filename=str(pdb_in))
    fixer.findMissingResidues()
    fixer.missingResidues = {}          # do not build unresolved loops
    fixer.findNonstandardResidues()
    fixer.replaceNonstandardResidues()
    fixer.removeHeterogens(keepWater=False)
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(7.4)
    with open(pdb_out, "w") as fh:
        PDBFile.writeFile(fixer.topology, fixer.positions, fh, keepIds=True)
    return pdb_out


def build_system(receptor_pdb, lig_smiles, lig_conf_mol):
    """Parameterise receptor + ligand and return OpenMM objects for the 3 states."""
    import openmm as mm
    from openmm import app, unit
    from openmm.app import PDBFile, Modeller, ForceField
    from openmmforcefields.generators import SystemGenerator
    from openff.toolkit.topology import Molecule

    off_mol = Molecule.from_rdkit(lig_conf_mol, allow_undefined_stereo=True)

    # GB implicit solvent requires a non-periodic nonbonded method. SystemGenerator
    # rejects nonbondedMethod inside forcefield_kwargs — it belongs in the
    # periodic/nonperiodic variants, and this system has no box.
    ff_kwargs = dict(constraints=app.HBonds, rigidWater=True,
                     removeCMMotion=False, hydrogenMass=3 * unit.amu)
    gen = SystemGenerator(
        forcefields=["amber/ff14SB.xml", "implicit/gbn2.xml"],
        small_molecule_forcefield="gaff-2.11",
        molecules=[off_mol],
        forcefield_kwargs=ff_kwargs,
        nonperiodic_forcefield_kwargs=dict(nonbondedMethod=app.NoCutoff),
    )
    return gen, off_mol


def energy_of(system, topology, positions, tol=5.0, steps=200):
    """Minimise briefly and return potential energy in kcal/mol."""
    import openmm as mm
    from openmm import unit
    integrator = mm.LangevinMiddleIntegrator(300 * unit.kelvin, 1 / unit.picosecond,
                                             0.002 * unit.picoseconds)
    ctx = mm.Context(system, integrator, mm.Platform.getPlatformByName("CPU"))
    ctx.setPositions(positions)
    mm.LocalEnergyMinimizer.minimize(ctx, tol, steps)
    e = ctx.getState(getEnergy=True).getPotentialEnergy()
    del ctx, integrator
    return e.value_in_unit(unit.kilocalorie_per_mole)


def pose_to_mol(pdbqt_text, smiles):
    """Docked pose -> RDKit mol with receptor-frame coordinates and correct bond orders.

    THE POSE IS THE POINT. An earlier version embedded a fresh conformer from SMILES,
    which sits in its own frame near the origin — so the "complex" was a protein and a
    ligand floating apart, and the interaction energy was noise. The giveaway was the
    cognate ligand scoring +23 kcal/mol.
    """
    import tempfile
    from meeko import PDBQTMolecule, RDKitMolCreate
    from rdkit import Chem
    from rdkit.Chem import AllChem
    with tempfile.NamedTemporaryFile("w", suffix=".pdbqt", delete=False) as fh:
        fh.write(pdbqt_text); path = fh.name
    try:
        pm = PDBQTMolecule.from_file(path, skip_typing=True)
        mols = RDKitMolCreate.from_pdbqt_mol(pm)
        if not mols or mols[0] is None:
            return None
        m = mols[0]
        # Keep only the top-ranked pose. RemoveAllConformers() invalidates any live
        # reference, so copy the conformer before dropping the rest — otherwise
        # AddConformer re-adds a dangling object and RDKit raises
        # "conf->getNumAtoms() == this->getNumAtoms()".
        if m.GetNumConformers() > 1:
            keep = Chem.Conformer(m.GetConformer(0))
            m.RemoveAllConformers()
            m.AddConformer(keep, assignId=True)
        m = Chem.AddHs(m, addCoords=True)
        return m
    except Exception:
        return None
    finally:
        import os; os.unlink(path)


def score_one(receptor_pdb, smiles, pose_pdbqt, seed=42):
    """ΔG_bind estimate in kcal/mol from the DOCKED pose, or None on failure."""
    from openmm.app import PDBFile, Modeller

    m = pose_to_mol(pose_pdbqt, smiles)
    if m is None:
        return None

    gen, off_mol = build_system(receptor_pdb, smiles, m)

    pdb = PDBFile(str(receptor_pdb))
    lig_top = off_mol.to_topology().to_openmm()
    lig_pos = off_mol.conformers[0].to_openmm()   # now the docked coordinates

    pdb.topology.setPeriodicBoxVectors(None)
    lig_top.setPeriodicBoxVectors(None)

    model = Modeller(pdb.topology, pdb.positions)
    model.add(lig_top, lig_pos)
    model.topology.setPeriodicBoxVectors(None)
    sys_complex = gen.create_system(model.topology)
    e_complex = energy_of(sys_complex, model.topology, model.positions)

    sys_rec = gen.create_system(pdb.topology)
    e_rec = energy_of(sys_rec, pdb.topology, pdb.positions)

    sys_lig = gen.create_system(lig_top)
    e_lig = energy_of(sys_lig, lig_top, lig_pos)

    return e_complex - e_rec - e_lig


def _score_worker(task):
    """One compound, one core.

    OpenMM's CPU platform spreads a single system across every core, and it scales
    badly: the serial run held ~7 cores and still took 564s per compound. The Vina
    screen hit the same wall and the same fix applied — one ligand per core, N at a
    time, was 4x faster than one ligand on 10 cores. Same shape of problem here.
    """
    receptor, smiles, pose, seed, vina = task
    try:
        g = score_one(receptor, smiles, pose, seed)
    except Exception:
        g = None
    return {"SMILES": smiles, "vina": vina, "mmgbsa": g}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("shortlist")
    ap.add_argument("--receptor", required=True, help="protein-only PDB")
    ap.add_argument("--controls", required=True)
    ap.add_argument("-o", "--out", default="results/mmgbsa.json")
    ap.add_argument("--top", type=int, default=200)
    ap.add_argument("--poses", help="screen JSON holding Ligand PDBQT per compound")
    ap.add_argument("--control-poses", help="dir with <name>_docked.pdbqt")
    ap.add_argument("--cognate", help="control that is co-crystallised in the receptor")
    ap.add_argument("--workers", type=int, default=8,
                    help="compounds in flight; each pinned to one core")
    ap.add_argument("--resume", action="store_true",
                    help="keep controls and compounds already in the output file")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rows = json.loads(Path(args.shortlist).read_text())[:args.top]
    controls = json.loads(Path(args.controls).read_text())

    # docked poses, in the receptor frame — required, not optional
    poses = {}
    if args.poses:
        for r in json.loads(Path(args.poses).read_text()).values():
            if r.get("Ligand PDBQT"):
                poses[r["SMILES"]] = r["Ligand PDBQT"]
    cposes = {}
    for name in controls:
        f = Path(args.control_poses or "") / f"{name}_docked.pdbqt"
        if f.exists():
            cposes[name] = f.read_text()
    print(f"poses: {len(poses)} shortlist, {len(cposes)} controls")

    # Resume: controls and compounds already computed are not recomputed.
    done, already, prior = [], set(), {}
    if args.resume and Path(args.out).exists():
        d = json.loads(Path(args.out).read_text())
        done = [c for c in d.get("compounds", []) if c.get("mmgbsa") is not None]
        already = {c["SMILES"] for c in done}
        prior = {k: v for k, v in d.get("controls", {}).items() if v is not None}

    # --- receptor prep, once ------------------------------------------------
    fixed = Path(args.receptor).with_name(Path(args.receptor).stem + "_fixed.pdb")
    if not fixed.exists():
        print(f"preparing receptor (adding missing atoms + hydrogens) ...", flush=True)
        prepare_receptor(args.receptor, fixed)
    args.receptor = str(fixed)
    print(f"receptor: {args.receptor}\n")

    # --- controls first: if the method cannot rank known drugs, stop -------
    print(f"control check ({len(controls)} known compounds) — this gates the run\n")
    cres = {}
    if len(prior) >= 2:
        # The gate is about the method, not this process; a passing result carries over.
        cres = prior
        for name, g in cres.items():
            print(f"  {name:<12} {g:>9.2f} kcal/mol   (from previous run)")
    for name, smi in ({} if cres else controls).items():
        t0 = time.time()
        try:
            if name not in cposes:
                raise RuntimeError("no docked pose for this control")
            g = score_one(args.receptor, smi, cposes[name], args.seed)
        except Exception as e:
            g = None
            print(f"  {name:<12} FAILED: {str(e)[:60]}")
        cres[name] = g
        if g is not None:
            print(f"  {name:<12} {g:>9.2f} kcal/mol   ({time.time()-t0:.0f}s)")

    ok = {k: v for k, v in cres.items() if v is not None}
    if len(ok) < 2:
        sys.exit("\nfewer than 2 controls scored — cannot judge the method. Stopping.")

    # A previous version only counted results here, so a run where the cognate ligand
    # scored +23 kcal/mol (i.e. non-binding) proceeded to burn 37 minutes. Check the
    # thing the gate claims to check.
    problems = []
    if args.cognate and args.cognate in ok and ok[args.cognate] > 0:
        problems.append(f"cognate {args.cognate} scores {ok[args.cognate]:+.2f} "
                        f"(positive = non-binding); its pose is crystallographic, so "
                        f"this cannot be right")
    if all(v > 0 for v in ok.values()):
        problems.append("every control scores positive — no binding predicted at all")
    if problems:
        print("\nCONTROL GATE FAILED:")
        for p in problems:
            print(f"  - {p}")
        sys.exit("\nMethod is not trustworthy on this target. Not scoring the shortlist.")
    print("\ncontrol gate passed — proceeding")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump({"controls": cres, "compounds": done}, open(args.out, "w"), indent=2)

    tasks = [(args.receptor, r["SMILES"], poses[r["SMILES"]], args.seed, r["Vina Score"])
             for r in rows
             if r["SMILES"] in poses and r["SMILES"] not in already]
    out = list(done)
    print(f"\nscoring {len(tasks)} compounds on {args.workers} workers "
          f"({len(already)} already done) ...", flush=True)

    t0 = time.time()
    with mp.get_context("spawn").Pool(args.workers) as pool:
        for i, res in enumerate(pool.imap_unordered(_score_worker, tasks), 1):
            if res["mmgbsa"] is not None:
                out.append(res)
            if i % 10 == 0 or i == len(tasks):
                rate = (time.time() - t0) / i
                json.dump({"controls": cres, "compounds": out}, open(args.out, "w"), indent=2)
                best = min((c["mmgbsa"] for c in out), default=float("nan"))
                print(f"  {i}/{len(tasks)} | {len(out)} scored | {rate:.0f}s each | "
                      f"best {best:.2f} | {rate*(len(tasks)-i)/60:.0f} min left", flush=True)

    # --- verdict -----------------------------------------------------------
    if out:
        try:
            from scipy.stats import spearmanr
            rho, p = spearmanr([c["vina"] for c in out], [c["mmgbsa"] for c in out])
            print(f"\nSpearman vina vs MM-GBSA: rho={rho:.3f} (p={p:.2g})")
        except Exception:
            pass
        out.sort(key=lambda c: c["mmgbsa"])
        print(f"\ntop 10 by MM-GBSA:")
        print(f"{'rank':>5} {'vina':>8} {'mmgbsa':>10}  SMILES")
        for i, c in enumerate(out[:10], 1):
            print(f"{i:>5} {c['vina']:>8.2f} {c['mmgbsa']:>10.2f}  {c['SMILES'][:46]}")
    json.dump({"controls": cres, "compounds": out}, open(args.out, "w"), indent=2)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
