"""Run the starter analyses on every corpus in CORPORA. Outputs -> outputs/<corpus>/, figures/<corpus>_*.png
Reading order normalisation (verified this session from the jar sign's position, see notes/TRANSCRIPTION.md):
  M77 (IM77/IDF80 export): stored in reading order -> no reversal
  icitweb (yajnadevam/indus-website dump, ICIT/Wells-style numbers): stored in visual L->R order -> reverse
  cisi_mayig (Carlson's CISI digitisation, Parpola numbers): stored in visual L->R order -> reverse
"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(__file__))
import indus_lib as L
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data/joyboseroy_indus_decipher/data")
CORPORA = {
  "M77": dict(path=f"{D}/m77_indusscript_real_corpus.csv", reverse=False, breakers={"MSg0"}),
  "icitweb": dict(path=f"{D}/indus_website_real_corpus.csv", reverse=True, breakers={"G0", "G999"}),
  "cisi_mayig": dict(path=f"{D}/cisi_real_corpus.csv", reverse=True, breakers={"P000"}),
}
if len(sys.argv) > 1 and sys.argv[1] == "--toy":
    CORPORA = {"TOY": dict(path=os.path.join(ROOT, "data/toy/toy_corpus.csv"), reverse=False, breakers={"X"})}

summary = {}
for name, cfg in CORPORA.items():
    out = os.path.join(ROOT, "outputs", name); os.makedirs(out, exist_ok=True)
    fig = os.path.join(ROOT, "figures"); os.makedirs(fig, exist_ok=True)
    df, T = L.load_csv(cfg["path"], reverse=cfg["reverse"]); S = [s for _, s in T]; B = cfg["breakers"]
    freq = L.sign_frequency(S, B); freq.to_csv(f"{out}/sign_frequency.csv", index=False)
    pos = L.positional(S, B); pos.to_csv(f"{out}/positional.csv", index=False)
    for n in (2, 3, 4):
        c = L.ngrams(S, n, B)
        pd.DataFrame([(" ".join(k), v) for k, v in c.most_common()], columns=["ngram", "count"]).to_csv(f"{out}/ngrams_{n}.csv", index=False)
    z_all = L.zipf_fit(freq); z_top = L.zipf_fit(freq, 100)
    # Zipf figure
    plt.figure(figsize=(5, 4)); plt.loglog(freq["rank"], freq["count"], ".", ms=3)
    plt.title(f"{name}: rank-frequency"); plt.xlabel("rank"); plt.ylabel("count"); plt.tight_layout(); plt.savefig(f"{fig}/{name}_zipf.png", dpi=120); plt.close()
    # entropy curve
    nsig = len(freq); sizes = sorted(set([k for k in (10, 20, 50, 100, 200, 300, 400, 600) if k < nsig] + [nsig]))
    ec = L.entropy_vs_tokens(S, sizes, B, reps=10); ec.to_csv(f"{out}/cond_entropy_curve.csv", index=False)
    plt.figure(figsize=(5, 4))
    plt.plot(ec.k, ec.H_real, "o-", label="real")
    plt.plot(ec.k, ec.H_within_shuffle, "s--", label="shuffled within text")
    plt.plot(ec.k, ec.H_global_shuffle, "^:", label="global shuffle (length-preserving)")
    plt.xlabel("# most frequent signs kept"); plt.ylabel("H(next|prev), bits"); plt.title(f"{name}: bigram conditional entropy"); plt.legend(fontsize=7); plt.tight_layout(); plt.savefig(f"{fig}/{name}_cond_entropy.png", dpi=120); plt.close()
    # positional figure (top 25 signs)
    p = pos.head(25).set_index("sign")[["solo_pct", "initial_pct", "medial_pct", "final_pct"]]
    p.plot(kind="bar", stacked=True, figsize=(9, 4)); plt.ylabel("% of occurrences"); plt.title(f"{name}: positional profile, top-25 signs (reading order; undamaged texts only)"); plt.tight_layout(); plt.savefig(f"{fig}/{name}_positional.png", dpi=120); plt.close()
    # segmentation
    segt, segs = L.branching_entropy_segments(S, B)
    pd.DataFrame([(" ".join(k), len(k), v) for k, v in segs.most_common()], columns=["segment", "length", "count"]).to_csv(f"{out}/segments_branching_entropy.csv", index=False)
    lens = [len(s) for s in S]
    rng = random.Random(1)
    summary[name] = dict(
        n_texts=len(S), n_tokens=int(freq["count"].sum()), n_sign_types=nsig,
        hapax=int((freq["count"] == 1).sum()), mean_len=float(np.mean(lens)), median_len=float(np.median(lens)), max_len=int(max(lens)),
        signs_for_50pct_tokens=int((freq["cum_freq"] < 0.5).sum() + 1), signs_for_80pct_tokens=int((freq["cum_freq"] < 0.8).sum() + 1),
        top10=freq.head(10)[["sign", "count"]].values.tolist(),
        zipf_all=z_all, zipf_top100=z_top,
        H_unigram=L.unigram_entropy(S, B), H_cond_real=L.conditional_entropy(S, B),
        H_cond_within_shuffle=float(np.mean([L.conditional_entropy(L.shuffle_within(S, rng), B) for _ in range(20)])),
        H_cond_global_shuffle=float(np.mean([L.conditional_entropy(L.shuffle_global(S, rng), B) for _ in range(20)])),
        direction=L.direction_score(S, B),
        top_final_pct=pos[pos.total >= 50].sort_values("final_pct", ascending=False).head(8)[["sign", "total", "final_pct"]].round(1).values.tolist(),
        top_initial_pct=pos[pos.total >= 50].sort_values("initial_pct", ascending=False).head(8)[["sign", "total", "initial_pct"]].round(1).values.tolist(),
        top_bigrams=[(" ".join(k), v) for k, v in L.ngrams(S, 2, B).most_common(8)],
        top_trigrams=[(" ".join(k), v) for k, v in L.ngrams(S, 3, B).most_common(6)],
    )
json.dump(summary, open(os.path.join(ROOT, "outputs", "summary.json" if "TOY" not in summary else "summary_toy.json"), "w"), indent=1, default=str)
print(json.dumps(summary, indent=1, default=str))
