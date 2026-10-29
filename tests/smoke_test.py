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

# 5. restricted-content checker
r = subprocess.run([sys.executable, f'{ROOT}/tools/check_public.py'], capture_output=True, text=True, cwd=ROOT)
print(r.stdout.strip()); check(r.returncode == 0, 'tools/check_public.py clean')

print(f'\n{len(fails)} failure(s)'); sys.exit(1 if fails else 0)
