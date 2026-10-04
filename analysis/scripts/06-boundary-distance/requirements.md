# Requirements — Step 6: Distance to Preserve Boundary

Status: Implemented (`distance_to_boundary.R`) and verified against
both synthetic test data and the real, live-GBIF pipeline output. See
`README.md` for the two rounds of scope correction this step's
requirements below already reflect, and for the real out-of-memory bug
found and fixed when this step first ran against the full dataset.

## 1. Purpose

For each species that qualifies for the Preserve's latitudinal extent,
compute two comparable "closest approach to the Preserve" figures using
true geodesic distance, and preserve full original record detail for
both.

## 2. Inputs

| ID | Requirement |
|----|-------------|
| REQ-06-IN-1 | The system shall read Step 5's full coordinate-complete output (`../05-filter-latrange-overlap/output/dwc_coords_complete.csv`) — every record, regardless of latitude — not the latitude-restricted overlap file. |
| REQ-06-IN-2 | The system shall read Step 5's latitude-overlap output (`../05-filter-latrange-overlap/output/dwc_latrange_overlap.csv`) solely to obtain the list of in-extent species, reusing Step 5's species-name normalization rather than re-deriving it. |
| REQ-06-IN-3 | The system shall read the authoritative Preserve boundary polygon and validate it (`sf::st_is_valid()`), warning explicitly if invalid rather than proceeding silently. |

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-06-F-1 | The system shall compute the true geodesic distance from every coordinate-complete record to the Preserve boundary polygon, using `sf::st_distance()` under the S2 spherical geometry engine — not naive planar distance on raw lon/lat degrees. |
| REQ-06-F-2 | A record whose point falls inside the Preserve polygon shall have a distance of exactly 0 and shall be flagged `inside_preserve = TRUE`. |
| REQ-06-F-3 | Each record shall be flagged `record_lat_in_band`, indicating whether that specific record's own latitude falls within the Preserve's latitude band. |
| REQ-06-F-4 | For each in-extent species (per REQ-06-IN-2), the system shall compute output (a): the closest record considering ONLY that species' records whose own latitude falls within the Preserve's band. |
| REQ-06-F-5 | For each in-extent species, the system shall compute output (b): the closest record considering ALL of that species' records, including ones whose own latitude falls outside the band. |
| REQ-06-F-6 | Both (a) and (b) shall be scoped to exactly the same species set (in-extent species) — neither output shall include a species that does not qualify for the latitudinal extent, and neither shall ever collapse to a single global row across all species. |
| REQ-06-F-7 | Both (a) and (b) shall retain every original column from the coordinate-complete dataset, not just summary statistics. |
| REQ-06-F-8 | The system shall report, per in-extent species, whether (a) and (b) select the same record or differ, via a `differs` flag, printed as a console comparison table. |

## 4. Outputs

| ID | Requirement |
|----|-------------|
| REQ-06-OUT-1 | The system shall write every coordinate-complete record, with computed distance and flag columns, to `output/dwc_distance_to_boundary.csv`, sorted nearest-first. |
| REQ-06-OUT-2 | The system shall write output (a) to `output/nearest_record_per_species_within_extent.csv`. |
| REQ-06-OUT-3 | The system shall write output (b) to `output/nearest_record_per_species_including_outside_extent.csv`. |
| REQ-06-OUT-4 | Both (a) and (b) shall include an `n_tied_at_min` column recording how many of that species' candidate records shared the exact minimum distance. |

## 5. Error Handling / Edge Cases

| ID | Requirement |
|----|-------------|
| REQ-06-ERR-1 | Records with non-numeric or missing coordinates (should not occur given Step 5's own filtering, but checked defensively) shall be dropped, with the count reported. |
| REQ-06-ERR-2 | When multiple records tie for a species' minimum distance, the system shall deterministically keep the first in input row order (not a data-quality judgment) and record the tie count (REQ-06-OUT-4) rather than resolving it silently. |

## 6. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-06-NFR-1 | Distance computation shall use the same geodesic method (S2 via `sf`) throughout the pipeline for consistency with Step 5's and Step 8's spatial calculations. |
| REQ-06-NFR-2 | No distance threshold shall be applied to filter either output — both surface every in-extent species' nearest record for review, regardless of how far it is. |

## 7. Dependencies

- R packages: `readr`, `dplyr`, `sf`.
- Upstream: Step 5 (both outputs), `../reference-data/jldp_boundary.geojson`.
- Downstream: Step 7 reads `nearest_record_per_species_including_outside_extent.csv` (output b).

## 8. Out of Scope

- Convex-hull / range-envelope overlap testing — Step 8.
- Any distance-threshold-based filtering or alerting.

## 9. Verification Status

Verified with a purpose-built test case: a species with one record
inside the latitude band (14.5 km from the boundary) and a second
record outside the band but only 5.0 km away — output (a) correctly
selected the in-band record, output (b) correctly selected the closer
out-of-band record for the same species, confirming REQ-06-F-4/F-5/F-6
all hold and genuinely diverge when they should. A second species with
no closer out-of-band record correctly came back identical in both
outputs. A third species with no record anywhere in the latitude band
correctly appeared in neither output. Distance method (REQ-06-F-1) was
independently sanity-checked against the real boundary polygon: its own
centroid returned 0 m, a point offset ~0.15° east returned a measurable
outside distance, and downtown Santa Barbara returned ≈61.2 km,
consistent with its known real-world distance.

**Also verified against the real pipeline run** — this is where a real
bug surfaced that no synthetic test case had exercised: computing
distance for all 4,658,904 real records in one `st_distance()` call
exhausted available memory and the process was killed outright (REQ
coverage above was all still correct; the implementation just couldn't
run at this scale). Fixed by batching the computation (see README);
re-run after the fix completed successfully in ~3.5 minutes, writing
all three outputs and covering 19,945 in-extent species in output (b),
6,609 in output (a).
