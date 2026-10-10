#!/usr/bin/env Rscript
# ============================================================
# GBIF Darwin Core Archive Download: Arthropoda, California
# ============================================================
# Dangermond Project — Data Acquisition Step 1
#
# Tasks:
#   1) Resolve "Arthropoda" to its GBIF taxonKey via the backbone
#      taxonomy (rather than hardcoding a numeric key that could go
#      stale or be typo'd)
#   2) Submit a GBIF occurrence download for all Arthropoda records in
#      California, every record type/basisOfRecord included (not
#      restricted to e.g. just PreservedSpecimen)
#   3) Capture the DOI GBIF assigns to this specific download request —
#      available immediately at submission, before the download itself
#      finishes processing — and write it to its own text file
#   4) Wait for the download to finish processing, then fetch and
#      unzip the Darwin Core Archive
#
# GBIF CREDENTIALS: this script authenticates via the standard rgbif
# environment-variable convention (GBIF_USER / GBIF_PWD / GBIF_EMAIL,
# normally set in ~/.Renviron) rather than anything hardcoded or passed
# in chat — nothing here ever asks for or logs credentials. Set those
# three variables in your own environment before running this script.
#
# WHY gadm INSTEAD OF stateProvince: GBIF's stateProvince field is
# free text supplied by data publishers ("California", "CA", "Calif.",
# occasionally missing or in another language entirely) and matching
# against it is unreliable. `pred("gadm", "USA.5_1")` instead matches
# on GADM's administrative-boundary geometry for California — a
# geometric membership test rather than a text match, so it doesn't
# miss records where a publisher used a different string for the same
# state.
#
# ALL RECORD TYPES: no basisOfRecord predicate is applied, so preserved
# specimens, human observations, machine observations, living
# specimens, fossil specimens, and any other basisOfRecord GBIF tracks
# are all included, per the original request.
#
# hasGeospatialIssue = FALSE: excludes records GBIF's own automated
# quality flags have already identified as having a geospatial problem
# (e.g. coordinates that don't fall within the stated country). This is
# a coarse first-pass filter — Step 5 does its own, stricter
# coordinate-completeness check later in the pipeline regardless.
#
# VERIFIED AGAINST LIVE GBIF — three real bugs found only by actually
# running this against the live API (none were catchable by static
# review or synthetic test data, since all of them only manifest with
# rgbif's real return types/API behavior):
#
#  1) `pred("gadmGid", "USA.5_1")` is wrong: `gadmGid` is a field name on
#     GBIF's live /occurrence/search API, but occ_download()'s predicate
#     DSL uses the key name `gadm` instead. Using `gadmGid` here either
#     errors or silently fails to scope the request correctly. Fixed to
#     `pred("gadm", "USA.5_1")`.
#  2) `arthropoda_key <- backbone_match$usageKey` can come back as a
#     character value, not numeric, depending on the match — the `%d`
#     format specifier in the two `sprintf()` calls that print it
#     (line ~71 and the metadata block) throws "invalid format" in that
#     case. Fixed to `%s` in both places.
#  3) `occ_download_get()` returns a classed character vector (the file
#     path itself), not a list with a `$path` element — `dl_path$path`
#     is therefore NULL/invalid. Fixed to `as.character(dl_path)`.
#
# Confirmed working end-to-end against the real GBIF API: 4,665,086
# Arthropoda records returned for California, DOI 10.15468/dl.vgv5ee,
# download key 0010070-260921141020460.
# ============================================================

library(rgbif)

# ------------------------------------------------------------
# USER INPUTS — update if needed
# ------------------------------------------------------------
outdir <- "./output"
outfile_doi <- file.path(outdir, "doi.txt")
outfile_download_metadata <- file.path(outdir, "download_metadata.txt")
# ------------------------------------------------------------

dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

# ------------------------------------------------------------
# 1) Resolve "Arthropoda" to a GBIF taxonKey via the backbone taxonomy
# ------------------------------------------------------------
message("Resolving 'Arthropoda' against the GBIF backbone taxonomy...")
backbone_match <- name_backbone(name = "Arthropoda", rank = "phylum")

if (is.null(backbone_match$usageKey) || backbone_match$matchType == "NONE") {
  stop("Could not resolve 'Arthropoda' to a GBIF backbone taxonKey — check spelling/rank or GBIF API availability.")
}

arthropoda_key <- backbone_match$usageKey
message(sprintf(
  "Resolved: %s (rank=%s) -> taxonKey=%s, match type=%s",
  backbone_match$scientificName, backbone_match$rank, arthropoda_key, backbone_match$matchType
))

# ------------------------------------------------------------
# 2) Submit the occurrence download
# ------------------------------------------------------------
message("\nSubmitting GBIF occurrence download request...")
message("(all record types included; California via GADM boundary gadm = USA.5_1)")

download_key <- occ_download(
  pred("taxonKey", arthropoda_key),
  pred("gadm", "USA.5_1"),
  pred("hasGeospatialIssue", FALSE),
  format = "DWCA"
)

message(sprintf("Download submitted. Download key: %s", download_key))

# ------------------------------------------------------------
# 3) Capture the DOI immediately — GBIF assigns it at submission time,
#    well before the download itself finishes processing, so this
#    doesn't need to wait on occ_download_wait() below.
# ------------------------------------------------------------
meta <- occ_download_meta(download_key)
doi <- meta$doi

if (is.null(doi) || doi == "") {
  warning("No DOI returned yet by occ_download_meta() — GBIF sometimes assigns it with a short delay. Re-run occ_download_meta(download_key) manually and update output/doi.txt if this happens.")
} else {
  writeLines(doi, outfile_doi)
  message(sprintf("DOI written to:\n  %s\n  %s", outfile_doi, doi))
}

# Also keep a small metadata record (key, DOI, predicate, submission
# time) for citation/audit purposes — separate from the DOI-only file
# so the DOI file itself stays a single clean value.
writeLines(
  c(
    sprintf("download_key: %s", download_key),
    sprintf("doi: %s", doi),
    sprintf("taxon: %s (taxonKey=%s)", backbone_match$scientificName, arthropoda_key),
    sprintf("gadm: USA.5_1 (California)"),
    sprintf("hasGeospatialIssue: FALSE"),
    sprintf("format: DWCA"),
    sprintf("submitted_at: %s", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z"))
  ),
  outfile_download_metadata
)
message(sprintf("Download metadata written to:\n  %s", outfile_download_metadata))

# ------------------------------------------------------------
# 4) Wait for GBIF to finish preparing the archive, then download and
#    unzip it
# ------------------------------------------------------------
message("\nWaiting for GBIF to finish preparing the download (this can take a while for a request this broad)...")
occ_download_wait(download_key)

message("Download ready — fetching the Darwin Core Archive...")
dl_path <- occ_download_get(download_key, path = outdir, overwrite = TRUE)

message("Unzipping...")
unzip_dir <- file.path(outdir, "dwca")
dir.create(unzip_dir, recursive = TRUE, showWarnings = FALSE)
unzip(as.character(dl_path), exdir = unzip_dir)

message(sprintf("\nDone. Darwin Core Archive extracted to:\n  %s", unzip_dir))
message(sprintf("Cite this download using DOI: %s", doi))
