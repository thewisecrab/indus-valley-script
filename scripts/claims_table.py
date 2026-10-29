"""Session 4: build outputs/claims/all_proposals.csv. Every row comes from a source opened in sessions 2-4.
The page refs are book pages (Parpola 1994 scan offsets are verified in LOG.md, session 4)."""
import pandas as pd, sqlite3, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P94 = 'Parpola, A. 1994. Deciphering the Indus Script. Cambridge UP (Internet Archive scan, data/books)'
P94r = P94 + ' (reporting another author)'
M15 = 'Mahadevan, I. 2015. Interpreting the Indus Script: The Dravidian Solution. Convocation address, Dravidian University, Kuppam, 26 Feb 2015 (booklet, unpaginated; data/papers/Mahadevan_Indus-Dravidian_2015.pdf)'
MU19 = 'Mukhopadhyay, B. A. 2019. Interrogating Indus inscriptions to unravel their mechanisms of meaning conveyance. Palgrave Communications 5:73'
W15 = 'Wells, B. K. 2015. The Archaeology and Epigraphy of Indus Writing. Archaeopress (publisher sample: front matter/TOC only)'
R = []
def add(M, value, meaning, lang, prop, cite, page, ctype, basis, mconf, note=''):
    R.append(dict(sign_M=M, value=value, meaning=meaning, language=lang, proponent=prop, citation=cite, page=page,
                  claim_type=ctype, sign_mapping_basis=basis, sign_mapping_confidence=mconf, note=note))
# --- Parpola 1994 (own proposals) ---
add('M059', 'mīn', "'fish' = homophone 'star'", 'Proto-Dravidian', 'Parpola', P94, '181; 187-188', 'logo-rebus', 'Parpola names plain fish sign; M059 = plain fish in M77', 'high')
add('M108|M109+M059', 'aṟu-mīn', "'six stars' = Pleiades", 'Proto-Dravidian', 'Parpola (after Heras)', P94, '194', 'sequence', "numeral 6 = M108/M109", 'high')
add('M102|M103+M059', 'mū-m-mīn', "'three stars'", 'Proto-Dravidian', 'Parpola', P94, '194', 'sequence', 'numeral 3', 'high')
add('M110|M112+M059', 'eḻu-mīn', "'seven stars' = Ursa Major", 'Proto-Dravidian', 'Parpola', P94, '194', 'sequence', 'numeral 7', 'high')
add('M065', 'mēy-mīn', "'roofed fish' = 'black star' = Saturn", 'Proto-Dravidian', 'Parpola', P94, '197', 'logo-rebus', 'roof-over-fish sign; M065 in M77', 'medium')
add('M403', 'muruku', "ring/bangle = 'Muruku' (god)", 'Proto-Dravidian', 'Parpola', P94, '276 (Fig. 15.2 no. 11)', 'logo-rebus', 'visual: glyphsim top-1 of the Fig. 15.2 crop', 'low')
add('M103?+M403', 'cūl + muruku', "hearth of three stones + bangle", 'Proto-Dravidian', 'Parpola', P94, '276 (Fig. 15.2 no. 12)', 'sequence', 'three strokes read as hearth; visual', 'low')
add('M403+M087', 'Muruku-Vēḷ', 'bangle + intermediate space', 'Proto-Dravidian', 'Parpola', P94, '276 (Fig. 15.2 no. 14)', 'sequence', 'visual', 'low')
add('M087', 'vēḷ(i)', "'intermediate space' (two long strokes) / 'white'", 'Proto-Dravidian', 'Parpola', P94, '276-277 (Fig. 15.2 nos. 14-15)', 'logo-rebus', 'two long vertical strokes = M087', 'medium')
add('M087+M059', 'vēḷ-mīn', "'white star' = Venus", 'Proto-Dravidian', 'Parpola', P94, '277 (Fig. 15.2 no. 15)', 'sequence', 'M087 + plain fish', 'medium')
add('fig-tree sign (unmapped)+M059', 'vaṭa-mīn', "'banyan star' = North Star", 'Proto-Dravidian', 'Parpola', P94, '277 (Fig. 15.2 no. 16)', 'sequence', 'fig sign not mapped to an M number', 'none')
add('fig-tree sign+M087', 'vaṭa + vēḷ(i)', '', 'Proto-Dravidian', 'Parpola', P94, '277 (Fig. 15.2 no. 17)', 'sequence', 'unmapped', 'none')
add('M104+fig-tree sign', 'nāl + vaṭa', "'hanging rope'", 'Proto-Dravidian', 'Parpola', P94, '277 (Fig. 15.2 no. 18)', 'sequence', 'unmapped fig sign', 'none')
add('crab sign (unmapped)', 'kōḷ', "'grasper' = 'planet'", 'Proto-Dravidian', 'Parpola', P94, '277 (Fig. 15.2 nos. 19-21)', 'logo-rebus', 'unmapped', 'none')
add('M328', '(no phonetic value given)', 'pot U', 'Proto-Dravidian', 'Parpola', P94, '277 (Fig. 15.2 no. 22)', 'other', 'visual', 'medium')
add('M001', 'āḷ / āṇ', "'man; servant'", 'Proto-Dravidian', 'Parpola', P94, '188; 277 (Fig. 15.2 no. 23)', 'logo-rebus', 'standing man = M001', 'high')
add('M342', 'ā (+ -tu)', "'(head of) cow' = genitive/possessive suffix *-ā", 'Proto-Dravidian', 'Parpola', P94, '188; 277 (Fig. 15.2 no. 24)', 'morpheme', 'jar sign = M342', 'high')
add('fish-with-dot (unmapped)', 'pottu', "dot = 'pottu'", 'Proto-Dravidian', 'Parpola', P94, '264', 'logo-rebus', 'unmapped', 'none')
# --- reported by Parpola 1994 ---
add('M342', '-at(tu)', 'Proto-Dravidian oblique-case suffix, via rebus ati/atti fig', 'Proto-Dravidian', 'Knorozov / Soviet team', P94r, '59-60', 'morpheme', 'most frequent sign = jar M342', 'high')
add('star sign (unmapped)', 'sukka', "'star'", 'Proto-Dravidian', 'Knorozov / Soviet team', P94r, '59-60', 'logo-rebus', 'unmapped', 'none')
add('M342', '(priest)', "jar = 'priest'", 'Proto-Dravidian', 'Mahadevan (early)', P94r, '60', 'logogram', 'jar', 'high')
add('spear sign (unmapped; M211?)', '(soldier)', "'soldier'", 'Proto-Dravidian', 'Mahadevan (early)', P94r, '60', 'logogram', 'M211 by description only', 'low')
add('arrow + half fig leaf (unmapped)', 'amp-ara', "'public space'", 'Proto-Dravidian', 'Fairservis', P94r, '60', 'sequence', 'unmapped', 'none')
add('M108|M109+M059', '(Pleiades)', "'6'+fish = Pleiades (first proposed)", 'Proto-Dravidian', 'Heras', P94r, '59; 277', 'sequence', 'numeral 6', 'high')
# --- Mahadevan 2015 ---
add('M342', '-(a)nṟu', 'masculine singular suffix', 'Early Dravidian', 'Mahadevan', M15, 'unpag. (Paradigm of gender)', 'morpheme', 'jar named', 'high')
add('M211', 'ampu > -(a)mpu', "arrow 'ampu' = non-masculine singular suffix (after Mahadevan 1998)", 'Early Dravidian', 'Mahadevan', M15, 'unpag. (Interpreting the arrow sign)', 'morpheme', 'arrow = M211', 'high')
add('four-stroke modifier (on M060)', '-(a)r', 'epicene plural', 'Early Dravidian', 'Mahadevan', M15, 'unpag.', 'morpheme', 'fish+4 strokes ~ M060 (by drawing)', 'medium')
add('M267+M099', 'aka-tt-(i)', "'lord of the house'", 'Early Dravidian', 'Mahadevan', M15, 'unpag.', 'sequence', 'most frequent initial pair', 'high')
add('M267', 'aka-(tt-i)', "'palace (fort, court)'", 'Early Dravidian', 'Mahadevan', M15, 'unpag. (place-sign chart)', 'logogram', 'glyphsim top-1 0.899 of chart crop + text', 'high')
add('M284', 'pāḻ(-i)', "'city'", 'Early Dravidian', 'Mahadevan', M15, 'unpag. (place-sign chart)', 'logogram', 'glyphsim top-1 0.88 + text', 'high')
add('M264', 'ampal(a)', "'assembly (place at four-road junction)'", 'Early Dravidian', 'Mahadevan', M15, 'unpag. (place-sign chart)', 'logogram', 'glyphsim top-1 0.839 of chart crop', 'medium')
add('M150', 'kēr(-i)', "'exclusive quarters'", 'Early Dravidian', 'Mahadevan', M15, 'unpag. (place-sign chart)', 'logogram', 'glyphsim top-1 0.913 of chart crop', 'medium')
add('M149', 'pāṭ(-i)', "'ordinary quarters'", 'Early Dravidian', 'Mahadevan', M15, 'unpag. (place-sign chart)', 'logogram', 'glyphsim top-1 0.905 of chart crop', 'medium')
add('M267 variant (not separately cropped)', 'cūḻ(-i)', "palace row, second value ('counsel')", 'Early Dravidian', 'Mahadevan', M15, 'unpag. (place-sign chart)', 'logogram', 'second sign in palace row not segmented', 'low')
add('M261|M373', '(house)', "'house'", 'Early Dravidian', 'Mahadevan', M15, 'unpag.', 'logogram', 'text', 'medium')
add('M047|M048', 'muruku', "seated deity = Muruku", 'Early Dravidian', 'Mahadevan', M15, 'unpag. (Fig. 4C labels "47", "48")', 'logogram', 'figure labels M47/M48 explicitly', 'high')
add('M012', 'poṟ-ay', "'bearer (sustainer)'", 'Early Dravidian', 'Mahadevan', M15, 'unpag. (Indus heritage chart)', 'logogram', 'glyphsim top-1 0.933 (M013 0.930 tie)', 'medium')
add('M015', 'cāt(t)-poṟ-ay', "'jar-bearer (food-bearer)'", 'Early Dravidian', 'Mahadevan', M15, 'unpag. (Indus heritage chart)', 'logogram', 'glyphsim top-1 0.94', 'high')
add('M014', 'ey-poṟ-ay', "'arrow-bearer (arms-bearer)'", 'Early Dravidian', 'Mahadevan', M15, 'unpag. (Indus heritage chart)', 'logogram', 'glyphsim top-1 0.929', 'high')
# --- Wells 2015 (sample) ---
add('M267+M342 (W861+W740)', "'cow at the city'", 'sequence reading of H-176', 'unspecified', 'Wells', W15, '93 (Fig. 6.12 caption, TOC only)', 'sequence', 'W861=M267, W740=M342 (Carlson; glyph checked)', 'high', 'caption only; no argument available')
# --- Mukhopadhyay 2019 (class-level) ---
add('phrase-final signs (class)', '(functional morphemes)', 'PF signs are functional/terminal markers', 'none (non-phonetic)', 'Mukhopadhyay', MU19, 'whole article', 'functional', 'class-level', 'n/a')
add('numeral/stroke signs (class)', '(quantifiers)', 'stroke signs quantify', 'none (non-phonetic)', 'Mukhopadhyay', MU19, 'whole article', 'functional', 'class-level', 'n/a')
df = pd.DataFrame(R)
# bulk keys
x = pd.read_csv(f'{ROOT}/data/lipi/xlits.csv', dtype=str, keep_default_na=False)
x = x[~x.sign.isin(['000', '999'])]
yk = pd.DataFrame(dict(sign_M='', sign_W='W'+x.sign, value=x.xlit, meaning='canonical=' + x.canonical, language='Sanskrit',
    proponent='Yajnadevam', citation='yajnadevam/lipi xlits.csv (GitHub, commit fc8813a)', page='n/a', claim_type='syllabic key',
    sign_mapping_basis='lipi sign id (ICIT/Wells-style number)', sign_mapping_confidence='n/a', note='fitted to the corpus by its author'))
fc = pd.read_csv(f'{ROOT}/data/field-cady_indus_valley_script_corpus/indus_dravidian_mapping_100.csv', dtype=str)
fc = fc[~fc.Indus_Sign.isin(['000', '999'])]
fk = pd.DataFrame(dict(sign_M='', sign_W='W'+fc.Indus_Sign, value=fc.Dravidian_Syllable, meaning='', language='Dravidian (surname syllables)',
    proponent='Field Cady (unsupervised optimal transport)', citation='github field-cady/indus_valley_script_corpus indus_dravidian_mapping_100.csv (commit 3030826, 2026-03-13)',
    page='n/a', claim_type='syllabic key', sign_mapping_basis='lipi sign id', sign_mapping_confidence='n/a', note='machine-generated; MIT'))
# W for hand rows via Carlson concordance
c = sqlite3.connect(f'{ROOT}/map/indus_map.sqlite')
cc = pd.read_sql('select parpola_id, scheme, other_id from sign_concordance', c)
m2p = cc[cc.scheme == 'mahadevan'].groupby('other_id').parpola_id.apply(set).to_dict()
p2w = cc[cc.scheme == 'wells'].groupby('parpola_id').other_id.apply(set).to_dict()
def wfor(m):
    ms = re.findall(r'M\d{3}', m); out = []
    for mm in ms:
        ws = sorted({w for p in m2p.get(mm, ()) for w in p2w.get(p, ())}); out.append(mm + ':' + '/'.join(ws) if ws else mm + ':?')
    return '; '.join(out)
df['sign_W'] = df.sign_M.apply(wfor)
df['testable'] = df.sign_mapping_confidence.isin(['high', 'medium'])
out = pd.concat([df, yk, fk], ignore_index=True)
out.insert(0, 'row', range(1, len(out)+1))
out.to_csv(f'{ROOT}/outputs/claims/all_proposals.csv', index=False)
print(len(df), 'hand-sourced rows;', len(yk), 'Yajnadevam;', len(fk), 'Field-Cady;', df.testable.sum(), 'hand rows testable')
