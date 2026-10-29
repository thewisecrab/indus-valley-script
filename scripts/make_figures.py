"""Figures for the manuscript, generated from project outputs."""
import os, json, shutil, pandas as pd, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); F = f'{ROOT}/paper/figures'; os.makedirs(F, exist_ok=True)
# Fig 1 positional profile of top classed signs
c = pd.read_csv(f'{ROOT}/outputs/structure/sign_classes_M77.csv')
top = c.sort_values('freq', ascending=False).head(40)
col = {'TERMINAL': 'C3', 'INITIAL': 'C0', 'PRE-TERMINAL': 'C1', 'NUMERAL-STROKE': 'C2', 'BOUND-COLLOCATE': 'C4', 'STAND-ALONE': 'C5', 'MEDIAL/UNSPECIFIED': '0.6'}
fig, ax = plt.subplots(figsize=(6.5, 5))
for k, g in c.groupby('cls'):
    ax.scatter(g.init_share, g.final_share, s=np.sqrt(g.freq) * 3, c=col[k], label=f'{k} ({len(g)})', alpha=.7, edgecolor='k', lw=.3)
for r in top.head(15).itertuples(): ax.annotate(r.sign, (r.init_share, r.final_share), fontsize=6)
ax.set_xlabel('share of occurrences text-initial'); ax.set_ylabel('share text-final'); ax.legend(fontsize=6); ax.set_title('M77 signs (freq ≥ 10): positional profile and class')
fig.tight_layout(); fig.savefig(f'{F}/fig1_positional_classes.png', dpi=150); plt.close(fig)
# Fig 2 W700 formula
w = json.load(open(f'{ROOT}/outputs/anchors/w700_vs_weights.json'))['numeral_adjacent_to_700']
fig, ax = plt.subplots(figsize=(5, 3.2)); ks = list(w); ax.bar(ks, [w[k] for k in ks], color='C2'); ax.set_ylabel('tokens adjacent to W700'); ax.set_title('Stroke numerals in the W700 tablet formula (ICIT/lipi)')
plt.xticks(rotation=30, fontsize=7); fig.tight_layout(); fig.savefig(f'{F}/fig2_w700_numerals.png', dpi=150); plt.close(fig)
# Fig 3 claim harness: vidyut + rebus
e = json.load(open(f'{ROOT}/outputs/claims/E_vidyut_parse.json'))
keys = ['mechanical_real', 'mechanical_shuffled_within', 'mechanical_shuffled_global', 'mechanical_permuted_key', 'markov_nonsense_matched_length']
fig, axs = plt.subplots(1, 2, figsize=(9, 3.4))
axs[0].bar(range(len(keys)), [e[k]['full_parse'] for k in keys], color=['C0', '0.6', '0.6', '0.4', '0.4'])
axs[0].set_xticks(range(len(keys))); axs[0].set_xticklabels(['real order', 'shuffled\nwithin', 'shuffled\nglobal', 'permuted\nkey', 'Markov\nnonsense'], fontsize=7)
axs[0].set_ylabel('share fully parsed by vidyut'); axs[0].set_title('Yajnadevam key: Sanskrit parse test', fontsize=9)
r = pd.read_csv(f'{ROOT}/outputs/claims/F_rebus_summary.csv'); x = np.arange(len(r))
for i, (k, cc) in enumerate([('real', 'C0'), ('shuffled_global', '0.6'), ('shuffled_within', '0.35')]): axs[1].bar(x + (i - 1) * .27, r[k], .27, color=cc, label=k)
axs[1].set_xticks(x); axs[1].set_xticklabels([s.split('_')[0] for s in r.lexicon], rotation=40, fontsize=7); axs[1].legend(fontsize=6); axs[1].set_ylabel('held-out compound hit rate')
axs[1].set_title('Fitted rebus keys by lexicon (held-out)', fontsize=9)
fig.tight_layout(); fig.savefig(f'{F}/fig3_claim_harness.png', dpi=150); plt.close(fig)
for f in ['seg_bpe_heldout.png', 'heaps_comparanda.png', 'M77_cond_entropy.png', 'M77_zipf.png']:
    if os.path.exists(f'{ROOT}/figures/{f}'): shutil.copy(f'{ROOT}/figures/{f}', F)
print(os.listdir(F))
# Fig 4 linguistic measures
M = pd.read_csv(f'{ROOT}/outputs/structure/linguistic_measures.csv')
fig, axs = plt.subplots(1, 2, figsize=(10, 5.2), sharey=True); y = np.arange(len(M))
colr = ['C3' if s.startswith('Indus') else '0.5' if any(t in s for t in ['memoryless', 'badges', 'rigid']) else 'C0' for s in M.system]
axs[0].barh(y, M.Hcond_ratio_to_shuffle, color=colr); axs[0].set_yticks(y); axs[0].set_yticklabels(M.system, fontsize=7); axs[0].invert_yaxis()
axs[0].set_xlabel('H(next|prev) / same after global shuffle'); axs[0].set_title('Conditional entropy (Miller–Madow, 9k tokens)', fontsize=9)
axs[1].barh(y, M.r_over_R.fillna(0), color=colr); axs[1].scatter(M.r_over_R_shuffled, y, marker='|', color='k', s=80, label='within-corpus shuffle')
axs[1].axvline(0.10, ls='--', color='k', lw=.8); axs[1].set_xlabel('Sproat r/R (adjacent share of repeats)'); axs[1].legend(fontsize=7); axs[1].set_title('Repetition measure (Sproat 2014); dashed = 0.10', fontsize=9)
fig.tight_layout(); fig.savefig(f'{F}/fig4_linguistic_measures.png', dpi=150); plt.close(fig)
# Fig 5 HMM held-out gains
s3 = json.load(open(f'{ROOT}/outputs/structure/structure3_dedup.json'))
h = s3['hmm_seal_dedup']; sg = s3['segmentation_dedup']
fig, axs = plt.subplots(1, 2, figsize=(9, 3.4))
axs[0].plot(h['K'], h['gain_real'], 'o-', label='real seal texts'); axs[0].plot(h['K'], h['gain_shuffled'], 'o--', label='within-text shuffled'); axs[0].axhline(0, color='k', lw=.5)
axs[0].set_xlabel('HMM states K'); axs[0].set_ylabel('held-out log-lik gain vs K=1 (nats/token)'); axs[0].legend(fontsize=7); axs[0].set_title('Slot HMM, deduplicated seals', fontsize=9)
for n, c in [('M77_full_dedup', 'C0'), ('ICIT_full_dedup', 'C1')]:
    axs[1].plot(sg[n]['K'], sg[n]['real'], 'o-', color=c, label=n + ' real'); axs[1].plot(sg[n]['K'], sg[n]['shuffled'], 'o--', color=c, alpha=.6, label=n + ' shuffled')
axs[1].set_xlabel('BPE merges'); axs[1].set_ylabel('held-out bits/sign'); axs[1].legend(fontsize=6); axs[1].set_title('Segmentation MDL, deduplicated', fontsize=9)
fig.tight_layout(); fig.savefig(f'{F}/fig5_hmm_seg_dedup.png', dpi=150); plt.close(fig)
