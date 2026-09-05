#!/bin/bash
# Cheap progress check. Streams the score fields out of screen_results.json with
# grep rather than json.load, so it stays fast as the file grows past 17 MB
# (each record carries a full docked PDBQT).
cd /Users/ebukaobi/Documents/PersonalizedMedcine
if pgrep -f "[r]un_screen.py" >/dev/null; then
  echo "RUNNING  elapsed $(ps -o etime= -p $(pgrep -f '[r]un_screen.py' | head -1) | tr -d ' ')"
else
  echo "FINISHED"
fi
tail -1 screen.log
grep -o '"Vina Score": *-\?[0-9.]*' screen_results.json 2>/dev/null \
  | sed 's/.*: *//' | sort -n > /tmp/_scores.txt
n=$(wc -l < /tmp/_scores.txt | tr -d ' ')
[ "$n" -eq 0 ] && { echo "no scores yet"; exit 0; }
best=$(head -1 /tmp/_scores.txt)
med=$(sed -n "$(( n/2 + 1 ))p" /tmp/_scores.txt)
ada=$(awk '$1 < -10.83' /tmp/_scores.txt | wc -l | tr -d ' ')
bi=$(awk '$1 < -12.26' /tmp/_scores.txt | wc -l | tr -d ' ')
echo "$n scored | best $best | median $med"
echo "beat Adagrasib -10.83: $ada | beat BI-0474 -12.26: $bi"
