#!/usr/bin/env Rscript
# ============================================================
# Darwin Core Merge & Deduplicate
# ============================================================
# Dangermond Project — Data Acquisition Step 3
#
# Tasks:
#   1) Read an arbitrary number of Darwin Core files (not just two),
#      each with its own path and delimiter, and append them into one
#      table
#   2) Report on column-header differences across the input files
#      before merging, so a source missing an expected field (e.g.
#      'order'/'family') is visible immediately rather than discovered
#      later as a silent gap
#   3) Deduplicate the merged table, first by occurrenceID, then by
#      institutionCode + collectionCode + catalogNumber for records
#      still missing occurrenceID
#
# WHY A GENERALIZED {name, path, delim} INPUT LIST (not two hardcoded
# file variables): this started as a two-file script assuming both
# inputs were split parts of a single GBIF download (same format,
# tab-delimited). That assumption turned out to be wrong once a real
# second scenario showed up — a Symbiota portal export (CSV) merged
# with a GBIF export (TSV): two genuinely different sources, not a
# split download. Rather than hardcode a second special case, inputs
# are now a `tribble()` of {name, path, delim} rows, so this script
# handles both "reassemble a GBIF split download" and "merge
# Symbiota + GBIF" (or any other combination) the same way. Add a row,
# re-run.
#
# NA-COLLAPSE DEDUPLICATION BUG — confirmed with a test before this fix
# was written, not just suspected: dplyr's `distinct()` and
# `group_by() + slice(1)` treat NA as a normal matching value, not as
# "unknown, don't match anything." If several records are legitimately
# missing occurrenceID (NA), a naive `distinct(occurrenceID, .keep_all
# = TRUE)` treats all of those NAs as duplicates of EACH OTHER and
# collapses them down to a single row — silently discarding real,
# distinct records that simply lack an ID, not actual duplicates.
#
# Verified directly:
#   x <- tibble(id = c(NA, NA, "a"), val = c(1, 2, 3))
#   distinct(x, id, .keep_all = TRUE)
#   #> id     val
#   #> NA       1      <- "2" is gone. Both NA rows were DIFFERENT
#   #>  a       3          records, not duplicates of each other.
#
# FIX: split into two groups — rows that DO have the key present, and
# rows that are missing it. Deduplicate only the "has key" group (where
# a real duplicate judgment is possible), pass the "missing key" group
# through untouched, then recombine with bind_rows(). Applied at both
# dedup stages (occurrenceID first, then institutionCode +
# collectionCode + catalogNumber for whatever's left without an
# occurrenceID).
# ============================================================

library(readr)
library(dplyr)
library(purrr)
library(tibble)

# ------------------------------------------------------------
# USER INPUTS — list every file to merge here. Add/remove rows as
# needed; each file gets its own delimiter so mixed-format merges
# (e.g. Symbiota CSV + GBIF TSV) work the same as same-format ones.
# ------------------------------------------------------------
input_files <- tribble(
  ~name,             ~path,                                  ~delim,
  "gbif_part1",      "../02-trim-gbif-columns/output/occurrence_trimmed.txt", "\t",
  # "symbiota_export", "path/to/symbiota_export.csv",         ",",
)
# NOTE: pointed at Step 2's column-trimmed output (14 columns) rather
# than the full 230-column DwC-A export directly — the raw occurrence.txt
# (6.84 GB) is too large to move through most transfer paths in one
# piece. Step 2 keeps every column this pipeline (Steps 3-10) actually
# uses, and the join keys used for dedup here (occurrenceID,
# institutionCode+collectionCode+catalogNumber) are exactly the columns
# it keeps, so full record detail can be rejoined later from the
# original file if needed. Row count out of Step 2's trim (4,665,086)
# matched the live GBIF download's total record count exactly when
# verified against the real data.

outdir <- "./output"
outfile_merged <- file.path(outdir, "dwc_merged_deduplicated.csv")
outfile_header_report <- file.path(outdir, "column_header_report.txt")
# ------------------------------------------------------------

dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

# ------------------------------------------------------------
# 1) Read every input file with its own declared delimiter
# ------------------------------------------------------------
message(sprintf("Reading %d input file(s)...", nrow(input_files)))

read_one <- function(name, path, delim) {
  message(sprintf("  [%s] %s (delim=%s)", name, path, ifelse(delim == "\t", "\\t", delim)))
  df <- read_delim(path, delim = delim, show_col_types = FALSE, guess_max = 100000)
  df$source_file <- name
  df
}

all_data <- pmap(input_files, read_one)
names(all_data) <- input_files$name

for (nm in names(all_data)) {
  message(sprintf("  [%s] %d records, %d columns", nm, nrow(all_data[[nm]]), ncol(all_data[[nm]])))
}

# ------------------------------------------------------------
# 2) Column-header comparison report, generalized to N files — flags
#    any column present in some files but not others, so a source
#    missing an expected field is visible up front.
# ------------------------------------------------------------
message("\nBuilding column-header comparison report...")

all_cols <- sort(unique(unlist(lapply(all_data, function(d) setdiff(names(d), "source_file")))))

header_matrix <- sapply(all_data, function(d) all_cols %in% setdiff(names(d), "source_file"))
header_df <- as_tibble(header_matrix) %>%
  mutate(column = all_cols, .before = 1)

report_lines <- c(
  "COLUMN HEADER COMPARISON",
  sprintf("Files compared: %s", paste(names(all_data), collapse = ", ")),
  "",
  sprintf("Columns present in ALL files: %d", sum(rowSums(header_matrix) == ncol(header_matrix))),
  sprintf("Columns present in SOME but not all files: %d", sum(rowSums(header_matrix) > 0 & rowSums(header_matrix) < ncol(header_matrix))),
  "",
  "Per-column presence (TRUE = column present in that file):",
  capture.output(print(header_df, n = Inf))
)
writeLines(report_lines, outfile_header_report)
message(sprintf("Header report written to:\n  %s", outfile_header_report))

# ------------------------------------------------------------
# 3) Merge (bind_rows aligns by column name, filling NA for columns
#    missing from a given source — exactly what we want here)
# ------------------------------------------------------------
merged <- bind_rows(all_data)
message(sprintf("\nMerged: %d records, %d columns (before deduplication)", nrow(merged), ncol(merged)))

# ------------------------------------------------------------
# 4) Deduplicate — NA-safe (see header comment for the bug this avoids)
# ------------------------------------------------------------
dedupe_na_safe <- function(df, key_cols) {
  key_present <- df %>% filter(if_all(all_of(key_cols), ~ !is.na(.)))
  key_missing <- df %>% filter(if_any(all_of(key_cols), is.na))

  key_present_deduped <- key_present %>% distinct(across(all_of(key_cols)), .keep_all = TRUE)

  bind_rows(key_present_deduped, key_missing)
}

message("\nDeduplicating by occurrenceID (NA-safe)...")
n_before <- nrow(merged)
if ("occurrenceID" %in% names(merged)) {
  dedup_stage1 <- dedupe_na_safe(merged, "occurrenceID")
} else {
  warning("No occurrenceID column found — skipping this dedup stage entirely.")
  dedup_stage1 <- merged
}
message(sprintf("  %d -> %d records", n_before, nrow(dedup_stage1)))

message("Deduplicating remaining records by institutionCode + collectionCode + catalogNumber (NA-safe)...")
fallback_keys <- c("institutionCode", "collectionCode", "catalogNumber")
if (all(fallback_keys %in% names(dedup_stage1))) {
  n_before2 <- nrow(dedup_stage1)
  dedup_final <- dedupe_na_safe(dedup_stage1, fallback_keys)
  message(sprintf("  %d -> %d records", n_before2, nrow(dedup_final)))
} else {
  warning(sprintf(
    "One or more fallback key columns missing (%s) — skipping this dedup stage.",
    paste(setdiff(fallback_keys, names(dedup_stage1)), collapse = ", ")
  ))
  dedup_final <- dedup_stage1
}

message(sprintf("\nTotal: %d -> %d records after both dedup stages (%d removed)",
                 n_before, nrow(dedup_final), n_before - nrow(dedup_final)))

# ------------------------------------------------------------
# 5) Write output
# ------------------------------------------------------------
write_csv(dedup_final, outfile_merged)
message(sprintf("Merged/deduplicated file written to:\n  %s", outfile_merged))

message("\nDone.")
