"""Session 8: positional nulls for the positive control. Same texts as pc_run.py seed 0 (word-aligned, length-matched
to M77) and the same measures. Nulls (the reference for tools/evaluate_key.py):
  within      signs of each text permuted (as pc_run.py; re-run here so the 4+-sign subset can be reported)
  edgefixed   first and last sign kept in place, interior permuted (texts of 2-3 signs unchanged)
  posglobal   signs re-dealt across texts within position classes (first / middle / last): keeps where each sign stands,
              destroys the sequences
Each is also reported on texts of >= 4 signs ('_4plus'). Tells how much a CORRECT key loses when the script's
positional habits are preserved. Output: positive_control/outputs/pc_positional_nulls.csv. Deterministic
(random.Random(zlib.crc32(label))). Usage: python positive_control/scripts/pc_positional_nulls.py [--nshuf 100] [--procs 8]"""
import os, sys, zlib, random, collections, argparse
ap = argparse.ArgumentParser(); ap.add_argument('--nshuf', type=int, default=100); ap.add_argument('--procs', type=int, default=8)
E = ap.parse_args(); sys.argv = [sys.argv[0]]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import pc_run as P
import numpy as np, pandas as pd
from multiprocessing import Pool
def edge(s, r):
    s = list(s)
    if len(s) <= 3: return tuple(s)
    mid = s[1:-1]; return tuple([s[0]] + r.sample(mid, len(mid)) + [s[-1]])
def posglobal(seqs, r):
    cls = lambda i, n: 'F' if i == 0 else ('L' if i == n - 1 else 'M')
    pools = {'F': [], 'M': [], 'L': []}
    for s in seqs:
        for i, x in enumerate(s): pools[cls(i, len(s))].append(x)
    for k in sorted(pools): r.shuffle(pools[k])
    it = {k: iter(v) for k, v in pools.items()}
    return [tuple(next(it[cls(i, len(s))]) for i in range(len(s))) for s in seqs]
J = {}
def work(job):
    kind, rep = job; r = random.Random(zlib.crc32(f"{J['label']}|{kind}|{rep}".encode()))
    seqs = J['seqs']
    if kind == 'within': seqs = [tuple(r.sample(list(s), len(s))) for s in seqs]
    elif kind == 'edgefixed': seqs = [edge(s, r) for s in seqs]
    else: seqs = posglobal(seqs, r)
    return kind, P.score_set(J['kind'], seqs, J['key'])
if __name__ == '__main__':
    rows = []
    for cname, kind in [('sanskrit_classical', 'skt'), ('sanskrit_vedic', 'skt'), ('akkadian_NA_letters', 'akk')]:
        texts = P.load(cname)
        types = collections.defaultdict(collections.Counter)
        for t in texts:
            for s, v in t['tok']: types[s][v] += 1
        fixed = {s: sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for s, c in types.items()}
        seqs = [tuple(s) for s in P.textsets(texts, 7, P.A.n)['lenmatch_wordaligned']]   # the seed-0 sample of pc_run.py
        m4 = np.array([len(s) >= 4 for s in seqs])
        for keyname, key in [('correct', None)] + ([('fixed_one_value_per_sign', fixed)] if kind == 'akk' else []):
            J.update(kind=kind, seqs=seqs, key=key, label=f'{cname}|{keyname}')
            real = P.score_set(kind, seqs, key)
            jobs = [(k, i) for k in ['within', 'edgefixed', 'posglobal'] for i in range(E.nshuf)]
            with Pool(E.procs) as p: res = p.map(work, jobs, chunksize=2)
            by = collections.defaultdict(list)
            for k, x in res: by[k].append(x)
            for m in real:
                row = dict(corpus=cname, key=keyname, textset='lenmatch_wordaligned', measure=m, n_texts=len(seqs), n_texts_4plus=int(m4.sum()),
                           real=round(float(real[m].mean()), 4), real_4plus=round(float(real[m][m4].mean()), 4), n_shuf=E.nshuf)
                for k in ['within', 'edgefixed', 'posglobal']:
                    v = np.array([x[m].mean() for x in by[k]]); v4 = np.array([x[m][m4].mean() for x in by[k]])
                    row[f'drop_{k}'] = round(float(real[m].mean() - v.mean()), 4); row[f'p_{k}'] = round(float((1 + (v >= real[m].mean()).sum()) / (len(v) + 1)), 4)
                    row[f'drop_{k}_4plus'] = round(float(real[m][m4].mean() - v4.mean()), 4); row[f'p_{k}_4plus'] = round(float((1 + (v4 >= real[m][m4].mean()).sum()) / (len(v4) + 1)), 4)
                rows.append(row); print(row, flush=True)
            pd.DataFrame(rows).to_csv(f'{P.OUT}/pc_positional_nulls.csv', index=False)
