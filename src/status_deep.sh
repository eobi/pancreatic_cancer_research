#!/bin/bash
cd /Users/ebukaobi/Documents/PersonalizedMedcine
n=$(pgrep -f "[r]un_screen.py" | wc -l | tr -d ' ')
echo "arms running: $n"
for arm in sim random; do
  f=screen_g12d_${arm}.json
  grep -o '"Vina Score": *-\?[0-9.]*' $f 2>/dev/null | sed 's/.*: *//' | sort -n > /tmp/_$arm.txt
  c=$(wc -l < /tmp/_$arm.txt | tr -d ' ')
  [ "$c" -eq 0 ] && { echo "  $arm: none yet"; continue; }
  printf "  %-7s %6s scored | best %s | median %s | beat AM-2383: %s | beat MRTX: %s\n" \
    "$arm" "$c" "$(head -1 /tmp/_$arm.txt)" "$(sed -n "$((c/2+1))p" /tmp/_$arm.txt)" \
    "$(awk '$1<-12.71' /tmp/_$arm.txt|wc -l|tr -d ' ')" "$(awk '$1<-13.77' /tmp/_$arm.txt|wc -l|tr -d ' ')"
done
tail -1 screen_sim.log; tail -1 screen_rand.log
