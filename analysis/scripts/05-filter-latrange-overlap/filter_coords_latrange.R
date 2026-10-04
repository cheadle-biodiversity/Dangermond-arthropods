#!/usr/bin/env Rscript
# ============================================================
# Coordinate Filtering & Latitude Range Overlap
# ============================================================
# Dangermond Project — Data Acquisition Step 5
#
# Tasks:
#   1) Load the merged/deduplicated DwC file, with BOLD-placeholder
#      records resolved against the CIBI spreadsheet where possible
#      (output of Step 4, ../04-resolve-cibi-bold-ids/)
#   2) Remove records missing decimalLatitude or decimalLongitude
#   3) Save the coordinate-complete records as a CSV
#   4) Normalize scientificName across sources before grouping (see
#      "Fix" note below)
#   5) For each species, compute min/max latitude
#   6) Keep only species whose latitude range overlaps with the
#      Dangermond Preserve's latitude range, read from the authoritative
#      boundary polygon (../reference-data/jldp_boundary.geojson) rather
#      than a hardcoded number (see "Boundary source" note below)
#   7) Save the overlap species dataset as a CSV
#
# FIX — cross-source species-name mismatch (confirmed with test data
# before this fix was written, not just suspected): grouping directly
# on the raw `scientificName` string silently fragments a single species
# into multiple groups when sources format names differently — e.g. GBIF's
# interpreted export typically includes full authorship
# ("Formica rufa Linnaeus, 1758") while a Symbiota-network export is
# often the bare binomial ("Formica rufa"). In a test case with the same
# species present in both sources (one record at 34.5°, one at 34.6°,
# spanning the Dangermond boundary), the un-normalized version fragmented
# it into two "species," one of which was silently dropped from the
# overlap results entirely — not because of anything biological, just a
# naming-format difference between sources.
#
# Fix applied: derive `scientificName_clean` (genus + specific epithet
# only, authorship/year stripped) and group on that instead. The
# original `scientificName` is kept in the output for reference/audit,
# and every distinct raw name folded into a group is listed in the
# summary so nothing is hidden by the normalization.
#
# Note on scope: this operates at the species level by design — a
# trinomial (subspecies/variety) is folded up to its parent species
# (e.g. "Formica rufa rufa Linnaeus, 1758" -> "Formica rufa"). A name
# that doesn't start with a capitalized genus-like token (blank, a
# hybrid-formula name, an unusual OCR/data-entry artifact) is left
# unchanged rather than guessed at, and will simply form its own group.
#
# BOUNDARY SOURCE (changed from an earlier hardcoded version of this
# script): lat_min/lat_max used to be hardcoded as 34.442106/34.574661.
# Once an authoritative boundary file for the Preserve
# (../reference-data/jldp_boundary.geojson — see that folder's README
# for provenance/validation) became available, those hardcoded numbers
# turned out to be close but not exact: off by roughly 20-50 meters on
# each end from the polygon's true bounding box (34.442303/34.574189).
# This script now computes lat_min/lat_max directly from that boundary
# file every run, so there's one authoritative source instead of two
# slightly different numbers, and it stays correct if the boundary
# geometry is ever revised.
# ============================================================

library(readr)
library(dplyr)
library(sf)

# ------------------------------------------------------------
# USER INPUTS — update paths if needed
# ------------------------------------------------------------
infile <- "../04-resolve-cibi-bold-ids/output/dwc_merged_cibi_resolved.csv"

outdir <- "./output"

outfile_coords  <- file.path(outdir, "dwc_coords_complete.csv")
outfile_overlap <- file.path(outdir, "dwc_latrange_overlap.csv")

boundary_file <- "../reference-data/jldp_boundary.geojson"
# ------------------------------------------------------------

# Create output directory if it doesn't exist
dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

# ------------------------------------------------------------
# Dangermond Preserve latitude bounding box — derived from the boundary
# polygon rather than hardcoded (see "BOUNDARY SOURCE" note above)
# ------------------------------------------------------------
boundary <- st_read(boundary_file, quiet = TRUE)
boundary_bbox <- st_bbox(boundary)
lat_min <- unname(boundary_bbox["ymin"])
lat_max <- unname(boundary_bbox["ymax"])
message(sprintf("Preserve latitude range (from %s): %.6f - %.6f",
                 basename(boundary_file), lat_min, lat_max))

# ------------------------------------------------------------
# Helper: strip authorship/year down to "Genus species", leaving names
# that don't match the expected pattern (NA, blank, an unusual format)
# untouched rather than guessing. Implemented with sub() rather than
# regexpr()+regmatches() deliberately: regmatches() silently DROPS
# non-matching elements from its result instead of returning NA/as-is
# for them, which shifts every subsequent element out of alignment with
# the input vector — a real bug caught while testing this fix. sub() is
# always one-to-one with its input, so no realignment issue is possible.
#
# BOLD BIN COLLAPSE BUG — found only by running against the real GBIF
# download, not by inspecting the code: 715,978 real records (mostly
# from the Centre for Biodiversity Genomics / Stroud Water Research
# Center, basisOfRecord = MATERIAL_SAMPLE) carry a DNA-barcode BIN
# identifier as their `scientificName`, e.g. "BOLD:ABX4063",
# "BOLD:AAA2326" — each code identifying a genuinely distinct barcode
# cluster, not the same taxon. The regex above matches "BOLD" as if it
# were a genus-like token and discards everything after it (the actual
# distinguishing ":ABX4063" part), collapsing all ~716K of these
# genuinely different records into one fake "species" literally named
# "BOLD". Confirmed directly: that merged group had ~6,000 distinct
# coordinate locations and a convex hull of ~535,000 km^2 — large
# enough to spuriously "overlap" the 99 km^2 Preserve and would have
# shown up as a top result in Step 6's overlap ranking despite not
# being a real species at all.
#
# Fix: BOLD-prefixed identifiers are left completely untouched (each
# keeps its own full "BOLD:XXXXXXX" as its own group) rather than run
# through the genus/species regex — same "leave unusual formats alone
# rather than guess" principle the rest of this function already
# follows, just made to actually catch this specific real-world case.
# Checked and confirmed no other ":"-delimited placeholder prefix
# appears anywhere in this dataset's scientificName column, so this
# stays a narrow, targeted fix rather than a broad heuristic.
# ------------------------------------------------------------
clean_scientific_name <- function(x) {
  bold_like <- !is.na(x) & grepl("^BOLD:", x)
  cleaned <- sub("^([A-Z][a-zA-Z-]+(?:\\s+[a-z][a-zA-Z-]+)?).*$", "\\1", x, perl = TRUE)
  cleaned[bold_like] <- x[bold_like]
  cleaned
}

# ------------------------------------------------------------
# 1) Load merged/deduplicated file
# ------------------------------------------------------------
message("Reading input file...")
df <- read_csv(infile, show_col_types = FALSE)
message(sprintf("Loaded: %d records, %d columns", nrow(df), ncol(df)))

# ------------------------------------------------------------
# 2) Remove records missing decimalLatitude or decimalLongitude
# ------------------------------------------------------------

# Coerce coordinate columns to numeric in case they were read as character
df <- df %>%
  mutate(
    decimalLatitude  = suppressWarnings(as.numeric(decimalLatitude)),
    decimalLongitude = suppressWarnings(as.numeric(decimalLongitude))
  )

n_before <- nrow(df)
df_coords <- df %>%
  filter(!is.na(decimalLatitude) & !is.na(decimalLongitude))
n_after <- nrow(df_coords)

message(sprintf("Records with coordinates    : %d", n_after))
message(sprintf("Records dropped (no coords) : %d", n_before - n_after))

# ------------------------------------------------------------
# 3) Normalize scientificName for cross-source grouping
# ------------------------------------------------------------
df_coords <- df_coords %>%
  mutate(scientificName_clean = clean_scientific_name(scientificName))

n_changed <- sum(!is.na(df_coords$scientificName) &
                  df_coords$scientificName != df_coords$scientificName_clean)
message(sprintf(
  "Names normalized (authorship/rank stripped): %d of %d",
  n_changed, sum(!is.na(df_coords$scientificName))
))

# ------------------------------------------------------------
# 4) Save coordinate-complete dataset (includes both the original
#    scientificName and the normalized scientificName_clean, so the
#    normalization is auditable rather than hidden)
# ------------------------------------------------------------
write_csv(df_coords, outfile_coords)
message(sprintf("Coordinate-complete file written to:\n  %s", outfile_coords))

# ------------------------------------------------------------
# 5) Compute per-species latitude range, grouped on the normalized name
# ------------------------------------------------------------
message("\nComputing per-species latitude range...")

species_lat <- df_coords %>%
  filter(!is.na(scientificName_clean)) %>%
  group_by(scientificName_clean) %>%
  summarise(
    lat_min_sp     = min(decimalLatitude, na.rm = TRUE),
    lat_max_sp     = max(decimalLatitude, na.rm = TRUE),
    n_records      = n(),
    raw_names      = paste(sort(unique(scientificName)), collapse = " | "),
    .groups = "drop"
  )

message(sprintf("Unique species with coordinates: %d", nrow(species_lat)))

# ------------------------------------------------------------
# 6) Keep species whose latitude range overlaps with Dangermond
#
#    Two ranges [A_min, A_max] and [B_min, B_max] overlap when:
#      A_min <= B_max  AND  A_max >= B_min
# ------------------------------------------------------------
species_overlap <- species_lat %>%
  filter(lat_min_sp <= lat_max & lat_max_sp >= lat_min)

message(sprintf("Species overlapping %.6f – %.6f: %d",
                lat_min, lat_max, nrow(species_overlap)))

# ------------------------------------------------------------
# 7) Subset full coordinate-complete records to overlap species,
#    then save
# ------------------------------------------------------------
df_overlap <- df_coords %>%
  filter(scientificName_clean %in% species_overlap$scientificName_clean)

message(sprintf("Records for overlap species : %d", nrow(df_overlap)))

write_csv(df_overlap, outfile_overlap)
message(sprintf("Overlap dataset written to:\n  %s", outfile_overlap))

# ------------------------------------------------------------
# Summary table printed to console
# ------------------------------------------------------------
message("\n============================================================")
message("PER-SPECIES LATITUDE SUMMARY (overlap species)")
message("============================================================")

summary_tbl <- species_overlap %>%
  arrange(scientificName_clean) %>%
  select(scientificName_clean, lat_min_sp, lat_max_sp, n_records, raw_names)

print(summary_tbl, n = Inf)

message("\nDone.")
