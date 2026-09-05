"""
Rescore docked poses with an independent scoring function (consensus check).

Vina and Vinardo are separately parameterised empirical functions. If a compound's
rank is real, both should like it. If a rank is an artefact of Vina's particular
weighting, Vinardo will disagree. This costs seconds per compound because the pose
is already known — it is a single-point score, not a re-dock.

    python src/rescore.py data/shortlists/top200_g12v.json \
        --receptor targets/g12v/rec.pdbqt --box targets/g12v/box.txt \
        --controls targets/g12v/controls.json -o results/rescore_g12v.json

Reports Spearman correlation between the two functions and flags compounds where they
disagree strongly — those are the ones not to trust.
"""
import argparse, json, subprocess, tempfile, multiprocessing as mp
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
RDLogger.DisableLog("rdApp.*")

HERE = Path(__file__).resolve().parent


def _find_vina():
    for c in (HERE / "bin" / "vina", HERE.parent / "bin" / "vina"):
        if c.exists():
            return c
    return HERE.parent / "bin" / "vina"


_g = {}


def _init(receptor, box, scoring, seed):
    RDLogger.DisableLog("rdApp.*")
    _g.update(receptor=receptor, box=box, scoring=scoring, seed=seed, vina=str(_find_vina()))


def _score(smi):
    """Dock with the chosen function. Returns best score or None."""
    from meeko import MoleculePreparation, PDBQTWriterLegacy
    try:
        m0 = Chem.MolFromSmiles(smi)
        if m0 is None:
            return smi, None
        m = Chem.AddHs(m0)
        p = AllChem.ETKDGv3(); p.randomSeed = _g["seed"]
        if AllChem.EmbedMolecule(m, p) != 0:
            return smi, None
        AllChem.MMFFOptimizeMolecule(m, maxIters=500)
        setups = MoleculePreparation().prepare(m)
        if not setups:
            return smi, None
        pdbqt, ok, _ = PDBQTWriterLegacy.write_string(setups[0])
        if not ok:
            return smi, None
        b = _g["box"]
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); (d / "l.pdbqt").write_text(pdbqt)
            cmd = [_g["vina"], "--receptor", _g["receptor"], "--ligand", str(d / "l.pdbqt"),
                   "--center_x", f"{b[0]}", "--center_y", f"{b[1]}", "--center_z", f"{b[2]}",
                   "--size_x", f"{b[3]}", "--size_y", f"{b[4]}", "--size_z", f"{b[5]}",
                   "--out", str(d / "o.pdbqt"), "--scoring", _g["scoring"],
                   "--exhaustiveness", "8", "--num_modes", "3",
                   "--seed", str(_g["seed"]), "--cpu", "1"]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                return smi, None
            for line in r.stdout.splitlines():
                p2 = line.split()
                if len(p2) >= 4 and p2[0] == "1":
                    return smi, float(p2[1])
        return smi, None
    except Exception:
        return smi, None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("shortlist")
    ap.add_argument("--receptor", required=True)
    ap.add_argument("--box", required=True)
    ap.add_argument("--controls")
    ap.add_argument("--scoring", default="vinardo")
    ap.add_argument("-o", "--out", default="results/rescore.json")
    ap.add_argument("-j", "--jobs", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    box = [float(x) for x in Path(args.box).read_text().split()]
    rows = json.loads(Path(args.shortlist).read_text())
    smiles = [r["SMILES"] for r in rows]
    controls = json.loads(Path(args.controls).read_text()) if args.controls else {}

    todo = smiles + list(controls.values())
    print(f"{len(rows)} shortlist + {len(controls)} controls, scoring={args.scoring}, {args.jobs} workers\n")

    with mp.Pool(args.jobs, initializer=_init,
                 initargs=(args.receptor, box, args.scoring, args.seed)) as pool:
        res = dict(pool.map(_score, todo, chunksize=1))

    vina = {r["SMILES"]: r["Vina Score"] for r in rows}
    paired = [(vina[s], res[s], s) for s in smiles if res.get(s) is not None]
    print(f"rescored {len(paired)}/{len(smiles)}")

    # rank agreement
    try:
        from scipy.stats import spearmanr
        rho, pval = spearmanr([p[0] for p in paired], [p[1] for p in paired])
        print(f"\nSpearman rank correlation vina vs {args.scoring}: rho={rho:.3f} (p={pval:.2g})")
    except Exception:
        rho = None

    print(f"\ncontrols under {args.scoring}:")
    for n, s in controls.items():
        v = res.get(s)
        print(f"  {n:<12} {v if v is None else f'{v:>7.2f}'}")

    paired.sort(key=lambda t: t[1])
    print(f"\ntop 10 by {args.scoring}:")
    print(f"{'rank':>5} {'vina':>8} {args.scoring:>9}  SMILES")
    for i, (v, w, s) in enumerate(paired[:10], 1):
        print(f"{i:>5} {v:>8.2f} {w:>9.2f}  {s[:46]}")

    out = [{"SMILES": s, "vina": v, args.scoring: w} for v, w, s in paired]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump({"scoring": args.scoring, "spearman": rho,
               "controls": {n: res.get(s) for n, s in controls.items()},
               "compounds": out}, open(args.out, "w"), indent=2)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
