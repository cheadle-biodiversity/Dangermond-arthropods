# Dangermond Project — Step 2: Trim GBIF Columns

New step, added after Step 1 was first run against the real, live GBIF
API. Picks up after Step 1 (`../01-download-gbif-arthropoda-ca/`) and
produces a column-reduced copy of the raw Darwin Core Archive export,
small enough to actually move and process.

## Why this step exists

Steps 3 through 7 of this pipeline only ever use a small subset of the
~230 columns a GBIF Darwin Core `occurrence.txt` export contains
(dedup identifiers, taxonomy, and coordinates) — everything else
(citation/rights metadata, event remarks, geological context,
free-text locality notes, media links, etc.) is dead weight for this
pipeline's purposes, but dominates the file's actual byte size.

This was discovered to be a real, practical problem rather than a
theoretical one: the real GBIF query for this project (all Arthropoda
occurrences in California) came back as a single **6.84 GB, 230-column**
file — far too large to move through a browser upload (30 MB limit) or
most device-to-cloud transfer paths (typically capped well under
1 GB per file). Trimming to just the needed columns first, before any
transfer or further processing, was the practical fix that unblocked
the rest of the pipeline.

## What's produced

**`output/occurrence_trimmed.txt`** — the same rows as the input, with
only these 14 columns, in this order:

```
gbifID, occurrenceID, institutionCode, collectionCode, catalogNumber,
basisOfRecord, decimalLatitude, decimalLongitude, scientificName,
kingdom, phylum, class, order, family
```

## Key decisions

**Columns selected by name, not position.** GBIF's column order can
differ across different downloads/export settings, so this reads the
real header and selects the needed columns by name — same philosophy
as Step 1 resolving the taxon key by name rather than a hardcoded ID.
A missing expected column fails fast with an explicit error (checked
against just the header line, before committing to reading the whole
multi-GB file), rather than partway through an hours-long parse.

**Nothing is permanently discarded.** The full original file is never
modified or deleted by this script, only read. A later step rejoins
full record detail back onto the small, final per-species outputs
using the same `occurrenceID` / `institutionCode`+`collectionCode`+
`catalogNumber` matching keys Step 3's dedup already uses — so
detail is deferred, not lost, until the data is small enough that
carrying every column stops being a problem.

**Two equivalent implementations.** `trim_gbif_columns.R` reads the
file with `readr::read_tsv(col_types = cols_only(...))`, which parses
column-by-column at the C++ level and never materializes the ~216
unwanted columns in memory. `trim_gbif_columns.py` does the same thing
by streaming the file line-by-line with Python's `csv` module. Both
exist because R wasn't guaranteed to be available on every machine
this step might run on; in practice, only the R version has been run
against the real data to date — the machine available for the real run
had a working R/RStudio setup but no working Python on `PATH` (a
Windows "App execution alias" stub shadowed the real installation).
The Python version is kept as a verified-on-synthetic-data reference
implementation for environments where that isn't the case.

## Verified against the real download

Run against the real 6.84 GB, 230-column `occurrence.txt`: produced a
**914,209,952-byte (≈872 MB) output — an ~87% size reduction** — with
**4,665,086 rows**, matching the original download's total record
count exactly, and all 14 expected columns present and correctly
ordered. No bugs surfaced in this step itself; the column selection
and row count matched expectations on the first real run.

Getting that 872 MB file transferred further still took one more
step not part of this script: gzip-compressing it (R's built-in
`gzfile()` connection, run in chunks to avoid loading the whole file
into memory) brought it down to 170 MB, under the transfer path's
per-file limit. That compression step is a one-off transfer workaround
specific to this project's environment, not part of the pipeline
itself, so it isn't included here.

## Paths

`input_path`/`output_path` at the top of each script assume they're
run from inside this folder, with Step 1's extracted `occurrence.txt`
present (or copied/transferred in, if moving it to a different
environment than the one Step 1 ran in — see this step's own header
comment for why that was necessary on this project).
