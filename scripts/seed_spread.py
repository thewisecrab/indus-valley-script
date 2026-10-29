"""Session 6: spread of the claim-test results over seed replicates (scripts/run_claim_seeds.sh).
Replicate 0 = outputs/claims (canonical), replicates 1.. = outputs/claims/seeds/s<k>. Optional --old DIR adds the
pre-session-6 (hash-order dependent) values for comparison. Output: outputs/claims/seed_spread.csv"""
import os, sys, json, glob
import pandas as pd, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); C = f'{ROOT}/outputs/claims'
def metrics(d):
    m = {}
    B = json.load(open(f'{d}/B_fixed_key_segmentability.json'))
    for r in B['rows']:
        for k in ['real', 'shuffled_within_mean', 'shuffled_global_mean', 'permuted_key_mean']: m[f'B|{r["lexicon"]}|{k}'] = r[k]
    Cf = pd.read_csv(f'{d}/C_fitted_keys.csv')
    for (l, c), g in Cf.groupby(['lexicon', 'corpus']): m[f'C|{l}|{c}|heldout_mean'] = g.heldout.mean()
    F = pd.read_csv(f'{d}/F_rebus_summary.csv', index_col=0)
    for l in F.index:
        for c in F.columns: m[f'F|{l}|{c}|heldout'] = F.loc[l, c]
    S = json.load(open(f'{d}/loo_phonetic_summary.json')); g = S.get('global_mean_p_alt_by_condition', {})
    for k in ['Yajnadevam|real|sanskrit_MW', 'FittedToShuffled|real|sanskrit_MW', 'FittedToReal_randominit|real|sanskrit_MW', 'FieldCady|real|proto_dravidian_PDR']:
        if k in g: m[f'LOO|{k}|mean_p_alt'] = g[k]['mean']
    if 'Yajnadevam_vs_FittedToShuffled_MWU_less' in S: m['LOO|MWU_p_Yajnadevam_lt_FittedToShuffled'] = S['Yajnadevam_vs_FittedToShuffled_MWU_less']['p']
    for kn in ['Yajnadevam', 'FieldCady', 'FittedToShuffled', 'FittedToReal_randominit']:
        m[f'LOO|{kn}|beats_all_nulls'] = S[kn]['beats_all_nulls']
        for cond, v in S[kn]['q05_by_condition'].items(): m[f'LOO|{cond}|p05'] = v['p05']; m[f'LOO|{cond}|q05'] = v['q05']
    return m
reps = {'s0': metrics(C)}
for d in sorted(glob.glob(f'{C}/seeds/s[0-9]*')):
    if os.path.basename(d) != 's0_hashcheck' and os.path.exists(f'{d}/loo_phonetic_summary.json'): reps[os.path.basename(d)] = metrics(d)
D = pd.DataFrame(reps)
out = pd.DataFrame(dict(canonical_s0=D.s0, mean=D.mean(axis=1), min=D.min(axis=1), max=D.max(axis=1), n_replicates=D.notna().sum(axis=1)))
if '--old' in sys.argv:
    out['pre_session6'] = pd.Series(metrics(sys.argv[sys.argv.index('--old') + 1]))
out.round(4).to_csv(f'{C}/seed_spread.csv', index_label='metric'); print(out.round(4).to_string())
