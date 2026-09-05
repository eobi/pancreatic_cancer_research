"""
Convert Kaggle docking output into the results.json shape connector.py already consumes.

    python adapt_results.py KRAS_G12C_scored.json -o P01116_new_results.json

Fills every field that RDKit can compute locally. The ADMET columns (ClinTox, AMES,
QED, logP, Lipinski, TPSA, BBB, Bioavailability, Carcinogens) come from the admet-ai
service and are left absent unless you pass --admet, which requires `pip install admet-ai`.
"AI Predicted IC50" is deliberately omitted - the current model returns a 10-wide bucket
from three descriptors and does not track measured potency.
"""
import argparse, json, os, sys

from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, Descriptors, Draw, FilterCatalog
from rdkit.Chem.rdMolDescriptors import CalcMolFormula
from rdkit.Contrib.SA_Score import sascorer

RDLogger.DisableLog("rdApp.*")

_p = FilterCatalog.FilterCatalogParams()
_p.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS)
_PAINS = FilterCatalog.FilterCatalog(_p)
_EPOXIDE = Chem.MolFromSmarts("[C]1[O][C]1")


def sa_category(v):
    return "Easy" if v < 4 else ("Moderate" if v <= 6 else "Difficult")


def score_result(dock_score, sa_score):
    """connector.score_result: 0.65 * dock + 0.2 * normalised SA."""
    norm_sa = (10 - sa_score) / 9        # normalize(-sa, -10, -1)
    return 0.65 * dock_score + 0.2 * norm_sa


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scored", help="{TARGET}_scored.json downloaded from Kaggle")
    ap.add_argument("-o", "--out", default="results.json")
    ap.add_argument("--images", metavar="DIR", help="also render molecule PNGs into DIR")
    ap.add_argument("--admet", action="store_true", help="run admet-ai locally (slow, needs the package)")
    ap.add_argument("--fda", nargs="*", default=[], help="SMILES to mark as FDA Approved")
    args = ap.parse_args()

    scored = json.load(open(args.scored))
    fda = set(args.fda)
    if args.images:
        os.makedirs(args.images, exist_ok=True)

    admet = None
    if args.admet:
        try:
            from admet_ai import ADMETModel
            admet = ADMETModel()
        except ImportError:
            sys.exit("admet-ai not installed. pip install admet-ai, or drop --admet.")

    rows = []
    for smiles, d in scored.items():
        m = Chem.MolFromSmiles(smiles)
        if m is None:
            print(f"skip unparseable: {smiles[:50]}")
            continue

        sa = sascorer.calculateScore(m)
        rec = {
            "AI Model": "None" if smiles in fda else "screened",
            "SMILES": smiles,
            "FDA Approved": smiles in fda,
            "Molecular Formula": CalcMolFormula(m),
            "Molecular Weight": Descriptors.MolWt(m),
            "DiffDock Confidence": d["DiffDock Confidence"],
            "GNINA Minimized Affinity (Binding Energy)": d["GNINA Minimized Affinity (Binding Energy)"],
            "Adjusted Dock Score": d["Adjusted Dock Score"],
            "Good Docking Quality": d["Good Docking Quality"],
            "Ligand SDF": d["Ligand SDF"],
            "Synthesis Accessibility Score": sa,
            "Synthesis Accessibility Difficulty": sa_category(sa),
            "Overall Score": score_result(d["Adjusted Dock Score"], sa),
            "Epoxide Ring Present": m.HasSubstructMatch(_EPOXIDE),
            "PAINS": _PAINS.HasMatch(m),
        }

        if args.images:
            AllChem.Compute2DCoords(m)
            path = os.path.join(args.images, f"{CalcMolFormula(m)}_{abs(hash(smiles)) % 10**8}.png")
            Draw.MolToImage(m).save(path)
            rec["Molecular Img"] = path

        if admet:
            rec.update({k: v for k, v in admet.predict(smiles=smiles).items()
                        if k in ("ClinTox", "AMES", "QED", "logP", "Lipinski", "tpsa",
                                 "BBB_Martins", "Bioavailability_Ma", "Carcinogens_Lagunin",
                                 "hydrogen_bond_acceptors", "hydrogen_bond_donors")})

        rows.append(rec)

    rows.sort(key=lambda r: r["Overall Score"], reverse=True)
    json.dump(rows, open(args.out, "w"), indent=2)

    good = sum(r["Good Docking Quality"] for r in rows)
    print(f"{len(rows)} molecules -> {args.out}")
    print(f"{good} pass the docking-quality filter")
    if not admet:
        print("\nADMET columns absent. Add them with --admet, or POST to your /tox endpoint.")


if __name__ == "__main__":
    main()
