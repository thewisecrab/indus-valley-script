# Calibrated structural analysis of the Indus script

> **UNREVIEWED PREPRINT / WORKING DRAFT.** Nothing here has been peer-reviewed. The results and wording may change. Please cite it as a preprint and treat every claim as provisional.

> **AI assistance.** This analysis was carried out with substantial help from an AI research assistant; visual sign judgements were made by the AI, not a human. Every result is produced by the scripts here; `REPRODUCIBILITY.md` lists which ones run from a fresh clone and which need inputs we cannot redistribute.

Code, derived statistics and manuscript for a null-model-calibrated study of the Indus script (c. 2600–1900 BCE). Two independent machine-readable transcriptions are used: Mahadevan 1977 (M77) and an ICIT-derived corpus.

**What the study finds**

- Positional sign classes, a slot template and recurrent multi-sign units are real. They are tested against shuffles, on held-out and deduplicated data, and across the two corpora.
- Linguistic status is **undetermined** by internal statistics. A synthetic, non-linguistic emblem system passes the same structural tests.
- No published phonetic sign value beats null models in per-sign leave-one-out tests.
- Published results are replicated on our data: Nair 2026's Zipf slope and conditional entropy, and Yadav et al. 2010's bigram perplexity drop. Yadav's restoration "sensitivity" turns out to be matched by a frequency-only baseline. See `outputs/compare/` and manuscript §1.1 and §4.12.

**Session 6 additions (29 October 2026)**

- **Pre-registered held-out tests** (`prereg/`, committed before the run): 7 of 8 structural predictions replicated in every primary split with enough data (CISI transcription, ICIT regions, ICIT object types). **H7, numeral+fish as a unit, only partially replicated**: it failed on ICIT pottery (4 vs 2.16 expected, p = 0.109) and only just passed on CISI (p = 0.046). Results: `outputs/prereg/`.
- **Robustness:** all 90 tests pass across M77, ICIT and CISI under native, Parpola-level, numerals-collapsed and allograph sign schemes (`outputs/robustness/`).
- **Real non-linguistic comparanda** (Sproat 2014 corpora, Apache-2.0): the Indus profile is mixed, emblem-like in order and edge structure, language-like in avoiding repeats. Linguistic status stays undetermined (`outputs/emblem/`).
- **Claim-scoring benchmark:** `scripts/bench_score.py` and `bench/template_submission.csv` score any sign→value key against shuffles, other lexicons, noise-fitted keys and per-sign leave-one-out. No key tested so far beats all nulls (`bench/results/`).
- **Open sign list** (`outputs/signlist/`, 1,132 entries, derived data only) and a **blind rater kit** for human checks of the AI-made concordance judgements (`rater_kit/`; no raters recruited yet).
- **Deterministic reruns:** the controls no longer depend on Python's hash seed. `scripts/run_claim_seeds.sh` reruns them over five seeds; the spread is in `outputs/claims/seed_spread.csv`.

**Status:** unreviewed preprint (working draft), not peer-reviewed. Maintained by the Indus Valley Script project contributors.

## Layout

| Path | What |
|---|---|
| `scripts/` | all analysis code (Python) |
| `scripts/fetch_data.sh` | fetch the openly hosted inputs; instructions for the restricted ones |
| `tests/smoke_test.py`, `.github/workflows/smoke.yml` | offline smoke test, run by GitHub Actions on every push |
| `tools/check_public.py` | scan the repo for restricted files and patterns (run before every push) |
| `tools/build_public_repo.py` | how this repo was assembled from the private project |
| `outputs/` | derived statistics only (frequencies, positional profiles, bigram counts, test statistics, concordance scores) |
| `outputs/compare/` | prior-work matrix, replications, synthetic-baseline results |
| `prereg/` | pre-registered predictions, frozen sign sets and checksums (session 6) |
| `outputs/prereg/`, `outputs/robustness/`, `outputs/emblem/` | held-out, merge-scheme and non-linguistic-comparison results |
| `outputs/signlist/` | open machine-readable sign list (CSV, JSON, JSON schema) |
| `bench/` | claim-scoring benchmark: submission template, examples, scored results |
| `rater_kit/` | blind human-rater sheet, protocol and scorer (answer key withheld; SHA-256 published) |
| `map/schema.sql`, `map/seed/` | SQLite schema and seed tables for the sign map |
| `paper/manuscript_public.md`, `paper/manuscript_public.pdf` | manuscript, public version (unreviewed preprint) |
| `data_open/` | Met Open Access images (CC0), Wikimedia Commons images (per-file licences, see ATTRIBUTION.md), toy corpus |

## Quick start

Clone over SSH with `git clone git@github.com:thewisecrab/indus-valley-script.git`, or over HTTPS with `git clone https://github.com/thewisecrab/indus-valley-script.git`.


```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python tests/smoke_test.py        # offline: compiles everything, re-runs the toy pipeline, checks headline numbers
bash scripts/fetch_data.sh        # fetched inputs; read its output for the restricted ones
python scripts/run_all.py         # frequencies, positions, n-grams for M77 / ICIT / CISI (reproduces outputs/<corpus>/ exactly)
```

Some analyses need inputs that cannot be fetched (for example the M77 object-type codes, which come from OCR of the printed concordance). `REPRODUCIBILITY.md` lists, script by script, what runs from a fresh clone.

Full instructions are in `REPRODUCIBILITY.md`, and the exclusions are in `DATA_POLICY.md`.

## Licence

- Code: MIT (`LICENSE`).
- Text, figures and derived result tables: CC BY 4.0 (`LICENSE-CC-BY-4.0.txt`).
- Scope of each licence: `LICENSE-SCOPE.md`.
- Third-party images in `data_open/` keep their own licences.
- See `DATA_POLICY.md` for the GPL notes.

## Citation

See `CITATION.cff`.
