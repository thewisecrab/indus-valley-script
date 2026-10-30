# Shuffle benchmark: Yajnadevam_key_lipi_fc8813a

**Verdict: NO SUPPORT FROM SIGN ORDER**

- Primary test: key, measure M3.
- The proposal reads the shuffled inscriptions as well as or better than the real ones (real 0.579 vs within-text shuffled 0.591; drop -0.012, BH q = 1).
- Correct keys for real Sanskrit/Akkadian at the same text lengths lose at least +0.165 on this measure under the same shuffle (positive control).
- This does not show that every value in the proposal is wrong. It shows that this test gives no evidence that the proposal reads the inscriptions.
- Ceiling warning: 99.4% of real texts already pass M1. When almost anything passes, the measure cannot separate a right reading from a wrong one.
- Ceiling warning: 95.8% of real texts already pass M2. When almost anything passes, the measure cannot separate a right reading from a wrong one.

Mode: key; language: Sanskrit; lexicon: sanskrit_MW (172432 words; length-stratified subsample 4361); mean signs per text: 4.27; shuffles: 200 per null (R3b: a quarter).


| Test | Measure | n | Real | Within-shuffle (95% range) | Drop | q | Positional re-deal drop | q | Interior-only drop, 4+ signs | q | Global shuffle drop | q | Permuted key | q |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| key | M1 | 2317 | 0.994 | 0.990 (0.986-0.993) | +0.004 | 0.0391 | -0.002 | 1 | +0.001 | 0.672 | +0.003 | 0.163 | 0.987 | 0.672 |
| key | M2 | 2317 | 0.958 | 0.935 (0.929-0.941) | +0.022 | 0.015 | +0.010 | 0.015 | +0.009 | 0.015 | +0.018 | 0.015 | 0.925 | 0.359 |
| key | M3 | 2317 | 0.579 | 0.591 (0.579-0.606) | -0.012 | 1 | -0.013 | 1 | -0.020 | 1 | -0.022 | 1 | 0.494 | 0.187 |

Positive control (correct keys, word-aligned texts of about 4.2 signs; positive_control/outputs/pc_summary.csv and pc_positional_nulls.csv):

| Measure | Corpus | Key | Real | Within-shuffle | Drop | Positional re-deal drop | Interior-only drop, 4+ signs |
|---|---|---|---|---|---|---|---|
| M1 | sanskrit_classical | correct | 0.904 | 0.862 | +0.043 | +0.036 | +0.028 |
| M1 | sanskrit_vedic | correct | 0.919 | 0.879 | +0.040 | +0.029 | +0.028 |
| M1 | akkadian_NA_letters | correct | 0.979 | 0.730 | +0.249 | +0.339 | +0.225 |
| M1 | akkadian_NA_letters | fixed_one_value_per_sign | 0.855 | 0.679 | +0.176 | +0.226 | +0.149 |
| M2 | sanskrit_classical | correct | 0.722 | 0.656 | +0.065 | +0.038 | +0.037 |
| M2 | sanskrit_vedic | correct | 0.729 | 0.684 | +0.045 | +0.019 | +0.014 |
| M2 | akkadian_NA_letters | correct | 0.769 | 0.613 | +0.155 | +0.239 | +0.105 |
| M2 | akkadian_NA_letters | fixed_one_value_per_sign | 0.723 | 0.585 | +0.138 | +0.191 | +0.099 |
| M3 | sanskrit_classical | correct | 0.535 | 0.334 | +0.201 | +0.223 | +0.189 |
| M3 | sanskrit_vedic | correct | 0.530 | 0.364 | +0.165 | +0.209 | +0.159 |

M1: splits into words of the full lexicon. M2: same, 4,361-word length-stratified subsample. M3: complete vidyut Sanskrit parse. Positional re-deal: signs re-dealt across texts within first / middle / last position (keeps where each sign stands, destroys the sequences). Interior-only: first and last sign kept, middle shuffled, scored on texts of 4+ signs. p one-sided, (1 + #null >= real)/(N + 1); q = Benjamini-Hochberg across every test in this table. This benchmark never certifies a decipherment.
