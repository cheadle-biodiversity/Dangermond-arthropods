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
| 4 | [`scripts/04-resolve-cibi-bold-ids/`](scripts/04-resolve-cibi-bold-ids/) | Resolve BOLD-placeholder (`BOLD:XXXXXXX`) records against the CIBI Barcode Project spreadsheet, where a real identification is available. |
| 5 | [`scripts/05-filter-latrange-overlap/`](scripts/05-filter-latrange-overlap/) | Filter to coordinate-complete records; flag species whose latitude range overlaps the Preserve's latitude band. |
| 6 | [`scripts/06-boundary-distance/`](scripts/06-boundary-distance/) | Compute each in-extent species' true geodesic distance to the Preserve boundary. |
| 7 | [`scripts/07-summary-tables-figures/`](scripts/07-summary-tables-figures/) | Summary table and figures: species counts by order/family and distance bin. |
| 8 | [`scripts/08-species-mcp-overlap/`](scripts/08-species-mcp-overlap/) | Minimum convex polygon per species; test for spatial overlap with the Preserve boundary. |

`reference-data/` holds inputs shared across more than one step (the
Preserve boundary polygon, and now the CIBI barcode identifications),
kept in one place rather than duplicated.

Step 2 was added after Step 1 was first run against the real, live
GBIF API: the real download came back as a single ~6.8 GB, 230-column
file, far too large to move through most transfer paths in one piece.
Step 2 keeps only the columns every later step actually needs (dedup
identifiers, taxonomy, coordinates), cutting the file to about 870 MB
(~87% smaller) while preserving every record and column downstream
steps rely on — full Darwin Core detail can be rejoined later onto the
small final outputs using the same identifier columns Step 3's dedup
already keys on.

Step 4 was added after the (then-)Step 4 verification run (now Step 5)
revealed how many records — 715,978, about 15% of the dataset — carry
a BOLD Systems BIN placeholder instead of a real identification. It
resolves whichever of those it can against a known barcode project's
own data, before any other step groups or counts by species. See that
step's `README.md` for why only a fraction of matches (the true
species-rank ones) actually change anything downstream, and why a
broader BOLD-API-based resolution was investigated but deliberately
left out of scope for now.

Step 4 is optional: anyone running this pipeline without BOLD
identification data of their own can simply not supply a reference
file (or point it at a path that doesn't exist), and this step runs as
a no-op pass-through — Step 3's data flows through unchanged, and no
other step needs any edit. There is no separate "skip this step" flag
or configuration; absence of the reference file is the only input
needed to skip it.

## Running the pipeline

Each step's script is run from inside its own folder (relative paths
assume that working directory) and reads its input from the previous
step's `output/` folder:

```
cd scripts/01-download-gbif-arthropoda-ca && Rscript download_arthropoda_ca.R
cd ../02-trim-gbif-columns            && Rscript trim_gbif_columns.R
cd ../03-merge-deduplicate            && Rscript dwc_merge_deduplicate.R
cd ../04-resolve-cibi-bold-ids        && Rscript resolve_cibi_bold_ids.R
cd ../05-filter-latrange-overlap      && Rscript filter_coords_latrange.R
cd ../06-boundary-distance            && Rscript distance_to_boundary.R
cd ../07-summary-tables-figures       && Rscript summarize_taxon_distance.R
cd ../08-species-mcp-overlap          && Rscript species_mcp_overlap.R
```

Step 1 requires GBIF credentials set as environment variables
(`GBIF_USER`, `GBIF_PWD`, `GBIF_EMAIL`) — see that step's `README.md`.
Step 2 is also available as an equivalent Python script
(`trim_gbif_columns.py`) for environments where R isn't the preferred
tool; only the R version has been run against the real data to date.

## Status

**All eight steps have now been run end-to-end against the real, live
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
- **Step 4 (new)**: not a bug — a data-coverage question. 715,978
  records are DNA-barcode samples whose `scientificName` is a BOLD BIN
  identifier (e.g. `BOLD:ABX4063`), not a taxonomic name. This step
  resolves 9,776 of them against the user's CIBI Barcode Project
  spreadsheet (3,144 to a real species; the rest only to genus/family/
  subfamily/tribe, and deliberately left as placeholders rather than
  risk recreating the Step 5 BOLD-collapse bug at genus/family
  granularity). The other ~706,000 are out of scope for this step; see
  that step's `README.md`. This step is also optional — verified to run
  as a clean pass-through (zero changes, identical row count) when no
  reference file is supplied, so it's safe to leave in the pipeline
  unconditionally.
- **Step 5**: a real data-quality bug, not a code bug — the
  species-name-cleaning step was collapsing all 715,978 BOLD-barcode
  records into one fake "species" literally named `BOLD`, instead of
  treating each distinct BIN code as its own group. Fixed by leaving
  BOLD-prefixed identifiers untouched. See that step's `README.md` for
  the records this affected.
- **Step 6**: computing geodesic distance for all ~4.66M
  coordinate-complete records in a single `st_distance()` call
  exhausted available memory and was killed by the environment running
  it. Fixed by batching the computation.
- **Step 7**: the order+family chart's height formula was sized for a
  handful of families per order (all synthetic test data ever had);
  real data produced 1,031 order:family combinations, asking for a
  ~152-inch-tall image that failed to render/upload anywhere useful.
  Fixed with a fixed maximum height and a multi-column legend.
- **Step 8**: two real problems, found only by running at real scale.
  (1) Combining ~27,000 individual species-hull polygons with
  `do.call(rbind, ...)` is a classic quadratic-blowup pattern in R and
  effectively never finished on the real species count — fixed by
  combining attributes and geometries separately (seconds instead of
  indefinitely). (2) In one run, the per-species loop itself (25-30
  minutes against the full real dataset) was killed partway through by
  the environment it ran in, with no prior checkpoint to resume from —
  fixed by adding an incremental checkpoint every 2,000 species, so a
  resumed run picks up where it left off instead of starting over.

None of these fixes required any manual, one-off intervention to get a
correct result — each is now a permanent part of its script, so a
fresh run of Steps 1-8 in order needs no on-the-fly adjustment.

Still pending:

- A utility script to rejoin full Darwin Core record detail from the
  original (untrimmed) `occurrence.txt` onto Step 8's small final
  per-species outputs, using the same `occurrenceID` /
  `institutionCode`+`collectionCode`+`catalogNumber` keys Step 3's
  dedup already uses.
- A broader resolution of the ~706,000 BOLD-placeholder records Step 4
  doesn't cover, via BOLD Systems' own public API — investigated and
  found technically feasible (the flagged records collapse to only
  16,995 distinct BIN codes), but deliberately set aside for now in
  favor of reporting the CIBI-only coverage as a known limitation. See
  Step 4's `README.md`.

## R package dependencies

`rgbif`, `readr`, `dplyr`, `sf`, `tidyr`, `forcats`, `ggplot2`,
`purrr`, `tibble`.
