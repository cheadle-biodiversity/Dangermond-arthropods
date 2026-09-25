#!/usr/bin/env Rscript
# ============================================================
# Species Minimum Convex Polygons & Overlap with the Dangermond
# Preserve Boundary
# ============================================================
# Dangermond Project — Data Acquisition Step 6
#
# Tasks:
#   1) Load Step 3's FULL coordinate-complete dataset (every species,
#      any latitude — not the latitude-band-restricted overlap file;
#      see "Why the full dataset" below)
#   2) For each species, build a minimum convex polygon (MCP / convex
#      hull) from its distinct occurrence coordinates
#   3) Flag species that don't have enough usable geometry for a hull
#      (fewer than 3 distinct coordinate locations, or all of them
#      collinear) and report them separately rather than dropping them
#      silently or forcing a degenerate shape
#   4) Load the authoritative Preserve boundary polygon and test each
#      species' hull for overlap (any spatial intersection — a hull
#      that fully contains the Preserve, sits fully inside it, or just
#      clips an edge all count; see "Overlap test" below)
#   5) For every species with a hull, compute the overlap area (0 if
#      none) and what percentage of the Preserve's total area that
#      overlap represents
#   6) Write three outputs: a summary table, an insufficient-data
#      report, and a GeoJSON of every hull built (so they can be viewed
#      on a map / brought into GIS software)
#
# WHY THE FULL COORDINATE-COMPLETE DATASET (not Step 3's latitude-band-
# restricted output): that band was a coarse pre-filter built for a
# different analysis (a quick "does this species' latitude range even
# reach this far" check on the RAW latitude values) — it is not a real
# range boundary, and restricting to it here would silently drop
# occurrence points a species' true range hull needs. That could both
# hide real overlaps (a species whose full range wraps around the
# Preserve but happens to have few in-band records) and distort hull
# shape generally (a hull built from an artificially narrowed point set
# isn't the same shape as the true MCP). This step re-derives overlap
# independently, from each species' full known range, rather than
# reusing Step 3's coarse filter.
#
# NOTE — THE HULL IS A TRUE 2D CONVEX HULL, NOT A LATITUDE-ONLY TEST:
# st_convex_hull() below operates on each species' full (longitude,
# latitude) point set, so both east-west and north-south spread shape
# the polygon. It is easy to mistake a hull for a simple lat/lon
# bounding box if test points happen to be placed at rectangle corners
# (a shortcut used for some of the synthetic verification data in this
# step's README, purely to make expected overlap percentages easy to
# hand-calculate) — but the underlying method follows the actual
# outermost points of the input, in both directions, not a min/max
# range along one axis. A hull built from realistically scattered
# points comes out as an irregular polygon, not a rectangle; see the
# README for a worked example.
#
# CAVEAT THIS IMPLIES — read before interpreting results: a minimum
# convex polygon is the tightest CONVEX shape enclosing every occurrence
# point. It is not a true range map, and it is not evidence the species
# was ever recorded at the Preserve. For a species recorded across a
# wide swath of California, its MCP can be very large and will often
# overlap the Preserve simply because the Preserve's coordinates fall
# somewhere inside that broad convex envelope — even with zero actual
# records anywhere near it. "Overlaps the Preserve" here means "the
# Preserve falls within this species' convex range envelope," not "this
# species has been recorded at the Preserve" — Step 4's boundary-
# distance output is the place to look for actual recorded proximity,
# and Step 5's distance bins for how that breaks down by taxon. Expect
# most widely-distributed species to show overlap under this method;
# that is the expected behavior of a convex-hull method, not a bug.
#
# INSUFFICIENT DATA: a convex hull needs at least 3 distinct, non-
# collinear points. Species with fewer than 3 distinct coordinate
# locations, or whose distinct locations are all collinear (hull
# degenerates to a line or point instead of a polygon), are written to
# a separate report rather than being dropped silently or force-fit
# with an arbitrarily chosen buffer distance.
#
# OVERLAP TEST: sf::st_intersects() — true for ANY spatial intersection,
# including a hull that fully contains the Preserve or is fully
# contained by it, not just a partial/edge overlap. (sf::st_overlaps()
# would exclude those containment cases, which is not what "overlap"
# means in plain usage, and was deliberately not used here.)
#
# AREA METHOD: sf::st_area() on unprojected WGS84 geometry, consistent
# with Step 4's distance calculation — as of sf >= 1.0 this uses the S2
# spherical geometry engine (`sf_use_s2()` is TRUE by default) for true
# geodesic area, not naive planar area on raw lon/lat degrees.
#
# PERFORMANCE NOTE: this loops over species one at a time (hull
# construction and the overlap test aren't natively vectorized across
# groups in sf). For the full Arthropoda-in-California dataset, with
# potentially many thousands of species, this could take a while. Data
# is split by species once up front (not re-filtered from the full
# table on every iteration) to avoid an accidental O(n_species ×
# n_records) scan, but if this still becomes slow in practice, batching
# the hull/area/intersects calls instead of looping row-by-row would be
# the natural next optimization — not attempted here since it hasn't
# been shown to be necessary yet.
# ============================================================

library(readr)
library(dplyr)
library(sf)

# ------------------------------------------------------------
# USER INPUTS — update paths if needed
# ------------------------------------------------------------
infile        <- "../03-filter-latrange-overlap/output/dwc_coords_complete.csv"
boundary_file <- "../reference-data/jldp_boundary.geojson"

outdir <- "./output"
outfile_summary      <- file.path(outdir, "species_mcp_overlap_summary.csv")
outfile_insufficient <- file.path(outdir, "species_insufficient_data.csv")
outfile_polygons     <- file.path(outdir, "species_mcp_polygons.geojson")
# ------------------------------------------------------------

dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

# ------------------------------------------------------------
# 1) Load the coordinate-complete dataset and the boundary
# ------------------------------------------------------------
message("Reading coordinate-complete input file...")
df <- read_csv(infile, show_col_types = FALSE)
message(sprintf("Loaded: %d records, %d columns", nrow(df), ncol(df)))

species_col <- if ("scientificName_clean" %in% names(df)) "scientificName_clean" else "scientificName"

df <- df %>%
  mutate(
    decimalLatitude  = suppressWarnings(as.numeric(decimalLatitude)),
    decimalLongitude = suppressWarnings(as.numeric(decimalLongitude))
  ) %>%
  filter(!is.na(decimalLatitude), !is.na(decimalLongitude), !is.na(.data[[species_col]]))

message(sprintf("Usable records (coordinates + species name present): %d", nrow(df)))

message("Reading boundary polygon...")
boundary <- st_read(boundary_file, quiet = TRUE)
if (!all(st_is_valid(boundary))) {
  warning("Boundary geometry failed validity check (st_is_valid) — results below may be unreliable.")
}
preserve_area_m2 <- as.numeric(st_area(boundary))
message(sprintf("Preserve area: %.2f km^2", preserve_area_m2 / 1e6))

# ------------------------------------------------------------
# 2) Build a minimum convex polygon per species and test it against
#    the Preserve boundary
# ------------------------------------------------------------
message("\nBuilding minimum convex polygons per species...")

species_groups <- split(df, df[[species_col]])
species_list   <- names(species_groups)
n_species      <- length(species_list)
message(sprintf("Species to process: %d", n_species))

progress_every <- max(1, round(n_species / 10))

summary_rows      <- vector("list", n_species)
insufficient_rows <- vector("list", n_species)
hull_geoms        <- vector("list", n_species)

for (i in seq_along(species_list)) {
  sp         <- species_list[i]
  sp_records <- species_groups[[i]]
  n_records  <- nrow(sp_records)

  # Distinct coordinate locations only — repeat visits to the same spot
  # add no geometric information toward a convex hull.
  distinct_pts <- sp_records %>%
    distinct(decimalLongitude, decimalLatitude)
  n_distinct <- nrow(distinct_pts)

  if (n_distinct < 3) {
    insufficient_rows[[i]] <- tibble(
      species              = sp,
      n_records            = n_records,
      n_distinct_locations = n_distinct,
      reason               = "fewer than 3 distinct coordinate locations"
    )
    next
  }

  pts_sf   <- st_as_sf(distinct_pts, coords = c("decimalLongitude", "decimalLatitude"), crs = 4326)
  hull_sfc <- st_convex_hull(st_union(pts_sf))
  hull_sf  <- st_sf(geometry = hull_sfc)

  # Degeneracy check, two parts. (1) Sometimes the hull comes back as an
  # actual LINESTRING/POINT (caught by geometry type). (2) Sometimes it
  # doesn't: GEOS/S2 can instead return a genuine POLYGON type for
  # exactly (or very nearly) collinear input, but one that's an
  # infinitesimally thin sliver with near-zero area from floating-point
  # noise, not a real polygon with usable area — confirmed empirically
  # with a test case of 4 points on the same meridian, which came back
  # as a "POLYGON" with area ~1.8e-8 km^2 (0.018 m^2) rather than a
  # LINESTRING. A hard area floor of 1 m^2 catches this: no real species
  # occurrence hull should legitimately be smaller than that given
  # typical GPS/GBIF coordinate precision, so anything below it is
  # numerical noise from near-collinear points, not a real range.
  hull_area_m2  <- as.numeric(st_area(hull_sf))
  degenerate_area <- hull_area_m2 < 1
  degenerate_type <- as.character(st_geometry_type(hull_sf))[1] != "POLYGON"

  if (degenerate_type || degenerate_area) {
    insufficient_rows[[i]] <- tibble(
      species              = sp,
      n_records            = n_records,
      n_distinct_locations = n_distinct,
      reason               = if (degenerate_type) {
        "distinct locations are collinear (degenerate hull, no polygon)"
      } else {
        "distinct locations are collinear or nearly collinear (hull area is effectively zero)"
      }
    )
    next
  }

  overlaps <- lengths(st_intersects(hull_sf, boundary)) > 0

  if (overlaps) {
    overlap_geom    <- tryCatch(st_intersection(hull_sf, boundary), error = function(e) NULL)
    overlap_area_m2 <- if (is.null(overlap_geom) || nrow(overlap_geom) == 0) {
      0
    } else {
      sum(as.numeric(st_area(overlap_geom)))
    }
  } else {
    overlap_area_m2 <- 0
  }

  pct_covered <- 100 * overlap_area_m2 / preserve_area_m2

  summary_rows[[i]] <- tibble(
    species                 = sp,
    n_records               = n_records,
    n_distinct_locations    = n_distinct,
    hull_area_km2           = hull_area_m2 / 1e6,
    overlaps_preserve       = overlaps,
    overlap_area_km2        = overlap_area_m2 / 1e6,
    pct_of_preserve_covered = pct_covered
  )

  hull_geoms[[i]] <- st_sf(
    species                 = sp,
    n_records               = n_records,
    n_distinct_locations    = n_distinct,
    hull_area_km2           = hull_area_m2 / 1e6,
    overlaps_preserve       = overlaps,
    overlap_area_km2        = overlap_area_m2 / 1e6,
    pct_of_preserve_covered = pct_covered,
    geometry                = st_geometry(hull_sf)
  )

  if (i %% progress_every == 0) {
    message(sprintf("  ...processed %d / %d species", i, n_species))
  }
}

# ------------------------------------------------------------
# 3) Assemble and write outputs
# ------------------------------------------------------------
summary_tbl <- bind_rows(summary_rows) %>%
  arrange(desc(overlaps_preserve), desc(pct_of_preserve_covered), species)

write_csv(summary_tbl, outfile_summary)
message(sprintf(
  "\nSpecies with a valid hull: %d (%d overlap the Preserve, %d do not)",
  nrow(summary_tbl), sum(summary_tbl$overlaps_preserve), sum(!summary_tbl$overlaps_preserve)
))
message(sprintf("Summary table written to:\n  %s", outfile_summary))

insufficient_tbl <- bind_rows(insufficient_rows) %>%
  arrange(species)

write_csv(insufficient_tbl, outfile_insufficient)
message(sprintf(
  "Species without enough data for a hull: %d",
  nrow(insufficient_tbl)
))
message(sprintf("Insufficient-data report written to:\n  %s", outfile_insufficient))

valid_hulls <- Filter(Negate(is.null), hull_geoms)
if (length(valid_hulls) > 0) {
  all_hulls_sf <- do.call(rbind, valid_hulls)
  st_write(all_hulls_sf, outfile_polygons, delete_dsn = TRUE, quiet = TRUE)
  message(sprintf("Hull geometries written to:\n  %s", outfile_polygons))
} else {
  message("No species had enough data to build a hull — no GeoJSON written.")
}

message("\n============================================================")
message("TOP OVERLAPPING SPECIES BY % OF PRESERVE COVERED")
message("============================================================")
print(
  summary_tbl %>%
    filter(overlaps_preserve) %>%
    select(species, n_records, hull_area_km2, overlap_area_km2, pct_of_preserve_covered) %>%
    head(20),
  n = Inf
)

message("\nDone.")
