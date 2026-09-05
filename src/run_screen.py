"""
Parallel site-directed screen. One Vina process per ligand, one core each.

Vina's intra-run threading scales poorly, so N single-core runs in parallel beat one
N-core run. Checkpoints every 25 completions and skips what is already done, so it
survives an interrupt.

    python run_screen.py selected.json -o screen_results.json -j 10
"""
import argparse, json, multiprocessing as mp, os, subprocess, tempfile, time
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors
from rdkit.Chem.rdMolDescriptors import CalcMolFormula

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent

def _find_vina():
    """bin/vina lives at the project root; scripts live in src/. Check both."""
    here = Path(__file__).resolve().parent
    for cand in (here / "bin" / "vina", here.parent / "bin" / "vina"):
        if cand.exists():
            return cand
    return here.parent / "bin" / "vina"        # for the error message

_g = {}


def _init(receptor, box, exh, seed):
    RDLogger.DisableLog("rdApp.*")
    _g.update(receptor=receptor, box=box, exh=exh, seed=seed,
              vina=str(_find_vina()))


def _dock_one(smi):
    from meeko import MoleculePreparation, PDBQTWriterLegacy
    try:
        m0 = Chem.MolFromSmiles(smi)
        if m0 is None:
            return None
        m = Chem.AddHs(m0)
        p = AllChem.ETKDGv3(); p.randomSeed = _g["seed"]
        if AllChem.EmbedMolecule(m, p) != 0:
            return None
        AllChem.MMFFOptimizeMolecule(m, maxIters=500)
        setups = MoleculePreparation().prepare(m)
        if not setups:
            return None
        pdbqt, ok, _err = PDBQTWriterLegacy.write_string(setups[0])
        if not ok:
            return None

        b = _g["box"]
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "l.pdbqt").write_text(pdbqt)
            cmd = [_g["vina"], "--receptor", _g["receptor"], "--ligand", str(d / "l.pdbqt"),
                   "--center_x", f"{b[0]}", "--center_y", f"{b[1]}", "--center_z", f"{b[2]}",
                   "--size_x", f"{b[3]}", "--size_y", f"{b[4]}", "--size_z", f"{b[5]}",
                   "--out", str(d / "o.pdbqt"), "--exhaustiveness", str(_g["exh"]),
                   "--num_modes", "5", "--seed", str(_g["seed"]), "--cpu", "1"]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                return None
            scores = [float(l.split()[1]) for l in r.stdout.splitlines()
                      if l.split() and l.split()[0].isdigit() and len(l.split()) >= 4]
            if not scores:
                return None
            pose = (d / "o.pdbqt").read_text() if (d / "o.pdbqt").exists() else ""

        return smi, {
            "SMILES": smi,
            "Vina Score": scores[0],
            "Vina Poses": len(scores),
            "Molecular Formula": CalcMolFormula(m0),
            "Molecular Weight": Descriptors.MolWt(m0),
            "Rotatable Bonds": rdMolDescriptors.CalcNumRotatableBonds(m0),
            "Ligand PDBQT": pose,
        }
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ligands")
    ap.add_argument("-o", "--out", default="screen_results.json")
    ap.add_argument("--receptor", default="work/rec.pdbqt")
    ap.add_argument("--box", default="work/box.txt")
    ap.add_argument("--exhaustiveness", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("-j", "--jobs", type=int, default=mp.cpu_count())
    args = ap.parse_args()

    box = [float(x) for x in Path(args.box).read_text().split()]
    ligands = json.load(open(args.ligands))
    out = Path(args.out)
    results = json.loads(out.read_text()) if out.exists() else {}
    todo = [s for s in ligands if s not in results]
    print(f"{len(ligands):,} ligands | {len(results):,} done | {len(todo):,} to go")
    print(f"receptor {args.receptor} | exhaustiveness {args.exhaustiveness} | {args.jobs} workers",
          flush=True)

    t0, n = time.time(), 0
    with mp.Pool(args.jobs, initializer=_init,
                 initargs=(args.receptor, box, args.exhaustiveness, args.seed)) as pool:
        for res in pool.imap_unordered(_dock_one, todo, chunksize=1):
            n += 1
            if res:
                results[res[0]] = res[1]
            if n % 25 == 0 or n == len(todo):
                json.dump(results, open(out, "w"))
                rate = (time.time() - t0) / n
                print(f"  {n:,}/{len(todo):,} | {len(results):,} scored | "
                      f"{rate:.1f}s per ligand | {rate*(len(todo)-n)/3600:.1f} h left",
                      flush=True)

    json.dump(results, open(out, "w"))
    scores = sorted(r["Vina Score"] for r in results.values())
    print(f"\n{len(results):,} scored -> {out}")
    if scores:
        print(f"  best {scores[0]:.2f} | median {scores[len(scores)//2]:.2f} | worst {scores[-1]:.2f}")


if __name__ == "__main__":
    main()
