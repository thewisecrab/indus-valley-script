"""Global calibration block of outputs/claims/loo_phonetic_summary.json (session 6: this computation was
originally run ad hoc after loo_signs.py; it is now a script so the paper's numbers have a provenance).
Reads outputs/claims/loo_phonetic_all_conditions.csv and adds to loo_phonetic_summary.json:
  global_mean_p_alt_by_condition  mean / median / count / share p<=0.05 of the per-sign p_alt, by condition
  Yajnadevam_vs_FittedToShuffled_MWU_less  one-sided Mann-Whitney U, Yajnadevam p_alt < fitted-to-shuffled p_alt
                                           (both on the real corpus with the Sanskrit (MW) lexicon)
  alt_value_pool_sizes  kept if already present (written alongside the keys; see loo_signs.py)
Run: python scripts/loo_global_calibration.py [--check]   (--check: recompute and compare, write nothing)"""
import os, sys, json
import pandas as pd
from scipy.stats import mannwhitneyu
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.environ.get('INDUS_CLAIMS_OUT') or f'{ROOT}/outputs/claims'
A = pd.read_csv(f'{OUT}/loo_phonetic_all_conditions.csv', dtype={'sign': str})
g = {c: dict(mean=round(float(x.p_alt.mean()), 3), median=round(float(x.p_alt.median()), 3), count=int(len(x)),
             frac_p_le_0_05=round(float((x.p_alt <= 0.05).mean()), 3))
     for c, x in sorted(A.groupby('condition'), key=lambda kv: kv[0])}
g = {c: {('frac_p_le_0.05' if k == 'frac_p_le_0_05' else k): v for k, v in d.items()} for c, d in g.items()}
y = A[A.condition == 'Yajnadevam|real|sanskrit_MW'].p_alt; f = A[A.condition == 'FittedToShuffled|real|sanskrit_MW'].p_alt
mwu = dict(p=float(mannwhitneyu(y, f, alternative='less').pvalue))
S = json.load(open(f'{OUT}/loo_phonetic_summary.json'))
if '--check' in sys.argv:
    old_g = S.get('global_mean_p_alt_by_condition', {}); old_m = S.get('Yajnadevam_vs_FittedToShuffled_MWU_less', {})
    diff = [c for c in set(g) | set(old_g) if g.get(c) != old_g.get(c)]
    same_mwu = bool(old_m) and abs(old_m['p'] - mwu['p']) < 1e-12
    print(f'conditions: {len(g)}; differing: {sorted(diff)}; MWU p {mwu["p"]:.6f} vs committed {old_m.get("p")}: {"same" if same_mwu else "DIFFERENT"}')
    sys.exit(0 if not diff and same_mwu else 1)
pool = S.pop('alt_value_pool_sizes', None)
try:  # recompute the alternative-value pool sizes when the (restricted) keys are present locally
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import claim_harness as CH
    fc = pd.read_csv(f'{ROOT}/data/field-cady_indus_valley_script_corpus/indus_dravidian_mapping_100.csv', dtype=str)
    pool = dict(Yajnadevam=len({v for v in CH.load_key().values() if v}),
                FieldCady=len({v for s, v in zip(fc.Indus_Sign, fc.Dravidian_Syllable) if s not in ('000', '999') and v}))
except Exception: pass
S['global_mean_p_alt_by_condition'] = g
if pool is not None: S['alt_value_pool_sizes'] = pool
S['Yajnadevam_vs_FittedToShuffled_MWU_less'] = mwu
json.dump(S, open(f'{OUT}/loo_phonetic_summary.json', 'w'), indent=1)
print('Yajnadevam mean p_alt', g['Yajnadevam|real|sanskrit_MW']['mean'], '| FittedToShuffled', g['FittedToShuffled|real|sanskrit_MW']['mean'],
      '| FittedToReal_randominit', g['FittedToReal_randominit|real|sanskrit_MW']['mean'], '| MWU p', round(mwu['p'], 3))
