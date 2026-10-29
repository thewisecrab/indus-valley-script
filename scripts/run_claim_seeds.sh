#!/usr/bin/env bash
# Session 6: deterministic claim-test runs. Replicate 0 is canonical (outputs/claims/); replicates 1..N-1 go to
# outputs/claims/seeds/s<k>/; "s0_hashcheck" re-runs replicate 0 under a different PYTHONHASHSEED to prove determinism.
# Usage: bash scripts/run_claim_seeds.sh [N=5]
set -euo pipefail
cd "$(dirname "$0")/.."; PY=${PYTHON:-python}; N=${1:-5}
run () { # k outdir hashseed
  mkdir -p "$2"
  if [ "$2" != outputs/claims ]; then cp outputs/claims/loo_phonetic_summary.json "$2/" 2>/dev/null || true; fi
  export INDUS_LEXSEED=$1 INDUS_CLAIMS_OUT=$2 PYTHONHASHSEED=$3
  $PY scripts/claim_harness.py B > "$2/_B.log"; $PY scripts/claim_harness.py C > "$2/_C.log"
  $PY scripts/rebus_harness.py > "$2/_F.log"; $PY scripts/loo_signs.py > "$2/_loo.log"
  $PY scripts/loo_global_calibration.py >> "$2/_loo.log"; echo "replicate $1 -> $2 done"
}
run 0 outputs/claims 1
run 0 outputs/claims/seeds/s0_hashcheck 2
for k in $(seq 1 $((N-1))); do run $k outputs/claims/seeds/s$k $((k+2)); done
