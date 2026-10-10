# Dangermond Project — Step 1: GBIF Download (Arthropoda, California)

The entry point of the pipeline. Queries GBIF for every Arthropoda
occurrence record in California — every record type, not just
preserved specimens — and downloads the resulting Darwin Core Archive.

## What's produced

1. **`output/dwca/`** — the unzipped Darwin Core Archive (occurrence
   data plus GBIF's standard DwC-A companion files).
2. **`output/doi.txt`** — the DOI GBIF assigns to this specific
   download request, on its own so it's easy to grab for citation.
   GBIF assigns this at submission time, before the archive itself has
   finished being prepared, so the script writes it out early rather
   than waiting on the full download.
3. **`output/download_metadata.txt`** — a small audit record (download
   key, DOI, resolved taxon key, predicates used, submission
   timestamp) kept separate from the DOI-only file so that file stays
   a single clean value.

## Key decisions

**Resolve "Arthropoda" via the backbone taxonomy, not a hardcoded
key:** `rgbif::name_backbone(name = "Arthropoda", rank = "phylum")`
looks up the current GBIF backbone taxonKey at run time, rather than
hardcoding a numeric ID that could go stale or be mistyped with no
obvious symptom.

**California via `gadm`, not `stateProvince`:** GBIF's
`stateProvince` field is free text supplied by individual data
publishers ("California", "CA", "Calif.", sometimes missing or in
another language) and matching against it as a string is unreliable.
`pred("gadm", "USA.5_1")` matches on GADM's actual administrative
boundary geometry for California instead — a geometric membership
test, not a text match — so it doesn't silently miss records where a
publisher used a different string for the same state. (Note the
predicate key is `gadm`, not `gadmGid` — see "Verified against the
real GBIF download" below for why that distinction mattered in
practice.)

**All record types included:** no `basisOfRecord` predicate is
applied, so preserved specimens, human observations, machine
observations, living specimens, fossil specimens, and anything else
GBIF tracks are all included, per the original request.

**`hasGeospatialIssue = FALSE`:** excludes records GBIF's own automated
quality checks have already flagged as having a geospatial problem
(e.g. coordinates outside the stated country). This is a coarse
first-pass filter only — Step 5 does its own stricter
coordinate-completeness check later regardless, so this isn't the only
line of defense against bad coordinates.

## Credentials

GBIF downloads require an account. This script authenticates via
`rgbif`'s standard environment-variable convention (`GBIF_USER` /
`GBIF_PWD` / `GBIF_EMAIL`, normally set in `~/.Renviron`) rather than
anything hardcoded in the script or shared in chat — set those three
variables in your own environment before running it.

## Verified against the real GBIF download

This step has been run end-to-end against the live GBIF API using the
user's own credentials (never shared in chat — see "Credentials"
above). That real run surfaced three bugs that no static review or
synthetic test data had caught, since all three only manifest with
`rgbif`'s actual live-API behavior:

1. `pred("gadmGid", "USA.5_1")` is wrong: `gadmGid` is a field name on
   GBIF's `/occurrence/search` API, but `occ_download()`'s predicate
   DSL uses the key name `gadm` instead. Using `gadmGid` here either
   errors or silently fails to scope the request to California. Fixed
   to `pred("gadm", "USA.5_1")` — this is the predicate actually used
   by the script now (see "Key decisions" above).
2. `backbone_match$usageKey` can come back as a character value, not
   numeric, depending on the match — the `%d` format specifier in the
   two `sprintf()` calls that print it threw "invalid format" in that
   case. Fixed to `%s` in both places.
3. `occ_download_get()` returns a classed character vector (the file
   path itself), not a list with a `$path` element — `dl_path$path`
   was therefore `NULL`/invalid. Fixed to `as.character(dl_path)`.

**Confirmed working end-to-end against the real GBIF API**:
4,665,086 Arthropoda records returned for California, DOI
`10.15468/dl.vgv5ee`, download key `0010070-260921141020460`,
submitted 2026-09-28. `output/doi.txt` and `output/download_metadata.txt`
in this repo are the real files this run produced, kept as the
citation/audit record for that specific download — not placeholders
or reconstructed examples.

An earlier revision of this file carried a caveat saying this script
had only been reconstructed from conversation history after a
workspace reset and not yet re-run for real — that was accurate at the
time it was written, but became stale once the real run above
happened and was never updated to match. This section replaces it.

## Paths

Everything writes to `./output/`, created automatically if it doesn't
exist.
