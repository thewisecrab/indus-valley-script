"""Build the unified Indus 'map' as SQLite (map/indus_map.sqlite) + network exports.
Only data obtained and checked this session is loaded. Every row carries a source_id."""
import sqlite3, csv, json, os, glob, re, sys
from collections import Counter, defaultdict
import pandas as pd, networkx as nx
sys.path.insert(0, os.path.dirname(__file__)); import indus_lib as L
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = f"{R}/map/indus_map.sqlite"
if os.path.exists(DB): os.remove(DB)
con = sqlite3.connect(DB); cur = con.cursor()
cur.executescript(open(f"{R}/map/schema.sql").read())
def load_seed(table, path):
    df = pd.read_csv(path, dtype=str).fillna(""); df.to_sql(table, con, if_exists="append", index=False); return len(df)
n = {t: load_seed(t, f"{R}/map/seed/{t}.csv") for t in ["sources", "leads", "claims", "comparanda_scripts", "comparanda_languages"]}
# dataset sources
ds = [("ds_m77", "IM77/IDF80 Mahadevan corpus export (indusscript.in Firestore) as converted in joyboseroy/indus_decipher@cd60034", "", "https://github.com/joyboseroy/indus_decipher", "dataset", "MIT repo; upstream RMRL/ASI rights unclear - private research use only", "yes"),
      ("ds_icitweb", "yajnadevam/indus-website DB dump as converted in joyboseroy/indus_decipher (ICIT-style sign numbers, CISI object ids)", "", "https://github.com/yajnadevam/indus-website", "dataset", "GPL-3.0", "yes"),
      ("ds_mayig", "M. Carlson, mayig/indus-valley-script-corpus@ad2f1e2 (CISI digitisation, Parpola numbering, Parpola-Wells-Mahadevan sign matching)", "2024-2025", "https://github.com/mayig/indus-valley-script-corpus", "dataset", "MIT", "yes"),
      ("ds_commons", "Wikimedia Commons categories Indus script / Indus civilization seals / Indus script tablets", "", "https://commons.wikimedia.org/wiki/Category:Indus_script", "images", "per file (CC0/PD/CC BY/CC BY-SA)", "yes"),
      ("ds_met", "Metropolitan Museum of Art Open Access API", "", "https://metmuseum.github.io/", "images", "CC0 for isPublicDomain objects", "yes")]
cur.executemany("INSERT INTO sources VALUES (?,?,?,?,?,?,?)", ds)
D = f"{R}/data/joyboseroy_indus_decipher/data"
CORP = [("M77", f"{D}/m77_indusscript_real_corpus.csv", False, "MSg", "mahadevan", "ds_m77", {"MSg0"}),
        ("icitweb", f"{D}/indus_website_real_corpus.csv", True, "G", "icit_wells", "ds_icitweb", {"G0", "G999"}),
        ("cisi_mayig", f"{D}/cisi_real_corpus.csv", True, "P", "parpola", "ds_mayig", {"P000"})]
def norm(tok, prefix, scheme):
    num = tok[len(prefix):]
    if scheme == "parpola": return "P" + num.zfill(3)
    if scheme == "mahadevan": return "M" + str(int(num)).zfill(3)
    return "W" + str(int(num)).zfill(3)
sites = {}
for corpus, path, rev, pre, scheme, src, brk in CORP:
    df = pd.read_csv(path, dtype=str).fillna("")
    for _, r in df.iterrows():
        seq = r["sign_sequence"].split()
        if rev: seq = seq[::-1]
        site = r.get("site", "") if r.get("site", "") not in ("", "unknown") else None
        if site and site not in sites:
            sites[site] = len(sites) + 1; cur.execute("INSERT INTO sites(site_id,name,source_id) VALUES (?,?,?)", (sites[site], site, src))
        cisi = r.get("cisi_number", "").strip()
        if cisi in ("-", "--", "?", "unknown"): cisi = ""
        obj_id = f"{corpus}:{cisi or (r['inscription_id'].split('.')[0] if corpus == 'M77' else r['inscription_id'])}"
        cur.execute("INSERT OR IGNORE INTO objects(object_id,corpus,cisi_id,site_id,object_type,motif,source_id) VALUES (?,?,?,?,?,?,?)",
                    (obj_id, corpus, cisi or (r["inscription_id"] if corpus == "cisi_mayig" else None), sites.get(site),
                     r.get("object_type") if r.get("object_type") not in ("", "unknown") else None, r.get("motif") if r.get("motif") not in ("", "unknown") else None, src))
        iid = f"{corpus}:{r['inscription_id']}"
        cur.execute("INSERT INTO inscriptions VALUES (?,?,?,?,?,?,?,?)", (iid, obj_id, corpus, len(seq), r.get("damaged"), "reversed_to_reading_order" if rev else "as_stored_reading_order", scheme, src))
        cur.executemany("INSERT INTO sign_tokens VALUES (?,?,?,?,?)", [(iid, i + 1, norm(t, pre, scheme), scheme, 1 if t in brk else 0) for i, t in enumerate(seq)])
# sign list + concordance from mayig features (MIT)
for fp in sorted(glob.glob(f"{R}/data/mayig_indus-valley-script-corpus/features/P*.json")):
    j = json.load(open(fp)); pid = j["id"]
    cur.execute("INSERT OR IGNORE INTO signs VALUES (?,?,?,?)", (pid, "parpola", j.get("description", "").strip(), "ds_mayig"))
    for w in j.get("wells_graphemes", []):
        cur.execute("INSERT INTO sign_concordance VALUES (?,?,?,?,?)", (pid, "wells", w, "ds_mayig", "hand-matched by M. Carlson; unverified"))
    for m in j.get("mahadevan_graphemes", []):
        cur.execute("INSERT INTO sign_concordance VALUES (?,?,?,?,?)", (pid, "mahadevan", m, "ds_mayig", "hand-matched by M. Carlson; unverified"))
    for v in j.get("parpola_graphemes", []):
        cur.execute("INSERT INTO sign_concordance VALUES (?,?,?,?,?)", (pid, "parpola_variant", v, "ds_mayig", "Parpola 1994 variant numbers as recorded by Carlson"))
for scheme, pre in [("mahadevan", "M"), ("icit_wells", "W")]:
    for (sid,) in cur.execute("SELECT DISTINCT sign_id FROM sign_tokens WHERE scheme=?", (scheme,)).fetchall():
        con.execute("INSERT OR IGNORE INTO signs VALUES (?,?,?,?)", (sid, scheme, None, "ds_m77" if scheme == "mahadevan" else "ds_icitweb"))
# claimed sign values (Yajnadevam) from field-cady xlits.csv - recorded as a CLAIM, not data
xl = pd.read_csv(f"{R}/data/field-cady_indus_valley_script_corpus/xlits.csv", dtype=str).fillna("")
for _, r in xl.iterrows():
    cur.execute("INSERT INTO claimed_sign_values VALUES (?,?,?,?,?)", ("C7", "W" + r["sign"].zfill(3), r["xlit"], "field-cady/xlits.csv (derived from yajnadevam/lipi; upstream licence not stated)", "fringe"))
# images
if os.path.exists(f"{R}/data/images/commons/manifest.csv"):  # session 6: optional (fresh clones)
    for row in csv.DictReader(open(f"{R}/data/images/commons/manifest.csv")):
        cur.execute("INSERT INTO images(file,object_ref,description,license,license_url,attribution,source_url,source_id,downloaded) VALUES (?,?,?,?,?,?,?,?,?)",
                    (row["local_file"] or None, None, row["title"] + " | " + row["description"][:200], row["license"], row["license_url"], row["artist"], row["page"], "ds_commons", row["downloaded"]))
elif os.path.exists(f"{R}/data_open/images/commons/manifest.csv"):  # session 7: public repo ships the open subset in data_open/
    for row in csv.DictReader(open(f"{R}/data_open/images/commons/manifest.csv")):
        cur.execute("INSERT INTO images(file,object_ref,description,license,license_url,attribution,source_url,source_id,downloaded) VALUES (?,?,?,?,?,?,?,?,?)",
                    ("data_open/images/commons/" + row["file"], None, row["title"], row["license"], row["license_url"], row["author"], row["source_page"], "ds_commons", "yes"))
_met = f"{R}/data/images/met/manifest.csv" if os.path.exists(f"{R}/data/images/met/manifest.csv") else f"{R}/data_open/images/met/manifest.csv"
if os.path.exists(_met):
    for row in csv.DictReader(open(_met)):
        cur.execute("INSERT INTO images(file,object_ref,description,license,license_url,attribution,source_url,source_id,downloaded) VALUES (?,?,?,?,?,?,?,?,?)",
                    (row["local_file"] or None, "Met " + row["accession"], f"{row['title']} | {row['date']} | {row['medium']}", "CC0" if row["isPublicDomain"] == "True" else "unknown",
                     "https://creativecommons.org/publicdomain/zero/1.0/", "The Metropolitan Museum of Art", row["url"], "ds_met", "yes" if row["local_file"].startswith("met_") else "no"))
con.commit()
# ---- concordance cross-check: does Carlson's 1:1 M<->W matching agree with corpus behaviour? ----
def profile(corpus, breakers):
    q = con.execute("SELECT inscription_id, group_concat(sign_id,' ') FROM (SELECT * FROM sign_tokens t JOIN inscriptions i USING(inscription_id) WHERE i.corpus=? ORDER BY inscription_id, position) GROUP BY inscription_id", (corpus,)).fetchall()
    S = [s.split() for _, s in q]; f = L.sign_frequency(S, breakers).set_index("sign"); p = L.positional(S, breakers).set_index("sign")
    return f, p
fM, pM = profile("M77", {"M000"}); fW, pW = profile("icitweb", {"W000", "W999"})
conc = pd.read_sql("SELECT a.parpola_id, a.other_id AS W, b.other_id AS M FROM sign_concordance a JOIN sign_concordance b USING(parpola_id) WHERE a.scheme='wells' AND b.scheme='mahadevan'", con)
one = conc.groupby("parpola_id").filter(lambda g: g.W.nunique() == 1 and g.M.nunique() == 1).drop_duplicates("parpola_id")
rows = []
for _, r in one.iterrows():
    if r.M in fM.index and r.W in fW.index and r.M in pM.index and r.W in pW.index:
        rows.append(dict(parpola=r.parpola_id, M=r.M, W=r.W, relfreq_M=fM.loc[r.M, "rel_freq"], relfreq_W=fW.loc[r.W, "rel_freq"],
                         final_M=pM.loc[r.M, "final_pct"], final_W=pW.loc[r.W, "final_pct"], init_M=pM.loc[r.M, "initial_pct"], init_W=pW.loc[r.W, "initial_pct"], nM=pM.loc[r.M, "total"], nW=pW.loc[r.W, "total"]))
cc = pd.DataFrame(rows); cc.to_csv(f"{R}/outputs/concordance_crosscheck.csv", index=False)
big = cc[(cc.nM >= 30) & (cc.nW >= 30)]
from scipy.stats import spearmanr
res = dict(n_one_to_one_pairs=len(one), n_pairs_in_both_corpora=len(cc), n_pairs_freq30=len(big),
           spearman_relfreq=spearmanr(cc.relfreq_M, cc.relfreq_W).correlation if len(cc) > 2 else None,
           spearman_final_pct_freq30=spearmanr(big.final_M, big.final_W).correlation if len(big) > 2 else None,
           spearman_initial_pct_freq30=spearmanr(big.init_M, big.init_W).correlation if len(big) > 2 else None)
# ---- networks ----
G = nx.DiGraph()
q = con.execute("SELECT inscription_id, group_concat(sign_id,' ') FROM (SELECT * FROM sign_tokens t JOIN inscriptions i USING(inscription_id) WHERE i.corpus='M77' AND t.is_damage_marker=0 ORDER BY inscription_id, position) GROUP BY inscription_id").fetchall()
bg = L.ngrams([s.split() for _, s in q], 2)
for (a, b), k in bg.items():
    if k >= 5: G.add_edge(a, b, weight=k)
nx.write_graphml(G, f"{R}/map/m77_bigram_network_min5.graphml")
B = nx.Graph()
for site, sign, k in con.execute("SELECT s.name, t.sign_id, count(*) FROM sign_tokens t JOIN inscriptions i USING(inscription_id) JOIN objects o USING(object_id) JOIN sites s USING(site_id) WHERE i.corpus='icitweb' AND t.is_damage_marker=0 GROUP BY 1,2"):
    B.add_node(site, kind="site"); B.add_node(sign, kind="sign"); B.add_edge(site, sign, weight=k)
nx.write_graphml(B, f"{R}/map/icitweb_site_sign_bipartite.graphml")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
top = [n for n, _ in sorted(G.degree(weight="weight"), key=lambda x: -x[1])[:40]]
H = G.subgraph(top); pos = nx.spring_layout(H, seed=3, k=0.6)
plt.figure(figsize=(10, 8)); w = [H[u][v]["weight"] for u, v in H.edges()]
nx.draw_networkx(H, pos, node_size=[30 + 3 * H.degree(n, weight="weight") ** 0.8 for n in H], font_size=7, width=[0.3 + x / 60 for x in w], arrowsize=6, node_color="#cfe3f7", edge_color="#888")
plt.title("M77: bigram network among the 40 most connected signs (edges >=5 occurrences, reading order)"); plt.axis("off"); plt.tight_layout(); plt.savefig(f"{R}/figures/M77_bigram_network.png", dpi=120); plt.close()
# site summary
site_tab = pd.read_sql("SELECT s.name site, count(DISTINCT o.object_id) objects, count(t.sign_id) tokens FROM sites s JOIN objects o USING(site_id) JOIN inscriptions i USING(object_id) JOIN sign_tokens t USING(inscription_id) WHERE o.corpus='icitweb' GROUP BY 1 ORDER BY 2 DESC", con)
site_tab.to_csv(f"{R}/outputs/icitweb_sites.csv", index=False)
counts = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ["sources", "sites", "objects", "inscriptions", "sign_tokens", "signs", "sign_concordance", "images", "claims", "claimed_sign_values", "leads", "comparanda_scripts", "comparanda_languages"]}
res.update(table_counts=counts, images_downloaded=con.execute("SELECT count(*) FROM images WHERE downloaded='yes'").fetchone()[0],
           m77_network=dict(nodes=G.number_of_nodes(), edges=G.number_of_edges()), bipartite=dict(nodes=B.number_of_nodes(), edges=B.number_of_edges()),
           top_sites=site_tab.head(8).values.tolist())
json.dump(res, open(f"{R}/outputs/map_build_summary.json", "w"), indent=1, default=float); print(json.dumps(res, indent=1, default=float))
