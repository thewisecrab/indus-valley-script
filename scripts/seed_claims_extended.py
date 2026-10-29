"""Session 7: the two seed-sensitive claims, over all available replicates (outputs/claims = replicate 0,
outputs/claims/seeds/s<k>). Reports medians and 2.5-97.5% percentile intervals across replicates.
(1) Per-sign LOO calibration: Yajnadevam's mean alternative-value p vs two calibration keys hill-climbed in each
    replicate (one fitted to a within-text-shuffled corpus, one fitted to the real corpus from a random start).
    Per replicate: the paired difference (calibration key minus Yajnadevam; > 0 means Yajnadevam is better) and the
    replicate's one-sided Mann-Whitney p. Across replicates: Wilcoxon signed-rank test of the paired differences.
(2) Fitted rebus keys: held-out compound hit rate on the real corpus per lexicon, its gain over the better of the two
    shuffled corpora, and each lexicon's rank (1 = highest) per replicate.
Output: outputs/claims/seed_claims_extended.json"""
import os, glob, json
import numpy as np, pandas as pd
from scipy.stats import wilcoxon, binomtest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); C = f'{ROOT}/outputs/claims'
import re
dirs = [C] + sorted([d for d in glob.glob(f'{C}/seeds/s*') if re.fullmatch(r's\d+', os.path.basename(d))], key=lambda d: int(os.path.basename(d)[1:]))
q = lambda x: [round(float(np.percentile(x, 2.5)), 4), round(float(np.percentile(x, 97.5)), 4)]
def summ(x): x = np.asarray(x, float); return dict(n=len(x), median=round(float(np.median(x)), 4), interval_95=q(x), min=round(float(x.min()), 4), max=round(float(x.max()), 4))
out = {}
L = []
for d in dirs:
    p = f'{d}/loo_phonetic_summary.json'
    if not os.path.exists(f'{d}/loo_phonetic_all_conditions.csv'): continue
    S = json.load(open(p)); g = S['global_mean_p_alt_by_condition']
    L.append(dict(rep=os.path.basename(d), yaj=g['Yajnadevam|real|sanskrit_MW']['mean'], shuf=g['FittedToShuffled|real|sanskrit_MW']['mean'],
                  rr=g['FittedToReal_randominit|real|sanskrit_MW']['mean'], mwu=S['Yajnadevam_vs_FittedToShuffled_MWU_less']['p'],
                  beats=S['Yajnadevam']['beats_all_nulls']))
L = pd.DataFrame(L); d1 = L.shuf - L.yaj; d2 = L.rr - L.yaj
out['loo'] = dict(n_replicates=len(L), yajnadevam_mean_p=summ(L.yaj), fitted_to_shuffled_mean_p=summ(L.shuf), fitted_to_real_random_start_mean_p=summ(L.rr),
                  diff_shuffled_minus_yaj=summ(d1), diff_random_start_minus_yaj=summ(d2),
                  share_yaj_better_than_shuffled=round(float((d1 > 0).mean()), 3), share_yaj_better_than_random_start=round(float((d2 > 0).mean()), 3),
                  wilcoxon_p_yaj_better_than_shuffled=float(wilcoxon(d1, alternative='greater').pvalue), wilcoxon_p_yaj_better_than_random_start=float(wilcoxon(d2, alternative='greater').pvalue),
                  per_replicate_mwu_p=summ(L.mwu), share_mwu_p_below_05=round(float((L.mwu < .05).mean()), 3),
                  sign_test_mwu_below_05_vs_expected_05=float(binomtest(int((L.mwu < .05).sum()), len(L), .05, alternative='greater').pvalue),
                  any_sign_beats_all_nulls=int(L.beats.sum()))
F = []
for d in dirs:
    f = f'{d}/F_rebus_summary.csv'
    if not os.path.exists(f): continue
    s = pd.read_csv(f, index_col=0); s['gain'] = s['real'] - s[['shuffled_within', 'shuffled_global']].max(1); s['rank'] = s['real'].rank(ascending=False)
    s['rep'] = os.path.basename(d); F.append(s.reset_index().rename(columns={'index': 'lexicon', s.index.name or 'lexicon': 'lexicon'}))
F = pd.concat(F); lexcol = F.columns[0]
rb = {}
for lx, g in F.groupby(lexcol):
    rb[lx] = dict(real=summ(g.real), gain_over_better_shuffle=summ(g.gain), share_real_beats_both_shuffles=round(float((g.gain > 0).mean()), 3),
                  rank=summ(g['rank']), rank_counts={int(k): int(v) for k, v in g['rank'].value_counts().sort_index().items()})
piv = F.pivot(index='rep', columns=lexcol, values='real'); dr = 'dravidian_DEDR_forms+PDR'
out['rebus'] = dict(n_replicates=int(piv.shape[0]), by_lexicon=rb,
                    dravidian_above={lx: round(float((piv[dr] > piv[lx]).mean()), 3) for lx in piv.columns if lx != dr},
                    median_rank_order=sorted(rb, key=lambda k: rb[k]['real']['median'], reverse=True))
json.dump(out, open(f'{C}/seed_claims_extended.json', 'w'), indent=1)
print(json.dumps(out['loo'], indent=1)); print(out['rebus']['median_rank_order'], out['rebus']['dravidian_above'])
for lx, v in rb.items(): print(f"{lx:28s} real med {v['real']['median']:.3f} {v['real']['interval_95']}  gain med {v['gain_over_better_shuffle']['median']:+.3f} {v['gain_over_better_shuffle']['interval_95']} beats {v['share_real_beats_both_shuffles']}  rank med {v['rank']['median']}")
