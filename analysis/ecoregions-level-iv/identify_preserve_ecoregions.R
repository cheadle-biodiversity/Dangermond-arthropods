#!/usr/bin/env Rscript
# Identify EPA Level IV regions intersecting Dangermond and their areas.
# Keep full regions for species-pool screening and clipped regions for maps.
library(sf)

args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grepl("^--file=", args)])
stopifnot(length(script) == 1)
root <- normalizePath(file.path(dirname(script), "../.."), mustWork = TRUE)
source_dir <- file.path(root, "data/raw/epa/region9_level_iv/2026-10-27")
boundary_file <- file.path(root, "analysis/reference-data/jldp_boundary.geojson")
out <- file.path(root, "outputs/ecoregions-level-iv/2026-10-27")
dir.create(out, recursive = TRUE, showWarnings = FALSE)

eco <- st_read(file.path(source_dir, "extracted/reg9_eco_l4.shp"), quiet = TRUE)
boundary <- st_read(boundary_file, quiet = TRUE)
stopifnot(all(st_is_valid(boundary)))
boundary <- st_transform(boundary, st_crs(eco))
boundary_geometry <- st_union(st_geometry(boundary))
area_m2 <- as.numeric(st_area(boundary_geometry))
hits <- eco[lengths(st_intersects(eco, boundary_geometry)) > 0, ]
stopifnot(nrow(hits) > 0, all(st_is_valid(hits)))

cols <- c("US_L4CODE", "US_L4NAME", "US_L3CODE", "US_L3NAME")
clipped <- suppressWarnings(st_intersection(hits[, cols], boundary_geometry))
clipped$overlap_area_m2 <- as.numeric(st_area(clipped))
clipped <- clipped[clipped$overlap_area_m2 > 0, ]
clipped$overlap_area_acres <- clipped$overlap_area_m2 / 4046.8564224
clipped$pct_of_preserve_area <- 100 * clipped$overlap_area_m2 / area_m2
clipped <- clipped[order(-clipped$pct_of_preserve_area), ]
summary <- st_drop_geometry(clipped)
write.csv(summary, file.path(out, "preserve_ecoregions_level_iv.csv"), row.names = FALSE)

# These are different products: regional polygons vs. preserve-only portions.
st_write(st_transform(hits[, cols], 4326),
         file.path(out, "matching_full_ecoregions.geojson"),
         delete_dsn = TRUE, quiet = TRUE)
st_write(st_transform(clipped, 4326),
         file.path(out, "ecoregions_within_preserve.geojson"),
         delete_dsn = TRUE, quiet = TRUE)

coverage <- as.numeric(st_area(st_union(st_geometry(clipped)))) / area_m2
stopifnot(coverage > 0, coverage <= 1.000001)
writeLines(c(
  "EPA Region 9 Level IV overlay; source downloaded 2026-10-27.",
  paste("Source manifest:", file.path(source_dir, "archive_manifest.json")),
  paste("Boundary:", boundary_file),
  paste("Source polygons:", nrow(eco)),
  paste("Positive-area intersecting regions:", nrow(summary)),
  paste("Percent of preserve covered:", 100 * coverage),
  "Areas calculated in the EPA source's Albers equal-area CRS.",
  "Ecoregion boundaries do not delineate individual beach or backdune habitats."
), file.path(out, "overlay_notes.txt"))
print(summary)
cat("Percent of preserve covered:", 100 * coverage, "\n")
