# Shuffle benchmark: Yajnadevam_readings_lipi_fc8813a

**Verdict: WEAK: ORDER EFFECT SMALLER THAN A CORRECT KEY OR LARGELY POSITIONAL**

- Primary test: R3_derived_values_heldout, measure M3.
- Real sign order helps (drop +0.139, q = 0.0089; correct keys lose at least +0.165 under the same shuffle).
- Positional control (signs re-dealt across texts within first/middle/last position): drop +0.046 (q = 0.017); correct keys lose at least +0.209 under this control.
- Positional control (interior signs shuffled, texts of 4+ signs): drop +0.073 (q = 0.0089); correct keys lose at least +0.159 under this control.
- Order effects that shrink under the positional controls come from the script's positional habits (some signs mostly stand first or last, and a reading can give those signs word-initial or word-final forms) rather than from reading the sequence. This is not evidence of a decipherment.
- Readings mode: R2 shuffles the per-sign pieces of each published reading. The proponent could adjust each real reading (word division, sandhi, vowels) to fit its neighbours, and shuffled pieces get no such adjustment, so R2 mostly measures how fluent the readings are. R2m checks this: the same readings re-cut against a random other inscription. R3 is the fair test: the values the readings actually give each sign are learned from 80% of inscriptions and read the other 20% (held out) mechanically.

Mode: readings; language: Sanskrit; lexicon: sanskrit_MW (172432 words; length-stratified subsample 4361); mean signs per text: 4.87; shuffles: 200 per null (R3b: a quarter).

Fluency (descriptive, no null): complete vidyut parse of the readings as written 0.783; with word spaces removed 0.745.

R3_derived_values_heldout: {'train_readings': 1367, 'heldout_texts': 386, 'signs_with_values': 560}
R3b_derived_top2_any_heldout: {'train_readings': 1367, 'heldout_texts': 386, 'signs_with_values': 560}

| Test | Measure | n | Real | Within-shuffle (95% range) | Drop | q | Positional re-deal drop | q | Interior-only drop, 4+ signs | q | Global shuffle drop | q | Permuted key | q |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R2_piece_shuffle | M1 | 1694 | 0.993 | 0.837 (0.818-0.851) | +0.156 | 0.0089 | +0.143 | 0.0089 | +0.118 | 0.0089 | +0.214 | 0.0089 | – | – |
| R2_piece_shuffle | M2 | 1694 | 0.938 | 0.730 (0.711-0.749) | +0.208 | 0.0089 | +0.212 | 0.0089 | +0.171 | 0.0089 | +0.275 | 0.0089 | – | – |
| R2_piece_shuffle | M3 | 1694 | 0.745 | 0.333 (0.315-0.351) | +0.412 | 0.0089 | +0.382 | 0.0089 | +0.307 | 0.0089 | +0.470 | 0.0089 | – | – |
| R2m_mismatch_control | M1 | 1694 | 0.993 | 0.798 (0.782-0.817) | +0.195 | 0.0089 | +0.221 | 0.0089 | +0.177 | 0.0089 | +0.259 | 0.0089 | – | – |
| R2m_mismatch_control | M2 | 1694 | 0.938 | 0.684 (0.664-0.702) | +0.254 | 0.0089 | +0.301 | 0.0089 | +0.281 | 0.0089 | +0.327 | 0.0089 | – | – |
| R2m_mismatch_control | M3 | 1694 | 0.745 | 0.343 (0.329-0.361) | +0.402 | 0.0089 | +0.455 | 0.0089 | +0.357 | 0.0089 | +0.477 | 0.0089 | – | – |
| R3_derived_values_heldout | M1 | 386 | 0.909 | 0.862 (0.837-0.886) | +0.048 | 0.0089 | +0.022 | 0.0647 | +0.019 | 0.139 | +0.059 | 0.0089 | 0.795 | 0.0647 |
| R3_derived_values_heldout | M2 | 386 | 0.769 | 0.742 (0.707-0.775) | +0.028 | 0.115 | +0.003 | 0.497 | -0.037 | 0.975 | +0.042 | 0.0522 | 0.690 | 0.204 |
| R3_derived_values_heldout | M3 | 386 | 0.541 | 0.403 (0.373-0.440) | +0.139 | 0.0089 | +0.046 | 0.017 | +0.073 | 0.0089 | +0.118 | 0.0089 | 0.295 | 0.017 |
| R3b_derived_top2_any_heldout | M1 | 386 | 0.992 | 0.973 (0.956-0.984) | +0.019 | 0.0527 | +0.005 | 0.288 | +0.011 | 0.139 | +0.016 | 0.03 | 0.918 | 0.0527 |
| R3b_derived_top2_any_heldout | M2 | 386 | 0.966 | 0.927 (0.905-0.943) | +0.040 | 0.03 | +0.006 | 0.302 | +0.006 | 0.377 | +0.031 | 0.0527 | 0.851 | 0.0527 |
| R3b_derived_top2_any_heldout | M3 | 386 | 0.777 | 0.659 (0.625-0.687) | +0.118 | 0.03 | +0.029 | 0.0527 | +0.024 | 0.139 | +0.124 | 0.03 | 0.476 | 0.0527 |

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
