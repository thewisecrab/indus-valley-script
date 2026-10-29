"""Core analysis library for the Indus workstream.
All functions take a list of texts; each text is a list of sign IDs (strings),
in READING ORDER (first element = first sign read).
Damage/unknown placeholders should be passed as the token in `breakers`;
n-gram functions never form n-grams across them.
"""
from collections import Counter
import math, random
import numpy as np
import pandas as pd

def load_csv(path, id_col="inscription_id", seq_col="sign_sequence", reverse=False):
    df = pd.read_csv(path, dtype=str).fillna("")
    texts = []
    for _, r in df.iterrows():
        s = r[seq_col].split()
        if reverse: s = s[::-1]
        if s: texts.append((r[id_col], s))
    return df, texts

def split_on_breakers(seq, breakers):
    chunk = []
    for t in seq:
        if t in breakers:
            if chunk: yield chunk
            chunk = []
        else:
            chunk.append(t)
    if chunk: yield chunk

def sign_frequency(texts, breakers=()):
    c = Counter(t for s in texts for t in s if t not in breakers)
    df = pd.DataFrame(c.most_common(), columns=["sign", "count"])
    df["rank"] = np.arange(1, len(df) + 1)
    df["rel_freq"] = df["count"] / df["count"].sum()
    df["cum_freq"] = df["rel_freq"].cumsum()
    return df

def positional(texts, breakers=(), min_count=1):
    """Position classes per sign: solo (text of length 1), initial, medial, final.
    Only texts with NO breaker are used so positions are trustworthy."""
    pos = {}
    for s in texts:
        if any(t in breakers for t in s): continue
        n = len(s)
        for i, t in enumerate(s):
            d = pos.setdefault(t, Counter())
            if n == 1: d["solo"] += 1
            elif i == 0: d["initial"] += 1
            elif i == n - 1: d["final"] += 1
            else: d["medial"] += 1
    rows = []
    for t, d in pos.items():
        tot = sum(d.values())
        if tot < min_count: continue
        rows.append(dict(sign=t, total=tot, **{k: d.get(k, 0) for k in ["solo", "initial", "medial", "final"]}))
    df = pd.DataFrame(rows)
    for k in ["solo", "initial", "medial", "final"]:
        df[k + "_pct"] = 100 * df[k] / df["total"]
    return df.sort_values("total", ascending=False)

def ngrams(texts, n, breakers=(), boundary=False):
    c = Counter()
    for s in texts:
        for ch in split_on_breakers(s, breakers):
            seq = (["<s>"] + ch + ["</s>"]) if boundary else ch
            for i in range(len(seq) - n + 1):
                c[tuple(seq[i:i + n])] += 1
    return c

def zipf_fit(freq_df, rmax=None):
    """OLS fit of log f = a - b log r over ranks 1..rmax, plus discrete power-law MLE exponent (Clauset-style, xmin=1 approx)."""
    d = freq_df if rmax is None else freq_df[freq_df["rank"] <= rmax]
    x, y = np.log(d["rank"].values), np.log(d["count"].values)
    b, a = np.polyfit(x, y, 1)
    yhat = a + b * x
    r2 = 1 - ((y - yhat) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return dict(slope=b, intercept=a, r2=r2, n_ranks=len(d))

def conditional_entropy(texts, breakers=(), boundary=False):
    """Bigram conditional entropy H(Y|X) in bits, ML (plug-in) estimate."""
    bg = ngrams(texts, 2, breakers, boundary)
    left = Counter()
    for (a, b), k in bg.items(): left[a] += k
    N = sum(bg.values())
    H = 0.0
    for (a, b), k in bg.items():
        H -= (k / N) * math.log2(k / left[a])
    return H

def unigram_entropy(texts, breakers=()):
    c = Counter(t for s in texts for t in s if t not in breakers)
    N = sum(c.values())
    return -sum(k / N * math.log2(k / N) for k in c.values())

def shuffle_within(texts, rng):
    out = []
    for s in texts:
        s2 = list(s); rng.shuffle(s2); out.append(s2)
    return out

def shuffle_global(texts, rng):
    """Preserve text lengths and global unigram distribution, destroy all sequence structure."""
    pool = [t for s in texts for t in s]; rng.shuffle(pool)
    out, i = [], 0
    for s in texts:
        out.append(pool[i:i + len(s)]); i += len(s)
    return out

def entropy_vs_tokens(texts, sizes, breakers=(), reps=10, seed=0):
    """Rao-style curve: conditional entropy as a function of the number of most frequent tokens kept
    (other signs mapped to a single UNK class)."""
    freq = sign_frequency(texts, breakers)
    rows = []
    rng = random.Random(seed)
    for k in sizes:
        keep = set(freq["sign"].head(k))
        mapped = [[t if (t in keep or t in breakers) else "UNK" for t in s] for s in texts]
        real = conditional_entropy(mapped, breakers)
        w = [conditional_entropy(shuffle_within(mapped, rng), breakers) for _ in range(reps)]
        g = [conditional_entropy(shuffle_global(mapped, rng), breakers) for _ in range(reps)]
        rows.append(dict(k=k, H_real=real, H_within_shuffle=np.mean(w), H_within_sd=np.std(w),
                         H_global_shuffle=np.mean(g), H_global_sd=np.std(g)))
    return pd.DataFrame(rows)

def branching_entropy_segments(texts, breakers=(), threshold=None):
    """Harris-style unsupervised segmentation: place a boundary after position i when the
    forward branching entropy H(next | current sign) rises relative to the previous position
    (a local increase), or exceeds a threshold. Returns segmented texts and segment counts.
    This is a crude heuristic for proposing candidate 'words'/phrases; it is NOT evidence of words."""
    bg = ngrams(texts, 2, breakers, boundary=True)
    nxt = {}
    for (a, b), k in bg.items(): nxt.setdefault(a, Counter())[b] += k
    def H(a):
        c = nxt.get(a)
        if not c: return 0.0
        N = sum(c.values()); return -sum(k / N * math.log2(k / N) for k in c.values())
    segs = Counter(); seg_texts = []
    for s in texts:
        out = []
        for ch in split_on_breakers(s, breakers):
            hs = [H(t) for t in ch]
            cur = [ch[0]]
            for i in range(1, len(ch)):
                boundary = (hs[i - 1] > (hs[i - 2] if i >= 2 else 0)) if threshold is None else hs[i - 1] > threshold
                if boundary:
                    out.append(tuple(cur)); cur = [ch[i]]
                else:
                    cur.append(ch[i])
            out.append(tuple(cur))
        for sg in out: segs[sg] += 1
        seg_texts.append(out)
    return seg_texts, segs

def direction_score(texts, breakers=()):
    """Compare positional concentration of signs at text-start vs text-end.
    Returns entropy of initial-sign and final-sign distributions (lower = more formulaic)."""
    ini = Counter(); fin = Counter()
    for s in texts:
        if any(t in breakers for t in s) or len(s) < 2: continue
        ini[s[0]] += 1; fin[s[-1]] += 1
    def ent(c):
        N = sum(c.values()); return -sum(k / N * math.log2(k / N) for k in c.values())
    return dict(H_initial=ent(ini), H_final=ent(fin), top_initial=ini.most_common(5), top_final=fin.most_common(5))
