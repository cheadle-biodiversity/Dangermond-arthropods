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
| 2 | [`scripts/02-merge-deduplicate/`](scripts/02-merge-deduplicate/) | Merge multiple Darwin Core sources and deduplicate (NA-safe). |
| 3 | [`scripts/03-filter-latrange-overlap/`](scripts/03-filter-latrange-overlap/) | Filter to coordinate-complete records; flag species whose latitude range overlaps the Preserve's latitude band. |
| 4 | [`scripts/04-boundary-distance/`](scripts/04-boundary-distance/) | Compute each in-extent species' true geodesic distance to the Preserve boundary. |
| 5 | [`scripts/05-summary-tables-figures/`](scripts/05-summary-tables-figures/) | Summary table and figures: species counts by order/family and distance bin. |
| 6 | [`scripts/06-species-mcp-overlap/`](scripts/06-species-mcp-overlap/) | Minimum convex polygon per species; test for spatial overlap with the Preserve boundary. |

`reference-data/` holds inputs shared across more than one step (the
Preserve boundary polygon), kept in one place rather than duplicated.

## Running the pipeline

Each step's script is run from inside its own folder (relative paths
assume that working directory) and reads its input from the previous
step's `output/` folder:

```
cd scripts/01-download-gbif-arthropoda-ca && Rscript download_arthropoda_ca.R
cd ../02-merge-deduplicate           && Rscript dwc_merge_deduplicate.R
cd ../03-filter-latrange-overlap     && Rscript filter_coords_latrange.R
cd ../04-boundary-distance           && Rscript distance_to_boundary.R
cd ../05-summary-tables-figures      && Rscript summarize_taxon_distance.R
cd ../06-species-mcp-overlap         && Rscript species_mcp_overlap.R
```

Step 1 requires GBIF credentials set as environment variables
(`GBIF_USER`, `GBIF_PWD`, `GBIF_EMAIL`) — see that step's `README.md`.

## Status

Steps 2 through 6 have been verified end-to-end against synthetic test
data built to match each step's real input schema (see each step's
`README.md` "Verified before use" section, and its `requirements.md`
"Verification Status" section, for what was specifically tested and
which bugs that testing caught). **Step 1 has not yet been run against
the live GBIF API** — it requires user-supplied credentials that were
deliberately never introduced into the environment that built this
pipeline. Once Step 1 is run for real, later steps should be re-checked
against the actual data shape GBIF returns; Step 2's column-header
report is the intended first place to catch any schema mismatch.

## R package dependencies

`rgbif`, `readr`, `dplyr`, `sf`, `tidyr`, `forcats`, `ggplot2`,
`purrr`, `tibble`.
