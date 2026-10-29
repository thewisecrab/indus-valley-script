"""Anchor analyses (session 2) on ICIT-derived lipi inscriptions.csv (private research use) + Sproat weights.xml (GPL-3).
1 numerals  2 motif/site/type correlations  3 West-Asian/Gulf vs Indus-proper  4 duplicates & moulded tablets"""
import re, json, random, collections, os, math
import pandas as pd, numpy as np
import xml.etree.ElementTree as ET
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = f'{ROOT}/outputs/anchors'
d = pd.read_csv(f'{ROOT}/data/lipi/inscriptions.csv', dtype=str, keep_default_na=False)
d['type0'] = d.type.str.split(':').str[0]
def segments(text):
    """reading-order segments split at damage (000, 999) and line/side breaks '/'; ICIT stored visual order -> reversed"""
    segs = []
    for part in text.split('/'):
        s = list(reversed(re.findall(r'\d+', part))); cur = []
        for x in s:
            if x in ('000', '999'): 
                if cur: segs.append(cur); cur = []
            else: cur.append(x)
        if cur: segs.append(cur)
    return segs[::-1] if segs else []
d['segs'] = d.text.apply(segments)
d['signs'] = d.segs.apply(lambda ss: [x for s in ss for x in s])
d['damaged'] = d.text.str.contains(r'000|999|\[|\]')
R = {}
rng = np.random.default_rng(0)

# ---------- 1 numerals ----------
SHORT = {'001':1,'002':2,'003':3,'004':4,'005':5,'006':6,'007':7,'014':4,'015':5,'016':6,'017':7,'018':8,'019':9,'020':10}
LONG = {'031':1,'032':2,'033':3,'034':4,'035':5}
NUM = {**SHORT, **LONG}
tok = collections.Counter(x for s in d.signs for x in s)
num_tokens = {k: tok.get(k, 0) for k in NUM}
val_short = collections.Counter(); val_long = collections.Counter()
for k, v in SHORT.items(): val_short[v] += tok.get(k, 0)
for k, v in LONG.items(): val_long[v] += tok.get(k, 0)
# what follows a short-stroke numeral in reading order (counted item)?
nxt = collections.Counter(); prv = collections.Counter(); pos = collections.Counter()
for ss in d.segs:
    for s in ss:
        for i, x in enumerate(s):
            if x in SHORT:
                if i + 1 < len(s): nxt[s[i+1]] += 1
                else: nxt['<END>'] += 1
                if i > 0: prv[s[i-1]] += 1
                else: prv['<START>'] += 1
                pos['initial' if i == 0 else 'final' if i == len(s)-1 else 'medial'] += 1
by_type = d.assign(hasnum=d.signs.apply(lambda s: any(x in SHORT for x in s))).groupby('type0').hasnum.agg(['mean','sum','count'])
# weights
W = ET.parse(f'{ROOT}/data/weights/weights.xml').getroot()
wv = []
for w in W.findall('weight'):
    try: wv.append((float(w.findtext('value')), w.findtext('provenance'), (w.findtext('shape') or '')))
    except: pass
unit = 0.8570  # Hemmy 1938 calculated unit (g), stated in Hemmy 1938 conclusion (data/weights/Hemmy-1938...pdf)
ratios = [1, 2, 8/3, 4, 8, 16, 32, 64, 160, 200, 320, 640, 1600, 3200, 6400, 8000, 12800]
cls = collections.Counter(); unassigned = 0
for v, p, sh in wv:
    r = v/unit; best = min(ratios, key=lambda q: abs(math.log(r/q)))
    if abs(math.log(r/best)) < math.log(1.15): cls[best] += 1
    else: unassigned += 1
R['numerals'] = dict(short_stroke_value_tokens=dict(sorted(val_short.items())), long_stroke_value_tokens=dict(sorted(val_long.items())),
    short_positions=dict(pos), next_sign_after_short_numeral_top=nxt.most_common(15), prev_sign_before_short_numeral_top=prv.most_common(10),
    share_texts_with_short_numeral_by_type=by_type.round(3).reset_index().to_dict('records'),
    weights_n=len(wv), weights_by_ratio_class_within15pct={str(round(k, 2)): v for k, v in sorted(cls.items())}, weights_unassigned=unassigned)
# simple binary-preference test: among short-stroke values 1..10, share of powers of two vs others relative to a smooth (log-linear) fit
vals = np.array([val_short.get(i, 0) for i in range(1, 11)], float)
x = np.arange(1, 11); ok = vals > 0
coef = np.polyfit(x[ok], np.log(vals[ok]), 1); pred = np.exp(np.polyval(coef, x))
R['numerals']['short_value_obs_vs_loglinear'] = [dict(value=int(i), obs=int(o), fit=round(float(p), 1), ratio=round(float(o/p), 2)) for i, o, p in zip(x, vals, pred)]

# ---------- 2 motif / site / type correlations (Indus-proper, seals with motif) ----------
def enrich(groups, min_tok=20, n_perm=500, label=''):
    """groups: Series of group label per row (index aligned with d). log-odds ratio with informative Dirichlet prior (Monroe et al. 2008)
    + permutation p-value for top signs."""
    rows = d.loc[groups.index]; g = groups
    counts = collections.defaultdict(collections.Counter)
    for lab, ss in zip(g, rows.signs):
        for x in set(ss): counts[lab][x] += 1   # presence per text
    ntext = g.value_counts().to_dict()
    allc = collections.Counter(); [allc.update(c) for c in counts.values()]
    N = len(g); out = []
    for lab, c in counts.items():
        for x, k in c.items():
            if allc[x] < min_tok: continue
            a = k + 0.5; b = ntext[lab] - k + 0.5; c2 = allc[x] - k + 0.5; dd = (N - ntext[lab]) - (allc[x] - k) + 0.5
            lor = math.log(a/b) - math.log(c2/dd); se = math.sqrt(1/a + 1/b + 1/c2 + 1/dd)
            out.append(dict(group=lab, sign=x, k=k, n_group=ntext[lab], sign_total=allc[x], lor=lor, z=lor/se))
    E = pd.DataFrame(out)
    # permutation null for max |z| within each group
    gl = g.values.copy(); sets = [set(s) for s in rows.signs]; maxz = collections.defaultdict(list)
    signs_ok = [x for x in allc if allc[x] >= min_tok]
    pres = {x: np.array([x in s for s in sets]) for x in signs_ok}
    for _ in range(n_perm):
        perm = rng.permutation(gl)
        for lab in ntext:
            m = perm == lab; n1 = m.sum(); best = 0
            for x in signs_ok:
                k = pres[x][m].sum(); a = k+.5; b = n1-k+.5; c2 = allc[x]-k+.5; dd = (N-n1)-(allc[x]-k)+.5
                z = (math.log(a/b)-math.log(c2/dd))/math.sqrt(1/a+1/b+1/c2+1/dd); best = max(best, abs(z))
            maxz[lab].append(best)
    E['p_maxperm'] = [ (np.sum(np.array(maxz[r.group]) >= abs(r.z))+1)/(n_perm+1) for r in E.itertuples()]
    E.sort_values('z', ascending=False).to_csv(f'{OUT}/enrich_{label}.csv', index=False)
    return E

seals = d[(d.type0 == 'SEAL') & ~d.symbol.isin(['None', '-', '']) & d.region.isin(['Inter-Riverine','Lower Indus','Gujarat/Kutch','Eastern Headwaters','Upper Indus'])].copy()
seals['motif'] = seals.symbol.str.split(':').str[0].replace({'Bull':'Bull1'})
top_m = seals.motif.value_counts(); keep = top_m[top_m >= 25].index
sm = seals[seals.motif.isin(keep)]
E = enrich(sm.motif, label='motif_seals', n_perm=300)
R['motif'] = dict(n_seals=len(sm), motifs=sm.motif.value_counts().to_dict(),
    significant_p_lt_0_05=E[(E.p_maxperm < 0.05)].sort_values('z', ascending=False)[['group','sign','k','n_group','sign_total','lor','z','p_maxperm']].round(3).to_dict('records'),
    top_z_per_motif=E.sort_values('z', ascending=False).groupby('group').head(3)[['group','sign','k','n_group','sign_total','z','p_maxperm']].round(3).to_dict('records'))
# jar sign 740 rate by motif
R['motif']['jar740_rate_by_motif'] = sm.groupby('motif').signs.apply(lambda s: round(float(np.mean(['740' in x for x in s])), 3)).to_dict()
# site
ms = d[d.site.isin(['Mohenjo-daro', 'Harappa']) & (d.signs.str.len() > 0) & (d.type0 == 'SEAL')]
if len(ms) < 100:
    ms = d[d.site.str.contains('Mohenjo|Harappa', regex=True) & (d.signs.str.len() > 0)]
R['site_values'] = d.site.value_counts().head(8).to_dict()
ms = ms.assign(site2=ms.site.str.replace(r'.*Mohenjo.*', 'Mohenjo-daro', regex=True).str.replace(r'.*Harappa.*', 'Harappa', regex=True))
E2 = enrich(ms.site2, label='site_MD_vs_HP_seals_only', n_perm=200)
R['site'] = dict(n=ms.site2.value_counts().to_dict(),
    significant_p_lt_0_01=E2[(E2.p_maxperm < 0.01)].sort_values('z', ascending=False)[['group','sign','k','n_group','sign_total','lor','z','p_maxperm']].round(3).head(30).to_dict('records'))
# object type x length
R['type_length'] = d[~d.damaged & (d.signs.str.len() > 0)].groupby('type').signs.apply(lambda s: s.str.len().mean()).round(2).sort_values().to_dict()

# ---------- 3 West Asian / Gulf vs Indus proper ----------
GULF = {'Failaka','Qala\'at al-Bahrain','Saar','Karzakan','Janabiyah','Dilmun','Hajar','Ra\'s al-Junayz','Salut','Kalba'}
MESO_IRAN = {'Kish','Nippur','Tell Umma','Tello','Girsu','Ur','Susa','Luristan','Tepe Yahya','Murda Sang'}
CAS = {'Altyn Depe','Gonur Depe'}
d['zone'] = np.where(d.site.isin(GULF), 'Gulf', np.where(d.site.isin(MESO_IRAN), 'Mesopotamia/Iran', np.where(d.site.isin(CAS), 'Central Asia', 'Indus+borderlands')))
west = d[d.zone != 'Indus+borderlands']
indus = d[(d.zone == 'Indus+borderlands') & (d.signs.str.len() > 0)]
ib = collections.Counter(); iu = collections.Counter()
for ss in indus.segs:
    for s in ss:
        iu.update(s); ib.update(zip(s, s[1:]))
def bigram_attest(segs_list):
    tot = att = 0
    for ss in segs_list:
        for s in ss:
            for b in zip(s, s[1:]): tot += 1; att += ib[b] > 0
    return tot, att
wt, wa = bigram_attest(west.segs)
# null: random Indus texts matched on segment-length profile, attestation measured against the Indus corpus minus the sampled texts
lens = [len(s) for ss in west.segs for s in ss if len(s) >= 2]
pool = [s for ss in indus.segs for s in ss]
random.seed(0)   # session 7: this null was unseeded (different on every run)
null = []
for _ in range(300):
    tot = att = 0
    for L in lens:
        cand = [s for s in random.sample(pool, 400) if len(s) == L] or [s for s in pool if len(s) == L]
        s = random.choice(cand)
        for b in zip(s, s[1:]): tot += 1; att += (ib[b] - 1) > 0   # leave-one-out
    null.append(att/max(tot, 1))
gulf_signs = collections.Counter(x for s in west.signs for x in s)
R['west'] = dict(n_objects=west.zone.value_counts().to_dict(), n_with_signs=int((west.signs.str.len() > 0).sum()),
    types={'|'.join(k): v for k, v in west.groupby('zone').type.value_counts().to_dict().items()}, motifs={'|'.join(k): v for k, v in west.groupby('zone').symbol.value_counts().to_dict().items()},
    bigrams_total=wt, bigrams_attested_in_indus=wa, attested_share=round(wa/max(wt,1), 3),
    null_attested_share_mean=round(float(np.mean(null)), 3), null_2_5pct=round(float(np.percentile(null, 2.5)), 3), null_97_5pct=round(float(np.percentile(null, 97.5)), 3),
    signs_unattested_in_indus=[x for x in gulf_signs if iu[x] == 0],
    jar740_share_tokens_west=round(gulf_signs['740']/max(1, sum(gulf_signs.values())), 3),
    jar740_share_tokens_indus=round(iu['740']/sum(iu.values()), 3),
    final_sign_west=collections.Counter(s[-1] for ss in west.segs for s in ss[-1:]).most_common(8),
    sign_090_091_west=gulf_signs['090'] + gulf_signs['091'], sign_090_091_indus=iu['090'] + iu['091'],
    texts=west[['site','type','symbol','text']].to_dict('records'))
# circular SEAL:C share
R['west']['seal_shape_C_share'] = {z: round(float((g.type == 'SEAL:C').mean()), 3) for z, g in d.groupby('zone')}

# ---------- 4 duplicates & moulded tablets ----------
full = d[~d.damaged & (d.signs.str.len() >= 2)]
key = full.signs.apply(lambda s: '-'.join(s))
grp = full.assign(k=key).groupby('k')
dup_sets = grp.filter(lambda g: len(g) > 1)
by_t = full.assign(k=key).assign(dup=lambda x: x.k.map(x.k.value_counts()) > 1).groupby('type').dup.agg(['mean','sum','count'])
multi_site = grp.site.nunique(); multi_site = multi_site[multi_site > 1]
moulded = full[full.type == 'TAB:B']
mk = moulded.signs.apply(lambda s: '-'.join(s)).value_counts()
R['duplicates'] = dict(n_complete_texts_len2plus=len(full), n_distinct=int(key.nunique()), n_in_duplicate_sets=len(dup_sets),
    n_duplicate_sets=int((key.value_counts() > 1).sum()),
    dup_share_by_type=by_t[by_t['count'] >= 20].round(3).reset_index().to_dict('records'),
    texts_shared_across_sites=int(len(multi_site)), examples_across_sites=[dict(text=k, sites=sorted(grp.get_group(k).site.unique())) for k in multi_site.index[:15]],
    TAB_B_n=len(moulded), TAB_B_distinct=int(len(mk)), TAB_B_largest_sets=mk.head(10).to_dict(),
    TAB_B_sites=moulded.site.value_counts().head(5).to_dict())
# do moulded-tablet texts also occur on seals?
seal_texts = set(full[full.type0 == 'SEAL'].signs.apply(lambda s: '-'.join(s)))
R['duplicates']['TAB_B_distinct_texts_also_on_seals'] = int(sum(1 for k in mk.index if k in seal_texts))
json.dump(R, open(f'{OUT}/anchors_summary.json', 'w'), indent=1, default=str)
print(json.dumps({k: (v if k != 'west' else {kk: vv for kk, vv in v.items() if kk != 'texts'}) for k, v in R.items()}, indent=1, default=str)[:14000])
