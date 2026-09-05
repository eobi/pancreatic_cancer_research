"""
Score gate coverage across published campaigns from full text.

For each paper: which molecular properties are COMPUTED, and which carry an explicit
threshold that REMOVED molecules? Per the rubric (papers/SURVEY-RUBRIC.md), ambiguity counts
against gating, so this scorer is deliberately conservative and will UNDERSTATE coverage.
That bias is stated rather than corrected, because the alternative is a scorer tuned until
it produces the answer we expected.

A property counts as GATING only if a filter verb appears within a short window of the
property mention: removed, discarded, excluded, filtered out, eliminated, retained only,
cut off, threshold of, criteria of, must be, were kept if.

    python survey_score.py -o results/survey_scored.json
"""
import argparse, json, glob, os, re

PROPS = {
    "docking":      [r"docking score", r"binding affinity", r"binding energy", r"vina score",
                     r"glide score", r"docking energy"],
    "SA_score":     [r"synthetic accessibility", r"\bSA[ _-]?score", r"\bSAscore",
                     r"synthesizability", r"retrosynthetic accessibility", r"\bRAscore"],
    "PAINS":        [r"\bPAINS\b", r"pan.assay interference"],
    "toxicity":     [r"\btoxicit", r"\bAMES\b", r"mutagenic", r"carcinogen", r"hepatotox",
                     r"\bhERG\b", r"\bDILI\b", r"cardiotox", r"\bClinTox\b"],
    "QED":          [r"\bQED\b", r"drug.likeness"],
    "Lipinski":     [r"lipinski", r"rule of five", r"\bRo5\b"],
    "logP":         [r"\blogP\b", r"lipophilicit", r"partition coefficient"],
    "MW":           [r"molecular weight", r"\bMW\b"],
    "TPSA":         [r"\bTPSA\b", r"polar surface area"],
    "ADMET":        [r"\bADMET\b", r"\bADME\b", r"pharmacokinetic"],
    "solubility":   [r"solubilit", r"\blogS\b", r"aqueous solub"],
    "reactive":     [r"reactive group", r"unstable group", r"structural alert", r"\bBRENK\b",
                     r"\bMCF\b", r"medicinal chemistry filter", r"toxicophore"],
    "novelty":      [r"\bnovelty\b", r"tanimoto", r"similarity to known"],
    "selectivity":  [r"selectivit", r"off.target"],
}
GATE_VERBS = (r"(remov|discard|exclud|filter(?:ed)?\s+out|eliminat|retain(?:ed)?\s+only|"
              r"cut.?off|threshold|criteri|were\s+kept|must\s+(?:be|have)|"
              r"only\s+(?:those|compounds|molecules)|screened\s+out|rejected|"
              r"selected\s+if|passed\s+the)")
WINDOW = 260


def score(text):
    t = re.sub(r"\s+", " ", text)
    tl = t.lower()
    computed, gating, evid = [], [], {}
    for name, pats in PROPS.items():
        hits = [m for p in pats for m in re.finditer(p, tl)]
        if not hits:
            continue
        computed.append(name)
        for m in hits:
            w = tl[max(0, m.start() - WINDOW): m.end() + WINDOW]
            g = re.search(GATE_VERBS, w)
            if g:
                gating.append(name)
                evid[name] = t[max(0, m.start() - 90): m.end() + 130]
                break
    return sorted(set(computed)), sorted(set(gating)), evid


def is_eligible(text):
    """Rubric inclusion: proposes molecules, names a shortlist, is not a review."""
    tl = text.lower()
    if re.search(r"\bthis review\b|\bwe review\b|\breview article\b", tl[:6000]):
        return False, "review"
    if not re.search(r"hit compound|lead compound|top.ranked|shortlist|selected compound|"
                     r"candidate molecule|best compound|final compound", tl):
        return False, "no shortlist named"
    return True, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="results/survey_scored.json")
    a = ap.parse_args()
    meta = {r["pmcid"]: r for r in json.load(open("data/survey/all_candidates.json"))}
    rows, skipped = [], []
    for f in sorted(glob.glob("data/survey/fulltext/*.xml")):
        pm = os.path.basename(f)[:-4]
        txt = open(f, errors="ignore").read()
        txt = re.sub(r"<[^>]+>", " ", txt)
        if len(txt) < 4000:
            skipped.append((pm, "too short")); continue
        ok, why = is_eligible(txt)
        if not ok:
            skipped.append((pm, why)); continue
        comp, gat, ev = score(txt)
        if not comp:
            skipped.append((pm, "no properties found")); continue
        m = meta.get(pm, {})
        rows.append({"pmcid": pm, "year": m.get("year"), "title": (m.get("title") or "")[:80],
                     "computed": comp, "gating": gat,
                     "n_computed": len(comp), "n_gating": len(gat),
                     "coverage": round(len(gat) / len(comp), 3),
                     "stability_gate": ("reactive" in gat) or ("PAINS" in gat),
                     "evidence": ev})
    rows.sort(key=lambda r: r["coverage"])
    json.dump({"scored": rows, "skipped": skipped}, open(a.out, "w"), indent=2)

    import statistics as st
    cov = [r["coverage"] for r in rows]
    print(f"  scored {len(rows)} papers, skipped {len(skipped)}")
    print(f"  median gate coverage : {st.median(cov):.2f}")
    print(f"  mean                 : {st.mean(cov):.2f}")
    print(f"  IQR                  : {sorted(cov)[len(cov)//4]:.2f} .. {sorted(cov)[3*len(cov)//4]:.2f}")
    print(f"  papers with a stability/PAINS gate: "
          f"{sum(r['stability_gate'] for r in rows)}/{len(rows)}")
    inert = {}
    for r in rows:
        for p in r["computed"]:
            if p not in r["gating"]:
                inert[p] = inert.get(p, 0) + 1
    print("\n  most frequently computed-but-inert:")
    for p, n in sorted(inert.items(), key=lambda x: -x[1])[:8]:
        print(f"    {p:<14} {n:>3}/{len(rows)} papers")
    print(f"\n  wrote {a.out}")


if __name__ == "__main__":
    main()
