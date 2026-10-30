#!/usr/bin/env Rscript
# ============================================================
# Trim GBIF Occurrence Columns (Arthropoda, California)
# ============================================================
# Dangermond Project — proposed Step 2 (column reduction)
#
# Purpose: Steps 2-10 of this pipeline only ever use a small subset of
# the ~230 columns a GBIF Darwin Core occurrence.txt export contains
# (dedup identifiers, taxonomy, and coordinates) — everything else
# (citation/rights metadata, event remarks, geological context,
# free-text locality notes, media links, etc.) is dead weight for this
# pipeline's purposes, but dominates the file's actual byte size.
#
# This reads only the needed columns — selected BY NAME rather than by
# fixed column position, since GBIF's column order can differ across
# different downloads/export settings (same philosophy as Step 1
# resolving the taxon key by name rather than a hardcoded ID).
# `readr::read_tsv()` with `col_types = cols_only(...)` parses the file
# without ever materializing the ~216 unwanted columns in memory, so
# this stays practical even on a multi-gigabyte file.
#
# WHY THIS EXISTS: the raw download for this project's real GBIF query
# came back as a single ~6.8 GB, 230-column file — far too large to
# move through a browser upload (30 MB limit) or even most
# device-to-cloud transfer paths (typically capped well under 1 GB per
# file). Trimming to just the needed columns first, before any
# transfer or further processing, was the practical fix. (An
# equivalent Python version of this script exists too — this R
# version exists because Python wasn't reliably available on the
# machine running the real download; both do the same thing.)
#
# WHAT'S NOT LOST: the full original file is untouched by this script
# (only ever read, never modified or deleted) — a later step rejoins
# full record detail back onto the small, final per-species outputs
# using the same occurrenceID / institutionCode+collectionCode+
# catalogNumber matching keys Step 3 (merge/dedup) already uses, so
# nothing is permanently discarded, only deferred until the data is
# small enough that carrying every column is no longer a problem.
# ============================================================

library(readr)

# ------------------------------------------------------------
# USER INPUTS — update if needed
# ------------------------------------------------------------
input_path <- "occurrence.txt"
output_path <- "occurrence_trimmed.txt"

# Columns to keep, in this order. Must match the exact header names in
# the input file (case-sensitive, standard Darwin Core term names).
columns_to_keep <- c(
  "gbifID",
  "occurrenceID",
  "institutionCode",
  "collectionCode",
  "catalogNumber",
  "basisOfRecord",
  "decimalLatitude",
  "decimalLongitude",
  "scientificName",
  "kingdom",
  "phylum",
  "class",
  "order",
  "family"
)
# ------------------------------------------------------------

if (!file.exists(input_path)) {
  stop(sprintf("Input file not found: %s", input_path))
}

# ------------------------------------------------------------
# 1) Check the header up front for the columns we need, before
#    committing to reading the whole (potentially multi-GB) file —
#    a missing column should fail fast and clearly, not partway
#    through an hours-long parse.
# ------------------------------------------------------------
message(sprintf("Reading header from %s...", input_path))
header_line <- read_lines(input_path, n_max = 1)
actual_cols <- strsplit(header_line, "\t", fixed = TRUE)[[1]]

missing_cols <- setdiff(columns_to_keep, actual_cols)
if (length(missing_cols) > 0) {
  stop(sprintf(
    paste(
      "The following expected column(s) were not found in '%s' header: %s\n",
      "This usually means the export's column set differs from what this",
      "script expects — check the header and update columns_to_keep above,",
      "or investigate why they're missing before proceeding."
    ),
    input_path, paste(missing_cols, collapse = ", ")
  ))
}

message(sprintf(
  "Keeping %d of %d columns: %s",
  length(columns_to_keep), length(actual_cols), paste(columns_to_keep, collapse = ", ")
))

# ------------------------------------------------------------
# 2) Build a col_types spec that names every column we want and marks
#    every other column col_skip() — readr's C++ parser never
#    materializes a skipped column's values in memory, so this reads
#    efficiently regardless of how wide the input file is.
# ------------------------------------------------------------
col_type_for <- function(name) {
  if (name %in% c("decimalLatitude", "decimalLongitude")) {
    col_double()
  } else {
    col_character()
  }
}

spec_list <- setNames(
  lapply(actual_cols, function(nm) {
    if (nm %in% columns_to_keep) col_type_for(nm) else col_skip()
  }),
  actual_cols
)

# ------------------------------------------------------------
# 3) Read (columns-only, so memory stays proportional to the 14 kept
#    columns rather than all 230) and write back out.
# ------------------------------------------------------------
message("\nReading full file (this will take a while for a multi-GB input)...")
trimmed <- read_tsv(
  input_path,
  col_types = do.call(cols_only, spec_list),
  quote = "",
  progress = TRUE
)

message(sprintf("\nRead %s rows.", format(nrow(trimmed), big.mark = ",")))

# Column order in the output follows columns_to_keep, not whatever
# order they happened to appear in the input.
trimmed <- trimmed[, columns_to_keep]

message(sprintf("Writing trimmed output to %s...", output_path))
write_tsv(trimmed, output_path, na = "")

message(sprintf(
  "\nDone. %s rows, %d columns written to:\n  %s",
  format(nrow(trimmed), big.mark = ","), ncol(trimmed), output_path
))
