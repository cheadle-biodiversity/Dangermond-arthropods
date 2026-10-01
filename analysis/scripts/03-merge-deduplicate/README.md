# Dangermond Project — Step 3: Merge & Deduplicate

Picks up after Step 2 (the column-trimmed GBIF export, or any set of
raw Darwin Core exports) and produces one clean, deduplicated table.

## What's produced

1. **`output/dwc_merged_deduplicated.csv`** — every input file appended
   together, then deduplicated.
2. **`output/column_header_report.txt`** — which columns are present in
   every input file vs. only some of them, checked before merging.

## Key decisions

**A generalized `{name, path, delim}` input list, not two hardcoded
file variables:** this started as a two-file script under the
assumption that both inputs were split parts of a single GBIF download
(same format, same delimiter). That assumption turned out to be wrong
once a real second scenario came up — a Symbiota portal export (CSV)
merged with a GBIF export (TSV), two genuinely different sources, not
a split download. Rather than hardcode a second special case, inputs
are declared as a `tribble()` of rows, each with its own delimiter, so
the same script handles "reassemble a GBIF split download,"
"merge Symbiota + GBIF," or any other combination — add a row, re-run.

**Column-header comparison before merging, generalized to N files:**
flags any column present in some input files but not others, so a
source missing an expected field (e.g. one export not carrying
`order`/`family`) is visible immediately rather than discovered later
as a silent gap somewhere downstream.

**NA-safe deduplication** — the important bug fix in this step. See
below.

## The NA-collapse deduplication bug

Confirmed with a direct test before this fix was written, not just
suspected. dplyr's `distinct()` and `group_by() + slice(1)` treat `NA`
as an ordinary matching value, not as "unknown, don't match anything."
If several records are legitimately missing `occurrenceID` (`NA`), a
naive `distinct(occurrenceID, .keep_all = TRUE)` treats every one of
those `NA`s as a duplicate of every other `NA` — and collapses them all
down to a single row, silently discarding real, distinct records that
simply lack an ID. They were never actual duplicates of each other.

Verified directly:

```r
x <- tibble(id = c(NA, NA, "a"), val = c(1, 2, 3))
distinct(x, id, .keep_all = TRUE)
#> id     val
#> NA       1      <- record "2" is gone. Both NA rows were DIFFERENT
#>  a       3          records, not duplicates of each other.
```

**Fix:** split each dedup pass into two groups — rows that actually
have the key present, and rows missing it. Deduplicate only the
"key present" group, where a real duplicate judgment is possible; pass
the "key missing" group through untouched; recombine with
`bind_rows()`. Applied at both dedup stages: first `occurrenceID`, then
`institutionCode + collectionCode + catalogNumber` for whatever's left
without an `occurrenceID`.

## Missing columns

If `occurrenceID` or any of the three fallback key columns
(`institutionCode`, `collectionCode`, `catalogNumber`) is missing
entirely from the merged data, that dedup stage is skipped with an
explicit warning rather than erroring out or silently doing nothing —
the header report is the place to check first if that happens.

## Verified against the real download

Run against the real, live-GBIF output of Steps 1-2 (4,665,086 records,
14 columns after trimming): 4,658,904 records remained after both
dedup stages (6,182 duplicates removed — 6,164 by `occurrenceID`, 18
more by the institution/collection/catalog-number fallback). The
NA-collapse bug above was caught and fixed before this real run, using
a synthetic test case; the real run itself didn't surface any further
issues in this step.

## Paths

Edit the `input_files` tribble at the top of the script to point at
your actual input files — the one example row assumes Step 2's
column-trimmed output; uncomment/add rows for additional sources (e.g.
a Symbiota export).
