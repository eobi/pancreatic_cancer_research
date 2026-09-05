"""
Pick which gated compounds are worth docking.

Docking is the expensive tier (~22 s/ligand even parallelised), so 500k survivors
cannot all be scored. This enriches for the chemotype that actually binds the target
instead of sampling at random.

    python select_ligands.py ligands.json -n 3000 -o selected.json

Ranks by maximum Tanimoto similarity (Morgan r2, 2048 bit) to the reference binders
in work/controls.json, then keeps a diverse subset so the shortlist is not fifty
near-duplicates of one scaffold.
"""
import argparse, json, multiprocessing as mp
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
RDLogger.DisableLog("rdApp.*")

_g = {}


def _init(ref_smiles):
    RDLogger.DisableLog("rdApp.*")
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    _g["gen"] = gen
    _g["refs"] = [gen.GetFingerprint(Chem.MolFromSmiles(s)) for s in ref_smiles]


def _score(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return smi, 0.0, None
    fp = _g["gen"].GetFingerprint(m)
    return smi, max(DataStructs.BulkTanimotoSimilarity(fp, _g["refs"])), fp


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ligands")
    ap.add_argument("-n", "--number", type=int, default=3000)
    ap.add_argument("-o", "--out", default="selected.json")
    ap.add_argument("--controls", default="work/controls.json")
    ap.add_argument("--pool", type=int, default=30000,
                    help="rank this many by similarity, then diversify down to -n")
    ap.add_argument("--diversity", type=float, default=0.85,
                    help="reject a candidate more similar than this to one already kept")
    ap.add_argument("-j", "--jobs", type=int, default=mp.cpu_count())
    args = ap.parse_args()

    ligands = json.load(open(args.ligands))
    refs = list(json.load(open(args.controls)).values())
    print(f"{len(ligands):,} gated compounds, {len(refs)} reference binders")

    with mp.Pool(args.jobs, initializer=_init, initargs=(refs,)) as pool:
        scored = pool.map(_score, ligands, chunksize=512)

    scored = [(s, sim, fp) for s, sim, fp in scored if fp is not None]
    scored.sort(key=lambda t: -t[1])
    print(f"similarity to references: best {scored[0][1]:.3f}, "
          f"median {scored[len(scored)//2][1]:.3f}")

    # diversify: walk the ranked pool, keep anything not too close to a current keeper
    kept, kept_fps = [], []
    for smi, sim, fp in scored[:args.pool]:
        if kept_fps and max(DataStructs.BulkTanimotoSimilarity(fp, kept_fps)) > args.diversity:
            continue
        kept.append(smi); kept_fps.append(fp)
        if len(kept) >= args.number:
            break

    json.dump(kept, open(args.out, "w"), indent=1)
    print(f"\nselected {len(kept):,} -> {args.out}")
    print(f"  similarity window: {scored[0][1]:.3f} down to "
          f"{min(s for x, s, f in scored[:args.pool] if x in set(kept)):.3f}")
    print(f"  pairwise similarity capped at {args.diversity}")


if __name__ == "__main__":
    main()
