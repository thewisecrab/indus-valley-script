"""Session 4: NSB (Nemenman-Shafee-Bialek 2002) entropy estimates for the sign inventory (unigram) and the
bigram conditional entropy H(next | previous). Self-implemented, since the `ndd` package failed to build.
For each beta on a log grid, the posterior weight is p(n|beta) * dxi/dbeta * beta. The reported spread is the
posterior s.d. of E[H|beta], which is a lower bound on the full posterior s.d. Results are in bits.
Alphabet size K matters: it is reported for K = observed types, the Chao1 estimate, and the published list size."""
import os, json, collections, math, random, numpy as np
from scipy.special import gammaln, digamma, polygamma
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(f'{ROOT}/scripts/structure2.py').read(); exec(src.split('# ============ 1. Segmentation')[0])
LN2 = math.log(2)
def nsb(counts, K):
    n = np.array([c for c in counts if c > 0], float); N = n.sum(); K = max(K, len(n)); k0 = K - len(n)
    betas = np.exp(np.linspace(np.log(1e-4), np.log(1e3), 600))
    logp = []; EH = []
    for b in betas:
        lp = gammaln(K*b) - gammaln(N + K*b) + np.sum(gammaln(n + b) - gammaln(b))
        dxi = K*polygamma(1, K*b + 1) - polygamma(1, b + 1)
        logp.append(lp + np.log(max(dxi, 1e-300)) + np.log(b))
        A = N + K*b
        eh = digamma(A + 1) - (np.sum((n + b)*digamma(n + b + 1)) + k0*b*digamma(b + 1))/A
        EH.append(eh)
    logp = np.array(logp); w = np.exp(logp - logp.max()); w /= w.sum(); EH = np.array(EH)
    m = float((w*EH).sum()); sd = float(np.sqrt((w*(EH - m)**2).sum()))
    return m/LN2, sd/LN2
def ml(counts):
    n = np.array([c for c in counts if c > 0], float); p = n/n.sum(); return float(-(p*np.log2(p)).sum())
def mm(counts):
    n = [c for c in counts if c > 0]; return ml(n) + (len(n)-1)/(2*sum(n)*LN2)
def chao1(c):
    f1 = sum(1 for v in c if v == 1); f2 = sum(1 for v in c if v == 2); return len([v for v in c if v]) + (f1*f1/(2*f2) if f2 else f1*(f1-1)/2)
def cond(texts, K, est):
    ctx = collections.defaultdict(collections.Counter)
    for s in texts:
        t = ['<s>'] + list(s) + ['</s>']
        for a, b in zip(t, t[1:]): ctx[a][b] += 1
    N = sum(sum(c.values()) for c in ctx.values()); tot = 0
    for a, c in ctx.items():
        h = est(list(c.values()), K) if est is nsb else (est(list(c.values())), 0)
        tot += sum(c.values())/N*h[0]
    return tot
def shuf_within(lines, r):
    out = []
    for s in lines: s = list(s); r.shuffle(s); out.append(s)
    return out
def dedup(L): return [list(t) for t in dict.fromkeys(tuple(s) for s in L)]
out = {}
for name, T, listK in [('M77_full_dedup', dedup(FULL), 417), ('ICIT_full_dedup', dedup(W_FULL), 712)]:
    c = collections.Counter(x for s in T for x in s); v = list(c.values()); Ks = {'observed': len(v), 'chao1': int(round(chao1(v))), 'list': listK}
    r = {'tokens': int(sum(v)), 'types': len(v), 'K': Ks, 'H1_ML': ml(v), 'H1_MillerMadow': mm(v)}
    for kn, K in Ks.items():
        m, sd = nsb(v, K); r[f'H1_NSB_K={kn}'] = [m, sd]
    for kn in ['observed', 'chao1']:
        K = Ks[kn] + 1
        r[f'Hcond_NSB_K={kn}'] = cond(T, K, nsb)
        sh = [cond(shuf_within(T, random.Random(i)), K, nsb) for i in range(3)]
        r[f'Hcond_NSB_K={kn}_shuffled_mean'] = float(np.mean(sh))
    r['Hcond_ML'] = cond(T, 0, ml); r['Hcond_MillerMadow'] = cond(T, 0, mm)
    out[name] = r; print(name, json.dumps(r, indent=1), flush=True)
json.dump(out, open(f'{ROOT}/outputs/structure/nsb_entropy.json', 'w'), indent=1)
