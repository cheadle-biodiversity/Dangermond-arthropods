# Requirements — Step 10: Species List for the Preserve's Shared Ecoregion(s)

Status: Implemented (`ecoregion_species_list.R`) and verified against the
real pipeline run (17,761 qualifying species of 29,262 statewide
species-level taxa; nearest distance range 0-698.4 km). See `README.md`
for full design rationale, including why ecoregion membership and nearest
distance are computed over different record subsets.

## 1. Purpose

Produce a single species list: every species-level-identified California
arthropod occurring on the same EPA Level III ecoregion(s) as the
Preserve (per Step 9), each paired with the distance from that species'
single nearest California occurrence record (among ALL its records
statewide) to the Preserve boundary.

## 2. Inputs

| ID | Requirement |
|----|-------------|
| REQ-10-IN-1 | The system shall read Step 6's output (`../06-boundary-distance/output/dwc_distance_to_boundary.csv`), using only the columns needed (`scientificName_clean`, coordinates, `distance_to_preserve_km`, and basic taxonomy), not the full 23-column file. |
| REQ-10-IN-2 | The system shall read Step 9's matched ecoregion polygon(s) (`../09-identify-preserve-ecoregions/output/preserve_ecoregions.geojson`). |

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-10-F-1 | The system shall classify a record as species-level if and only if `scientificName_clean` matches a true binomial pattern: a capitalized genus token followed by a single lowercase specific-epithet token, with nothing else (same test family as Step 5's `clean_scientific_name()` output shape). |
| REQ-10-F-2 | The system shall test every species-level record's coordinates for spatial intersection with the union of Step 9's matched ecoregion polygon(s). |
| REQ-10-F-3 | The system shall batch the spatial intersection test (250,000 records per batch) rather than testing all records in a single call, consistent with Step 6's own approach to large spatial operations in this environment. |
| REQ-10-F-4 | A species shall qualify for the output list if and only if at least one of its species-level records intersects the shared ecoregion(s). |
| REQ-10-F-5 | For each qualifying species, the nearest-distance-to-preserve value shall be the minimum `distance_to_preserve_km` across ALL of that species' statewide species-level records — not restricted to only the ecoregion-intersecting records (see README's "Why two separate questions" section). |
| REQ-10-F-6 | For each qualifying species, the system shall report which specific Step 9 ecoregion(s) (by `US_L3NAME`) its ecoregion-matching records actually fall into, not merely that it matched the union. |

## 4. Outputs

| ID | Requirement |
|----|-------------|
| REQ-10-OUT-1 | The system shall write one row per qualifying species to `output/ecoregion_species_list.csv`, sorted by nearest-distance-to-preserve ascending. |
| REQ-10-OUT-2 | Each row shall include: species name, kingdom/phylum/class/order/family, total statewide species-level record count, record count within the shared ecoregion(s), the specific ecoregion(s) present, and nearest-distance-to-preserve (km). |
| REQ-10-OUT-3 | The system shall report summary counts (species-level record count, unique statewide species-level taxa, qualifying species count, and a distance-distribution summary) to the console during the run. |

## 5. Error Handling / Edge Cases

| ID | Requirement |
|----|-------------|
| REQ-10-ERR-1 | The system shall halt with an explicit error if either Step 6's or Step 9's output file is missing (Step 9 must be run first). |
| REQ-10-ERR-2 | A species with no non-missing value for a given taxonomy column (kingdom/phylum/class/order/family) across all its records shall have that column reported as missing (`NA`) rather than the script failing. |

## 6. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-10-NFR-1 | This step shall read `distance_to_preserve_km` directly from Step 6's output rather than recomputing geodesic distance, avoiding duplicate, potentially-divergent distance logic. |
| REQ-10-NFR-2 | Column selection at read time (`cols_only()`) shall keep peak memory well within this environment's constraints for the full 4.66M-row, 1.3 GB input file — verified in the real run (full read plus batched spatial test completed in under a minute with no checkpointing needed, unlike Step 8's much longer per-species loop). |

## 7. Dependencies

- R packages: `readr`, `dplyr`, `sf`, `tidyr`.
- Upstream: Step 6 (`dwc_distance_to_boundary.csv`), Step 9 (`preserve_ecoregions.geojson`).
- Downstream: none — this is the final step in the pipeline.

## 8. Out of Scope

- Any map, chart, or other visualization of the resulting species list —
  list-only deliverable, per the adopted scope for this task.
- Restricting the nearest-distance calculation to only ecoregion-matching
  records (see REQ-10-F-5 and README's rationale).
- Re-testing non-species-level records (bare genus/family/BOLD
  placeholders) against the ecoregion polygons — out of scope by
  definition, since the deliverable is a *species* list.

## 9. Verification Status

**Verified against the real pipeline run**: 4,658,904 coordinate-complete
records read (9 columns only); 2,953,100 (63.39%) species-level across
29,262 unique statewide species-level taxa (REQ-10-F-1); spatial
intersection test against Step 9's 2-polygon union completed in ~45
seconds across 12 batches of up to 250,000 records (REQ-10-F-3),
confirming 1,650,743 species-level records fall inside the shared
ecoregion(s); 17,761 qualifying species identified (REQ-10-F-4, 60.70% of
statewide species-level taxa); nearest-distance-to-preserve computed
correctly across each qualifying species' full statewide record set
(REQ-10-F-5), ranging 0-698.4 km (median 200.7, mean 207.1); output
written with 17,761 data rows, sorted ascending by distance (REQ-10-OUT-1).
