# Analysis Pipeline

A numbered, reproducible R pipeline for Dangermond Preserve Arthropoda
occurrence data, from GBIF download through spatial summary analyses.
Each step lives in its own folder under `scripts/`, with its own
script, `README.md` (design rationale and verification notes), and
`requirements.md` (numbered, testable requirements).

## Pipeline steps

| Step | Folder | Purpose |
|------|--------|---------|
| 1 | [`scripts/01-download-gbif-arthropoda-ca/`](scripts/01-download-gbif-arthropoda-ca/) | Query and download the GBIF Darwin Core Archive for all Arthropoda occurrence records in California. |
| 2 | [`scripts/02-trim-gbif-columns/`](scripts/02-trim-gbif-columns/) | Reduce the raw ~230-column GBIF export to the ~14 columns the rest of this pipeline actually uses, so the file is small enough to move/process. |
| 3 | [`scripts/03-merge-deduplicate/`](scripts/03-merge-deduplicate/) | Merge multiple Darwin Core sources and deduplicate (NA-safe). |
| 4 | [`scripts/04-filter-latrange-overlap/`](scripts/04-filter-latrange-overlap/) | Filter to coordinate-complete records; flag species whose latitude range overlaps the Preserve's latitude band. |
| 5 | [`scripts/05-boundary-distance/`](scripts/05-boundary-distance/) | Compute each in-extent species' true geodesic distance to the Preserve boundary. |
| 6 | [`scripts/06-summary-tables-figures/`](scripts/06-summary-tables-figures/) | Summary table and figures: species counts by order/family and distance bin. |
| 7 | [`scripts/07-species-mcp-overlap/`](scripts/07-species-mcp-overlap/) | Minimum convex polygon per species; test for spatial overlap with the Preserve boundary. |

`reference-data/` holds inputs shared across more than one step (the
Preserve boundary polygon), kept in one place rather than duplicated.

Step 2 was added after Step 1 was first run against the real, live
GBIF API: the real download came back as a single ~6.8 GB, 230-column
file, far too large to move through most transfer paths in one piece.
Step 2 keeps only the columns every later step actually needs (dedup
identifiers, taxonomy, coordinates), cutting the file to about 870 MB
(~87% smaller) while preserving every record and column downstream
steps rely on — full Darwin Core detail can be rejoined later onto the
small final outputs using the same identifier columns Step 3's dedup
already keys on.

## Running the pipeline

Each step's script is run from inside its own folder (relative paths
assume that working directory) and reads its input from the previous
step's `output/` folder:

```
cd scripts/01-download-gbif-arthropoda-ca && Rscript download_arthropoda_ca.R
cd ../02-trim-gbif-columns            && Rscript trim_gbif_columns.R
cd ../03-merge-deduplicate            && Rscript dwc_merge_deduplicate.R
cd ../04-filter-latrange-overlap      && Rscript filter_coords_latrange.R
cd ../05-boundary-distance            && Rscript distance_to_boundary.R
cd ../06-summary-tables-figures       && Rscript summarize_taxon_distance.R
cd ../07-species-mcp-overlap          && Rscript species_mcp_overlap.R
```

Step 1 requires GBIF credentials set as environment variables
(`GBIF_USER`, `GBIF_PWD`, `GBIF_EMAIL`) — see that step's `README.md`.
Step 2 is also available as an equivalent Python script
(`trim_gbif_columns.py`) for environments where R isn't the preferred
tool; only the R version has been run against the real data to date.

## Status

**All seven steps have now been run end-to-end against the real, live
GBIF download** (4,665,086 Arthropoda occurrence records for
California; DOI `10.15468/dl.vgv5ee`) — not just synthetic test data.
Running against the real data surfaced several real bugs that no
amount of synthetic test data or static review had caught; each is
documented in detail in its own step's `README.md`, and summarized
here so they're visible from the top level:

- **Step 1**: two `rgbif` version-drift bugs (`occ_download()`'s
  predicate key is `gadm`, not the live-search-API field name
  `gadmGid`; `occ_download_get()` returns a plain classed character
  vector, not a list with a `$path` element) and one type bug (a
  resolved taxon key can come back as character, breaking a `%d`
  format spec). All fixed; see that step's `README.md`.
- **Step 2 (new)**: no bugs to report — built and verified directly
  against the real 230-column header and the full real file.
- **Step 3's** real input exposed no new issues beyond what synthetic
  testing already covered.
- **Step 4**: a real data-quality bug, not a code bug — 715,978 real
  records are DNA-barcode samples whose `scientificName` is a BOLD BIN
  identifier (e.g. `BOLD:ABX4063`), each one a distinct barcode
  cluster. The species-name-cleaning step was collapsing all of them
  into one fake "species" literally named `BOLD`. Fixed by leaving
  BOLD-prefixed identifiers untouched. See that step's `README.md` for
  the records this affected.
- **Step 5**: computing geodesic distance for all ~4.66M
  coordinate-complete records in a single `st_distance()` call
  exhausted available memory and was killed by the environment running
  it. Fixed by batching the computation.
- **Step 6**: the order+family chart's height formula was sized for a
  handful of families per order (all synthetic test data ever had);
  real data produced 1,031 order:family combinations, asking for a
  ~152-inch-tall image that failed to render/upload anywhere useful.
  Fixed with a fixed maximum height and a multi-column legend.
- **Step 7**: combining ~27,000 individual species-hull polygons with
  `do.call(rbind, ...)` is a classic quadratic-blowup pattern in R and
  effectively never finished on the real species count. Fixed by
  combining attributes and geometries separately (seconds instead of
  indefinitely).

None of these fixes required any manual, one-off intervention to get a
correct result — each is now a permanent part of its script, so a
fresh run of Steps 1-7 in order needs no on-the-fly adjustment.

Still pending: a utility script to rejoin full Darwin Core record
detail from the original (untrimmed) `occurrence.txt` onto Step 5's
small final per-species outputs, using the same `occurrenceID` /
`institutionCode`+`collectionCode`+`catalogNumber` keys Step 3's dedup
already uses.

## R package dependencies

`rgbif`, `readr`, `dplyr`, `sf`, `tidyr`, `forcats`, `ggplot2`,
`purrr`, `tibble`.
