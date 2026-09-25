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

**California via `gadmGid`, not `stateProvince`:** GBIF's
`stateProvince` field is free text supplied by individual data
publishers ("California", "CA", "Calif.", sometimes missing or in
another language) and matching against it as a string is unreliable.
`pred("gadmGid", "USA.5_1")` matches on GADM's actual administrative
boundary geometry for California instead — a geometric membership
test, not a text match — so it doesn't silently miss records where a
publisher used a different string for the same state.

**All record types included:** no `basisOfRecord` predicate is
applied, so preserved specimens, human observations, machine
observations, living specimens, fossil specimens, and anything else
GBIF tracks are all included, per the original request.

**`hasGeospatialIssue = FALSE`:** excludes records GBIF's own automated
quality checks have already flagged as having a geospatial problem
(e.g. coordinates outside the stated country). This is a coarse
first-pass filter only — Step 3 does its own stricter
coordinate-completeness check later regardless, so this isn't the only
line of defense against bad coordinates.

## Credentials

GBIF downloads require an account. This script authenticates via
`rgbif`'s standard environment-variable convention (`GBIF_USER` /
`GBIF_PWD` / `GBIF_EMAIL`, normally set in `~/.Renviron`) rather than
anything hardcoded in the script or shared in chat — set those three
variables in your own environment before running it.

## Note on this copy (rebuilt after a workspace reset)

This script was reconstructed from conversation history after the
cloud workspace it originally lived in was reset. It has not
actually been re-run against the real GBIF API in this rebuild (that
would require live credentials, which were never shared in chat by
design — see "Credentials" above) — this is the same design as
originally built and reviewed, not a re-verified execution. If
anything about the predicate logic looks like it should behave
differently than described here, that's worth flagging before relying
on it for a real download.

## Paths

Everything writes to `./output/`, created automatically if it doesn't
exist.
