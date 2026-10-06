#!/usr/bin/env Rscript
# ============================================================
# Species List: California Arthropods Occurring in the Preserve's
# Shared Ecoregion(s), With Nearest-Boundary Distance
# ============================================================
# Dangermond Project — Step 10
#
# Produces the final deliverable for this biogeographic analysis: every
# species-level-identified California arthropod with at least one
# occurrence record falling inside the same EPA Level III ecoregion(s) the
# Preserve itself sits in (Step 9's result), paired with how close that
# species' single nearest California record (among ALL of its records
# statewide, not only the ones inside the shared ecoregion) comes to the
# Preserve boundary.
#
# WHY "NEAREST RECORD ANYWHERE IN CA", NOT JUST WITHIN THE SHARED ECOREGION
# ---------------------------------------------------------------------------
# A species can share the Preserve's habitat type in, say, the Klamath
# Mountains, 500 km north, while happening to also have a record 20 km from
# the Preserve in a different ecoregion. Restricting the distance
# calculation to only the ecoregion-matching records would report the wrong
# (larger) distance for a species that is, in fact, already documented
# close to the Preserve. Reporting the true minimum across every CA record
# for that species answers "how close has this species actually been found
# to the Preserve," while the ecoregion test above answers a separate
# question ("does this species occur on the Preserve's habitat type at
# all") — this script answers both, but doesn't conflate them.
#
# SPECIES-LEVEL RULE
# -------------------
# "Species-level identification" is the same binomial test already used
# throughout this pipeline's `scientificName_clean` column (Step 5's
# `clean_scientific_name()`): a capitalized genus token followed by a
# lowercase specific epithet (e.g. "Delia platura"). This naturally
# includes every species-rank CIBI-resolved record from Step 4 (which
# writes a real binomial into `scientificName` before Step 5 ever runs,
# so it's treated identically to any other GBIF species record), and
# naturally excludes bare genus/family names and any `BOLD:XXXXXXX`
# placeholder not resolved to species rank (which has no space and fails
# the binomial pattern).
#
# INPUTS
# -------
# - Step 6's output (`../06-boundary-distance/output/dwc_distance_to_boundary.csv`)
#   already carries, for every coordinate-complete record: `scientificName_clean`,
#   the coordinates, and `distance_to_preserve_km` — so this step reads
#   Step 6's output directly rather than re-deriving distance from Step 5's.
# - Step 9's output (`../09-identify-preserve-ecoregions/output/preserve_ecoregions.geojson`) —
#   the ecoregion polygon(s) that intersect the Preserve boundary.
#
# METHOD
# -------
# 1. Read only the columns needed (keeps memory use well below this
#    environment's limits for a 4.66M-row, 23-column file).
# 2. Filter to species-level records via the binomial test above.
# 3. Build point geometries (WGS84, matching GBIF's own coordinate
#    convention) and test each species-level record against the union of
#    Step 9's matched ecoregion polygon(s), in batches (consistent with
#    Step 6's own batching, though at this record count a single run
#    completes in under a minute and needs no checkpointing).
# 4. A species "qualifies" if at least one of its species-level records
#    falls inside the shared ecoregion(s).
# 5. For every qualifying species, report: record counts (statewide and
#    within the shared ecoregion), which of Step 9's ecoregion(s) it was
#    found in, nearest-to-boundary distance (km, minimum across ALL of
#    that species' statewide species-level records), and basic taxonomy.
# ============================================================

suppressMessages({
  library(readr)
  library(dplyr)
  library(sf)
  library(tidyr)
})

# ---- Paths (relative to this script's folder) ----
infile_distance   <- "../06-boundary-distance/output/dwc_distance_to_boundary.csv"
infile_ecoregions <- "../09-identify-preserve-ecoregions/output/preserve_ecoregions.geojson"
outdir            <- "output"
outfile           <- file.path(outdir, "ecoregion_species_list.csv")

if (!file.exists(infile_distance)) {
  stop("Step 6 output not found: ", infile_distance)
}
if (!file.exists(infile_ecoregions)) {
  stop("Step 9 output not found: ", infile_ecoregions,
       " (run identify_preserve_ecoregions.R first)")
}
if (!dir.exists(outdir)) dir.create(outdir, recursive = TRUE)

# ------------------------------------------------------------
# 1) Read Step 6's output, columns needed only
# ------------------------------------------------------------
cat("Reading Step 6 output (distance-to-boundary table)...\n")
df <- read_csv(
  infile_distance,
  col_types = cols_only(
    scientificName_clean   = col_character(),
    decimalLatitude        = col_double(),
    decimalLongitude       = col_double(),
    distance_to_preserve_km = col_double(),
    kingdom = col_character(),
    phylum  = col_character(),
    class   = col_character(),
    order   = col_character(),
    family  = col_character()
  ),
  progress = FALSE
)
n_input <- nrow(df)
cat("  ", n_input, "coordinate-complete records read.\n")

# ------------------------------------------------------------
# 2) Species-level filter (same binomial test as Step 5/clean_scientific_name)
# ------------------------------------------------------------
is_species_level <- !is.na(df$scientificName_clean) &
  grepl("^[A-Z][a-zA-Z-]+ [a-z][a-zA-Z-]+$", df$scientificName_clean)

cat("\nSpecies-level records (true binomial scientificName_clean):",
    sum(is_species_level), sprintf("(%.2f%% of coordinate-complete records)\n",
    100 * sum(is_species_level) / n_input))

sp <- df[is_species_level, ]
n_species_total <- length(unique(sp$scientificName_clean))
cat("Unique species-level names statewide:", n_species_total, "\n")
rm(df)

# ------------------------------------------------------------
# 3) Point-in-polygon test against Step 9's matched ecoregion(s), batched
# ------------------------------------------------------------
cat("\nReading Step 9 matched ecoregion polygon(s)...\n")
eco <- st_read(infile_ecoregions, quiet = TRUE)
cat("  ", nrow(eco), "ecoregion polygon(s):",
    paste(eco$US_L3NAME, collapse = "; "), "\n")
eco_union <- st_union(st_geometry(eco))

cat("\nTesting each species-level record against the shared ecoregion(s)...\n")
batch_size <- 250000
n_sp <- nrow(sp)
in_ecoregion <- logical(n_sp)

t_start <- Sys.time()
for (start in seq(1, n_sp, by = batch_size)) {
  end <- min(start + batch_size - 1, n_sp)
  pts <- st_as_sf(sp[start:end, c("decimalLongitude", "decimalLatitude")],
                   coords = c("decimalLongitude", "decimalLatitude"),
                   crs = 4326, remove = FALSE)
  in_ecoregion[start:end] <- st_intersects(pts, eco_union, sparse = FALSE)[, 1]
  cat(sprintf("  processed %d / %d records (%.1f sec elapsed)\n",
              end, n_sp, as.numeric(Sys.time() - t_start, units = "secs")))
}
sp$in_shared_ecoregion <- in_ecoregion

cat("\nSpecies-level records falling inside the shared ecoregion(s):",
    sum(sp$in_shared_ecoregion), "\n")

# ------------------------------------------------------------
# 4) Identify qualifying species and summarize
# ------------------------------------------------------------
qualifying_species <- unique(sp$scientificName_clean[sp$in_shared_ecoregion])
cat("\nQualifying species (>=1 record inside the shared ecoregion(s)):",
    length(qualifying_species), sprintf("(%.2f%% of the %d statewide species-level taxa)\n",
    100 * length(qualifying_species) / n_species_total, n_species_total))

sp_qual <- sp %>% filter(scientificName_clean %in% qualifying_species)

# Which specific ecoregion(s) (by name) did each qualifying species'
# ecoregion-matching records fall into? Computed once more, per-polygon,
# restricted to the already-small qualifying subset (cheap at this size).
qual_in_eco <- sp_qual %>% filter(in_shared_ecoregion)
pts_qual <- st_as_sf(qual_in_eco[, c("decimalLongitude", "decimalLatitude")],
                      coords = c("decimalLongitude", "decimalLatitude"),
                      crs = 4326, remove = FALSE)
per_poly_hits <- st_intersects(pts_qual, eco, sparse = FALSE)
qual_in_eco$ecoregion_names <- apply(per_poly_hits, 1, function(row) {
  paste(eco$US_L3NAME[row], collapse = " | ")
})

ecoregion_membership <- qual_in_eco %>%
  distinct(scientificName_clean, ecoregion_names) %>%
  group_by(scientificName_clean) %>%
  summarise(ecoregions_present = paste(sort(unique(unlist(strsplit(ecoregion_names, " \\| ")))),
                                        collapse = "; "),
            .groups = "drop")

species_list <- sp_qual %>%
  group_by(scientificName_clean) %>%
  summarise(
    kingdom = first(na.omit(kingdom)),
    phylum  = first(na.omit(phylum)),
    class   = first(na.omit(class)),
    order   = first(na.omit(order)),
    family  = first(na.omit(family)),
    n_ca_records_species_level = n(),
    n_records_in_shared_ecoregion = sum(in_shared_ecoregion),
    nearest_distance_to_preserve_km = min(distance_to_preserve_km, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  left_join(ecoregion_membership, by = "scientificName_clean") %>%
  rename(species = scientificName_clean) %>%
  arrange(nearest_distance_to_preserve_km) %>%
  select(species, kingdom, phylum, class, order, family,
         n_ca_records_species_level, n_records_in_shared_ecoregion,
         ecoregions_present, nearest_distance_to_preserve_km)

cat("\nFinal species list rows:", nrow(species_list), "\n")
cat("Nearest-distance summary (km):\n")
print(summary(species_list$nearest_distance_to_preserve_km))

write_csv(species_list, outfile)
cat("\nSpecies list written to", outfile, "\n")
