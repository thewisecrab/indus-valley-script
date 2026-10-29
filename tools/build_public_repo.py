"""Session 5: assemble repo_public/ from the private project, including ONLY publishable material.
Restricted inputs (M77 export, lipi/ICIT texts, M77/Parpola OCR, plate crops, SK-font renders, the SQLite map)
are never copied; tables carrying Yajnadevam/lipi sign values are redacted. See DATA_POLICY.md."""
import os, re, shutil, glob, json, subprocess
import pandas as pd
SRC = '/workspace/indus'; DST = f'{SRC}/repo_public'

def cp(rel, dst_rel=None):
    s = f'{SRC}/{rel}'; d = f'{DST}/{dst_rel or rel}'
    os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copy2(s, d)

# ---------- code ----------
for f in sorted(glob.glob(f'{SRC}/scripts/*.py')):
    cp(os.path.relpath(f, SRC))
cp('tools/build_public_repo.py')

# ---------- outputs (derived statistics only) ----------
KEEP = []
for corp in ['M77', 'icitweb', 'cisi_mayig', 'TOY']:
    for f in ['cond_entropy_curve.csv', 'positional.csv', 'sign_frequency.csv', 'ngrams_2.csv']:
        KEEP.append(f'outputs/{corp}/{f}')
KEEP += [f'outputs/TOY/{f}' for f in ['ngrams_3.csv', 'ngrams_4.csv', 'segments_branching_entropy.csv']]  # toy corpus is ours
KEEP += sorted(os.path.relpath(f, SRC) for f in glob.glob(f'{SRC}/outputs/anchors/*'))
KEEP += [f'outputs/claims/{f}' for f in ['A_summary.json', 'B_fixed_key_segmentability.json', 'C_fitted_keys.csv', 'C_summary.csv',
         'D_free_parameters.json', 'E_vidyut_parse.json', 'F_parpola_compounds.json', 'F_rebus_fitted.csv', 'F_rebus_summary.csv',
         'loo_fitted_noise_keys.json', 'loo_hand_claims.csv', 'loo_phonetic_per_sign.csv', 'loo_phonetic_all_conditions.csv',
         'loo_phonetic_summary.json', 'mahadevan_positional.json', 'parpola_num_fish.json']]
KEEP += ['outputs/comparanda/lookalike_tests.json', 'outputs/comparanda/lookalikes_top3.csv']
KEEP += sorted(os.path.relpath(f, SRC) for f in glob.glob(f'{SRC}/outputs/compare/*'))
KEEP += ['outputs/concordance_crosscheck.csv', 'outputs/icitweb_sites.csv', 'outputs/summary.json', 'outputs/summary_toy.json']
KEEP += [f'outputs/signmap/{f}' for f in ['concordance_accuracy.json', 'concordance_hungarian.csv', 'concordance_links_scored.csv',
         'concordance_proposals_unlinked_M.json', 'handcheck_pairs.csv', 'm_to_w_top10.json', 'm_w_pair_probs.csv.gz',
         'concordance_cv_rows.csv.gz', 'sign_map_full_summary.json']]
KEEP += [f'outputs/structure/{f}' for f in ['classes_summary.json', 'linguistic_measures.csv', 'linguistic_v2_and_slots.json',
         'nsb_entropy.json', 'sign_classes_M77.csv', 'structure2_summary.json', 'structure3_dedup.json', 'structure4_branching_entropy.json']]
for k in KEEP: cp(k)
# redact complete ICIT/lipi texts of >= 4 signs quoted as examples inside anchor JSONs
TXT = re.compile(r'[+\]\[]?\d{3}(?:-\d{3}){3,}[+\]\[]?')
for k in ['outputs/anchors/anchors_summary.json', 'outputs/anchors/w700_vs_weights.json']:
    t = open(f'{DST}/{k}').read()
    t = TXT.sub(lambda m: f'[ICIT text of {m.group(0).count("-") + 1} signs redacted]', t)
    open(f'{DST}/{k}', 'w').write(t)

# redacted tables: drop Yajnadevam/lipi key values (lipi has no licence) and private glyph paths
YV = re.compile(r'Sanskrit syllabic value\(s\)[^|]*?— Yajnadevam/lipi')
st = pd.read_csv(f'{SRC}/outputs/structure/sign_table.csv', dtype=str, keep_default_na=False)
st['literature_values'] = st.literature_values.str.replace(YV, 'Yajnadevam/lipi syllabic key value (not redistributed; see DATA_POLICY.md)', regex=True)
st.to_csv(f'{DST}/outputs/structure/sign_table_public.csv', index=False)
sm = pd.read_csv(f'{SRC}/outputs/signmap/sign_map_full.csv', dtype=str, keep_default_na=False)
sm = sm.drop(columns=['glyph_crop_private', 'glyph_render_private', 'yajnadevam_value_via_W', 'yajnadevam_value',
                      'lipi_canonical_decomposition_Yajnadevam'])
sm.to_csv(f'{DST}/outputs/signmap/sign_map_full_public.csv', index=False)
hp = pd.read_csv(f'{DST}/outputs/signmap/handcheck_pairs.csv', dtype=str, keep_default_na=False).rename(columns=lambda c: 'visual_judgement' if c.endswith('_visual_judgement') else c)
hp.to_csv(f'{DST}/outputs/signmap/handcheck_pairs.csv', index=False)
ap = pd.read_csv(f'{SRC}/outputs/claims/all_proposals.csv', dtype=str, keep_default_na=False)
mask = ap.proponent == 'Yajnadevam'
ap.loc[mask, 'value'] = '[redacted: lipi has no licence]'; ap.loc[mask, 'meaning'] = ''
ap.to_csv(f'{DST}/outputs/claims/all_proposals_public.csv', index=False)

# ---------- open data ----------
os.makedirs(f'{DST}/data_open/images/met', exist_ok=True); os.makedirs(f'{DST}/data_open/images/commons', exist_ok=True)
met = pd.read_csv(f'{SRC}/data/images/met/manifest.csv', dtype=str, keep_default_na=False)
for f in met.local_file:
    if f and os.path.exists(f'{SRC}/data/images/met/{f}'): shutil.copy2(f'{SRC}/data/images/met/{f}', f'{DST}/data_open/images/met/{f}')
met.to_csv(f'{DST}/data_open/images/met/manifest.csv', index=False)
com = pd.read_csv(f'{SRC}/data/images/commons/manifest.csv', dtype=str, keep_default_na=False)
OKLIC = {'CC0', 'Public domain', 'CC BY 3.0', 'CC BY 4.0', 'CC BY-SA 2.0', 'CC BY-SA 3.0', 'CC BY-SA 4.0'}
rows = []
for r in com.itertuples():
    if r.downloaded != 'yes' or r.license not in OKLIC or not os.path.exists(f'{SRC}/data/images/commons/{r.local_file}'): continue
    clean = re.sub(r'[^A-Za-z0-9._-]', '_', r.title.replace('File:', ''))
    shutil.copy2(f'{SRC}/data/images/commons/{r.local_file}', f'{DST}/data_open/images/commons/{clean}')
    artist = re.sub(r'<[^>]+>', '', r.artist).strip() or 'unknown'
    rows.append(dict(file=clean, title=r.title, author=artist, credit=re.sub(r'<[^>]+>', '', r.credit).strip(), license=r.license,
                     license_url=r.license_url, source_page=r.page))
pd.DataFrame(rows).to_csv(f'{DST}/data_open/images/commons/manifest.csv', index=False)
with open(f'{DST}/data_open/images/commons/ATTRIBUTION.md', 'w') as fh:
    fh.write('# Wikimedia Commons images: attribution\n\nEach file keeps its own licence (shown below). These files are NOT covered by the repository\'s MIT or CC BY 4.0 grants. CC BY-SA files must be shared under the same licence when adapted.\n\n| File | Author | Licence | Source |\n|---|---|---|---|\n')
    for r in rows: fh.write(f"| `{r['file']}` | {r['author'].replace('|', '/')} | [{r['license']}]({r['license_url']}) | {r['source_page']} |\n")
cp('data/toy/toy_corpus.csv', 'data_open/toy/toy_corpus.csv')
print('commons images:', len(rows), 'met images:', len(os.listdir(f"{DST}/data_open/images/met")) - 1)

# ---------- paper (public variant) ----------
body = open(f'{SRC}/paper/manuscript_body.md').read()
body = re.sub(r'!\[Fig\. 7\.[^\n]*\n', '*Fig. 7 (hand check of 40 concordance links, M77 crops beside SK-font renders) is omitted from the public version: both image sources are under copyright. The per-pair judgements are in `outputs/signmap/handcheck_pairs.csv`.*\n', body)
body = re.sub(r'!\[Fig\. 8\.[^\n]*\n', '*Fig. 8 (top visual look-alikes, M77 crops beside foreign glyphs) is omitted from the public version because the M77 crops are under copyright. Scores are in `outputs/comparanda/lookalikes_top3.csv`.*\n', body)
body = re.sub(r'^author: .*$', 'author: "Indus Valley Script project contributors"\nsubtitle: "UNREVIEWED PREPRINT: working draft, not peer-reviewed (29 October 2026; public version with restricted figures and lipi key values removed)"', body, count=1, flags=re.M)
body = body.replace('# Abstract', '<div class="preprint-banner">UNREVIEWED PREPRINT / WORKING DRAFT. This manuscript has not been peer-reviewed. Results are provisional and may change.</div>\n\n# Abstract', 1)
body = body.replace('- **Owner requirements.**', '- **Scope of the original brief.**')
assert 'prepared by' not in body
body = body.replace('`outputs/signmap/sign_map_full.csv`', '`outputs/signmap/sign_map_full_public.csv`')
assert 'fig7_' not in body and 'fig8_' not in body
tail = open(f'{SRC}/paper/appendix_tail.md').read()
tail = YV.sub('Yajnadevam/lipi syllabic key value (not redistributed)', tail)
tail = tail.replace('sign_map_full.csv', 'sign_map_full_public.csv')
os.makedirs(f'{DST}/paper/figures', exist_ok=True)
open(f'{DST}/paper/manuscript_public.md', 'w').write(body + tail)
for fig in re.findall(r'\]\((figures/[^)]+)\)', body + tail):
    cp(f'paper/{fig}')
cp('paper/style.css'); cp('paper/appendix_claims.md')
with open(f'{DST}/paper/style.css', 'a') as fh:
    fh.write('''
/* public preprint labelling */
.preprint-banner { border: 2px solid #b00; color: #b00; font-weight: bold; padding: 6px 10px; margin: 8px 0 16px; text-align: center; }
p.subtitle { color: #b00; font-weight: bold; }
body::before { content: "UNREVIEWED PREPRINT - WORKING DRAFT - NOT PEER-REVIEWED"; position: fixed; top: -11mm; left: 0; right: 0;
  text-align: center; font-size: 8pt; color: #b00; letter-spacing: 0.5px; }
body::after { content: "PREPRINT"; position: fixed; top: 45%; left: 0; right: 0; text-align: center; font-size: 110pt;
  color: rgba(180, 0, 0, 0.07); transform: rotate(-35deg); z-index: -1; pointer-events: none; }
@page { margin-top: 18mm; }
''')

# public data-availability section
md = open(f'{DST}/paper/manuscript_public.md').read()
start = md.index('# 7. Data and code availability'); end = md.index('# References')
md = md[:start] + """# 7. Data and code availability

This public version ships with code (MIT), our text and derived result tables (CC BY 4.0), and a small set of openly licensed images. It does **not** include the input corpora:

- the M77 export: ASI copyright, extracted via a logged-in session;
- the *lipi*/ICIT-derived texts and sign key: no licence;
- OCR of Mahadevan 1977 and Parpola 1994;
- plate crops and SK-font renders.

`scripts/fetch_data.sh` downloads the openly hosted inputs and explains how to obtain the rest. Users must check each upstream licence themselves. `DATA_POLICY.md` lists every exclusion and the reason for it. Figures 7 and 8 are omitted. Yajnadevam/*lipi* key values are redacted from the tables; the per-sign test statistics are kept.

""" + md[end:]
open(f'{DST}/paper/manuscript_public.md', 'w').write(md)

# docs, licences, fetch + check scripts
D = f'{SRC}/tools/repo_docs'
os.makedirs(f'{DST}/.github', exist_ok=True)
shutil.copy2(f'{D}/README.md', f'{DST}/.github/README.md')  # GitHub renders .github/README.md first
shutil.copy2(f'{D}/README_root_remote.md', f'{DST}/README.md')  # byte-identical to the remote's initial README (clean merge)
for f in ['LICENSE', 'LICENSE-SCOPE.md', 'LICENSE-CC-BY-4.0.txt', 'CITATION.cff', 'DATA_POLICY.md', 'REPRODUCIBILITY.md', 'requirements.txt', '.gitignore']:
    shutil.copy2(f'{D}/{f}', f'{DST}/{f}')
shutil.copy2(f'{D}/data_open_README.md', f'{DST}/data_open/README.md')
shutil.copy2(f'{D}/fetch_data.sh', f'{DST}/scripts/fetch_data.sh')
shutil.copy2(f'{D}/check_public.py', f'{DST}/tools/check_public.py')
print('repo assembled at', DST)
