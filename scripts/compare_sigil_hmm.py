"""Session 5 add-on: does the HMM slot-grammar gain (our sec. 3.x) also appear in a SIGIL-like non-linguistic emblem system?"""
import os, sys, json, random, collections, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(f'{ROOT}/scripts/compare_replications.py').read()
exec(s.split('res = {}\nEB = dedup')[0])  # loaders, sigil_like, dedup, shuf_within
s3 = open(f'{ROOT}/scripts/structure3_dedup.py').read()
exec('from hmmlearn.hmm import CategoricalHMM\n' + s3.split('from hmmlearn.hmm import CategoricalHMM')[1].split('which = sys.argv')[0])
EB = dedup(FULL); SY = dedup(sigil_like([len(t) for t in EB], seed=1)); out = {}
for name, L in [('M77_EBUDS_like_dedup', EB), ('SIGIL_like', SY)]:
    r = hmm_eval(L, seed=0)[0]; sh = hmm_eval(shuf_within(L, random.Random(30)), seed=0)[0]
    out[name] = dict(real={k: round(v, 4) for k, v in r.items()}, shuffled={k: round(v, 4) for k, v in sh.items()},
                     gain_K5_real=round(r[5]-r[1], 4), gain_K5_shuffled=round(sh[5]-sh[1], 4))
    print(name, out[name], flush=True)
json.dump(out, open(f'{ROOT}/outputs/compare/sigil_hmm.json', 'w'), indent=1)
