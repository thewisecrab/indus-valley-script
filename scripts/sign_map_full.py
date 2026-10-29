"""Session 4: full sign map, one row per sign of Mahadevan 1977 (M, 417 + damage marker M000) and per ICIT/lipi
sign id (W). It joins every session-1..4 product. Provisional classes for low-frequency signs come from
binomial tests against the corpus-wide initial/final base rates and are marked 'provisional'."""
import os, re, json, collections, sqlite3, numpy as np, pandas as pd
from scipy.stats import binomtest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); O = f'{ROOT}/outputs/signmap'
con = sqlite3.connect(f'{ROOT}/map/indus_map.sqlite')
signs = pd.read_sql('select * from signs', con)
cc = pd.read_sql('select parpola_id, scheme, other_id from sign_concordance', con)
m2p = cc[cc.scheme == 'mahadevan'].groupby('other_id').parpola_id.apply(lambda x: sorted(set(x))).to_dict()
p2m = cc[cc.scheme == 'mahadevan'].groupby('parpola_id').other_id.apply(lambda x: sorted(set(x))).to_dict()
p2w = cc[cc.scheme == 'wells'].groupby('parpola_id').other_id.apply(lambda x: sorted(set(x))).to_dict()
w2p = cc[cc.scheme == 'wells'].groupby('other_id').parpola_id.apply(lambda x: sorted(set(x))).to_dict()
p2v = cc[cc.scheme == 'parpola_variant'].groupby('parpola_id').other_id.apply(lambda x: sorted(set(x))).to_dict()
pdesc = dict(zip(signs[signs.scheme == 'parpola'].sign_id, signs[signs.scheme == 'parpola'].description))
links = pd.read_csv(f'{O}/concordance_links_scored.csv')
L = {(r.M, r.W): r for r in links.itertuples()}
hung = pd.read_csv(f'{O}/concordance_hungarian.csv'); hung = dict(zip(hung.M, hung.W_hungarian))
prop = {d['M']: d['top3'] for d in json.load(open(f'{O}/concordance_proposals_unlinked_M.json'))}
cls = pd.read_csv(f'{ROOT}/outputs/structure/sign_classes_M77.csv').set_index('sign')
gM = json.load(open(f'{ROOT}/paper/evidence/glyphs/index.json')); gW = json.load(open(f'{ROOT}/paper/evidence/glyphs_W/index.json'))
look = pd.read_csv(f'{ROOT}/outputs/comparanda/lookalikes_top3.csv')
claims = pd.read_csv(f'{ROOT}/outputs/claims/all_proposals.csv', dtype=str, keep_default_na=False)
hand = claims[claims.proponent.isin(['Yajnadevam', 'Field Cady (unsupervised optimal transport)']) == False]
loo_h = pd.read_csv(f'{ROOT}/outputs/claims/loo_hand_claims.csv'); loo_h = loo_h[loo_h.corpus == 'heldout_other_sites']
loo_p = pd.read_csv(f'{ROOT}/outputs/claims/loo_phonetic_per_sign.csv', dtype={'sign': str})
lp = {(r.key, r.sign): r for r in loo_p.itertuples()}
yk = claims[claims.proponent == 'Yajnadevam'].set_index('sign_W'); fk = claims[claims.proponent.str.startswith('Field Cady')].set_index('sign_W')
be = json.load(open(f'{ROOT}/outputs/structure/structure4_branching_entropy.json'))['top_BE_units']
# ---- M77 corpus stats (from map DB tokens + objects + sites) ----
tok = pd.read_sql("""select t.inscription_id, t.position, t.sign_id, t.is_damage_marker, o.object_type, s.name site
  from sign_tokens t join inscriptions i on t.inscription_id = i.inscription_id join objects o on i.object_id = o.object_id
  left join sites s on o.site_id = s.site_id where t.scheme = 'mahadevan'""", con)
def corpus_stats(tok):
    seqs = tok.sort_values(['inscription_id', 'position']).groupby('inscription_id')
    st = collections.defaultdict(lambda: dict(freq=0, solo=0, init=0, fin=0, med=0, left=collections.Counter(), right=collections.Counter(),
                                              site=collections.Counter(), otype=collections.Counter()))
    tot = dict(n=0, init=0, fin=0)
    for iid, g in seqs:
        # split at damage markers into clean runs
        runs, cur = [], []
        for r in g.itertuples():
            if r.is_damage_marker: 
                if cur: runs.append(cur); cur = []
            else: cur.append(r)
        if cur: runs.append(cur)
        for run in runs:
            n = len(run)
            for i, r in enumerate(run):
                d = st[r.sign_id]; d['freq'] += 1; d['site'][r.site] += 1; d['otype'][r.object_type] += 1
                if n == 1: d['solo'] += 1
                else:
                    tot['n'] += 1
                    if i == 0: d['init'] += 1; tot['init'] += 1
                    elif i == n-1: d['fin'] += 1; tot['fin'] += 1
                    else: d['med'] += 1
                if i > 0: d['left'][run[i-1].sign_id] += 1
                if i < n-1: d['right'][run[i+1].sign_id] += 1
    return st, tot
def prov_class(d, tot):
    n = d['freq'] - d['solo']
    if n < 1: return 'unresolved (solo/too rare)', np.nan, np.nan
    bi, bf = tot['init']/tot['n'], tot['fin']/tot['n']
    pi = binomtest(d['init'], n, bi, alternative='greater').pvalue; pf = binomtest(d['fin'], n, bf, alternative='greater').pvalue
    if pf < .05 and d['fin']/n > .5: c = 'TERMINAL-like (provisional)'
    elif pi < .05 and d['init']/n > .5: c = 'INITIAL-like (provisional)'
    elif n < 5: c = 'unresolved (n<5)'
    else: c = 'MEDIAL/UNSPECIFIED (provisional)'
    return c, pi, pf
top = lambda c, k=3: '; '.join(f'{a}({b})' for a, b in c.most_common(k))
stM, totM = corpus_stats(tok)
# ---- ICIT (lipi) stats, clean texts, reading order ----
lip = pd.read_csv(f'{ROOT}/data/lipi/inscriptions.csv', dtype=str, keep_default_na=False)
rows = []
for r in lip.itertuples():
    for li, part in enumerate(r.text.split('/')):
        s = list(reversed(re.findall(r'\d+', part)))
        for i, x in enumerate(s): rows.append(dict(inscription_id=f'{r.id}.{li}', position=i, sign_id='W'+x, is_damage_marker=int(x in ('000', '999')), object_type=r.type.split(':')[0], site=r.site))
stW, totW = corpus_stats(pd.DataFrame(rows))
# ---- assemble M rows ----
Ms = sorted(signs[signs.scheme == 'mahadevan'].sign_id)
out = []
for m in Ms:
    P = m2p.get(m, []); Ws = sorted({w for p in P for w in p2w.get(p, [])}); d = stM.get(m, None)
    r = dict(scheme='M', sign=m, description_M77=signs[(signs.sign_id == m)].description.iloc[0] if (signs.sign_id == m).any() else '',
             P=';'.join(P), P_description=' | '.join(str(pdesc.get(p, '')) for p in P), parpola_variants=';'.join(v for p in P for v in p2v.get(p, [])),
             allographs_M_same_P=';'.join(sorted({x for p in P for x in p2m.get(p, []) if x != m})),
             W_links=';'.join(Ws), W_link_confidence=' | '.join(f'{w}: {L[(m, w)].confidence} (model P(link)={L[(m, w)].p_link_raw:.2g})' for w in Ws if (m, w) in L),
             W_hungarian=hung.get(m, ''), W_proposed_if_unlinked='; '.join(f'{w}({p})' for w, p in prop.get(m, [])))
    if d:
        n = d['freq'] - d['solo']; c, pi, pf = prov_class(d, totM)
        r.update(freq_M77=d['freq'], solo=d['solo'], init_share=round(d['init']/n, 3) if n else np.nan, final_share=round(d['fin']/n, 3) if n else np.nan,
                 medial_share=round(d['med']/n, 3) if n else np.nan, top_left=top(d['left']), top_right=top(d['right']), sites=top(d['site']), object_types=top(d['otype']),
                 provisional_class=c, p_initial_binom=pi, p_final_binom=pf)
    else: r.update(freq_M77=0)
    if m in cls.index:
        q = cls.loc[m]; r.update(structural_class=q.cls, class_confidence=q.conf_distributional, class_bootstrap_stability=q.bootstrap_stability, icit_replication=q.icit_replication)
    else: r.update(structural_class='(not in session-3 class set: freq < threshold)', class_confidence=np.nan)
    r['glyph_crop_private'] = gM[m]['file'].replace(ROOT + '/', '') if m in gM else ''
    for s in ['linear_elamite', 'egyptian', 'cuneiform', 'brahmi', 'linear_a']:
        q = look[(look.M == m) & (look.script == s)]
        r[f'lookalike_{s}'] = f'{q.best.iloc[0]} {q.best_name.iloc[0]} ({q.score.iloc[0]})' if len(q) else ''
    hc = hand[hand.sign_M.str.contains(m)]
    r['published_claims'] = ' || '.join(f'{x.proponent}: {x.value} [{x.meaning}] ({'via Parpola ' if 'reporting' in x.citation else ''}{(re.search(r'[12][09]\d\d', x.citation) or re.search('', '')).group(0) or x.citation[:30]}: {x.page}; sign mapping {x.sign_mapping_confidence})' for x in hc.itertuples())
    lh = loo_h[loo_h.claim.str.contains(m)]
    r['claim_tests_heldout'] = ' || '.join(f'{x.claim}: obs {x.observed} vs null {x.null_mean}, p={x.p:.3g}, q={x.q_BH:.3g}' for x in lh.itertuples())
    r['BE_units'] = '; '.join(f'{u}({n})' for u, n in be if m in u.split('+'))
    # phonetic keys via 1:1 W link only
    w1 = Ws[0] if len(Ws) == 1 else ''
    if w1:
        k = w1[1:]
        if 'W'+k in yk.index: r['yajnadevam_value_via_W'] = yk.loc['W'+k].value; 
        if ('Yajnadevam', k) in lp: r['yajnadevam_LOO_p'] = lp[('Yajnadevam', k)].p_alt
        if 'W'+k in fk.index: r['fieldcady_value_via_W'] = fk.loc['W'+k].value
        if ('FieldCady', k) in lp: r['fieldcady_LOO_p'] = lp[('FieldCady', k)].p_alt
    r['phonetic_value_status'] = 'no value beats null (session 4 LOO); see claims'
    out.append(r)
MM = pd.DataFrame(out)
# ---- W rows ----
x = pd.read_csv(f'{ROOT}/data/lipi/xlits.csv', dtype=str, keep_default_na=False)
canon = dict(zip('W'+x.sign, x.canonical))
Wset = sorted(set(signs[signs.scheme == 'icit_wells'].sign_id) | set(stW) | set(canon))
wout = []
for w in Wset:
    if w in ('W000', 'W999'): continue
    P = w2p.get(w, []); Mlinks = sorted({m for p in P for m in p2m.get(p, [])}); d = stW.get(w)
    r = dict(scheme='W', sign=w, P=';'.join(P), P_description=' | '.join(str(pdesc.get(p, '')) for p in P), M_links=';'.join(Mlinks),
             M_link_confidence=' | '.join(f'{m}: {L[(m, w)].confidence}' for m in Mlinks if (m, w) in L),
             allographs_W_same_P=';'.join(sorted({y for p in P for y in p2w.get(p, []) if y != w})),
             lipi_canonical_decomposition_Yajnadevam=canon.get(w, ''))
    if d:
        n = d['freq'] - d['solo']; c, pi, pf = prov_class(d, totW)
        r.update(freq_ICIT=d['freq'], solo=d['solo'], init_share=round(d['init']/n, 3) if n else np.nan, final_share=round(d['fin']/n, 3) if n else np.nan,
                 top_left=top(d['left']), top_right=top(d['right']), sites=top(d['site']), object_types=top(d['otype']), provisional_class=c, p_initial_binom=pi, p_final_binom=pf)
    else: r.update(freq_ICIT=0)
    k = w[1:]
    if w in yk.index: r['yajnadevam_value'] = yk.loc[w].value
    if ('Yajnadevam', k) in lp: r['yajnadevam_LOO_p'] = lp[('Yajnadevam', k)].p_alt; r['yajnadevam_LOO_q'] = lp[('Yajnadevam', k)].q_alt
    if w in fk.index: r['fieldcady_value'] = fk.loc[w].value
    if ('FieldCady', k) in lp: r['fieldcady_LOO_p'] = lp[('FieldCady', k)].p_alt
    r['glyph_render_private'] = gW[w]['file'].replace(ROOT + '/', '') if w in gW else ''
    wout.append(r)
WW = pd.DataFrame(wout)
FULL = pd.concat([MM, WW], ignore_index=True)
FULL.to_csv(f'{O}/sign_map_full.csv', index=False)
summ = dict(M_rows=len(MM), M_attested_in_M77=int((MM.freq_M77 > 0).sum()), M_with_W_link=int((MM.W_links != '').sum()),
            M_with_strong_or_supported_link=int(MM.W_link_confidence.fillna('').str.contains('strong|supported').sum()),
            M_with_session3_class=int(MM.class_confidence.notna().sum()), M_glyph=int((MM.glyph_crop_private != '').sum()),
            M_with_published_claim=int((MM.published_claims != '').sum()),
            W_rows=len(WW), W_attested_ICIT=int((WW.freq_ICIT > 0).sum()), W_with_M_link=int((WW.M_links != '').sum()),
            provisional_class_counts_M=MM.provisional_class.value_counts().to_dict(), provisional_class_counts_W=WW.provisional_class.value_counts().to_dict())
json.dump(summ, open(f'{O}/sign_map_full_summary.json', 'w'), indent=1, default=str); print(json.dumps(summ, indent=1, default=str))
