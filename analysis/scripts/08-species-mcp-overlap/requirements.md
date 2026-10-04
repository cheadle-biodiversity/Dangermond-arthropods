# Requirements — Step 8: Species Minimum Convex Polygons & Preserve Overlap

Status: Implemented (`species_mcp_overlap.R`) and verified against
synthetic test data and against the real, live-GBIF pipeline output
(53,763 species processed; 27,348 with a valid hull). See `README.md`
for full design rationale, including a clarification on what the
convex-hull method actually tests (it is not a latitude- or
bounding-box-only test), and the real `do.call(rbind, ...)`
performance bug found only by running this step at real scale.

## 1. Purpose

For every species with enough occurrence data, build a minimum convex
polygon (MCP) representing its overall known range envelope, and
determine whether that envelope spatially overlaps the Dangermond
Preserve boundary — independent of, and answering a different question
from, Steps 5-6's point-distance analysis.

## 2. Inputs

| ID | Requirement |
|----|-------------|
| REQ-08-IN-1 | The system shall read Step 5's FULL coordinate-complete output (`../05-filter-latrange-overlap/output/dwc_coords_complete.csv`) — every species, any latitude — and shall NOT use Step 5's latitude-restricted overlap file, since that filter is not a real range boundary and would distort or omit hull-relevant points. |
| REQ-08-IN-2 | The system shall read the authoritative Preserve boundary polygon and validate it (`sf::st_is_valid()`), warning explicitly if invalid. |

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-08-F-1 | For each species, the system shall build a minimum convex polygon from that species' distinct `(decimalLongitude, decimalLatitude)` occurrence coordinates, using a true two-dimensional convex hull (`sf::st_convex_hull()`) — sensitive to spread in both longitude and latitude, not a one-dimensional range or bounding-box test. |
| REQ-08-F-2 | Duplicate coordinate locations for the same species shall be collapsed to one before hull construction (repeat visits to the same point add no geometric information). |
| REQ-08-F-3 | A species with fewer than 3 distinct coordinate locations shall NOT receive a hull, and shall instead be recorded in the insufficient-data output (REQ-08-OUT-2) with an explicit reason. |
| REQ-08-F-4 | A species whose distinct locations are collinear (or nearly collinear, such that the resulting hull has no meaningful area) shall NOT receive a valid hull, and shall instead be recorded in the insufficient-data output with an explicit reason distinguishing it from REQ-08-F-3. |
| REQ-08-F-5 | For every species with a valid hull, the system shall test spatial overlap with the Preserve boundary using `sf::st_intersects()` — true for ANY intersection, including one polygon fully containing the other, not only a partial/edge overlap (`st_overlaps()` shall NOT be used, as it would incorrectly exclude containment cases). |
| REQ-08-F-6 | For every species with a valid hull, the system shall compute the hull's total area and, if it overlaps, the overlap area with the Preserve, both using true geodesic area (`sf::st_area()` under the S2 engine), not planar approximation on raw coordinates. |
| REQ-08-F-7 | For every overlapping species, the system shall compute what percentage of the Preserve's total area the overlap represents. |

## 4. Outputs

| ID | Requirement |
|----|-------------|
| REQ-08-OUT-1 | The system shall write one row per species with a valid hull to `output/species_mcp_overlap_summary.csv`, containing: species, record count, distinct-location count, hull area (km²), overlap flag, overlap area (km²), and percent of Preserve covered — sorted with overlapping species first, ranked by percent covered. |
| REQ-08-OUT-2 | The system shall write one row per species without enough data for a hull to `output/species_insufficient_data.csv`, with an explicit, human-readable reason per species (never silently dropped). |
| REQ-08-OUT-3 | The system shall write every valid hull's geometry, carrying the same attributes as REQ-08-OUT-1, to `output/species_mcp_polygons.geojson`. |

## 5. Error Handling / Edge Cases

| ID | Requirement |
|----|-------------|
| REQ-08-ERR-1 | A hull that comes back as a non-`POLYGON` geometry type (e.g. `LINESTRING`/`POINT` from collinear input) shall be caught and routed to REQ-08-OUT-2, not treated as valid. |
| REQ-08-ERR-2 | A hull that comes back as a `POLYGON` type but with area below a 1 m² floor (numerical noise from near-collinear input under geodesic/S2 geometry) shall ALSO be caught and routed to REQ-08-OUT-2 — geometry type alone is not a sufficient degeneracy check (see README for the confirmed failure case this addresses). |
| REQ-08-ERR-3 | Records with non-numeric, missing, or blank species-name/coordinate values shall be excluded from hull construction entirely, upstream of per-species grouping. |

## 6. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-08-NFR-1 | The area and overlap computation method shall be consistent with Step 6's geodesic distance method (same `sf`/S2 engine), so results are comparable in kind across the pipeline. |
| REQ-08-NFR-2 | Data shall be partitioned by species once up front (not re-filtered from the full table on every per-species iteration), to avoid an unnecessary O(n_species × n_records) scan. |
| REQ-08-NFR-3 | A convex hull is explicitly NOT a range map or evidence of actual recorded occurrence at the Preserve; this limitation shall be documented alongside the outputs (see README, "Read this before interpreting results") so results are not misread as equivalent to Steps 5-6's point-proximity findings. |
| REQ-08-NFR-4 | The per-species loop shall save an incremental checkpoint (species processed so far, keyed to the exact species list) at a regular interval, and shall resume from the latest matching checkpoint on restart rather than reprocessing already-completed species — the loop has been observed to take long enough, and this environment's memory tight enough, that a mid-run kill is a real possibility, not just a theoretical one (see README). |

## 7. Dependencies

- R packages: `readr`, `dplyr`, `sf`.
- Upstream: Step 5 (`dwc_coords_complete.csv` only — REQ-08-IN-1), `../reference-data/jldp_boundary.geojson`.
- Downstream: none (terminal output for this branch of the pipeline).

## 8. Out of Scope

- Any non-convex or kernel-density range estimate (this step is MCP only, by explicit request).
- A distance or proximity metric between hull and boundary when they don't overlap (overlap is boolean + area; near-miss distance is Step 6's domain).
- Batching/vectorizing the per-species loop beyond the up-front split (REQ-08-NFR-2) — noted as a future optimization if performance becomes an issue at full dataset scale.

## 9. Verification Status

Verified against a 7-species synthetic test set covering every
functional requirement above: a hull fully enclosing the Preserve
(100% covered), a hull partially overlapping it (68.1% covered), a
hull sampled from points genuinely inside the real Preserve polygon
(overlap area == hull area), a hull far away with no overlap, a
1-record species and a 2-distinct-location species (both correctly
routed to insufficient-data), and a collinear-points species. The
collinear case caught a real bug during verification: points collinear
in lon/lat degree space are not necessarily collinear under S2's
geodesic geometry, so the hull came back as a genuine but
near-zero-area `POLYGON` rather than a degenerate line — REQ-08-ERR-2
was added specifically to catch this, confirmed fixed by re-running the
same test case. A separate scattered-point (non-rectangular) test
confirmed REQ-08-F-1 is a true 2D hull, not a bounding-box or
latitude-only test.

**Also verified against the real pipeline run**: 53,763 species
processed; 27,348 with a valid hull (2,398 overlapping the Preserve,
24,950 not), 26,415 correctly routed to the insufficient-data report.
The per-species loop itself (REQ-08-NFR-2) completed in ~25-30 minutes
with flat memory, confirming it scales as designed. The real
bottleneck was downstream of the loop — combining ~27,000 individual
hull objects with `do.call(rbind, ...)` never finished (a classic
quadratic R anti-pattern, not something the loop-scaling requirements
above anticipated). Fixed by combining attributes and geometries
separately; re-run after the fix completed in seconds. A mid-run
checkpoint was also added so a future bug at the assembly stage
doesn't cost a re-run of the per-species loop. See README for full
detail on both.

**REQ-08-NFR-4 was added after a real mid-loop kill**, not
speculatively: on one run, in an environment with ~7.8 GB total memory
and no swap, the R process was killed partway through the per-species
loop with no error message. The incremental checkpoint/resume logic
was added in direct response and confirmed working on the run that
followed — it resumed from the last saved point rather than
reprocessing all 53,763 species. See README, "Real-data problem: the
per-species loop itself got killed mid-run."
