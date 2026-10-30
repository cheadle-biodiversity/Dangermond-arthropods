# Requirements — Step 9: Identify the Preserve's Shared EPA Level III Ecoregion(s)

Status: Implemented (`identify_preserve_ecoregions.R`) and verified against
the real EPA Region 9 Level III ecoregion shapefile and the real Preserve
boundary file (2 ecoregion polygons found to intersect, 91.94%/8.06% of
Preserve area respectively). See `README.md` for full design rationale,
including why "habitat type" is operationalized as EPA Level III
ecoregion and why the source files had to be user-supplied.

## 1. Purpose

Determine which EPA Level III ecoregion polygon(s), from the official
Region 9 shapefile, spatially overlap the Jack and Laura Dangermond
Preserve boundary — the shared-habitat-type reference Step 10 needs to
build its species list.

## 2. Inputs

| ID | Requirement |
|----|-------------|
| REQ-09-IN-1 | The system shall read the EPA Level III Ecoregions of Region 9 shapefile (`raw_download/reg9_eco_l3.shp`, with its companion `.shx`/`.dbf`/`.prj` files present in the same folder). |
| REQ-09-IN-2 | The system shall read the shared Preserve boundary file (`../reference-data/jldp_boundary.geojson`). |

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-09-F-1 | The system shall reproject the Preserve boundary into the ecoregion shapefile's native CRS before any spatial test, rather than reprojecting the (much larger) ecoregion dataset. |
| REQ-09-F-2 | The system shall identify every ecoregion polygon that spatially intersects the boundary polygon (`sf::st_intersects()`), not only the polygon containing the boundary's centroid. |
| REQ-09-F-3 | For every intersecting polygon, the system shall compute the true overlap area (via `st_intersection()` + `st_area()`), not merely record that intersection occurred. |
| REQ-09-F-4 | The system shall halt with an explicit error if zero ecoregion polygons intersect the boundary, rather than silently producing an empty downstream input for Step 10. |

## 4. Outputs

| ID | Requirement |
|----|-------------|
| REQ-09-OUT-1 | The system shall write a summary table (`output/preserve_ecoregions.csv`) of every matched ecoregion polygon: US/NA codes and names at Levels I-III, EPA Administrative Region, overlap area (m² and acres), and overlap as a percentage of total Preserve area. |
| REQ-09-OUT-2 | The system shall write the matched polygon geometry itself (`output/preserve_ecoregions.geojson`), reprojected to WGS84 to match GBIF's coordinate convention, for Step 10 to consume directly. |
| REQ-09-OUT-3 | The system shall report the same summary to the console during the run. |

## 5. Error Handling / Edge Cases

| ID | Requirement |
|----|-------------|
| REQ-09-ERR-1 | The system shall halt with an explicit error if either input file is missing. |
| REQ-09-ERR-2 | A polygon whose intersection with the boundary is topologically present but has zero computed area (a true edge-touching artifact) is not explicitly excluded by this script — none occurred in the real run (both matches were substantial, 8%+ of Preserve area), but see "Out of Scope" below. |

## 6. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-09-NFR-1 | This step shall use the shared `../reference-data/jldp_boundary.geojson`, not a separately hardcoded boundary, so it stays consistent with Steps 5/6/8's own use of that same file. |
| REQ-09-NFR-2 | The ecoregion source files (shapefile, metadata, symbology) shall be kept in this step's own `raw_download/` folder with their provenance documented, since they could not be fetched automatically by this pipeline's execution environment (see README). |

## 7. Dependencies

- R packages: `sf`, `dplyr`, `readr`.
- Upstream: `../reference-data/jldp_boundary.geojson`; user-supplied `raw_download/reg9_eco_l3.{shp,shx,dbf,prj}`.
- Downstream: Step 10 reads `output/preserve_ecoregions.geojson` for its point-in-polygon test.

## 8. Out of Scope

- A minimum-overlap-area or minimum-overlap-percentage threshold for
  excluding sliver matches — not needed for the real data (both real
  matches are substantial), so no threshold was implemented. A future user
  whose boundary happens to just graze a third ecoregion at the pixel/line
  level would see it included here; Step 10's results would reflect that
  faithfully, but nothing currently filters it out.
- Level IV (finer-grained) ecoregions — only Level III was requested.
- Automated download of the EPA source files — blocked at this pipeline's
  network layer; see README's "Data source" section.

## 9. Verification Status

**Verified against the real data**: 85 Level III ecoregion polygons read
(Region 9); Preserve boundary (WGS84) correctly reprojected into the
shapefile's native Albers Equal Area CRS; exactly 2 polygons found to
intersect — `US_L3CODE 6` ("Central California Foothills and Coastal
Mountains," 91.94% of Preserve area) and `US_L3CODE 85` ("Southern
California/Northern Baja Coast," 8.06% of Preserve area) — both well above
any plausible boundary-precision artifact threshold, confirming the
Preserve genuinely straddles a real ecoregion edge rather than the result
being a sliver (REQ-09-F-2/F-3). Output files written and consumed
directly by Step 10 without further transformation.
