#!/usr/bin/env Rscript
# ============================================================
# Distance to Dangermond Preserve Boundary
# ============================================================
# Dangermond Project — Data Acquisition Step 6
#
# Tasks:
#   1) Load the FULL coordinate-complete dataset (Step 5's
#      dwc_coords_complete.csv — every record, not just the ones whose
#      own latitude falls in the Preserve's band; see "Why the full
#      dataset" below)
#   2) Load Step 5's latitude-range-overlap output, just to know which
#      species are "in extent" (their range overlaps the Preserve's
#      latitude band) — every output below is scoped to these species
#      only
#   3) Load the authoritative Preserve boundary polygon
#      (../reference-data/jldp_boundary.geojson)
#   4) Compute every record's true geodesic distance to the Preserve
#      (0 if the point falls inside the boundary)
#   5) For each in-extent species, produce two comparable outputs (full
#      original record, all columns, plus distance):
#        a) closest record considering only that species' records whose
#           OWN latitude falls within the Preserve's band
#        b) closest record considering ALL of that species' records,
#           even ones outside the band — i.e. "closest overall" per
#           species, not restricted to in-band records
#      Both are per-species tables, scoped to the same set of in-extent
#      species — (b) is never a global single row across every species
#      in the dataset, and never includes a species that isn't in the
#      latitudinal extent at all.
#
# WHY BOTH (a) AND (b): a species can pass Step 5's filter because some
# of its records fall in the latitude band, while its single closest
# approach to the Preserve actually comes from a *different* record of
# that same species that happens to sit outside the band. (a) answers
# "how close does this species get, staying strictly within the band
# Step 5 already filtered to" and (b) answers "how close does this
# species actually get, period." When they pick different records, that
# is worth seeing side by side rather than only ever reporting one of
# the two.
#
# WHY THE FULL COORDINATE-COMPLETE DATASET AS INPUT (rather than Step
# 3's already-filtered overlap file): needed to compute (b) at all — a
# record outside the latitude band is exactly what Step 5's overlap
# file excludes, so (b) can only find it by starting from the full
# dataset and then narrowing to in-extent species after distance has
# been computed for everything.
#
# Verified with a purpose-built test case, not just reasoned about: a
# species with one record inside the latitude band (14.5 km from the
# boundary) and a second record outside the band but only 5.0 km from
# the boundary. (a) correctly reports the in-band record (14.5 km); (b)
# correctly reports the out-of-band record (5.0 km) for the same
# species — confirming the two outputs actually diverge when they
# should, not just in theory.
#
# Distance method: uses sf::st_distance() directly on unprojected
# WGS84 (lon/lat) geometry. As of sf >= 1.0, this uses the S2 spherical
# geometry engine (`sf_use_s2()` is TRUE by default) to compute true
# geodesic distances — NOT naive Euclidean distance on raw
# latitude/longitude degrees, which would be measurably wrong here:
# at this latitude (~34.5°N) one degree of longitude is roughly 17%
# shorter than one degree of latitude (~91.7 km vs ~111.3 km).
#
# Also verified directly against the real boundary polygon: the
# Preserve's own centroid came back inside (0 m), a point shifted ~0.15°
# east came back measurably outside (~6.0 km), and downtown Santa
# Barbara came back at 61.2 km (~38 mi), consistent with its known
# real-world distance from the Point Conception area.
#
# TIES: if more than one record shares the exact minimum distance within
# a group, one is kept (first in the input's row order — not a
# data-quality judgment) but `n_tied_at_min` records how many records
# shared that minimum, so a tie is visible rather than silently
# resolved. Same caveat as Step 2's duplicate-resolution order.
#
# PERFORMANCE NOTE: this computes distance for every coordinate-complete
# record (needed for (b) — see above), not a pre-filtered subset — for
# the full Arthropoda-in-California dataset that could be a large
# number of records. S2-based distance against a single polygon is
# efficient, but if this becomes slow in practice, a first-pass
# longitude-window filter would be the natural place to optimize — not
# attempted here since it hasn't been shown to be necessary yet.
# ============================================================

library(readr)
library(dplyr)
library(sf)

# ------------------------------------------------------------
# USER INPUTS — update paths if needed
# ------------------------------------------------------------
infile_coords  <- "../05-filter-latrange-overlap/output/dwc_coords_complete.csv"
infile_overlap <- "../05-filter-latrange-overlap/output/dwc_latrange_overlap.csv"
boundary_file  <- "../reference-data/jldp_boundary.geojson"

outdir <- "./output"
outfile_all_distances     <- file.path(outdir, "dwc_distance_to_boundary.csv")
outfile_nearest_within     <- file.path(outdir, "nearest_record_per_species_within_extent.csv")
outfile_nearest_incl_outside <- file.path(outdir, "nearest_record_per_species_including_outside_extent.csv")
# ------------------------------------------------------------

dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

# ------------------------------------------------------------
# 1) Load the full coordinate-complete dataset and the boundary
# ------------------------------------------------------------
message("Reading coordinate-complete input file...")
df <- read_csv(infile_coords, show_col_types = FALSE)
message(sprintf("Loaded: %d records, %d columns", nrow(df), ncol(df)))

message("Reading boundary polygon...")
boundary <- st_read(boundary_file, quiet = TRUE)
if (!all(st_is_valid(boundary))) {
  warning("Boundary geometry failed validity check (st_is_valid) — distances below may be unreliable.")
}

# Latitude band, derived from the same boundary file (consistent with
# Step 5, which does the same thing rather than hardcoding these).
boundary_bbox <- st_bbox(boundary)
lat_min <- unname(boundary_bbox["ymin"])
lat_max <- unname(boundary_bbox["ymax"])
message(sprintf("Preserve latitude range (from %s): %.6f - %.6f",
                 basename(boundary_file), lat_min, lat_max))

# Coerce coordinates to numeric and drop any that still aren't usable
# (should be redundant on Step 5's own output, kept as a safety check)
df <- df %>%
  mutate(
    decimalLatitude  = suppressWarnings(as.numeric(decimalLatitude)),
    decimalLongitude = suppressWarnings(as.numeric(decimalLongitude))
  )
n_before <- nrow(df)
df <- df %>% filter(!is.na(decimalLatitude) & !is.na(decimalLongitude))
if (nrow(df) < n_before) {
  message(sprintf("Dropped %d record(s) with unusable coordinates.", n_before - nrow(df)))
}

# ------------------------------------------------------------
# 2) Which species are "in extent" (passed Step 5's latitude-band
#    filter)? Read from Step 5's overlap output rather than
#    re-deriving it, so this step stays consistent with Step 5's own
#    (already-fixed) species-name normalization logic instead of
#    duplicating it. Both outputs below are scoped to this species set.
# ------------------------------------------------------------
species_col <- if ("scientificName_clean" %in% names(df)) "scientificName_clean" else "scientificName"

overlap_df <- read_csv(infile_overlap, show_col_types = FALSE)
in_extent_species <- unique(overlap_df[[species_col]])
in_extent_species <- in_extent_species[!is.na(in_extent_species)]
message(sprintf("Species in the latitudinal extent (per Step 5): %d", length(in_extent_species)))

# ------------------------------------------------------------
# 3) Compute geodesic distance from every record to the boundary
#
# BATCHED — found by actually running this against the real 4.66M-record
# dataset, not by static review: computing st_distance() (and
# st_intersects()) against all records in a single call OOM-killed the R
# process (confirmed via the container's cgroup OOM log: RSS hit ~6.1GB
# against a ~5.8GB limit, process killed mid-call, no output files
# written). st_as_sf() + the S2-backed st_distance()/st_intersects()
# calls apparently hold enough intermediate state per point that doing
# all 4.66M at once doesn't fit. The fix processes the points in
# fixed-size batches, converting only one batch to sf at a time and
# discarding it (rm + gc()) before the next — same inputs, same S2
# geodesic method, same output values, just bounded peak memory. Batch
# size of 250,000 was chosen conservatively (well under what OOM'd) and
# worked; a machine with more available memory could safely use a larger
# batch, but this is not worth re-tuning unless it becomes a speed
# bottleneck later.
# ------------------------------------------------------------
message("Computing distances to the Preserve boundary for all coordinate-complete records...")

batch_size <- 250000
n_total <- nrow(df)
n_batches <- ceiling(n_total / batch_size)

dist_m           <- numeric(n_total)
inside_preserve  <- logical(n_total)

for (b in seq_len(n_batches)) {
  row_start <- (b - 1) * batch_size + 1
  row_end   <- min(b * batch_size, n_total)
  idx       <- row_start:row_end

  batch_sf <- st_as_sf(df[idx, ], coords = c("decimalLongitude", "decimalLatitude"),
                        crs = 4326, remove = FALSE)

  dist_m[idx]          <- as.numeric(st_distance(batch_sf, boundary)[, 1])
  inside_preserve[idx] <- lengths(st_intersects(batch_sf, boundary)) > 0

  rm(batch_sf)
  gc(verbose = FALSE)

  message(sprintf("  ...batch %d / %d done (records %s-%s)",
                   b, n_batches, format(row_start, big.mark = ","), format(row_end, big.mark = ",")))
}

df$distance_to_preserve_m  <- dist_m
df$distance_to_preserve_km <- dist_m / 1000
df$inside_preserve         <- inside_preserve
df$record_lat_in_band      <- df$decimalLatitude >= lat_min & df$decimalLatitude <= lat_max

df_sorted <- df %>% arrange(distance_to_preserve_m)
write_csv(df_sorted, outfile_all_distances)
message(sprintf("All records with distance written to:\n  %s", outfile_all_distances))

# Restrict everything below to in-extent species only, once
in_extent_records <- df_sorted %>% filter(.data[[species_col]] %in% in_extent_species)

# ------------------------------------------------------------
# 4a) Per in-extent species: closest record among only that species'
#     records whose OWN latitude falls within the Preserve's band
# ------------------------------------------------------------
nearest_within <- in_extent_records %>%
  filter(record_lat_in_band) %>%
  group_by(.data[[species_col]]) %>%
  mutate(n_tied_at_min = sum(distance_to_preserve_m == min(distance_to_preserve_m))) %>%
  slice_min(distance_to_preserve_m, n = 1, with_ties = FALSE) %>%
  ungroup() %>%
  arrange(distance_to_preserve_m)

write_csv(nearest_within, outfile_nearest_within)
message(sprintf(
  "\n(a) Closest in-band record per in-extent species (%d species) written to:\n  %s",
  nrow(nearest_within), outfile_nearest_within
))

# ------------------------------------------------------------
# 4b) Per in-extent species: closest record among ALL of that species'
#     records, including ones outside the latitude band
# ------------------------------------------------------------
nearest_incl_outside <- in_extent_records %>%
  group_by(.data[[species_col]]) %>%
  mutate(n_tied_at_min = sum(distance_to_preserve_m == min(distance_to_preserve_m))) %>%
  slice_min(distance_to_preserve_m, n = 1, with_ties = FALSE) %>%
  ungroup() %>%
  arrange(distance_to_preserve_m)

write_csv(nearest_incl_outside, outfile_nearest_incl_outside)
message(sprintf(
  "(b) Closest record overall (any of that species' records) per in-extent species (%d species) written to:\n  %s",
  nrow(nearest_incl_outside), outfile_nearest_incl_outside
))

# ------------------------------------------------------------
# Show where (a) and (b) actually diverge — i.e. species whose true
# closest approach comes from a record outside the latitude band
# ------------------------------------------------------------
comparison <- nearest_within %>%
  select(all_of(species_col), within_km = distance_to_preserve_km) %>%
  full_join(
    nearest_incl_outside %>% select(all_of(species_col), overall_km = distance_to_preserve_km),
    by = species_col
  ) %>%
  mutate(differs = is.na(within_km) | is.na(overall_km) | within_km != overall_km) %>%
  arrange(desc(differs), overall_km)

message("\n============================================================")
message("(a) vs (b) PER SPECIES — where does the true closest approach")
message("    come from a record OUTSIDE the latitude band?")
message("============================================================")
print(comparison, n = Inf)

message("\nDone.")
