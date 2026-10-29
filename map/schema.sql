-- Unified Indus map schema (SQLite). Every factual row references sources.source_id.
CREATE TABLE sources (source_id TEXT PRIMARY KEY, citation TEXT, year TEXT, url TEXT, type TEXT, access TEXT, opened_this_session TEXT);
CREATE TABLE sites (site_id INTEGER PRIMARY KEY, name TEXT UNIQUE, region TEXT, country TEXT, lat REAL, lon REAL, period TEXT, source_id TEXT REFERENCES sources);
CREATE TABLE objects (object_id TEXT PRIMARY KEY, corpus TEXT, cisi_id TEXT, site_id INTEGER REFERENCES sites, object_type TEXT, material TEXT, motif TEXT,
  date_range TEXT, museum TEXT, accession TEXT, source_id TEXT REFERENCES sources);
CREATE TABLE inscriptions (inscription_id TEXT PRIMARY KEY, object_id TEXT REFERENCES objects, corpus TEXT, n_signs INTEGER, damaged TEXT,
  order_note TEXT, sign_scheme TEXT, source_id TEXT REFERENCES sources);
CREATE TABLE sign_tokens (inscription_id TEXT REFERENCES inscriptions, position INTEGER, sign_id TEXT, scheme TEXT, is_damage_marker INTEGER,
  PRIMARY KEY (inscription_id, position));   -- position 1 = first sign in READING order
CREATE TABLE signs (sign_id TEXT PRIMARY KEY, scheme TEXT, description TEXT, source_id TEXT);  -- M###=Mahadevan 1977, P###=Parpola 1994/CISI, W###=Wells/ICIT
CREATE TABLE sign_concordance (parpola_id TEXT, scheme TEXT, other_id TEXT, source_id TEXT, note TEXT);
CREATE TABLE images (image_id INTEGER PRIMARY KEY AUTOINCREMENT, file TEXT, object_ref TEXT, description TEXT, license TEXT, license_url TEXT,
  attribution TEXT, source_url TEXT, source_id TEXT, downloaded TEXT);
CREATE TABLE claims (claim_id TEXT PRIMARY KEY, proponent TEXT, year TEXT, language_or_type TEXT, method TEXT, scope TEXT, source_id TEXT, label TEXT, notes TEXT);
CREATE TABLE claimed_sign_values (claim_id TEXT REFERENCES claims, sign_id TEXT, value TEXT, provenance TEXT, label TEXT);
CREATE TABLE leads (lead_id TEXT PRIMARY KEY, url TEXT, platform TEXT, claimant_or_author TEXT, claim_summary TEXT, status TEXT, date_seen TEXT);
CREATE TABLE comparanda_scripts (id TEXT PRIMARY KEY, name TEXT, dates TEXT, region TEXT, script_type TEXT, sign_inventory TEXT,
  contact_evidence_with_indus TEXT, claimed_link_to_indus TEXT, label TEXT, source_ids TEXT);
CREATE TABLE comparanda_languages (id TEXT PRIMARY KEY, name TEXT, family TEXT, attested_dates TEXT, region TEXT, proposed_link_to_indus TEXT,
  evidence_summary TEXT, label TEXT, source_ids TEXT);
CREATE VIEW v_text AS SELECT i.corpus, i.inscription_id, o.cisi_id, s.name AS site, o.object_type, group_concat(t.sign_id, ' ') AS reading_order
  FROM inscriptions i JOIN objects o USING(object_id) LEFT JOIN sites s USING(site_id) JOIN (SELECT * FROM sign_tokens ORDER BY inscription_id, position) t USING(inscription_id)
  GROUP BY i.inscription_id;
