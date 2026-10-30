# Shuffle benchmark: FieldCady_PDR_syllables

**Verdict: NO SUPPORT FROM SIGN ORDER**

- Primary test: key, measure M2.
- The proposal reads the shuffled inscriptions as well as or better than the real ones (real 0.399 vs within-text shuffled 0.432; drop -0.033, BH q = 1).
- Correct keys for real Sanskrit/Akkadian at the same text lengths lose at least +0.045 on this measure under the same shuffle (positive control).
- This does not show that every value in the proposal is wrong. It shows that this test gives no evidence that the proposal reads the inscriptions.

Mode: key; language: Proto-Dravidian (syllabic); lexicon: proto_dravidian_PDR (4456 words; length-stratified subsample 4361); mean signs per text: 4.05; shuffles: 200 per null (R3b: a quarter).


| Test | Measure | n | Real | Within-shuffle (95% range) | Drop | q | Positional re-deal drop | q | Interior-only drop, 4+ signs | q | Global shuffle drop | q | Permuted key | q |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| key | M1 | 1016 | 0.519 | 0.517 (0.516-0.519) | +0.001 | 0.784 | +0.006 | 0.784 | +0.001 | 1 | -0.009 | 1 | 0.334 | 0.139 |
| key | M2 | 1016 | 0.399 | 0.432 (0.420-0.444) | -0.033 | 1 | +0.002 | 1 | -0.008 | 1 | -0.042 | 1 | 0.267 | 0.208 |

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

M1: splits into words of the full lexicon. M2: same, 4,361-word length-stratified subsample. M3: complete vidyut Sanskrit parse. Positional re-deal: signs re-dealt across texts within first / middle / last position (keeps where each sign stands, destroys the sequences). Interior-only: first and last sign kept, middle shuffled, scored on texts of 4+ signs. p one-sided, (1 + #null >= real)/(N + 1); q = Benjamini-Hochberg across every test in this table. This benchmark never certifies a decipherment.
