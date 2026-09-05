"""
Download ZINC20 2D tranches into one SMILES file.

files.docking.org rate-limits: parallel requests get 503 and silently write an HTML
error page into your .smi. This fetches serially, verifies each file is really SMILES,
retries, and skips what it already has, so it can be re-run after an interruption.

    python fetch_zinc.py --tranches IE IF JE JF -o library.smi

Tranche codes are {MW}{logP}{...}. For KRAS-scale drugs (Sotorasib 561, Adagrasib 604,
BI-0474 588) the useful mass bins are H..K. Check what you get with --profile.
"""
import argparse, re, sys, time, urllib.request, urllib.error
from pathlib import Path

BASE = "https://files.docking.org/2D"

# files.docking.org 403s urllib's default User-Agent. Identify properly.
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " \
     "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def _open(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout)


def listing(tranche, timeout=60):
    """Filenames inside one 2-letter tranche directory."""
    try:
        with _open(f"{BASE}/{tranche}/", timeout) as r:
            html = r.read().decode("utf-8", "replace")
    except Exception as e:
        print(f"  {tranche}: listing failed ({e})")
        return []
    return sorted(set(re.findall(r"([A-Z]{4}\.smi)", html)))


def grab(url, dest, tries=4, pause=6.0):
    """Fetch one .smi, rejecting HTML error pages. Returns line count or 0."""
    for attempt in range(tries):
        try:
            with _open(url, 120) as r:
                data = r.read()
        except Exception:
            time.sleep(pause * (attempt + 1))
            continue
        head = data[:200].lstrip().lower()
        if head.startswith(b"<!doctype") or head.startswith(b"<html"):
            time.sleep(pause * (attempt + 1))     # rate-limited, back off
            continue
        dest.write_bytes(data)
        return data.count(b"\n")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tranches", nargs="+", default=["IE", "IF", "JE", "JF"])
    ap.add_argument("-o", "--out", default="library.smi")
    ap.add_argument("--cache", default="zinc_cache")
    ap.add_argument("--max-files", type=int, default=12, help="per tranche")
    ap.add_argument("--profile", action="store_true", help="report MW/logP of the result")
    args = ap.parse_args()

    cache = Path(args.cache); cache.mkdir(parents=True, exist_ok=True)
    total = 0

    for t in args.tranches:
        files = listing(t)
        if not files:
            continue
        files = files[:args.max_files]
        print(f"{t}: {len(files)} files")
        for fn in files:
            dest = cache / fn
            if dest.exists() and dest.stat().st_size > 100:
                continue
            n = grab(f"{BASE}/{t}/{fn}", dest)
            print(f"    {fn:<12} {n if n else 'FAILED':>8}")
            total += n
            time.sleep(1.0)               # be a good citizen

    # merge, dedupe, strip headers
    seen, out = set(), Path(args.out)
    with out.open("w") as fh:
        for p in sorted(cache.glob("*.smi")):
            for i, line in enumerate(p.read_text(errors="replace").splitlines()):
                if i == 0 or not line.strip():
                    continue
                parts = line.split()
                smi = parts[0] if parts else ""
                zid = parts[1] if len(parts) > 1 else ""
                if smi and smi not in seen:
                    seen.add(smi)
                    # keep the id: without it the screen output has no vendor handle
                    fh.write(f"{smi}\t{zid}\n" if zid else smi + "\n")
    print(f"\nwrote {out} — {len(seen)} unique SMILES")

    if args.profile:
        from rdkit import Chem, RDLogger
        from rdkit.Chem import Descriptors, Crippen
        RDLogger.DisableLog("rdApp.*")
        import statistics as st, random
        sample = random.Random(0).sample(sorted(seen), min(3000, len(seen)))
        mw, lp = [], []
        for s in sample:
            m = Chem.MolFromSmiles(s)
            if m:
                mw.append(Descriptors.MolWt(m)); lp.append(Crippen.MolLogP(m))
        if mw:
            mw.sort(); lp.sort()
            print(f"\nprofile over {len(mw)} sampled:")
            print(f"  MW    median {st.median(mw):6.0f}   10-90%  {mw[len(mw)//10]:.0f} - {mw[9*len(mw)//10]:.0f}")
            print(f"  logP  median {st.median(lp):6.1f}   10-90%  {lp[len(lp)//10]:.1f} - {lp[9*len(lp)//10]:.1f}")
            print("  reference: Sotorasib MW 561 / Adagrasib 604 / BI-0474 588")


if __name__ == "__main__":
    main()
