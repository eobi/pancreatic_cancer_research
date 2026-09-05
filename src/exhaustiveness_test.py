"""
Does the screening exhaustiveness change the answer?

Every screen in this project ran at `run_screen.py`'s default **exhaustiveness 4**, while
every method-validation gate ran at **16**. The gate therefore never covered the
configuration the screens actually used — the same shape of defect as an MM-GBSA control
gate that counted results instead of ranking them.

That gap became urgent when G12R showed how decisive this parameter can be on this target
family: the same ligand in the same receptor gave

    exhaustiveness  16   ->  cognate redock 7.19 A   (FAIL)
    exhaustiveness 128   ->  cognate redock 0.99 A   (PASS)

If sampling is that decisive, screens run at 4 may be under-sampling systematically, and
the two headline negatives -- G12D nothing across 19,639, G12V 2 past cognate across
9,913 -- would be facts about the search rather than about the library.

This script re-docks a stratified sample of an existing shortlist at several
exhaustiveness values and asks three questions:

  1. Does the SCORE move with exhaustiveness, and in which direction?
  2. Does the RANKING move? (Spearman of each setting against the highest.)
  3. Would the SELECTION change -- who makes a top-N cut?

Question 3 is the one that matters. Scores drifting uniformly is harmless; a shortlist
that reorders means the screens must be redone.

    python exhaustiveness_test.py data/shortlists/top200_g12v.json \
        --receptor targets/g12v/rec.pdbqt --box targets/g12v/box.txt \
        -n 50 --levels 4,16,64,128 -o results/exhaustiveness_g12v.json
"""
import argparse, json, subprocess, sys, tempfile, time
import multiprocessing as mp
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from meeko import MoleculePreparation, PDBQTWriterLegacy
RDLogger.DisableLog("rdApp.*")

_g = {}


def _init(receptor, box, seed, vina):
    _g.update(receptor=receptor, box=box, seed=seed, vina=vina)


def _dock(task):
    """One ligand at one exhaustiveness. Same embedding seed across levels, so any
    difference is the SEARCH and not the starting conformer."""
    smi, exh = task
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
    pdbqt, ok, _ = PDBQTWriterLegacy.write_string(setups[0])
    if not ok:
        return None

    b = _g["box"]
    with tempfile.TemporaryDirectory() as d:
        d = Path(d); (d / "l.pdbqt").write_text(pdbqt)
        cmd = [_g["vina"], "--receptor", _g["receptor"], "--ligand", str(d / "l.pdbqt"),
               "--center_x", f"{b[0]}", "--center_y", f"{b[1]}", "--center_z", f"{b[2]}",
               "--size_x", f"{b[3]}", "--size_y", f"{b[4]}", "--size_z", f"{b[5]}",
               "--out", str(d / "o.pdbqt"), "--exhaustiveness", str(exh),
               "--num_modes", "5", "--seed", str(_g["seed"]), "--cpu", "1"]
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            return None
        scores = [float(l.split()[1]) for l in r.stdout.splitlines()
                  if l.split() and l.split()[0].isdigit() and len(l.split()) >= 4]
        if not scores:
            return None
    return {"SMILES": smi, "exh": exh, "score": scores[0], "secs": round(time.time() - t0, 1)}


def stratified(rows, n):
    """Sample across the whole score range, not just the top. If under-sampling hurts
    weak binders more than strong ones the effect is only visible with the full range."""
    rows = sorted(rows, key=lambda r: r["Vina Score"])
    if n >= len(rows):
        return rows
    step = len(rows) / n
    return [rows[int(i * step)] for i in range(n)]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("shortlist")
    ap.add_argument("--receptor", required=True)
    ap.add_argument("--box", required=True)
    ap.add_argument("-n", type=int, default=50)
    ap.add_argument("--levels", default="4,16,64,128")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).parent))
    from dock_site import _find_vina
    vina = _find_vina()

    rows = json.loads(Path(args.shortlist).read_text())
    if isinstance(rows, dict):
        rows = list(rows.values())
    sample = stratified(rows, args.n)
    levels = [int(x) for x in args.levels.split(",")]
    box = [float(x) for x in Path(args.box).read_text().split()]

    print(f"{len(sample)} compounds x {len(levels)} levels = "
          f"{len(sample)*len(levels)} docks, {args.workers} workers")
    print(f"score range of sample: {sample[0]['Vina Score']:.2f} .. "
          f"{sample[-1]['Vina Score']:.2f} kcal/mol\n")

    tasks = [(r["SMILES"], e) for e in levels for r in sample]
    out, t0 = [], time.time()
    with mp.get_context("spawn").Pool(
            args.workers, initializer=_init,
            initargs=(args.receptor, box, args.seed, vina)) as pool:
        for i, res in enumerate(pool.imap_unordered(_dock, tasks), 1):
            if res:
                out.append(res)
            if i % 25 == 0 or i == len(tasks):
                rate = (time.time() - t0) / i
                Path(args.out).parent.mkdir(parents=True, exist_ok=True)
                json.dump(out, open(args.out, "w"), indent=2)
                print(f"  {i}/{len(tasks)} | {rate:.1f}s each | "
                      f"{rate*(len(tasks)-i)/60:.0f} min left", flush=True)

    json.dump(out, open(args.out, "w"), indent=2)
    print(f"\nwrote {args.out}")
    analyse(out, levels)


def analyse(out, levels):
    from scipy.stats import spearmanr
    import statistics as st
    by = {e: {r["SMILES"]: r["score"] for r in out if r["exh"] == e} for e in levels}
    ref = max(levels)
    common = set.intersection(*[set(v) for v in by.values()]) if by else set()
    print(f"\n{len(common)} compounds scored at every level. Reference = ex{ref}.\n")
    print(f"  {'level':>6} {'median':>9} {'mean d vs ref':>15} {'rho vs ref':>12} "
          f"{'top10 kept':>11}")
    ref_rank = sorted(common, key=lambda s: by[ref][s])
    ref_top = set(ref_rank[:10])
    for e in levels:
        vals = [by[e][s] for s in common]
        d = [by[e][s] - by[ref][s] for s in common]
        rho = spearmanr([by[e][s] for s in common], [by[ref][s] for s in common])[0]
        top = set(sorted(common, key=lambda s: by[e][s])[:10])
        print(f"  ex{e:<4} {st.median(vals):>9.2f} {st.mean(d):>+15.2f} "
              f"{rho:>12.3f} {len(top & ref_top):>10}/10")
    print("\n  mean d vs ref > 0 means that level scores WEAKER than the reference,")
    print("  i.e. it is missing the better poses the deeper search finds.")


if __name__ == "__main__":
    main()
