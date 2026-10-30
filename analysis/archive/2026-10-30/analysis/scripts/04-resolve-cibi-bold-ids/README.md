# Dangermond Project — Step 4: Resolve BOLD-Placeholder Records Against an Optional Reference Dataset

New step, inserted after Step 3 was first run against the real,
live-GBIF data revealed how many records needed it. Picks up after
Step 3 (`../03-merge-deduplicate/`) and, before any of this pipeline's
name-cleaning or species-level grouping runs, resolves whichever
`BOLD:XXXXXXX` placeholder records it can against a known barcode
project's own identifications — for this project, the user's CIBI
Barcode Project spreadsheet.

**This step is optional.** Not every user of this pipeline will have
BOLD identification data to resolve against. If the reference file
below isn't present, this step runs as a no-op pass-through — Step 3's
data goes through completely unchanged — rather than erroring or
requiring anyone to edit Step 5's input path. See "Running without
reference data" below.

## Why this step exists

Step 4 (now Step 5)'s real-data verification surfaced 715,978 records
— about 15% of the merged dataset — whose `scientificName` is a BOLD
Systems BIN (Barcode Index Number) identifier like `BOLD:ABX4063`, not
a taxonomic name. These are DNA-barcode-only specimens, mostly from the
Centre for Biodiversity Genomics (`basisOfRecord = MATERIAL_SAMPLE`):
no formal identification had been promoted into GBIF's `scientificName`
field, only the barcode cluster it fell into.

Left alone, each distinct BIN code is correctly kept as its own group
(a prior bug that collapsed all of them into one fake species called
"BOLD" was fixed in Step 5 — see that step's README), but every one of
those 715,978 records still carries no more identification than family
rank at best.

The user's own CIBI Barcode Project spreadsheet — a direct BOLD Systems
export for 16,471 specimens from a related California survey — turned
out to carry real identifications for a meaningful slice of exactly
these records, keyed on `processid`, which is the same value GBIF
carries as `occurrenceID` for BOLD-sourced records. No fuzzy matching
is involved: either the ID is present in both datasets or it isn't.

## What's produced

**`output/dwc_merged_cibi_resolved.csv`** — the same 4,658,904 records
as Step 3's output, same columns, with three added:

- `cibi_matched` — `TRUE` if this record's `occurrenceID` matched a
  `processid` in the CIBI spreadsheet (only possible for BOLD-placeholder
  records to begin with).
- `cibi_identification` — the CIBI identification, at whatever rank it
  was recorded at, for every matched record (not just the ones that
  changed `scientificName` — see below).
- `cibi_identification_rank` — that identification's rank (`species`,
  `genus`, `family`, `subfamily`, or `tribe` in this dataset).

**`output/cibi_resolution_summary.csv`** — a small summary table (total
records, BOLD-placeholder count, match count, and the breakdown by
rank) for reporting purposes, independent of the main output.

## Key decision: only species-rank matches replace `scientificName`

The CIBI spreadsheet's own identifications are mostly NOT species-level
— of the 9,776 matches found in the real data, only 3,144 are resolved
to a full species name. The rest are genus (3,382), family (1,794),
subfamily (1,439), or tribe (17).

Writing a bare genus or family name into `scientificName` for those
would recreate, at a smaller scale, the exact bug Step 5 already fixed
for the literal "BOLD" placeholder: every record sharing that genus or
family would collapse into one fake "species" for later species-level
counts and Step 8's per-species convex hulls, even though CIBI's own
data explicitly does NOT claim they're the same species.

So only a true species-rank CIBI match replaces `scientificName` — a
real, unambiguous identification (e.g. "Delia platura"),
indistinguishable downstream from any other normally-identified GBIF
record. Every other matched record keeps its original `BOLD:XXXXXXX`
placeholder in `scientificName` (so it's still passed through unchanged
by Step 5's `clean_scientific_name()`, same as an unmatched BOLD
record), but carries its CIBI identification and rank in the two new
columns, so that information isn't lost — it's just kept out of the
species-level analysis and available for reporting instead.

## Running without reference data

If `infile_reference` doesn't exist when the script runs, it logs that
it's skipping resolution and writes Step 3's records straight through:
same row count, `scientificName` completely untouched, and the three
added columns still present but blank (`cibi_matched = FALSE`,
`cibi_identification`/`cibi_identification_rank = NA`) so Step 5 always
reads the same schema regardless of which path this step took. The
summary CSV records `reference_file_supplied = FALSE` and zeroes for
every match count, so a pass-through run is visibly distinguishable
from a real one, not silently indistinguishable from "zero matches
found."

Verified directly: running this script with the CIBI reference file
temporarily removed produced `reference_file_supplied = FALSE` and all
4,658,904 records written through with `scientificName` identical to
Step 3's output; restoring the file and re-running reproduced the
exact same 9,776/3,144 real numbers reported below, confirming the two
code paths don't interfere with each other.

To use a different reference dataset instead of CIBI's (another BOLD
Systems export, for a different survey or taxon group), point
`infile_reference` at it — it just needs `processid`, `species`,
`identification`, and `identification_rank` columns in the same shape.

## What this step does NOT do

- It does not attempt to resolve any of the other ~706,000
  BOLD-placeholder records not covered by the CIBI spreadsheet. A
  broader resolution via BOLD Systems' own public API was investigated
  and found technically feasible (the 715,978 flagged records collapse
  to only 16,995 distinct BIN codes, well within the API's batch
  limits), but was explicitly set aside for now — this step covers only
  what the CIBI spreadsheet itself can resolve.
- It does not touch, reorder, or drop any row. Every output row count
  matches the input exactly (verified below).
- It does not fill in `kingdom`/`phylum`/`class`/`order`/`family` from
  CIBI — GBIF's own export already carries these down to family for
  every BOLD-flagged record, so there's nothing missing at that level
  to backfill.

## Verified against the real pipeline run

Run against the real 4,658,904-record Step 3 output and the real CIBI
spreadsheet (16,471 records, 0 duplicate `processid`s):

- 715,978 BOLD-placeholder records found (matches Step 5's own count).
- 9,776 matched a CIBI `processid` (1.37% of the placeholders) — family
  1,794, genus 3,382, species 3,144, subfamily 1,439, tribe 17.
- 3,144 `scientificName` values replaced with a real species
  identification.
- 4,658,904 records written out — unchanged from the input row count.

This caused a small, expected ripple through every downstream step
that groups by species: Step 5's unique-species count moved from
53,632 to 53,763 (a net increase — species-level CIBI matches now split
out from their shared BIN-placeholder grouping rather than all counting
as one undifferentiated entry per BIN code), and Step 8's valid-hull
count moved from 27,327 to 27,348. See each downstream step's own
README/requirements for its updated real numbers.

## Paths

`infile_occurrences` points at Step 3's merged/deduplicated output.
`infile_reference` points at `../reference-data/cibi_barcode_identifications.csv`
by default — a cleaned extract (just the identification-relevant
columns) of the user's CIBI Barcode Project spreadsheet's "cibi barcode
results downloaded" sheet, kept in the shared reference-data folder
alongside the Preserve boundary file. Point it elsewhere (or delete/
rename that file) to use different reference data or none at all.
