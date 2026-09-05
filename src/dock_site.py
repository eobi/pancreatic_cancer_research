"""
Site-directed docking with AutoDock Vina, into a box defined by a crystal ligand.

Replaces blind docking (DiffDock) for targets whose binding site is already known
from a liganded structure. See runs/FINDINGS.md for why: on KRAS G12C / 8AFB, blind
docking put the cognate ligand below the quality threshold, failed to separate three
known drugs (0.4 kcal/mol spread), and swung 4.0 kcal/mol between identical runs.

Two modes:

    validate   Redock the crystal ligand and any reference drugs. Reports docking
               score AND symmetry-corrected RMSD to the crystal pose. A cognate
               redock under 2.0 A is the standard criterion for "this box and this
               scoring function work here". Run this before trusting any screen.

    screen     Dock a gated ligand list, write results in the results.json shape.

Requires: rdkit, meeko, gemmi, scipy, numpy, and the vina binary (bin/vina).
"""
import argparse, json, os, subprocess, sys, tempfile, time
from pathlib import Path

import numpy as np
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, rdMolAlign, Descriptors
from rdkit.Chem.rdMolDescriptors import CalcMolFormula

RDLogger.DisableLog("rdApp.*")

HERE = Path(__file__).parent
def _find_vina():
    """bin/vina lives at the project root; scripts live in src/. Check both."""
    here = Path(__file__).resolve().parent
    for cand in (here / "bin" / "vina", here.parent / "bin" / "vina"):
        if cand.exists():
            return cand
    return here.parent / "bin" / "vina"        # for the error message


VINA = _find_vina()


# --------------------------------------------------------------------------- prep

def embed_3d(smiles, seed=0xF00D):
    """SMILES -> a single low-energy 3D conformer."""
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return None
    m = Chem.AddHs(m)
    params = AllChem.ETKDGv3()
    params.randomSeed = seed
    if AllChem.EmbedMolecule(m, params) != 0:
        return None
    AllChem.MMFFOptimizeMolecule(m, maxIters=500)
    return m


def to_pdbqt(mol, out_path):
    """RDKit mol -> Vina PDBQT via meeko."""
    from meeko import MoleculePreparation, PDBQTWriterLegacy
    prep = MoleculePreparation()
    setups = prep.prepare(mol)
    if not setups:
        return False
    pdbqt, ok, err = PDBQTWriterLegacy.write_string(setups[0])
    if not ok:
        print(f"    meeko: {err}")
        return False
    Path(out_path).write_text(pdbqt)
    return True


# ------------------------------------------------------------------------- docking

def dock(ligand_pdbqt, receptor_pdbqt, box, out_pdbqt, exhaustiveness=16, n_poses=9,
         seed=42, cpu=None):
    cpu = cpu or os.cpu_count()
    """Run Vina. Returns list of pose scores (kcal/mol), best first."""
    cx, cy, cz, sx, sy, sz = box
    cmd = [str(VINA),
           "--receptor", str(receptor_pdbqt), "--ligand", str(ligand_pdbqt),
           "--center_x", f"{cx}", "--center_y", f"{cy}", "--center_z", f"{cz}",
           "--size_x", f"{sx}", "--size_y", f"{sy}", "--size_z", f"{sz}",
           "--out", str(out_pdbqt),
           "--exhaustiveness", str(exhaustiveness),
           "--num_modes", str(n_poses),
           "--seed", str(seed),          # deterministic, unlike DiffDock
           "--cpu", str(cpu)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"    vina failed: {(r.stderr or r.stdout).strip()[:300]}")
        return []
    scores = []
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0].isdigit():
            try:
                scores.append(float(parts[1]))
            except ValueError:
                pass
    return scores


def pose_to_mol(pdbqt_path, template_smiles):
    """First pose out of a Vina PDBQT, with bond orders from the template."""
    from meeko import PDBQTMolecule, RDKitMolCreate
    try:
        pm = PDBQTMolecule.from_file(str(pdbqt_path), skip_typing=True)
        mols = RDKitMolCreate.from_pdbqt_mol(pm)
        return mols[0] if mols and mols[0] is not None else None
    except Exception as e:
        print(f"    pose parse failed: {e}")
        return None


def rmsd_to_crystal(docked, crystal_pdb, template_smiles):
    """Symmetry-corrected RMSD of the best docked pose against the crystal ligand.

    A PDB ligand carries no bond orders, so RDKit cannot match it to the docked
    molecule directly - CalcRMS then maps atoms arbitrarily and returns a large,
    meaningless number. Bond orders must be assigned from the SMILES template first.
    """
    if docked is None:
        return None
    # RDKit's default PDB reader silently drops HETATM records for residues it cannot
    # resolve, returning a Mol with ZERO atoms rather than an error. flavor=1 reads them.
    # Hits any ligand extracted from an mmCIF-only entry, where 5-character CCD codes
    # (e.g. A1AG3) do not fit the 3-character PDB resName field.
    ref_raw = None
    for kw in ({"sanitize": False, "flavor": 1}, {"sanitize": False}):
        m = Chem.MolFromPDBFile(str(crystal_pdb), removeHs=True, **kw)
        if m is not None and m.GetNumAtoms() > 0:
            ref_raw = m
            break
    if ref_raw is None:
        print("    crystal reference has no readable atoms")
        return None
    try:
        ref = AllChem.AssignBondOrdersFromTemplate(Chem.MolFromSmiles(template_smiles), ref_raw)
    except Exception as e:
        print(f"    could not assign bond orders to crystal ligand: {e}")
        return None

    probe = Chem.RemoveHs(Chem.Mol(docked))
    best = None
    for cid in range(probe.GetNumConformers()):
        single = Chem.Mol(probe); single.RemoveAllConformers()
        single.AddConformer(probe.GetConformer(cid), assignId=True)
        try:
            r = rdMolAlign.CalcRMS(single, ref)
            best = r if best is None else min(best, r)
        except Exception:
            continue
    return best


# ------------------------------------------------------------------------ commands

def cmd_validate(args):
    box = [float(x) for x in Path(args.box).read_text().split()]
    work = Path(args.workdir); work.mkdir(parents=True, exist_ok=True)
    controls = json.loads(Path(args.controls).read_text())

    print(f"receptor  {args.receptor}")
    print(f"box       centre ({box[0]:.2f}, {box[1]:.2f}, {box[2]:.2f})  "
          f"size {box[3]:.1f} x {box[4]:.1f} x {box[5]:.1f}")
    print(f"crystal   {args.crystal}")
    print(f"exhaustiveness {args.exhaustiveness}, seed {args.seed}\n")

    rows = []
    for name, smi in controls.items():
        t0 = time.time()
        print(f"  {name} ...", end=" ", flush=True)
        mol = embed_3d(smi, seed=args.seed)
        if mol is None:
            print("EMBED FAILED"); continue
        lig = work / f"{name}.pdbqt"
        if not to_pdbqt(mol, lig):
            print("PDBQT FAILED"); continue
        out = work / f"{name}_docked.pdbqt"
        scores = dock(lig, args.receptor, box, out,
                      exhaustiveness=args.exhaustiveness, seed=args.seed)
        if not scores:
            print("DOCK FAILED"); continue

        rmsd = None
        if args.crystal and name == args.cognate:
            rmsd = rmsd_to_crystal(pose_to_mol(out, smi), args.crystal, smi)

        rows.append({"name": name, "score": scores[0], "n_poses": len(scores),
                     "rmsd": rmsd, "secs": time.time() - t0})
        print(f"{scores[0]:>7.2f} kcal/mol  ({time.time()-t0:.0f}s)")

    print(f"\n{'ligand':<12}{'score':>9}{'RMSD':>9}   verdict")
    print("-" * 52)
    rows.sort(key=lambda r: r["score"])
    for r in rows:
        cog = r["name"] == args.cognate
        rm = f"{r['rmsd']:.2f}" if r["rmsd"] is not None else "-"
        note = ""
        if cog:
            note = ("cognate redock OK" if (r["rmsd"] or 99) < 2.0
                    else "COGNATE REDOCK FAILS (>2.0 A)")
        print(f"{r['name']:<12}{r['score']:>9.2f}{rm:>9}   {note}")

    spread = max(r["score"] for r in rows) - min(r["score"] for r in rows)
    print(f"\nscore spread across controls: {spread:.2f} kcal/mol")
    cognate = next((r for r in rows if r["name"] == args.cognate), None)
    print()
    if cognate and cognate["rmsd"] is not None and cognate["rmsd"] < 2.0:
        print("PASS - the box and scoring function reproduce the crystal pose.")
        if spread < 1.0:
            print("     - but the controls barely separate; treat rank as coarse.")
    else:
        print("FAIL - the cognate ligand does not return to its crystal pose.")
        print("       Do not screen with this setup. Check the box, the protonation,")
        print("       or whether the site needs an ensemble of receptor structures.")
    json.dump(rows, open(work / "validation.json", "w"), indent=2)
    print(f"\nwrote {work/'validation.json'}")


def cmd_screen(args):
    box = [float(x) for x in Path(args.box).read_text().split()]
    work = Path(args.workdir); work.mkdir(parents=True, exist_ok=True)
    ligands = json.loads(Path(args.ligands).read_text())
    if isinstance(ligands, dict):
        ligands = list(ligands)

    out_path = Path(args.out)
    results = json.loads(out_path.read_text()) if out_path.exists() else {}
    todo = [s for s in ligands if s not in results]
    print(f"{len(ligands)} ligands, {len(results)} already done, {len(todo)} to go\n")

    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for i, smi in enumerate(todo):
            mol = embed_3d(smi, seed=args.seed)
            if mol is None:
                continue
            lig, out = tmp / "l.pdbqt", tmp / "o.pdbqt"
            if not to_pdbqt(mol, lig):
                continue
            scores = dock(lig, args.receptor, box, out,
                          exhaustiveness=args.exhaustiveness, seed=args.seed)
            if not scores:
                continue
            m = Chem.MolFromSmiles(smi)
            results[smi] = {
                "SMILES": smi,
                "Vina Score": scores[0],
                "Vina Poses": len(scores),
                "Molecular Formula": CalcMolFormula(m),
                "Molecular Weight": Descriptors.MolWt(m),
            }
            if (i + 1) % 25 == 0 or i + 1 == len(todo):
                json.dump(results, open(out_path, "w"), indent=2)
                rate = (time.time() - t0) / (i + 1)
                print(f"  {i+1}/{len(todo)} | {rate:.1f}s per ligand | "
                      f"{rate*(len(todo)-i-1)/3600:.1f} h remaining")

    json.dump(results, open(out_path, "w"), indent=2)
    print(f"\nwrote {out_path} ({len(results)} ligands)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="redock controls and check the cognate RMSD")
    v.add_argument("--receptor", default="work/rec.pdbqt")
    v.add_argument("--box", default="work/box.txt")
    v.add_argument("--crystal", default="work/ref_LXD.pdb")
    v.add_argument("--controls", default="work/controls.json")
    v.add_argument("--cognate", default="BI-0474")
    v.add_argument("--workdir", default="work/validate")
    v.add_argument("--exhaustiveness", type=int, default=16)
    v.add_argument("--seed", type=int, default=42)
    v.set_defaults(func=cmd_validate)

    s = sub.add_parser("screen", help="dock a gated ligand list")
    s.add_argument("ligands")
    s.add_argument("--receptor", default="work/rec.pdbqt")
    s.add_argument("--box", default="work/box.txt")
    s.add_argument("-o", "--out", default="screen_results.json")
    s.add_argument("--workdir", default="work/screen")
    s.add_argument("--exhaustiveness", type=int, default=8)
    s.add_argument("--seed", type=int, default=42)
    s.set_defaults(func=cmd_screen)

    args = ap.parse_args()
    if not VINA.exists():
        sys.exit(f"vina binary not found at {VINA}")
    args.func(args)


if __name__ == "__main__":
    main()
