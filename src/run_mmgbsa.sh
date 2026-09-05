#!/bin/bash
ENV=/private/tmp/claude-501/-Users-ebukaobi-Documents-Pentagon/53764bb8-dc7e-4e15-83e0-697503f0f4ef/scratchpad/mamba/envs/mmgbsa
export PATH="$ENV/bin:$PATH"
export PYTHONUNBUFFERED=1
cd /Users/ebukaobi/Documents/PersonalizedMedcine
exec $ENV/bin/python -u src/mmgbsa.py "$@"
