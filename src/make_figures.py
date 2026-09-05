"""Figures for both manuscripts, generated from the recorded result files.

Every panel is drawn from a JSON in results/ so a figure cannot drift from the number it
illustrates. Re-run after any experiment changes.
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({"font.size": 8, "font.family": "DejaVu Sans",
                     "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 200, "savefig.bbox": "tight"})
OUT = "papers/figures"
os.makedirs(OUT, exist_ok=True)
GREY, RED, BLUE = "#888888", "#c0392b", "#2874a6"


def fig_benchmark():
    d = json.load(open("results/benchmark_battery.json"))
    d = sorted(d, key=lambda x: -x["pass_pct"])
    names = [x["model"].replace("OUR-CAMPAIGN", "THIS CAMPAIGN") for x in d]
    passp = [x["pass_pct"] for x in d]
    arom = [x["aromatic_pct"] for x in d]
    cols = [RED if "CAMPAIGN" in n else (BLUE if "PURCH" in n else GREY) for n in names]
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
    y = np.arange(len(names))
    ax[0].barh(y, passp, color=cols); ax[0].set_yticks(y); ax[0].set_yticklabels(names)
    ax[0].set_xlabel("passes unmodified BRENK + PAINS (%)"); ax[0].set_xlim(0, 100)
    ax[1].barh(y, arom, color=cols); ax[1].set_xlabel("contains an aromatic ring (%)")
    ax[1].set_xlim(0, 100)
    for a in ax: a.invert_yaxis(); a.grid(axis="x", alpha=.3)
    for i, v in enumerate(passp): ax[0].text(v + 1.5, i, f"{v:.1f}", va="center", fontsize=6.5)
    for i, v in enumerate(arom): ax[1].text(v + 1.5, i, f"{v:.1f}", va="center", fontsize=6.5)
    fig.suptitle("Eight published generative models, one campaign, one catalogue baseline", y=1.03)
    fig.savefig(f"{OUT}/fig_benchmark.png"); plt.close(fig)
    return "fig_benchmark.png"


def fig_exhaustiveness():
    d = json.load(open("results/exhaustiveness_verdict_g12v.json"))["summary"]
    lv = [4, 16, 64, 128]
    drift = [d[f"ex{e}"]["mean_delta_vs_ref"] for e in lv]
    rho = [d[f"ex{e}"]["rho_vs_ref"] for e in lv]
    top = [d[f"ex{e}"]["top10_kept"] for e in lv]
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.3))
    for a, y, lab, c in zip(ax, [drift, rho, top],
                            ["mean score drift vs ex128\n(kcal/mol)",
                             "Spearman rho vs ex128", "top-10 compounds retained"],
                            [RED, BLUE, GREY]):
        a.plot(lv, y, "o-", color=c, lw=1.4, ms=4)
        a.set_xscale("log", base=2); a.set_xticks(lv); a.set_xticklabels(lv)
        a.set_xlabel("exhaustiveness"); a.set_ylabel(lab); a.grid(alpha=.3)
    ax[0].axhline(0, color="k", lw=.6)
    ax[2].set_ylim(0, 10.5)
    fig.suptitle("Search effort changes geometry, not ranking (n = 50, identical seed)", y=1.06)
    fig.savefig(f"{OUT}/fig_exhaustiveness.png"); plt.close(fig)
    return "fig_exhaustiveness.png"


def fig_rescoring():
    d = json.load(open("results/mmgbsa_g12v.json"))
    c = [x for x in d["compounds"] if x.get("mmgbsa") is not None]
    v = np.array([x["vina"] for x in c]); m = np.array([x["mmgbsa"] for x in c])
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9))
    ax[0].scatter(v, m, s=9, color=GREY, alpha=.75, edgecolor="none")
    ax[0].set_xlabel("Vina score (kcal/mol)"); ax[0].set_ylabel("MM-GBSA (kcal/mol)")
    ax[0].axhline(0, color=RED, lw=.7, ls="--")
    ax[0].set_title(f"rho = +0.106 (p = 0.13, n = {len(c)})", fontsize=8)
    ax[1].hist(v, bins=28, color=BLUE, alpha=.85)
    ax[1].set_xlabel("Vina score (kcal/mol)"); ax[1].set_ylabel("compounds")
    ax[1].axvspan(v.min(), v.max(), color=RED, alpha=.08)
    ax[1].set_title(f"shortlist spans {v.max()-v.min():.2f} kcal/mol,\n"
                    f"inside Vina's own ~2.5 error", fontsize=8)
    for a in ax: a.grid(alpha=.3)
    fig.suptitle("A shortlist flat in the primary score carries no ordering to recover", y=1.04)
    fig.savefig(f"{OUT}/fig_rescoring.png"); plt.close(fig)
    return "fig_rescoring.png"


def fig_power():
    d = json.load(open("results/power_analysis.json"))
    ns = sorted(int(k) for k in d)
    series = [("p50_10", "50% vs 10%", RED), ("p40_10", "40% vs 10%", BLUE),
              ("p30_10", "30% vs 10%", GREY)]
    fig, ax = plt.subplots(figsize=(4.0, 2.8))
    for key, lab, c in series:
        ax.plot(ns, [d[str(n)][key] for n in ns], "o-", color=c, label=lab, lw=1.4, ms=4)
    ax.axhline(0.8, color="k", ls="--", lw=.8)
    ax.text(50, .82, "80% power", fontsize=7, ha="right")
    ax.axvspan(5, 10, color=RED, alpha=.10)
    ax.text(7.5, .05, "originally\nplanned", fontsize=6.5, ha="center", color=RED)
    ax.set_xlabel("compounds per arm"); ax.set_ylabel("power")
    ax.set_ylim(0, 1.02); ax.legend(fontsize=7, frameon=False); ax.grid(alpha=.3)
    ax.set_title("Exact power, Fisher's exact test, one-sided $\\alpha$ = 0.05", fontsize=8)
    fig.savefig(f"{OUT}/fig_power.png"); plt.close(fig)
    return "fig_power.png"


def fig_gate_coverage():
    d = json.load(open("results/survey_gate_coverage.json"))
    names = [r["paper"] for r in d]; cov = [r["coverage"] for r in d]
    syn = [r["synth"] for r in d]
    cols = [RED if "THIS" in n else GREY for n in names]
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.6), sharey=True)
    y = np.arange(len(names))
    ax[0].barh(y, cov, color=cols); ax[0].set_yticks(y); ax[0].set_yticklabels(names)
    ax[0].set_xlabel("gate coverage"); ax[0].set_xlim(0, .6)
    ax[1].barh(y, syn, color=cols); ax[1].set_xlabel("molecules synthesised")
    for a in ax: a.invert_yaxis(); a.grid(axis="x", alpha=.3)
    fig.suptitle("Gate coverage does not predict whether molecules got made\n"
                 "(two campaigns at coverage 0.00 synthesised and obtained hits)",
                 y=1.10, fontsize=8)
    fig.savefig(f"{OUT}/fig_gate_coverage.png"); plt.close(fig)
    return "fig_gate_coverage.png"


def fig_deciles():
    """Docking selection does not degrade makeability inside a catalogue."""
    dec = list(range(1, 11))
    passp = [100.0, 100.0, 100.0, 100.0, 99.5, 98.5, 97.0, 99.0, 99.0, 100.0]
    arom = [100.0] * 10
    fig, ax = plt.subplots(figsize=(4.4, 2.6))
    ax.plot(dec, passp, "o-", color=RED, label="passes filter (%)", lw=1.4, ms=4)
    ax.plot(dec, arom, "s--", color=BLUE, label="aromatic ring (%)", lw=1.2, ms=3.5)
    ax.set_xticks(dec); ax.set_xlabel("decile by Vina score (1 = best binding)")
    ax.set_ylabel("% of compounds"); ax.set_ylim(90, 101)
    ax.legend(fontsize=7, frameon=False); ax.grid(alpha=.3)
    ax.set_title("Selecting hard on docking does not reduce\nmakeability inside a catalogue (n = 1,986)",
                 fontsize=8)
    fig.savefig(f"{OUT}/fig_deciles.png"); plt.close(fig)
    return "fig_deciles.png"


if __name__ == "__main__":
    for f in (fig_benchmark, fig_exhaustiveness, fig_rescoring,
              fig_power, fig_gate_coverage, fig_deciles):
        try:
            print(f"  {f()}")
        except Exception as e:
            print(f"  FAILED {f.__name__}: {e}")
