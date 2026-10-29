"""Summarise pc_results.csv -> pc_summary.csv and markdown tables (printed)."""
import os, pandas as pd, numpy as np
PC = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); O = f'{PC}/outputs'
R = pd.read_csv(f'{O}/pc_results.csv'); L = pd.read_csv(f'{O}/pc_results_by_length.csv')
g = R.groupby(['corpus', 'key', 'textset', 'measure'], sort=False)
rows = []
for k, d in g:
    s0 = d[d.sample_seed == 0].iloc[0]
    rows.append(dict(zip(['corpus', 'key', 'textset', 'measure'], k), n_texts=int(s0.n_texts), mean_len=s0.mean_len,
        real=s0.real, within=s0.within_mean, within_95=f'{s0.within_lo95:.3f}-{s0.within_hi95:.3f}', globl=s0.global_mean,
        global_95=f'{s0.global_lo95:.3f}-{s0.global_hi95:.3f}', permkey=s0.permkey_mean,
        drop_within=s0.drop_within, rel_drop_within=round(s0.drop_within / s0.real, 3) if s0.real else np.nan,
        drop_global=s0.drop_global, p_within=s0.p_within, p_global=s0.p_global, p_permkey=s0.p_permkey, n_shuf=int(s0.n_within), n_perm=int(s0.n_permkey),
        seeds=len(d), drop_within_range_over_seeds=f'{d.drop_within.min():.3f}..{d.drop_within.max():.3f}',
        drop_global_range_over_seeds=f'{d.drop_global.min():.3f}..{d.drop_global.max():.3f}',
        max_p_within_over_seeds=d.p_within.max(), max_p_global_over_seeds=d.p_global.max()))
S = pd.DataFrame(rows); S.to_csv(f'{O}/pc_summary.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40); pd.set_option('display.max_rows', 400)
print(S[['corpus', 'key', 'textset', 'measure', 'mean_len', 'real', 'within', 'globl', 'permkey', 'drop_within', 'drop_global', 'p_within', 'p_global', 'drop_within_range_over_seeds', 'max_p_within_over_seeds', 'max_p_global_over_seeds']].to_string(index=False))
print()
print(L[L.textset.isin(['lenmatch_wordaligned', 'lipi_test_texts_2317'])][['corpus', 'key', 'textset', 'measure', 'len_bin', 'n', 'real', 'within_mean', 'global_mean', 'drop_within', 'drop_global', 'p_within', 'p_global']].to_string(index=False))
