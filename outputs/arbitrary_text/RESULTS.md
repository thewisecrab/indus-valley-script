# Arbitrary-text control (session 8)

**Question.** If sign values are fitted with the freedom a Sanskrit decipherment of the Indus script allows, does *any* text come out reading as Sanskrit? The "Panini Protocol" page (Ugraśravas, https://ugrashravas.github.io/paniniprotocol, fetched 30 October 2026) makes this critique. It "deciphers" the US Constitution as Sanskrit using a letter-to-phoneme-class mapping it describes as nearly a replica of Yajnadevam's own classes. It also uses Yajnadevam's unicity-distance criterion: past about 475 translated symbols, a reading is supposed to be unique.

**Method** (`scripts/arbitrary_text_control.py`). This is the same fitting freedom as our earlier fitted-key test (claim harness part C):
- **Value inventory.** Sign values are drawn from the published Yajnadevam key's own value inventory.
- **Reading rule.** The *lipi* rule, with its optional inherent *a*.
- **Fitting.** Values are hill-climbed (3,000 swap or re-draw steps on the 150 most frequent sign types) on 80% of the texts.
- **Objectives.** Two runs: (i) segmentation into the 4,361-word Monier-Williams sample (M2, as in part C), and (ii) a complete vidyut 0.4 Sanskrit parse (M3).
- **Evaluation.** The fitted key reads the other 20% (449 texts) mechanically.

Every corpus is cut into 2,244 texts with the length distribution of the unique Indus texts of 2–8 signs. There are 3 fitting seeds and 50 within-text shuffles of the held-out texts. Benjamini–Hochberg q is computed across all p-values of each run. Results: `fit_M2/` and `fit_M3/` (`results.csv` per seed, `summary.json` means).

| "Signs" being read | Sign types | Held-out complete Sanskrit parse (M3), key fitted to M3 | Held-out M2, key fitted to M2 | Held-out symbols in fully parsed texts (of about 1,800–1,840) | Real order vs shuffled, held-out M3 |
|---|---|---|---|---|---|
| **US Constitution, letters** | 26 | **100%** (all 3 seeds) | 100% | 1,809–1,835 | +0.003 to +0.007, q ≥ .19 |
| US Constitution, English words | 857 | 86–90% | 99% | 1,524–1,568 | +0.02 to +0.06, q ≥ .12 |
| Random strings (Indus sign frequencies) | 529 | 92–93% | 98–99% | 1,649–1,672 | −0.004 to +0.009, q ≥ .65 |
| Neo-Assyrian Akkadian, cuneiform graphemes | 254 | 96–98% | 99–100% | 1,728–1,809 | −0.006 to +0.02, q ≥ .12 |
| **Indus texts** | 620 | 90–92% | 98% | 1,644–1,664 | 0.000 to +0.054, q ≥ .12 |
| Real classical Sanskrit, aksharas (values re-fitted, not its own) | 1,148 | 78–81% | 97–99% | 1,361–1,430 | −0.016 to 0.000, q = 1 |

For reference, the same measure on the Indus texts gives:
- the published Yajnadevam key: 0.579 (§4.22);
- random keys drawn from the same inventory, before fitting: 0.36–0.61 on the Indus training texts;
- the correct key on real Sanskrit texts of the same length: 0.535 (word-aligned, positive control).

**Findings.**
1. **Fitted values make any text read as Sanskrit, including held-out text.** With this fitting freedom, the US Constitution read letter by letter gets a complete Sanskrit parse in 100% of held-out texts. Random sign strings reach 92–93%, and Akkadian 96–98%. The Indus texts (90–92%) sit inside this range. A high readability score, even on held-out inscriptions, therefore does not distinguish the Indus script from English, from Akkadian, or from random strings.
2. **The unicity-distance criterion does not protect against this.** Each held-out set of 449 texts contains about 1,800–1,840 symbols. Fitted keys fully parse 1,360–1,835 of them in every corpus, several times the 475-symbol threshold. Unicity distance assumes a fixed cipher system and a natural-language plaintext source. A key fitted to a parser with many value choices and an optional vowel breaks both assumptions.
3. **No fitted key reads real sign order significantly better than shuffled order** on the held-out texts, in any corpus (all q ≥ .12; 50 shuffles, so the minimum p is .02). Real English words come closest (+2 to +6 points), and the Indus texts are similar (0 to +5 points). Correct keys for real Sanskrit lose 17–20 points on this measure under the same shuffle (§4.22). This is why the shuffle benchmark (`tools/evaluate_key.py`, `docs/SUBMIT_A_KEY.md`) uses sign order, not readability, as its test.
4. **Real Sanskrit scores lowest** (78–81%) when its aksharas are given re-fitted values. It has many more sign types (1,148), so the 150 fitted types cover less of the text. This is not evidence about Sanskrit. It shows that readability depends on how many sign types the fit can reach.

**What this does and does not show.** We reproduced the Panini Protocol's critique in a controlled form: the method's degrees of freedom are enough to make arbitrary text read as Sanskrit. This does not prove that any particular published reading is wrong. It means that high Sanskrit readability, including on held-out inscriptions and beyond the unicity distance, is not evidence for a decipherment. What a correct key must also show is a large loss under shuffling, as correct keys for known scripts do.

**Caveats.**
- We used Yajnadevam's value inventory and reading rule, but not his exact procedure (he assigns values by hand, using sign shapes and his own constraints).
- Our hill-climb is short (3,000 steps). A longer search would read even more.
- The vidyut parse accepts any sequence of valid Sanskrit words. It does not check meaning.
