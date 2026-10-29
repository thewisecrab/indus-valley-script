#!/usr/bin/env bash
# Session 7: extra replicates for the seed-sensitive claims only (fitted rebus keys; per-sign LOO calibration).
# Usage: bash scripts/run_claim_seeds_extra.sh FIRST LAST_LOO LAST_REBUS
#   replicates FIRST..LAST_LOO run rebus_harness + loo_signs + calibration into outputs/claims/seeds/s<k>/
#   replicates LAST_LOO+1..LAST_REBUS run rebus_harness only (cheap) into outputs/claims/seeds/s<k>/
set -euo pipefail
cd "$(dirname "$0")/.."; PY=${PYTHON:-python}
A=${1:-5}; L=${2:-19}; R=${3:-49}
for k in $(seq $A $R); do
  d=outputs/claims/seeds/s$k; mkdir -p $d; cp outputs/claims/loo_phonetic_summary.json "$d/" 2>/dev/null || true
  export INDUS_LEXSEED=$k INDUS_CLAIMS_OUT=$d PYTHONHASHSEED=$((k+2))
  $PY scripts/rebus_harness.py > "$d/_F.log"
  if [ $k -le $L ]; then $PY scripts/loo_signs.py > "$d/_loo.log"; $PY scripts/loo_global_calibration.py >> "$d/_loo.log"; else rm -f "$d/loo_phonetic_summary.json"; fi
  echo "replicate $k done $(date +%H:%M:%S)"
done
