#!/usr/bin/env Rscript
# ============================================================
# Resolve BOLD-Placeholder Records Against the CIBI Barcode Project
# ============================================================
# Dangermond Project — Step 4
#
# New step, inserted between Step 3 (merge/deduplicate) and the
# renumbered Step 5 (filter-latrange-overlap). Runs BEFORE Step 5's
# clean_scientific_name() does its genus/species parsing, so any real
# identification resolved here is treated downstream exactly like any
# other normally-identified GBIF record.
#
# WHY THIS STEP EXISTS
# ---------------------
# Step 2/3 already revealed that ~715,978 of our merged records carry
# a `scientificName` of the form `BOLD:XXXXXXX` — a DNA-barcode cluster
# ID (BIN), not a taxonomic name, assigned when no formal identification
# had been promoted into GBIF's scientificName field. Left alone, Step
# 5's name-cleaning correctly passes these through unchanged (a prior
# bug collapsed them all into one fake species called "BOLD" — fixed
# previously), but that still leaves every one of those records
# unidentified beyond family rank.
#
# The user's own CIBI Barcode Project spreadsheet is a direct export
# from BOLD Systems for specimens from a related California survey
# (16,471 records) and carries BOLD's own identification for each
# specimen, keyed by the same `processid` BOLD uses — which is exactly
# the value GBIF carries in `occurrenceID` for these records. Matching
# on that key lets us recover a real identification for whichever of
# our BOLD-flagged records happen to be covered by this spreadsheet,
# with no fuzzy matching involved: either the ID is present or it
# isn't.
#
# WHY ONLY SPECIES-RANK MATCHES REPLACE scientificName
# -------------------------------------------------------
# The CIBI spreadsheet's own `identification_rank` field shows most of
# its records are identified only to genus, family, subfamily, or
# tribe — not full species. Writing a bare genus or family name into
# `scientificName` would recreate exactly the bug this pipeline already
# fixed once for the literal "BOLD" placeholder: every record sharing
# that genus/family would collapse into one fake "species" for Step 6's
# species counts and Step 8's per-species convex hulls, even though
# they are known NOT to be the same species. So only a true
# species-rank CIBI match replaces `scientificName` (with CIBI's own
# binomial, e.g. "Delia platura") — a genuine, unambiguous identification,
# indistinguishable downstream from any other GBIF species record.
#
# Every other matched record (genus/family/subfamily/tribe/order/class
# rank) keeps its original `BOLD:XXXXXXX` placeholder untouched, but
# gets the CIBI identification and rank attached in two new columns
# (`cibi_identification`, `cibi_identification_rank`) so that
# information is not lost — it's just kept out of the species-level
# analysis and is available for reporting instead.
#
# SCOPE
# -----
# This only ever touches rows whose scientificName already starts with
# "BOLD:" AND whose occurrenceID matches a processid in the CIBI sheet.
# It never modifies any other row, never drops any row, and never
# changes row count.
# ============================================================

suppressMessages({
  library(readr)
  library(dplyr)
})

# ---- Paths (relative to this script's folder) ----
infile_occurrences <- "../03-merge-deduplicate/output/dwc_merged_deduplicated.csv"
infile_cibi        <- "../reference-data/cibi_barcode_identifications.csv"
outdir              <- "output"
outfile             <- file.path(outdir, "dwc_merged_cibi_resolved.csv")
summary_outfile     <- file.path(outdir, "cibi_resolution_summary.csv")

if (!file.exists(infile_occurrences)) {
  stop("Input occurrence file not found: ", infile_occurrences)
}
if (!file.exists(infile_cibi)) {
  stop("CIBI reference file not found: ", infile_cibi)
}
if (!dir.exists(outdir)) dir.create(outdir, recursive = TRUE)

cat("Reading merged occurrences...\n")
occ <- read_csv(
  infile_occurrences,
  col_types = cols(
    gbifID = col_character(),
    occurrenceID = col_character(),
    institutionCode = col_character(),
    collectionCode = col_character(),
    catalogNumber = col_character(),
    basisOfRecord = col_character(),
    decimalLatitude = col_double(),
    decimalLongitude = col_double(),
    scientificName = col_character(),
    kingdom = col_character(),
    phylum = col_character(),
    class = col_character(),
    order = col_character(),
    family = col_character(),
    source_file = col_character()
  ),
  progress = FALSE
)
cat("  ", nrow(occ), "records read.\n")

cat("Reading CIBI reference identifications...\n")
cibi <- read_csv(
  infile_cibi,
  col_types = cols(.default = col_character()),
  progress = FALSE
) %>%
  select(processid, species, identification, identification_rank) %>%
  rename(
    cibi_processid = processid,
    cibi_species = species,
    cibi_identification = identification,
    cibi_identification_rank = identification_rank
  )
cat("  ", nrow(cibi), "CIBI records read; ",
    sum(duplicated(cibi$cibi_processid)), " duplicate processids (should be 0).\n", sep = "")

is_bold <- !is.na(occ$scientificName) & grepl("^BOLD:", occ$scientificName)
cat("\nBOLD-placeholder records in this dataset:", sum(is_bold), "\n")

# Join only needs to touch BOLD rows, but we keep the full table intact
# and just attach columns to avoid any risk of row-order or row-count
# drift from a partial join.
occ <- occ %>%
  left_join(cibi, by = c("occurrenceID" = "cibi_processid"))

# A CIBI match is only meaningful for rows that were actually BOLD
# placeholders in the first place — occurrenceID collisions with
# non-BOLD rows (shouldn't happen, but guarded) do not count as matches.
occ$cibi_matched <- is_bold & !is.na(occ$cibi_identification)

n_matched <- sum(occ$cibi_matched)
cat("Matched to a CIBI identification:", n_matched,
    sprintf("(%.2f%% of BOLD-placeholder records)\n", 100 * n_matched / sum(is_bold)))

cat("\nMatched records by CIBI identification_rank:\n")
print(table(occ$cibi_identification_rank[occ$cibi_matched], useNA = "ifany"))

# Only species-rank matches replace scientificName (see header comment).
is_species_match <- occ$cibi_matched & occ$cibi_identification_rank == "species" &
  !is.na(occ$cibi_species) & occ$cibi_species != ""

cat("\nSpecies-rank CIBI matches (scientificName will be replaced):", sum(is_species_match), "\n")

occ$scientificName[is_species_match] <- occ$cibi_species[is_species_match]

# Drop the helper column now that it's served its purpose; keep the
# identification + rank columns for every row (NA where not matched).
occ <- occ %>% select(-cibi_species)

cat("\nWriting resolved occurrence table to", outfile, "...\n")
write_csv(occ, outfile)
cat("  ", nrow(occ), "records written (unchanged from input row count: ",
    nrow(occ) == 4658904, ").\n", sep = "")

# ---- Small summary table for reporting, independent of the main output ----
summary_tbl <- tibble(
  metric = c(
    "total_records",
    "bold_placeholder_records",
    "cibi_matched_records",
    "cibi_matched_species_rank",
    "cibi_matched_genus_rank",
    "cibi_matched_family_rank",
    "cibi_matched_subfamily_rank",
    "cibi_matched_tribe_rank",
    "cibi_matched_other_rank",
    "scientificName_replaced_with_real_species"
  ),
  value = c(
    nrow(occ),
    sum(is_bold),
    n_matched,
    sum(occ$cibi_matched & occ$cibi_identification_rank == "species", na.rm = TRUE),
    sum(occ$cibi_matched & occ$cibi_identification_rank == "genus", na.rm = TRUE),
    sum(occ$cibi_matched & occ$cibi_identification_rank == "family", na.rm = TRUE),
    sum(occ$cibi_matched & occ$cibi_identification_rank == "subfamily", na.rm = TRUE),
    sum(occ$cibi_matched & occ$cibi_identification_rank == "tribe", na.rm = TRUE),
    sum(occ$cibi_matched & !(occ$cibi_identification_rank %in%
          c("species", "genus", "family", "subfamily", "tribe")), na.rm = TRUE),
    sum(is_species_match)
  )
)
write_csv(summary_tbl, summary_outfile)
cat("\nSummary written to", summary_outfile, "\n")
print(summary_tbl)
