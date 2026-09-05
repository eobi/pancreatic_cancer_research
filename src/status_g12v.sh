#!/bin/bash
cd /Users/ebukaobi/Documents/PersonalizedMedcine
pgrep -f "[r]un_screen.py" >/dev/null && echo "RUNNING elapsed $(ps -o etime= -p $(pgrep -f '[r]un_screen.py'|head -1)|tr -d ' ')" || echo "FINISHED"
tail -1 logs/screen_g12v.log
grep -o '"Vina Score": *-\?[0-9.]*' data/screens/screen_g12v.json 2>/dev/null | sed 's/.*: *//' | sort -n > /tmp/_v.txt
n=$(wc -l < /tmp/_v.txt | tr -d ' '); [ "$n" -eq 0 ] && { echo "no scores yet"; exit 0; }
echo "$n scored | best $(head -1 /tmp/_v.txt) | median $(sed -n "$((n/2+1))p" /tmp/_v.txt)"
echo "beat AM-2383 -12.04: $(awk '$1<-12.04' /tmp/_v.txt|wc -l|tr -d ' ') | beat MRTX-1133 -12.64: $(awk '$1<-12.64' /tmp/_v.txt|wc -l|tr -d ' ')"
