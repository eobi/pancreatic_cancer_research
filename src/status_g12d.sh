#!/bin/bash
cd /Users/ebukaobi/Documents/PersonalizedMedcine
pgrep -f "[r]un_screen.py" >/dev/null && echo "RUNNING elapsed $(ps -o etime= -p $(pgrep -f '[r]un_screen.py'|head -1)|tr -d ' ')" || echo "FINISHED"
tail -1 screen_g12d.log
grep -o '"Vina Score": *-\?[0-9.]*' screen_g12d.json 2>/dev/null | sed 's/.*: *//' | sort -n > /tmp/_g.txt
n=$(wc -l < /tmp/_g.txt | tr -d ' '); [ "$n" -eq 0 ] && { echo "no scores yet"; exit 0; }
echo "$n scored | best $(head -1 /tmp/_g.txt) | median $(sed -n "$((n/2+1))p" /tmp/_g.txt)"
echo "beat AM-2383 -12.71: $(awk '$1<-12.71' /tmp/_g.txt|wc -l|tr -d ' ') | beat MRTX-1133 -13.77: $(awk '$1<-13.77' /tmp/_g.txt|wc -l|tr -d ' ')"
