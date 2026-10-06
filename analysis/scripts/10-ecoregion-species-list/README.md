# Dangermond Project — Step 10: Species List for the Preserve's Shared Ecoregion(s)

The final deliverable for this biogeographic analysis thread: every
species-level-identified California arthropod with at least one occurrence
record on the same EPA Level III ecoregion(s) the Preserve itself sits on
(Step 9's result), paired with how close that species has actually been
recorded to the Preserve — regardless of which ecoregion that particular
closest record happened to fall in.

## Why two separate questions, not one

This step deliberately keeps "does this species occur on the Preserve's
habitat type" and "how close has it been recorded to the Preserve"
separate, because they answer different things:

- **Ecoregion membership** (does it qualify at all) is tested only against
  records that actually fall inside Step 9's matched ecoregion(s) —
  anywhere those ecoregions occur in California, not just inside the
  Preserve.
- **Nearest distance** is the minimum `distance_to_preserve_km` (from Step
  6) across *every* species-level record for that species statewide, not
  only the ecoregion-matching ones.

A species documented mostly in, say, the Klamath Mountains (which share
the Preserve's ecoregion) but with one record 20 km from the Preserve in a
*different* ecoregion still qualifies on habitat type, and its reported
nearest distance correctly reflects that nearby record — not an inflated
distance from restricting the search to only the ecoregion-matching
subset. Conflating the two would understate how close some qualifying
species really are.

## Species-level rule

Same binomial test already used throughout this pipeline on
`scientificName_clean` (Step 5's `clean_scientific_name()`): a capitalized
genus token followed by a lowercase specific epithet (e.g. "Delia
platura"), with no third token or trailing text. This automatically
includes:

- Every normally-identified GBIF species record.
- Every species-rank CIBI-resolved record from Step 4 — Step 4 writes a
  real binomial into `scientificName` *before* Step 5 ever runs, so by the
  time this step's input (Step 6's output, built on Step 5's
  `scientificName_clean`) exists, a CIBI-resolved species is
  indistinguishable from any other species-level GBIF record.

And excludes:

- Bare genus/family/subfamily/tribe names (`scientificName_clean` is a
  single token, no space).
- Any `BOLD:XXXXXXX` placeholder not resolved to species rank by Step 4
  (left untouched by Step 5's cleaning, so it still has no space and fails
  the binomial pattern).

## Method

1. Reads Step 6's output directly (`../06-boundary-distance/output/dwc_distance_to_boundary.csv`)
   — it already carries `scientificName_clean` and `distance_to_preserve_km`
   for every coordinate-complete record, so no separate join with Step 5's
   output is needed. Only the 9 columns actually used are read (keeps
   memory well under this environment's limits for a 4.66M-row file).
2. Filters to species-level records (binomial test above).
3. Builds point geometries (WGS84) and tests each species-level record
   against the union of Step 9's matched ecoregion polygon(s), in 250k-row
   batches (consistent with Step 6's own batching approach, though at this
   record count — under 3 million — the whole test completes in well under
   a minute and needed no checkpointing).
4. A species qualifies if ≥1 of its species-level records falls inside the
   shared ecoregion(s).
5. For each qualifying species: counts (statewide species-level records,
   and how many of those fall within the shared ecoregion), which specific
   ecoregion(s) it was found in, nearest-to-boundary distance (km, minimum
   across every statewide species-level record for that species), and
   basic taxonomy (kingdom/phylum/class/order/family).

## What's produced

**`output/ecoregion_species_list.csv`** — one row per qualifying species,
sorted by nearest distance to the Preserve boundary (closest first):

| Column | Meaning |
|---|---|
| `species` | The binomial (`scientificName_clean`). |
| `kingdom`/`phylum`/`class`/`order`/`family` | Taxonomy (first non-missing value across that species' records). |
| `n_ca_records_species_level` | Total species-level occurrence records statewide. |
| `n_records_in_shared_ecoregion` | How many of those fall inside Step 9's matched ecoregion(s). |
| `ecoregions_present` | Which of Step 9's matched ecoregion(s), by name, this species' records actually fall in (semicolon-separated if more than one). |
| `nearest_distance_to_preserve_km` | Minimum `distance_to_preserve_km` across every statewide species-level record for this species — not just the ecoregion-matching ones (see "Why two separate questions" above). |

No map or chart is produced for this step — a list-only deliverable, per
the project's own stated preference for this analysis.

## Verified against the real pipeline run

- 4,658,904 coordinate-complete records read from Step 6's output.
- 2,953,100 (63.39%) are species-level by the binomial test, across 29,262
  unique species-level names statewide.
- 1,650,743 of those species-level records fall inside Step 9's two
  matched ecoregions.
- **17,761 species (60.70% of the 29,262 statewide species-level taxa)
  qualify** — at least one record on the same habitat type as the
  Preserve, anywhere in California.
- Nearest-distance-to-boundary across the qualifying list: minimum 0 km
  (species already recorded on the Preserve itself), median 200.7 km, mean
  207.1 km, maximum 698.4 km.

## What this step does NOT do

- It does not restrict the nearest-distance calculation to only
  ecoregion-matching records — see "Why two separate questions" above.
- It does not produce a map, chart, or any visualization — list only, per
  the adopted scope for this task.
- It does not re-derive `distance_to_preserve_km`; it reads it directly
  from Step 6's already-computed, already-verified output.

## Paths

`infile_distance` points at Step 6's output.
`infile_ecoregions` points at Step 9's `output/preserve_ecoregions.geojson`.
