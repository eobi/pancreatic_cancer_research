# Resuming the G12R screen

Stopped 2026-09-05 with **1,663 of 10,000 compounds scored**. The checkpoint is
`data/screens/screen_g12r.json` and `run_screen.py` skips anything already present, so
resuming costs nothing and repeats nothing.

## Command

```bash
ENV=<path to the mmgbsa env>
nohup nice -n 5 $ENV/bin/python -u src/run_screen.py data/gated/selected_g12r.json \
  -o data/screens/screen_g12r.json -j 8 --exhaustiveness 4 \
  --receptor targets/g12r/rec.pdbqt --box targets/g12r/box.txt \
  > logs/screen_g12r.log 2>&1 &
```

Roughly 8,300 compounds remain. At the clean rate of 4.5 s per ligand that is about
10 hours; it degraded to 8.9 s under contention, so run it when the machine is otherwise
idle.

## State at the stop

| quantity | value |
|---|---|
| scored | 1,663 of 10,000 (17%) |
| best Vina score | -11.99 kcal/mol |
| median | -9.12 |
| beat cognate RP03514 (-9.80) | 412 |
| **beat strongest control MRTX-1133 (-12.93)** | **0** |

Target validation is complete and unaffected: cognate redock 0.99 A at exhaustiveness 128
(`targets/g12r/validate_ex128/validation.json`). Exhaustiveness 4 is justified for screening
by the sensitivity analysis in `results/exhaustiveness_verdict_g12v.json`.

## What the partial result already supports

At 17 percent of the library, nothing approaches the strongest clinical control. The 412
compounds past the cognate are not a finding: RP03514 scores only -9.80 on this target, so
clearing it is easy, and the same pattern held on G12D (201 past a weak cognate, 0 past the
strong control). Completing the screen may change this, but the direction so far matches the
other two variants.
