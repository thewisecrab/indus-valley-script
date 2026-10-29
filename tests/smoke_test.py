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

# 5. restricted-content checker
r = subprocess.run([sys.executable, f'{ROOT}/tools/check_public.py'], capture_output=True, text=True, cwd=ROOT)
print(r.stdout.strip()); check(r.returncode == 0, 'tools/check_public.py clean')

print(f'\n{len(fails)} failure(s)'); sys.exit(1 if fails else 0)
