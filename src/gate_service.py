"""
Chemical reality gate, as a service.

Phase 4 of the pipeline, exposed over HTTP so it can be used on its own — by a chemist
with one structure, by a colleague's script, or by the orchestrator running a full target.
It needs nothing but RDKit: no receptor, no library, no GPU.

    uvicorn gate_service:app --host 0.0.0.0 --port 8090

    curl -X POST localhost:8090/check -H 'Content-Type: application/json' \
      -d '{"smiles":["NN(N1)C2CCC[C@H1]2CCCC3OC31CC=O"],"covalent":true}'

Why this one first: it answers "can this molecule exist" before anyone spends a chemist,
a GPU, or a year on it. In 2025 three structures went to synthesis carrying a triazane,
an epoxide and an aldehyde in one molecule; all three fail this check in milliseconds.

The service validates itself on startup and at /validate — it must pass known drugs and
reject the known-impossible molecules, or it reports itself unhealthy. A filter that has
not been checked against a known answer is the thing that caused the original problem.
"""
from typing import List, Optional
import sys
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent))
import prepare_ligands as gate_mod

app = FastAPI(
    title="Chemical reality gate",
    description="Can this molecule exist? Stability, self-reactivity and structural alerts.",
    version="1.0",
)

# --- the molecules this service is checked against -------------------------
# Approved / clinical compounds that MUST pass, and 2025 structures that MUST fail.
KNOWN_GOOD = {
    "Sotorasib": "CC(C)C1=NC=CC(C)=C1N1C(=O)N=C(N2CCN(C[C@@H]2C)C(=O)C=C)C2=CC(F)=C(N=C12)C1=C(O)C=CC=C1F",
    "Adagrasib": "[H][C@@]1(COC2=NC3=C(CCN(C3)C3=CC=CC4=C3C(Cl)=CC=C4)C(=N2)N2CCN(C(=O)C(F)=C)[C@@]([H])(CC#N)C2)CCCN1C",
    "MRTX-1133": "C#Cc1c(ccc2c1c(cc(c2)O)c3c(c4c(cn3)c(nc(n4)OC[C@@]56CCCN5C[C@@H](C6)F)N7C[C@H]8CC[C@@H](C7)N8)F)F",
}
KNOWN_BAD = {
    "2025 Hit 13": "NN(N1)C2CCC[C@H1]2CCCC3OC31CC=O",
    "2025 Hit 41": "NN(N)C1CCC[C@H1]1CCCC2OC2C=O",
    "2025 Hit 73": "NN(N)C1CCC[C@H1]1CCCC2OC2CN(OCC3CCCCCCCC=4)CC=43",
}

_ready = {"covalent": False, "noncovalent": False}


def _ensure(covalent: bool):
    """Initialise the gate's SMARTS and catalogues for this mode."""
    key = "covalent" if covalent else "noncovalent"
    if not _ready[key]:
        gate_mod._init(covalent)
        _ready[key] = True
    elif gate_mod._g.get("cov") != covalent:
        gate_mod._init(covalent)


class CheckRequest(BaseModel):
    smiles: List[str] = Field(..., description="Structures to check", max_length=10000)
    covalent: bool = Field(
        True,
        description="Exempt Michael acceptors. Required for covalent programmes such as "
                    "KRAS G12C — BRENK flags acrylamide, which rejects Sotorasib and "
                    "Adagrasib, whose warhead IS the mechanism.",
    )
    min_mw: float = 0
    max_mw: float = 1e9


class Verdict(BaseModel):
    smiles: str
    passes: bool
    reason: Optional[str] = None


@app.get("/health")
def health():
    """Is the service up, and does it still pass its own validation?"""
    v = validate()
    return {"status": "ok" if v["discriminates"] else "unhealthy", **v}


@app.post("/check", response_model=List[Verdict])
def check(req: CheckRequest):
    """Verdict per structure. `reason` names the group that failed."""
    _ensure(req.covalent)
    gate_mod._g["mw"] = (req.min_mw, req.max_mw)
    out = []
    for smi in req.smiles:
        why = gate_mod.gate(smi)
        out.append(Verdict(smiles=smi, passes=why is None, reason=why))
    return out


@app.get("/validate")
def validate():
    """Prove the gate still separates known-good from known-impossible.

    Run this before trusting any result. It is the check the 2025 pipeline never had.
    """
    _ensure(True)
    gate_mod._g["mw"] = (0, 1e9)
    good = {n: gate_mod.gate(s) for n, s in KNOWN_GOOD.items()}
    bad = {n: gate_mod.gate(s) for n, s in KNOWN_BAD.items()}
    good_ok = all(v is None for v in good.values())
    bad_ok = all(v is not None for v in bad.values())
    return {
        "discriminates": good_ok and bad_ok,
        "approved_drugs_pass": {n: (v is None) for n, v in good.items()},
        "impossible_molecules_rejected": {n: v for n, v in bad.items()},
        "note": "approved drugs must all pass; 2025 structures must all fail",
    }


@app.get("/rules")
def rules():
    """What the gate actually tests, so a chemist can argue with it."""
    return {
        "unstable_groups": gate_mod.UNSTABLE,
        "incompatible_pairs": [
            {"a": a, "b": b, "why": w} for a, b, w in gate_mod.INCOMPATIBLE
        ],
        "catalogues": ["PAINS", "BRENK"],
        "covalent_exemption": sorted(gate_mod.COVALENT_OK),
        "also_requires": "at least one aromatic ring",
    }
