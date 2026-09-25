# Dangermond Project — Reference Data

Shared inputs used by more than one pipeline step, kept in one place so
there's a single authoritative copy rather than duplicates drifting apart
across step folders.

## jldp_boundary.geojson

The Jack and Laura Dangermond Preserve boundary polygon, provided by the
user (originally selected from among CSV/shapefile/GeoJSON/KML options —
GeoJSON was recommended: single self-contained file, no companion
`.shx`/`.dbf`/`.prj` files to lose track of, and a coordinate reference
system fixed by the format spec to WGS84, matching the `decimalLatitude`/
`decimalLongitude` fields already used throughout this project).

**Validated before use** (not just assumed correct):

- Valid GeoJSON, `FeatureCollection` with 1 `Feature`, geometry type
  `Polygon`, CRS explicitly declared as `EPSG:4326` (WGS84).
- `properties.Name` = "The Dangermond Preserve"; `GIS_Acres` ≈ 24,458.6.
- 346 vertices; ring closure confirmed (first coordinate == last
  coordinate).
- `sf::st_is_valid()` returns `TRUE` — no self-intersections or other
  geometry defects.
- True bounding box: longitude -120.499302 to -120.357715, latitude
  34.442303 to 34.574189.
- Cross-checked against Step 3's previously-hardcoded latitude range
  (34.442106 / 34.574661, sourced separately before this boundary file
  was available): close but not identical, off by roughly 20-50 meters
  on each end. Step 3 now derives its latitude range from this file
  directly instead of carrying the slightly different hardcoded numbers
  — see that step's README/script for details.
- Distance sanity check (used while building Step 4): a test point at
  this polygon's centroid correctly returned 0 m (inside); a point
  offset ~0.15° east returned a measurable outside distance; downtown
  Santa Barbara returned ≈61.2 km (~38 mi), consistent with its known
  real-world distance from the Point Conception area.

## Note on this copy (re-uploaded after a workspace reset)

The cloud workspace this project's files live in was reset partway
through Step 6, which wiped every file on disk, including this one. The
user re-uploaded the original `jldp_boundary.geojson` (same file, same
346-vertex polygon, same `GlobalID`) so the project could be rebuilt
against the real boundary rather than a reconstruction — nothing in this
file is a guess or an approximation of the original.

## Used by

- `../03-filter-latrange-overlap/` — derives the Preserve's latitude
  range from this file's bounding box.
- `../04-boundary-distance/` — computes each occurrence record's true
  geodesic distance to this polygon.
- `../06-species-mcp-overlap/` — tests each species' minimum convex
  polygon for spatial overlap with this polygon.
