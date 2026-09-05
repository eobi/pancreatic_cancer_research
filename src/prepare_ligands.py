"""
Gate a compound library down to what is worth spending GPU time on.

Runs on the laptop. Measured throughput on an M1 Pro (10 cores): ~15,000 mol/s,
so a 1M-compound library takes about a minute and 48M takes under an hour.

    python prepare_ligands.py library.smi -o ligands.json --covalent

Input  : .smi / .csv / .txt (one SMILES per line, first whitespace field) or .json list
Output : ligands.json  (the survivors, for upload to Kaggle as a Dataset)
         ligands_rejected.csv  (every rejection with its reason, so nothing vanishes silently)
"""
import argparse, json, os, sys, csv, time, multiprocessing as mp

from rdkit import Chem, RDLogger
from rdkit.Chem import rdMolDescriptors, FilterCatalog, Descriptors

RDLogger.DisableLog("rdApp.*")

UNSTABLE = {
    "hydrazine N-N":     "[NX3;!$(N=*)]-[NX3;!$(N=*)]",
    "triazane N-N-N":    "[NX3;!$(N=*)]-[NX3;!$(N=*)]-[NX3;!$(N=*)]",
    "peroxide O-O":      "[OX2]-[OX2]",
    "epoxide":           "C1OC1",
    "aziridine":         "C1NC1",
    "azo N=N":           "[NX2]=[NX2]",
    # Nitroso and hydroxylamine only. The earlier pattern "[NX3]-[OX2H0,OX1]" also
    # matched NITRO groups, which rejected Venetoclax — nitro appears in many approved
    # drugs and is not an existence problem.
    "nitroso":           "[NX2]=[OX1]",
    "hydroxylamine":     "[NX3;!$([N+](=O)[O-]);!$(N=O)]-[OX2H1]",
    "boron":             "[B]",
    "strained alkene":   "[CX3]1=[CX3][CX4]1",
    "1,2-diketone":      "[CX3](=O)[CX3](=O)",
}

# Groups that react with each other inside one molecule. This is the check that
# would have caught the three structures sent for synthesis in 2025.
INCOMPATIBLE = [
    ("[NX3;!$(N=*)]-[NX3;!$(N=*)]", "[CX3H1](=O)[#6]", "hydrazine + aldehyde condense"),
    ("[NX3;!$(N=*)]-[NX3;!$(N=*)]", "C1OC1",           "hydrazine opens the epoxide"),
    ("[NX3;H2][CX4]",               "[CX3H1](=O)[#6]", "amine + aldehyde condense"),
]

# Catalogue rules that fire on APPROVED DRUGS. These express lead-likeness preference,
# not "can this molecule exist", so they must never gate. Derived by running BRENK+PAINS
# over a panel of marketed compounds (see work/catalogue_exemptions.json) rather than
# hand-picked one drug at a time — the hand-picked approach missed five of these.
#
#   Michael_acceptor_1           Sotorasib, Adagrasib, Osimertinib, Ibrutinib
#   triple_bond                  MRTX-1133, Erlotinib
#   Aliphatic_long_chain         Erlotinib, Gefitinib
#   nitro_group                  Venetoclax
#   Oxygen-nitrogen_single_bond  Venetoclax
#   phthalimide                  Thalidomide
DRUG_LIKE_OK = {
    "triple_bond",
    "Aliphatic_long_chain",
    "nitro_group",
    "Oxygen-nitrogen_single_bond",
    "phthalimide",
}
# Covalent warheads: only exempt for covalent programmes, since a Michael acceptor in a
# non-covalent programme is a genuine liability.
COVALENT_OK = {"Michael_acceptor_1"}

_g = {}


def _init(covalent, mw_range=(0, 1e9)):
    RDLogger.DisableLog("rdApp.*")
    _g["cov"] = covalent
    _g["mw"] = mw_range
    _g["unstable"] = {k: Chem.MolFromSmarts(v) for k, v in UNSTABLE.items()}
    _g["incompat"] = [(Chem.MolFromSmarts(a), Chem.MolFromSmarts(b), w)
                      for a, b, w in INCOMPATIBLE]
    p = FilterCatalog.FilterCatalogParams()
    p.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.BRENK)
    p.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS)
    _g["cat"] = FilterCatalog.FilterCatalog(p)


def gate(smiles):
    """None if the molecule passes, else the reason it failed."""
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return "unparseable"
    lo, hi = _g.get("mw", (0, 1e9))
    mw = Descriptors.MolWt(m)
    if not (lo <= mw <= hi):
        return f"MW outside {lo:.0f}-{hi:.0f}"
    for name, patt in _g["unstable"].items():
        if m.HasSubstructMatch(patt):
            return f"unstable group: {name}"
    for a, b, why in _g["incompat"]:
        if m.HasSubstructMatch(a) and m.HasSubstructMatch(b):
            return f"self-reactive: {why}"
    for hit in _g["cat"].GetMatches(m):
        desc = hit.GetDescription()
        if desc in DRUG_LIKE_OK:
            continue
        if _g["cov"] and desc in COVALENT_OK:
            continue
        return f"catalog: {desc}"
    if rdMolDescriptors.CalcNumAromaticRings(m) == 0:
        return "no aromatic ring"
    return None


def _work(smi):
    return smi, gate(smi)


def read_library(path):
    """Stream SMILES. A 22M-compound library will not fit in memory as a list."""
    if path.endswith(".json"):
        data = json.load(open(path))
        yield from (list(data) if isinstance(data, (list, dict)) else [])
        return
    seen = set()
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.lower().startswith(("smiles", "#")):
                continue
            smi = line.replace(",", " ").split()[0]
            if smi and smi not in seen:
                seen.add(smi)
                yield smi


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("library")
    ap.add_argument("-o", "--out", default="ligands.json")
    ap.add_argument("--covalent", action="store_true",
                    help="exempt Michael acceptors (use for KRAS G12C and other covalent targets)")
    ap.add_argument("-j", "--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--limit", type=int, help="keep only the first N survivors")
    ap.add_argument("--min-mw", type=float, default=0,
                    help="reject below this MW (KRAS G12C drugs are 560-604 Da)")
    ap.add_argument("--max-mw", type=float, default=1e9, help="reject above this MW")
    args = ap.parse_args()

    print(f"reading {args.library}")
    if args.covalent:
        print("covalent programme: Michael acceptors exempted")
    if args.min_mw or args.max_mw < 1e9:
        print(f"MW window: {args.min_mw:.0f} - {args.max_mw:.0f}")

    kept, rejected, n = [], [], 0
    rej_path = os.path.splitext(args.out)[0] + "_rejected.csv"
    t0 = time.time()
    with open(rej_path, "w", newline="") as rf:
        w = csv.writer(rf); w.writerow(["SMILES", "reason"])
        with mp.Pool(args.jobs, initializer=_init,
                     initargs=(args.covalent, (args.min_mw, args.max_mw))) as pool:
            for smi, why in pool.imap_unordered(_work, read_library(args.library),
                                                chunksize=512):
                n += 1
                if why is None:
                    kept.append(smi)
                else:
                    rejected.append(why)
                    w.writerow([smi, why])
                if n % 500_000 == 0:
                    print(f"  {n:,} screened | {len(kept):,} pass | "
                          f"{n/(time.time()-t0):,.0f} mol/s")
    smiles = range(n)   # only its length is used below

    if args.limit:
        kept = kept[:args.limit]

    json.dump(kept, open(args.out, "w"), indent=1)

    reasons = {}
    for why in rejected:
        reasons[why] = reasons.get(why, 0) + 1

    pct = 100 * len(kept) / n if n else 0
    print(f"\n{len(kept):,} pass ({pct:.2f}%), {len(rejected):,} rejected\n")
    for why, n in sorted(reasons.items(), key=lambda kv: -kv[1])[:15]:
        print(f"  {n:>8}  {why}")
    print(f"\nwrote {args.out} and {rej_path}")
    if not kept:
        print("\nNothing survived. If this is generated chemistry, the generator is the problem,")
        print("not the filter - check the aromatic-ring and unstable-group counts above.")


if __name__ == "__main__":
    main()
