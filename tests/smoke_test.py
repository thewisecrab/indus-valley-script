"""Offline smoke test for the public repository. Needs no restricted data and no network.
1. Every script under scripts/ and tools/ byte-compiles.
2. Unit checks of indus_lib on a hand-made example.
3. The toy pipeline (scripts/run_all.py --toy on data_open/toy) re-runs in a scratch copy and reproduces the
   committed outputs/TOY/*.csv and outputs/summary_toy.json exactly.
4. Headline numbers quoted in REPRODUCIBILITY.md match the committed result files, and the global LOO calibration
   block (mean p_alt by condition, Mann-Whitney p) recomputes exactly from the per-sign table.
5. tools/check_public.py finds no restricted content.
Run from the repo root: python tests/smoke_test.py"""
import os, sys, json, shutil, subprocess, tempfile, glob, filecmp
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []
def check(ok, what):
    print(('ok   ' if ok else 'FAIL ') + what)
    if not ok: fails.append(what)

# 1. compile
for f in sorted(glob.glob(f'{ROOT}/scripts/*.py') + glob.glob(f'{ROOT}/tools/*.py')):
    try: compile(open(f, encoding='utf-8').read(), f, 'exec'); ok = True
    except SyntaxError as e: ok = False; print(e)
    check(ok, f'compiles: {os.path.relpath(f, ROOT)}')

# 2. library unit checks
sys.path.insert(0, f'{ROOT}/scripts'); import indus_lib as L
T = [['A', 'B', 'C'], ['A', 'C'], ['B'], ['A', 'X', 'C']]
fr = L.sign_frequency(T, breakers={'X'}); check(dict(zip(fr.sign, fr['count'])) == {'A': 3, 'C': 3, 'B': 2}, 'sign_frequency counts, breaker excluded')
pos = L.positional(T, breakers={'X'}).set_index('sign')
check(pos.loc['A', 'initial'] == 2 and pos.loc['C', 'final'] == 2 and pos.loc['B', 'solo'] == 1 and pos.loc['B', 'medial'] == 1,
      'positional classes (text with a breaker skipped)')
check(list(L.split_on_breakers(['A', 'X', 'B', 'C'], {'X'})) == [['A'], ['B', 'C']], 'split_on_breakers')

# 3. toy pipeline determinism in a scratch copy
with tempfile.TemporaryDirectory() as tmp:
    shutil.copytree(f'{ROOT}/scripts', f'{tmp}/scripts')
    os.makedirs(f'{tmp}/data/toy'); shutil.copy2(f'{ROOT}/data_open/toy/toy_corpus.csv', f'{tmp}/data/toy/toy_corpus.csv')
    r = subprocess.run([sys.executable, f'{tmp}/scripts/run_all.py', '--toy'], capture_output=True, text=True, env={**os.environ, 'MPLBACKEND': 'Agg'})
    check(r.returncode == 0, 'run_all.py --toy exits 0' + ('' if r.returncode == 0 else ': ' + r.stderr[-400:]))
    if r.returncode == 0:
        for f in sorted(os.listdir(f'{ROOT}/outputs/TOY')):
            new = f'{tmp}/outputs/TOY/{f}'
            check(os.path.exists(new) and filecmp.cmp(new, f'{ROOT}/outputs/TOY/{f}', shallow=False), f'toy output reproduced: outputs/TOY/{f}')
        a = json.load(open(f'{tmp}/outputs/summary_toy.json')); b = json.load(open(f'{ROOT}/outputs/summary_toy.json'))
        check(a == b, 'toy output reproduced: outputs/summary_toy.json')

# 4. headline numbers (values as quoted in REPRODUCIBILITY.md section 4)
J = lambda p: json.load(open(f'{ROOT}/{p}'))
acc = J('outputs/signmap/concordance_accuracy.json')
check(round(acc['p']['top1'], 3) == 0.847, 'concordance top-1 = 0.847')
s3 = J('outputs/structure/structure3_dedup.json')['hmm_seal_dedup']
check(abs(s3['gain_real'][-1] - 0.38) < 0.01 and max(s3['gain_shuffled']) < 0.05, 'HMM gain dedup seals ~0.38 nats/token, shuffled ~0')
rep = J('outputs/compare/replications.json')
check(rep['perplexity']['M77_EBUDS_like_dedup']['2']['perplexity'] == 31.33, 'Yadav-style bigram perplexity M77 dedup = 31.33')
check(rep['nair_replication']['ICIT_lipi_dedup_undamaged']['hcond']['obs'] == 3.433, 'Nair-style H_cond ICIT dedup undamaged = 3.433')

r = subprocess.run([sys.executable, f'{ROOT}/scripts/loo_global_calibration.py', '--check'], capture_output=True, text=True, cwd=ROOT)
print(r.stdout.strip()); check(r.returncode == 0, 'global LOO calibration block recomputes from loo_phonetic_all_conditions.csv')

# 4b. session 6: pre-registration integrity and headline outcomes (including the partial failure of H7)
import hashlib
for line in open(f'{ROOT}/prereg/SHA256SUMS.txt'):
    h, f = line.split()
    check(hashlib.sha256(open(f'{ROOT}/{f}', 'rb').read()).hexdigest() == h, f'pre-registered file unchanged: {f}')
pr = J('outputs/prereg/prereg_heldout_summary.json')
check(pr['H7']['overall'] == 'partially replicated' and all(pr[h]['overall'] == 'replicated' for h in ['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H8']),
      'pre-registered held-out: H1-H6, H8 replicated; H7 partially')
rb = J('outputs/robustness/robustness_summary.json')
check(rb['passed'] == rb['cells'] == 90, 'robustness: 90/90 cells pass')
r = subprocess.run([sys.executable, f'{ROOT}/scripts/prereg_heldout.py', '--selftest'], capture_output=True, text=True, cwd=ROOT)
check(r.returncode == 0, 'prereg_heldout.py --selftest (synthetic data) passes')
sl = J('outputs/signlist/indus_open_signlist.json')
check(len(sl) == 1132 if isinstance(sl, list) else len(sl.get('signs', sl)) == 1132, 'open sign list has 1,132 entries')

# 4c. session 7: extended seeds, strict look-alike controls, H7 post hoc, emblem stability
se = J('outputs/claims/seed_claims_extended.json')
check(se['loo']['n_replicates'] >= 20 and se['rebus']['n_replicates'] >= 50 and se['loo']['any_sign_beats_all_nulls'] == 0,
      'seed claims: >= 20 LOO and >= 50 rebus replicates; no sign beats all nulls')
check(se['rebus']['by_lexicon']['dravidian_DEDR_forms+PDR']['rank']['median'] == 6.0, 'seed claims: Dravidian median rebus rank 6 of 8')
ls = J('outputs/comparanda/lookalikes_strict.json')['scripts']
check(ls['linear_elamite']['indus_no_strokes']['N2_p'] < 0.01 and ls['linear_b']['indus_no_strokes']['N2_p'] < 0.05,
      'strict look-alikes: Linear Elamite and (confound check) Linear B pass the complexity-matched null')
check('EXPLORATORY' in J('outputs/prereg/h7_posthoc_exploratory.json')['label'], 'H7 post hoc is labelled exploratory')
es = J('outputs/emblem/emblem_stability.json')
check(es['n_configs'] == 54 and 0.3 < es['share_of_configs_assigning_linguistic']['Indus M77 (dedup)'] < 0.7, 'emblem classifier stability: 54 configs, Indus M77 unstable')
check(all(os.path.exists(f'{ROOT}/data_open/comparanda_short/wiki_titles_{l}.txt') for l in ['fi', 'ta', 'sa']), 'Wikipedia title samples shipped')

# 4d. session 7 positive control: correct keys lose under shuffling; Yajnadevam's key does not on the parse
import csv
import pandas as pd
pc = {(r['corpus'], r['key'], r['textset'], r['measure']): r for r in csv.DictReader(open(f'{ROOT}/positive_control/outputs/pc_summary.csv'))}
sk = pc[('sanskrit_classical', 'correct', 'lenmatch_wordaligned', 'M3_vidyut')]; ya = pc[('indus_lipi', 'yajnadevam', 'lipi_test_texts_2317', 'M3_vidyut')]
ak = pc[('akkadian_NA_letters', 'correct', 'lenmatch_wordaligned', 'M1_seg_full')]; y2 = pc[('indus_lipi', 'yajnadevam', 'lipi_test_texts_2317', 'M2_seg_lm4361')]
check(float(sk['drop_within']) > 0.15 and float(sk['p_within']) <= 0.005 and float(ak['drop_within']) > 0.2, 'positive control: correct Sanskrit parse and Akkadian segmentation lose under shuffling')
check(float(ya['drop_within']) < 0 and float(y2['drop_within']) > 0 and float(y2['p_within']) <= 0.005, 'positive control: Yajnadevam key no parse gain; small significant M2 gain (corrected claim)')

# 4e. session 8: shuffle benchmark (tools/evaluate_key.py) runs offline on the toy corpus; headline results; positional nulls
import tempfile
with tempfile.TemporaryDirectory() as td:
    r = subprocess.run([sys.executable, f'{ROOT}/tools/evaluate_key.py', 'key', f'{ROOT}/bench/examples/toy_key.csv', f'{ROOT}/bench/examples/toy_key.meta.json',
                        '--corpus', 'toy', '--nshuf', '10', '--nperm', '5', '--procs', '1', '--out', td], capture_output=True, text=True, cwd=ROOT)
    check(r.returncode == 0 and os.path.exists(f'{td}/toy_demo_key.json') and 'Verdict' in open(f'{td}/toy_demo_key.md').read(),
          'evaluate_key.py toy demo runs offline' + ('' if r.returncode == 0 else ': ' + r.stderr[-400:]))
ek = J('bench/results/evaluate_key/Yajnadevam_key_lipi_fc8813a.json'); m3 = [x for x in ek['results'] if x['measure'] == 'M3'][0]
check(m3['drop_within'] < 0 and ek['verdict']['label'] == 'NO SUPPORT FROM SIGN ORDER', 'evaluate_key: Yajnadevam key, no parse gain from real order')
er = J('bench/results/evaluate_key/Yajnadevam_readings_lipi_fc8813a.json')
r3 = [x for x in er['results'] if x['test'] == 'R3_derived_values_heldout' and x['measure'] == 'M3'][0]
check(er['verdict']['label'].startswith('WEAK') and r3['drop_posglobal'] < 0.1, 'evaluate_key: Yajnadevam readings (R3) weak, largely positional')
pn = {(r['corpus'], r['key'], r['measure']): r for r in csv.DictReader(open(f'{ROOT}/positive_control/outputs/pc_positional_nulls.csv'))}
check(float(pn[('sanskrit_classical', 'correct', 'M3_vidyut')]['drop_posglobal']) > 0.15 and float(pn[('akkadian_NA_letters', 'correct', 'M1_seg_full')]['drop_posglobal']) > 0.2,
      'positive control: correct keys still lose when signs keep their usual positions')

# 4f. session 8: arbitrary-text control and structured-notation (Diener 2026 / Kriger & Hunt 2026) headline results
at = pd.read_csv(f'{ROOT}/outputs/arbitrary_text/fit_M3/results.csv')
check(at[at.corpus == 'us_constitution_letters'].heldout_M3.min() >= 0.99 and (at.q_M3 >= 0.05).all(),
      'arbitrary-text control: US Constitution letters fully parse as Sanskrit held out; no corpus shows a significant real-order gain')
sn = J('outputs/structured_notation/results.json'); qs = {(x['test'], x['label']): x['q_BH'] for x in sn['pvalues']}
check(sn['kriger_hunt_replication']['distinct_sequences'] == 176 and sn['D']['p_perm'] > 0.05 and qs[('C1', 'I2 reading pos 4 (Diener P4)')] > 0.05,
      'structured notation: K&H 176/179 distinct replicated; tariff locking and numeral field 4 not supported')

# 5. restricted-content checker
r = subprocess.run([sys.executable, f'{ROOT}/tools/check_public.py'], capture_output=True, text=True, cwd=ROOT)
print(r.stdout.strip()); check(r.returncode == 0, 'tools/check_public.py clean')

print(f'\n{len(fails)} failure(s)'); sys.exit(1 if fails else 0)
