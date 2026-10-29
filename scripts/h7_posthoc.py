"""Session 7, EXPLORATORY (post hoc; does not change the pre-registered verdicts in outputs/prereg/).
Why does H7 (a stroke numeral immediately precedes the fish M059) fail on ICIT pottery and the West/foreign split?
(1) Description of the relevant texts per split: count, mean length, share of texts with a numeral->fish adjacency.
(2) Power: texts of the same number (and, separately, the same length profile) are resampled from the pooled
    passing ICIT splits (texts not in the failing split), and the pre-registered permutation test is rerun; the
    pass rate estimates the power of the failing split under a homogeneous effect.
(3) Heterogeneity: Fisher exact test of the per-text adjacency rate in the failing split vs the rest of ICIT, and
    the same with the per-text excess over the within-text-shuffle expectation (permutation of split labels).
No ICIT text is written out (the texts are not redistributable).
Output: outputs/prereg/h7_posthoc_exploratory.json"""
import os, sys, json, random
import numpy as np
from scipy.stats import fisher_exact
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, f'{ROOT}/scripts')
import prereg_heldout as P
P.NPERM = 500
def exp_adj(s, N, F, rng, n=400):  # expected within-text-shuffle adjacency count for one text
    return np.mean([P.st_bigram([tuple(rng.sample(s, len(s)))], N, F) for _ in range(n)])
if __name__ == '__main__':
    sp = P.load_real(); N, F = P.S('NUMERAL', 'W'), P.S('M059', 'W'); rng = random.Random(11)
    rel = {k: sorted({tuple(s) for s in v[2] if len(s) >= 2 and set(s) & N and set(s) & F}) for k, v in sp.items() if v[0] == 'W'}
    desc = {}
    for k, R in rel.items():
        adj = [P.st_bigram([s], N, F) > 0 for s in R]
        desc[k] = dict(n_relevant=len(R), mean_len=round(float(np.mean([len(s) for s in R])), 2) if R else None,
                       texts_with_adjacency=int(sum(adj)), share_with_adjacency=round(float(np.mean(adj)), 3) if R else None)
    pot, west = 'ICIT object: POT (pottery)', [k for k in rel if k.startswith('ICIT region: West')][0]
    out = dict(label='EXPLORATORY post-hoc analysis; the pre-registered H7 verdict (partially replicated) is unchanged', descriptive=desc)
    for fail in [pot, west]:
        R = rel[fail]; others = sorted({s for k, v in rel.items() if k not in (fail,) and not k.startswith('ICIT region: West') and k.startswith('ICIT object') for s in v} - set(R))
        # (2) power by resampling n texts from the rest, unmatched and length-matched
        n = len(R); passes = []; passes_len = []; bylen = {}
        for s in others: bylen.setdefault(len(s), []).append(s)
        for b in range(400):
            smp = rng.sample(others, n); passes.append(P.perm_test(smp, lambda q: P.st_bigram(q, N, F), seed=b)[2] < P.ALPHA)
            sm2 = [rng.choice(bylen.get(len(s)) or bylen[min(bylen, key=lambda L: abs(L - len(s)))]) for s in R]
            passes_len.append(P.perm_test(sm2, lambda q: P.st_bigram(q, N, F), seed=10000 + b)[2] < P.ALPHA)
        # (3) heterogeneity
        a = [P.st_bigram([s], N, F) > 0 for s in R]; o = [P.st_bigram([s], N, F) > 0 for s in others]
        OR, pf = fisher_exact([[sum(a), len(a) - sum(a)], [sum(o), len(o) - sum(o)]])
        ex = {s: P.st_bigram([s], N, F) - exp_adj(list(s), N, F, rng) for s in R + others}
        diff = np.mean([ex[s] for s in R]) - np.mean([ex[s] for s in others]); allx = np.array([ex[s] for s in R + others]); null = []
        r2 = np.random.default_rng(3)
        for _ in range(5000):
            pr = r2.permutation(len(allx)); null.append(allx[pr[:n]].mean() - allx[pr[n:]].mean())
        null = np.array(null)
        out[fail] = dict(n_relevant=n, comparison='other ICIT object-type splits pooled (SEAL, TAB, other), texts not in this split',
                         n_comparison=len(others), power_same_n=round(float(np.mean(passes)), 3), power_same_lengths=round(float(np.mean(passes_len)), 3),
                         share_adjacency_split=round(float(np.mean(a)), 3), share_adjacency_rest=round(float(np.mean(o)), 3), fisher_OR=round(float(OR), 3), fisher_p=round(float(pf), 4),
                         mean_excess_split=round(float(np.mean([ex[s] for s in R])), 3), mean_excess_rest=round(float(np.mean([ex[s] for s in others])), 3),
                         excess_diff_p_two_sided=float((1 + (np.abs(null) >= abs(diff)).sum()) / (1 + len(null))))
        print(fail, out[fail], flush=True)
    json.dump(out, open(f'{ROOT}/outputs/prereg/h7_posthoc_exploratory.json', 'w'), indent=1)
    print(json.dumps(desc, indent=1))
