"""Session 6: open, machine-readable Indus sign list built ONLY from this project's derived tables plus the
MIT-licensed mayig/CISI concordance and descriptions. No glyph images, no transcribed texts, no lipi/Yajnadevam
key values, no sound values from any proposal (only the names of proponents and our test outcomes).
Inputs: outputs/signmap/sign_map_full_public.csv (built by tools/build_public_repo.py from sign_map_full.csv),
outputs/prereg/prereg_heldout_summary.json, prereg/sign_sets_session6.json, outputs/robustness/robustness_summary.json.
Output: outputs/signlist/indus_open_signlist.{csv,json}, indus_open_signlist.schema.json"""
import os, sys, json, re
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.environ.get('SIGNMAP_PUBLIC') or f'{ROOT}/outputs/signmap/sign_map_full_public.csv'
OUT = f'{ROOT}/outputs/signlist'; os.makedirs(OUT, exist_ok=True)
sm = pd.read_csv(SRC, dtype=str, keep_default_na=False)
sets = json.load(open(f'{ROOT}/prereg/sign_sets_session6.json'))
pre = json.load(open(f'{ROOT}/outputs/prereg/prereg_heldout_summary.json'))
HSET = {'TERMINAL': 'H1', 'INITIAL': 'H2', 'PRE-TERMINAL': 'H3', 'M342': 'H4', 'M267': 'H5', 'NUMERAL': 'H7'}
def num(x):
    try: return float(x)
    except ValueError: return None
def split(x, sep=';'): return [t.strip() for t in x.split(sep) if t.strip()]
rows = []
for r in sm.itertuples():
    sch = r.scheme
    pres = []
    for k, h in HSET.items():
        if r.sign in sets[k][sch]:
            s = pre[h]; pres.append(f"{k} set: {h} {s['overall']} ({s['passed']}/{s['splits_sufficient']} pre-registered splits)")
    proponents = sorted({re.split(r'[:\[(]', c)[0].strip() for c in r.published_claims.split('||') if c.strip()})
    rows.append(dict(
        id=r.sign, scheme={'M': 'Mahadevan 1977', 'W': 'Wells/ICIT'}[sch],
        parpola_id=r.P, parpola_description_mayig=r.P_description,
        concordance_W=r.W_links if sch == 'M' else '', concordance_M=r.M_links if sch == 'W' else '',
        concordance_confidence=(r.W_link_confidence if sch == 'M' else r.M_link_confidence),
        freq_M77=num(r.freq_M77) if sch == 'M' else None, freq_ICIT=num(r.freq_ICIT) if sch == 'W' else None,
        init_share=num(r.init_share), final_share=num(r.final_share), medial_share=num(r.medial_share), solo=num(r.solo),
        structural_class=r.structural_class, class_confidence=num(r.class_confidence), class_bootstrap_stability=num(r.class_bootstrap_stability),
        icit_replication=r.icit_replication, preregistered_tests='; '.join(pres),
        recurrent_units_branching_entropy=r.BE_units, phonetic_value_status=r.phonetic_value_status,
        published_value_proposals_by=('; '.join(proponents)), sites=r.sites, object_types=(str(r.object_types).replace('nan(', 'unrecorded(') if str(r.object_types) != 'nan' else '')))
D = pd.DataFrame(rows)
assert not D.astype(str).apply(lambda c: c.str.contains('Sanskrit syllabic value', regex=False)).any().any()
D.to_csv(f'{OUT}/indus_open_signlist.csv', index=False)
meta = dict(name='Indus open sign list (derived)', version='0.1 (session 6, 29 Oct 2026, unreviewed preprint)', licence='CC BY 4.0 (our derived data); parpola_description_mayig and concordance IDs from mayig/indus-valley-script-corpus (MIT)',
            n_signs=len(D), counts_by_scheme=D.scheme.value_counts().to_dict(),
            caution='Positional classes and units are structural findings; no sign has a phonetic value supported above null. Concordance links are Carlson\'s hand matches with our model confidence; they are not verified by a human epigrapher in this project.')
json.dump(dict(meta=meta, signs=json.loads(D.to_json(orient='records'))), open(f'{OUT}/indus_open_signlist.json', 'w'), indent=1, ensure_ascii=False)
props = {c: {'type': ['number', 'null'] if D[c].dtype != object else 'string'} for c in D.columns}
json.dump({'$schema': 'https://json-schema.org/draft/2020-12/schema', 'title': 'Indus open sign list', 'type': 'object',
           'properties': {'meta': {'type': 'object'}, 'signs': {'type': 'array', 'items': {'type': 'object', 'properties': props, 'required': ['id', 'scheme']}}}},
          open(f'{OUT}/indus_open_signlist.schema.json', 'w'), indent=1)
print(meta); print(D.structural_class.value_counts().head(8)); print((D.preregistered_tests != '').sum(), 'signs with pre-registered test results')
