#!/usr/bin/env Rscript
# ============================================================
# Identify EPA Level III Ecoregion(s) Overlapping the Preserve Boundary
# ============================================================
# Dangermond Project — Step 9
#
# Determines which EPA Level III ecoregion polygon(s) (Region 9 shapefile)
# spatially intersect the Jack and Laura Dangermond Preserve boundary, so
# Step 10 can identify California arthropod species that occur on the same
# habitat type(s) found on the Preserve, anywhere in the state — not just
# within the Preserve itself.
#
# WHY THIS STEP EXISTS
# ---------------------
# "Habitat type" is operationalized here as EPA Level III Ecoregion — the
# finest level in EPA's hierarchical ecoregion scheme readily available for
# EPA Region 9 as a single downloadable product (105 regions nationally, 85
# within EPA Region 9 covers AZ/CA/HI/NV/territories). A species sharing an
# ecoregion with the Preserve is, by this scheme's own definition, occurring
# in an area of general similarity in geology, physiography, vegetation,
# climate, soils, and hydrology to the Preserve — a reasonable proxy for
# "the same habitat type" at the scale this project operates at (statewide
# occurrence records, not fine-grained vegetation mapping).
#
# WHAT THIS STEP DOES
# --------------------
# 1. Reads the EPA Level III Ecoregions of Region 9 shapefile (85 polygons;
#    provided by the user — see "Data source" below for why this had to be
#    user-supplied rather than downloaded directly in this pipeline).
# 2. Reprojects the Preserve boundary (`../reference-data/jldp_boundary.geojson`,
#    WGS84) into the ecoregion shapefile's own CRS (USA Contiguous Albers
#    Equal Area Conic, NAD83) — the correct direction for this step, since
#    an equal-area CRS is what makes the overlap-area calculation below
#    meaningful, and reprojecting the single small boundary polygon is
#    cheaper and lower-risk than reprojecting all 85 national-extent polygons.
# 3. Finds every ecoregion polygon that spatially intersects the boundary
#    (`sf::st_intersects()`), not just the one containing the Preserve's
#    centroid — a preserve straddling an ecoregion edge genuinely occurs in
#    both.
# 4. For every intersecting polygon, computes the actual overlap area (not
#    just "touches"), to confirm each one is a real, substantial overlap
#    and not a sliver artifact of boundary-line precision.
# 5. Writes the result list and a standalone GeoJSON of just the matched
#    ecoregion polygon(s), reprojected to WGS84, for Step 10 to use directly
#    against GBIF's (also WGS84) occurrence coordinates.
#
# DATA SOURCE
# -----------
# The three EPA files (reg9_eco_l3.zip shapefile, .htm metadata, .lyr
# symbology) are served from an AWS S3 bucket
# (dmap-prod-oms-edc.s3.us-east-1.amazonaws.com) that this pipeline's cloud
# execution environment cannot reach directly — outbound requests to that
# host are rejected by the environment's own network egress policy at the
# connection level (not a data-license or authentication issue; confirmed
# via the environment's own proxy diagnostics, and a WebFetch-based
# retrieval attempt also failed). The user downloaded all three files
# directly from the URLs EPA publishes and supplied them to this project;
# they are kept in `raw_download/` alongside this script for reproducibility.
# Only the .shp/.shx/.dbf/.prj component files (not .sbn/.sbx, which are
# ArcGIS spatial-index caches `sf` doesn't need, or the Microsoft OLE2
# `.lyr` symbology file, which carries ArcGIS display colors, not geometry)
# are actually read by this script.
# ============================================================

suppressMessages({
  library(sf)
  library(dplyr)
  library(readr)
})

# ---- Paths (relative to this script's folder) ----
infile_ecoregions <- "raw_download/reg9_eco_l3.shp"
infile_boundary    <- "../reference-data/jldp_boundary.geojson"
outdir             <- "output"
outfile_summary    <- file.path(outdir, "preserve_ecoregions.csv")
outfile_geojson    <- file.path(outdir, "preserve_ecoregions.geojson")

if (!file.exists(infile_ecoregions)) {
  stop("Ecoregion shapefile not found: ", infile_ecoregions,
       " (expected reg9_eco_l3.shp alongside its .shx/.dbf/.prj in raw_download/)")
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
# pipeline) for Step 10's point-in-polygon test against occurrence records.
eco_hits_wgs84 <- st_transform(eco_hits, 4326)
st_write(eco_hits_wgs84, outfile_geojson, delete_dsn = TRUE, quiet = TRUE)
cat("Matched ecoregion polygon(s) (WGS84) written to", outfile_geojson, "\n")
