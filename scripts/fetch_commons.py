"""Fetch openly licensed images from Wikimedia Commons categories, recording license + attribution.
Only licenses matching ALLOWED are downloaded. Writes data/images/commons/manifest.csv"""
import requests, csv, os, re, time, sys
UA = {"User-Agent": "IndusResearchWorkspace/0.1 (personal research; python-requests)"}
API = "https://commons.wikimedia.org/w/api.php"
CATS = ["Category:Indus script", "Category:Indus civilization seals", "Category:Indus script tablets"]
ALLOWED = re.compile(r"^(CC0|Public domain|PD|CC BY(-SA)? [0-9.]+|CC BY(-SA)?)", re.I)
OUT = os.path.join(os.path.dirname(__file__), "..", "data/images/commons"); os.makedirs(OUT, exist_ok=True)
MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 80
rows, seen = [], set()
for cat in CATS:
    r = requests.get(API, params=dict(action="query", generator="categorymembers", gcmtitle=cat, gcmtype="file", gcmlimit=500,
        prop="imageinfo", iiprop="url|extmetadata|size|mime", iiurlwidth=1200, format="json"), headers=UA, timeout=60).json()
    for p in (r.get("query", {}).get("pages", {}) or {}).values():
        t = p["title"]
        if t in seen or "imageinfo" not in p: continue
        seen.add(t); ii = p["imageinfo"][0]; md = ii.get("extmetadata", {})
        lic = md.get("LicenseShortName", {}).get("value", "")
        strip = lambda s: re.sub("<[^>]+>", "", s or "").strip()
        row = dict(title=t, category=cat, license=lic, license_url=md.get("LicenseUrl", {}).get("value", ""),
                   artist=strip(md.get("Artist", {}).get("value", "")), credit=strip(md.get("Credit", {}).get("value", ""))[:200],
                   description=strip(md.get("ImageDescription", {}).get("value", ""))[:300], page=ii.get("descriptionurl"),
                   url=ii.get("thumburl") or ii.get("url"), mime=ii.get("mime"), downloaded="no", local_file="")
        if ALLOWED.match(lic) and ii.get("mime", "").startswith("image/") and sum(1 for x in rows if x["downloaded"] == "yes") < MAX:
            fn = re.sub(r"[^A-Za-z0-9._-]+", "_", t.replace("File:", ""))[:120]
            ext = os.path.splitext(row["url"])[1] or ".jpg"
            if not fn.lower().endswith(ext.lower()): fn += ext
            try:
                b = requests.get(row["url"], headers=UA, timeout=60); b.raise_for_status()
                open(os.path.join(OUT, fn), "wb").write(b.content); row["downloaded"] = "yes"; row["local_file"] = fn
            except Exception as e:
                row["downloaded"] = f"error:{e}"[:80]
            time.sleep(0.5)
        rows.append(row)
with open(os.path.join(OUT, "manifest.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows), "files listed;", sum(r["downloaded"] == "yes" for r in rows), "downloaded")
