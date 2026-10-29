# Pre-registration: held-out tests of the positive structural hypotheses (session 6)

Written and committed on 29 October 2026 (IST) **before** `scripts/prereg_heldout.py` was run on real data. Before this commit the script had only been run with `--selftest`, on synthetic data. The sign sets are frozen in `prereg/sign_sets_session6.json`, derived mechanically from the committed tables `outputs/structure/sign_classes_M77.csv` and `outputs/structure/sign_table.csv`. Results are reported whatever they show, including failures.

## Hypotheses (each is a one-sided prediction of more than the within-text-shuffle null)

| ID | Prediction | Statistic |
|---|---|---|
| H1 | Terminal-class signs (13 M signs with class confidence ≥ 0.85) are text-final | count of set tokens in final position |
| H2 | Initial-class signs (9 M signs, confidence ≥ 0.85) are text-initial | count in initial position |
| H3 | Pre-terminal-class signs (14 M signs, confidence ≥ 0.85) are penultimate | count in second-to-last position (texts of ≥ 3 signs) |
| H4 | The jar sign M342 is text-final | count in final position |
| H5 | M267 is text-initial | count in initial position |
| H6 | M267 is immediately followed by M099 (they act as a unit) | count of adjacent M267→M099 pairs in reading order |
| H7 | A stroke numeral immediately precedes the fish sign M059 | count of adjacent numeral→M059 pairs |
| H8 | Within a text, all initial-class tokens precede all terminal-class tokens (slot order) | number of texts satisfying the order |

The M sets are mapped to Parpola (P) and Wells/ICIT (W) IDs through the P and W columns of `sign_classes_M77.csv`, which hold Carlson's concordance. An ID that maps into two classes is dropped from both. The numeral set is every sign whose `structural_class` in `sign_table.csv` contains NUMERAL.

## Splits

Within each split we keep unique texts of length ≥ 2 only, since duplicates would inflate the counts. For ICIT these are damage-free single-line texts (as in `loo_hand.py`); for CISI they are undamaged texts.

**Primary splits (predictions apply):**

1. CISI/mayig transcription (Parpola numbering), Mohenjo-daro seals. **Caveat:** these are the same objects as in M77 and ICIT, so this split tests whether the result survives a different transcription and sign list. It does not test new objects.
2. ICIT, by region: Lower Indus; Inter-Riverine; Gujarat/Kutch; Eastern Headwaters + Upper Indus.
3. ICIT, by object type: SEAL; TAB (tablets); POT (pottery); other (TAG, MISC, BNGL, ROD, IMPL, BEAD).

**Exploratory split (no prediction made):** ICIT West/foreign (Persian Gulf, Mesopotamia, Iranian Plateau, Central Asia). Our earlier anchor analysis already found that Gulf seals use Indus signs in non-Indus sequences.

**Independence caveat.** The classes were derived on M77, which is dominated by Mohenjo-daro and Harappa, and were replicated on ICIT in session 3. The Lower Indus and Inter-Riverine splits, and the SEAL split, therefore overlap heavily with the data that defined the hypotheses. Gujarat/Kutch, Eastern Headwaters + Upper Indus, POT, other objects and, partly, TAB are the more independent tests.

## Test and decision rules

- **Null and p-value:** within-text permutation of sign order, 2,000 permutations with fixed seeds; p = (1 + #{null ≥ observed}) / 2001.
- **Pass:** p < 0.05. **Fail:** p ≥ 0.05. **Insufficient data:** fewer than 5 relevant texts in the split; this is neither a pass nor a fail.
- BH q-values are also reported across all primary tests.
- **Per-hypothesis verdict:**
  - *replicated*: passes in every primary split with sufficient data;
  - *partially replicated*: passes in some;
  - *not replicated*: passes in none.
- **Our prediction:** every hypothesis passes in every primary split with sufficient data. A failure counts against the hypothesis and will be reported in the manuscript and README.
- **Known risk:** small splits (Eastern Headwaters + Upper Indus, other objects) have low power, so some failures there may reflect power rather than absence of the effect. We will report the observed/null ratio alongside every verdict, but the verdict rule above stands.
