#!/usr/bin/env Rscript
# EPA Level III regions intersecting Dangermond Preserve.
# Regional membership is a candidate-pool criterion, not a habitat prediction.
suppressMessages({
  library(sf)
  library(dplyr)
  library(readr)
})

# Resolve paths from this script so it can run from any working directory.
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grepl("^--file=", args)])
stopifnot(length(script) == 1)
root <- normalizePath(file.path(dirname(script), "../.."), mustWork = TRUE)
infile_ecoregions <- file.path(root, "data/raw/epa/region9_level_iii/2026-10-27/extracted/reg9_eco_l3.shp")
infile_boundary <- file.path(root, "analysis/reference-data/jldp_boundary.geojson")
outdir <- file.path(root, "outputs/ecoregions-level-iii/2026-10-27")
outfile_summary <- file.path(outdir, "preserve_ecoregions.csv")
outfile_geojson <- file.path(outdir, "preserve_ecoregions.geojson")

if (!file.exists(infile_ecoregions)) {
  stop("Ecoregion shapefile not found: ", infile_ecoregions,
       " (expected the source shapefile and its companion files in the documented raw-data folder)")
}
if (!file.exists(infile_boundary)) {
  stop("Preserve boundary file not found: ", infile_boundary)
}
if (!dir.exists(outdir)) dir.create(outdir, recursive = TRUE)

cat("Reading EPA Level III ecoregions (Region 9)...\n")
eco <- st_read(infile_ecoregions, quiet = TRUE)
cat("  ", nrow(eco), "ecoregion polygons read. CRS:", st_crs(eco)$input, "\n")

cat("\nReading Preserve boundary...\n")
boundary <- st_read(infile_boundary, quiet = TRUE)
cat("  CRS:", st_crs(boundary)$input, "\n")

# Reproject the (single, small) boundary polygon into the ecoregion
# shapefile's own equal-area CRS, rather than reprojecting all 85
# national-extent ecoregion polygons.
boundary_proj <- st_transform(boundary, st_crs(eco))

cat("\nFinding ecoregion(s) that spatially intersect the Preserve boundary...\n")
hits <- st_intersects(eco, boundary_proj, sparse = FALSE)[, 1]
n_hits <- sum(hits)
cat("  ", n_hits, "ecoregion polygon(s) intersect the Preserve boundary.\n")

if (n_hits == 0) {
  stop("No ecoregion polygon intersects the Preserve boundary — check CRS handling and input files.")
}

eco_hits <- eco[hits, ]

# Compute the real overlap area for each matched ecoregion, both as a
# sanity check (a boundary-line-precision sliver would show near-zero area
# or near-zero percent) and as useful reporting context.
boundary_area_m2 <- as.numeric(st_area(boundary_proj))
overlap_area_m2 <- vapply(seq_len(nrow(eco_hits)), function(i) {
  inter <- suppressWarnings(st_intersection(st_geometry(eco_hits)[i], st_geometry(boundary_proj)))
  if (length(inter) == 0) return(0)
  as.numeric(sum(st_area(inter)))
}, numeric(1))

summary_tbl <- st_drop_geometry(eco_hits) %>%
  select(US_L3CODE, US_L3NAME, NA_L3CODE, NA_L3NAME, NA_L2NAME, NA_L1NAME, EPA_REGION) %>%
  mutate(
    overlap_area_m2 = overlap_area_m2,
    overlap_area_acres = overlap_area_m2 / 4046.8564224,
    pct_of_preserve_area = 100 * overlap_area_m2 / boundary_area_m2
  ) %>%
  arrange(desc(pct_of_preserve_area))

cat("\nIntersecting ecoregion(s):\n")
print(summary_tbl)

write_csv(summary_tbl, outfile_summary)
cat("\nSummary written to", outfile_summary, "\n")

# Write the matched ecoregion polygon(s) back out in WGS84 (to match GBIF's
# decimalLatitude/decimalLongitude convention used throughout this
# regional filtering workflow) for point-in-polygon selection of occurrence records.
eco_hits_wgs84 <- st_transform(eco_hits, 4326)
st_write(eco_hits_wgs84, outfile_geojson, delete_dsn = TRUE, quiet = TRUE)
cat("Matched ecoregion polygon(s) (WGS84) written to", outfile_geojson, "\n")
