"""
Structural audit of the cross-docked KRAS shortlist.

Answers one question: how many of the AI-generated molecules would survive the
filters a pharma discovery group runs before a structure reaches a chemist.

Requires: rdkit, openpyxl   ->   pip install rdkit openpyxl
Usage:    python audit_molecules.py source-cross_docked_kras.xlsx
"""
import sys, collections
import openpyxl
from rdkit import Chem, RDLogger
from rdkit.Chem import rdMolDescriptors, FilterCatalog

RDLogger.DisableLog("rdApp.*")

VARIANTS = ["KRAS_G12C", "KRAS_G12D", "KRAS_G12V", "KRAS_G13D"]

# Groups that are unstable, self-reactive, or genotoxic. A molecule carrying one
# of these is not a candidate regardless of how well it docks.
UNSTABLE = {
    "hydrazine N-N":      "[NX3;!$(N=*)]-[NX3;!$(N=*)]",
    "triazane N-N-N":     "[NX3;!$(N=*)]-[NX3;!$(N=*)]-[NX3;!$(N=*)]",
    "peroxide O-O":       "[OX2]-[OX2]",
    "epoxide":            "C1OC1",
    "aziridine":          "C1NC1",
    "azo N=N":            "[NX2]=[NX2]",
    "N-oxide / nitroso":  "[NX3]-[OX2H0,OX1]",
    "boron":              "[B]",
    "strained alkene":    "[CX3]1=[CX3][CX4]1",
    "1,2-diketone":       "[CX3](=O)[CX3](=O)",
}

# Pairs of groups that cannot coexist in one molecule: they react with each
# other. This is the check that would have stopped Hits 13, 41 and 73.
INCOMPATIBLE = [
    ("hydrazine N-N", "aldehyde",  "[NX3;!$(N=*)]-[NX3;!$(N=*)]", "[CX3H1](=O)[#6]",
     "hydrazine and aldehyde condense to a hydrazone"),
    ("hydrazine N-N", "epoxide",   "[NX3;!$(N=*)]-[NX3;!$(N=*)]", "C1OC1",
     "hydrazine opens the epoxide"),
    ("primary amine", "aldehyde",  "[NX3;H2][CX4]",               "[CX3H1](=O)[#6]",
     "amine and aldehyde condense to an imine"),
]


def load(path):
    rows = list(openpyxl.load_workbook(path, data_only=True).active.iter_rows(values_only=True))
    hdr = list(rows[0])
    return [dict(zip(hdr, r)) for r in rows[1:] if r[0] is not None]


def audit(path):
    data = load(path)
    gen = [d for d in data if d["FDA Approved"] not in (True, "True")]
    ref = [d for d in data if d["FDA Approved"] in (True, "True")]

    unstable = {k: Chem.MolFromSmarts(v) for k, v in UNSTABLE.items()}
    params = FilterCatalog.FilterCatalogParams()
    params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.BRENK)
    params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS)
    catalog = FilterCatalog.FilterCatalog(params)

    mol = lambda d: Chem.MolFromSmiles(d["SMILES"])

    print(f"{len(gen)} generated molecules, {len(ref)} reference drugs\n")

    # --- profile -----------------------------------------------------------
    for label, rows in (("generated", gen), ("reference drugs", ref)):
        ms = [mol(d) for d in rows]
        ms = [m for m in ms if m is not None]
        arom = sum(1 for m in ms if rdMolDescriptors.CalcNumAromaticRings(m) > 0)
        flagged = sum(1 for m in ms if any(m.HasSubstructMatch(p) for p in unstable.values()))
        print(f"{label}: {arom}/{len(ms)} have an aromatic ring | "
              f"{flagged}/{len(ms)} carry an unstable or genotoxic group | "
              f"mean rings {sum(rdMolDescriptors.CalcNumRings(m) for m in ms)/len(ms):.1f}")

    census = collections.Counter()
    for d in gen:
        for k, p in unstable.items():
            if mol(d).HasSubstructMatch(p):
                census[k] += 1
    print("\nalert census across generated set:")
    for k, v in census.most_common():
        print(f"  {k:<22} {v}")

    # --- self-reactive molecules -------------------------------------------
    print("\nmolecules whose own groups react with each other:")
    for d in gen:
        m = mol(d)
        hits = [why for a, b, sa, sb, why in INCOMPATIBLE
                if m.HasSubstructMatch(Chem.MolFromSmarts(sa))
                and m.HasSubstructMatch(Chem.MolFromSmarts(sb))]
        if hits:
            print(f"  {d['Hit Molecule']:<38} {'; '.join(hits)}")

    # --- gate funnel --------------------------------------------------------
    gates = [
        ("Parses and sanitizes",
         lambda d: mol(d) is not None),
        ("No unstable or genotoxic group",
         lambda d: not any(mol(d).HasSubstructMatch(p) for p in unstable.values())),
        ("Clears PAINS and BRENK",
         lambda d: not catalog.HasMatch(mol(d))),
        ("Has a drug-like ring system",
         lambda d: rdMolDescriptors.CalcNumAromaticRings(mol(d)) > 0),
        ("Synthesis accessibility < 5",
         lambda d: float(d["Synthesis Accessibility Score"]) < 5),
        ("Good docking on all four variants",
         lambda d: all(d[f"Good Docking Quality ({v})"] in (True, "True") for v in VARIANTS)),
    ]

    print(f"\ngate funnel:\n{len(gen):>5}  generated")
    survivors, prev = list(gen), len(gen)
    for name, fn in gates:
        survivors = [d for d in survivors if fn(d)]
        print(f"{len(survivors):>5}  {name}  (-{prev - len(survivors)})")
        prev = len(survivors)

    return survivors


if __name__ == "__main__":
    audit(sys.argv[1] if len(sys.argv) > 1 else "source-cross_docked_kras.xlsx")
