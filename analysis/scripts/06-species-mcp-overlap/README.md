# Dangermond Project — Step 6: Species Minimum Convex Polygons & Preserve Overlap

New step (no prior "other chat" version — built fresh for this
project). A different kind of analysis from Steps 4-5: instead of
"how close does each species get to the Preserve," this asks "does
each species' overall known range, as a minimum convex polygon (MCP),
overlap the Preserve at all."

## What's produced

1. **`species_mcp_overlap_summary.csv`** — one row per species that had
   enough data for a hull: record count, distinct-location count, hull
   area (km²), whether it overlaps the Preserve, the overlap area
   (km², 0 if none), and what percentage of the Preserve's total area
   that overlap represents. Sorted so overlapping species come first,
   ranked by percentage of the Preserve covered.
2. **`species_insufficient_data.csv`** — species that couldn't get a
   hull at all, with the reason (see "Insufficient data" below). Not
   dropped silently.
3. **`species_mcp_polygons.geojson`** — every hull actually built, as
   polygon features carrying the same summary columns as (1), so they
   can be opened in GIS software or plotted on a map alongside the
   Preserve boundary.

## Key decisions

**Which input dataset:** this uses Step 3's full coordinate-complete
output (`dwc_coords_complete.csv` — every species, any latitude), not
the latitude-band-restricted overlap file. That band was a coarse
pre-filter built for a different question (does this species' raw
latitude range even reach this far), not a real range boundary — using
it here would silently drop occurrence points a species' true range
hull needs, which could hide real overlaps or distort hull shape. This
step re-derives which species overlap the Preserve from each species'
full known range, independently of Step 3's filter.

**What "overlap" means:** `sf::st_intersects()` — true for any spatial
intersection at all, including a hull that fully *contains* the
Preserve, one fully *contained by* it, or just a partial/edge overlap.
`st_overlaps()` was deliberately not used, since it excludes the two
containment cases, which isn't what "overlap" means in plain usage.

**Insufficient data:** a convex hull needs at least 3 distinct,
non-collinear points. A species with fewer than 3 distinct coordinate
locations, or whose distinct locations are all collinear (hull
degenerates to a line/point instead of a real polygon), gets listed in
`species_insufficient_data.csv` with a reason rather than being dropped
silently or force-fit with an arbitrarily chosen buffer distance.

**Area method:** `sf::st_area()` directly on unprojected WGS84
geometry, consistent with Step 4's distance calculation — with `sf`'s
S2 spherical engine (`sf_use_s2()` is `TRUE` by default) this is true
geodesic area, not naive planar area on raw lon/lat degrees.

## This is a real 2D convex hull, not a latitude (or bounding-box) test

Worth stating explicitly, since it's easy to misread from a plot: the
hull is built with `sf::st_convex_hull()` on each species' full
`(decimalLongitude, decimalLatitude)` point set, so both east-west and
north-south spread shape the polygon — it is not derived from a
latitude range the way Step 3's coarse filter is.

The first verification plot made for this step (during the original
build) showed two of four synthetic test species' hulls as literal
rectangles, which understandably looked like it might mean only a
lat/lon bounding box was being tested. That was an artifact of the test
data, not the method: those two species' synthetic points happened to
be placed at rectangle corners, as a shortcut to make the expected
overlap percentage easy to compute by hand while verifying the script's
output — not a reflection of what a hull looks like from realistically
scattered occurrence points. Rebuilt with 17 randomly scattered points,
the resulting hull is an irregular polygon that clearly does not match
the lat/lon bounding box those same points would imply (the two shapes
were plotted side by side to confirm this directly, not just argued in
prose). Real GBIF occurrence data is scattered, so real species hulls
will be irregular polygons, not rectangles.

## Read this before interpreting results

A minimum convex polygon is the tightest **convex** shape enclosing
every occurrence point — it is not a true range map, and overlap here
is not evidence a species was ever actually recorded at the Preserve.
A species recorded across a wide swath of California will have a large
MCP that can easily overlap the Preserve just because the Preserve's
coordinates fall inside that broad convex envelope, even with zero
records anywhere nearby. **Expect most widely-distributed species to
show overlap under this method — that's the expected behavior of a
convex hull, not a bug.** If "has this species actually been recorded
near the Preserve" is the real question, Step 4's boundary-distance
output and Step 5's distance-bin breakdown answer that directly; this
step answers a different, broader question about range envelopes.

## Verified before use

- Built a 7-species synthetic test set covering every code path:
  - A hull built from 4 points far outside the Preserve's bounding box,
    clearly enclosing it entirely — confirmed `overlaps_preserve = TRUE`
    and `pct_of_preserve_covered ≈ 100%` (the whole Preserve is the
    intersection).
  - A hull covering only the western portion of the Preserve — confirmed
    a partial overlap (`68.1%` covered), not 0% or 100%.
  - A hull built from 3 points sampled *inside* the actual Preserve
    polygon (via `sf::st_sample()` against the real boundary file, not
    guessed coordinates) — confirmed `overlap_area_km2 == hull_area_km2`
    (the whole hull is inside the Preserve) and a small
    `pct_of_preserve_covered` (the hull itself is small relative to the
    Preserve).
  - A hull built from points far from the Preserve entirely (near Los
    Angeles) — confirmed `overlaps_preserve = FALSE` and both area
    columns are `0`.
  - A species with only 1 record, and one with only 2 distinct locations
    (despite 4 raw records, half of them exact duplicates) — both
    correctly routed to the insufficient-data report rather than
    producing a hull.
  - A species with 4 points intended to be collinear — see the bug
    below, this initially did **not** get caught.
  - All results also checked visually: hulls plotted against the real
    Preserve boundary polygon (not just its bounding box) confirmed the
    "fully encloses," "partial," and "fully inside" cases all look
    geometrically correct, not just numerically plausible.
- A follow-up scattered-point test (17 points, no rectangle corners)
  confirmed the hull tracks the actual outermost points in both
  directions rather than a lat/lon bounding box — see "This is a real
  2D convex hull" above.

- **A real bug caught only by testing, not by reading the code:** the
  first "collinear points" test case used 4 points differing by a
  constant amount in both latitude and longitude (a straight line in
  *lon/lat degree space*). That is **not** the same as collinear on the
  sphere — `sf`'s S2 engine works in real spherical geometry, where a
  constant-slope line in degrees is a rhumb line, not a geodesic — so
  the convex hull came back as a genuine (if extremely thin) `POLYGON`
  with nonzero area, not the `LINESTRING`/`POINT` the degeneracy check
  was looking for, and the species was incorrectly treated as valid.
  Caught by inspecting the actual output table and noticing the
  "collinear" species had a suspiciously tiny but nonzero area (`1.8e-8
  km²`) instead of appearing in the insufficient-data report. Fixed two
  ways: (1) the test case itself was corrected to use points that are
  *actually* geodesically collinear (same longitude — a meridian is a
  true geodesic), and (2) the degeneracy check in the script was
  hardened to not rely on geometry type alone — it now also flags any
  hull with area below a 1 m² floor as degenerate, since no real
  species occurrence hull should legitimately be smaller than that
  given ordinary GPS/GBIF coordinate precision. Re-tested after both
  fixes: the collinear species correctly landed in the insufficient-data
  report with an explicit "hull area is effectively zero" reason.

## Performance note

This loops over species one at a time (hull construction and the
overlap test aren't natively vectorized across groups in `sf`). Data is
split by species once up front, rather than re-filtered from the full
table on every iteration, to avoid an accidental O(n_species ×
n_records) scan — but for the full Arthropoda-in-California dataset,
with potentially many thousands of species, this could still take a
while to run. If that becomes a real bottleneck, batching the
hull/area/intersects calls instead of looping row-by-row would be the
natural next optimization — not attempted here since it hasn't been
shown to be necessary yet.

## Note on this copy (rebuilt after a workspace reset)

This script and its test-verified fixes were reconstructed from
conversation history after the cloud workspace they originally lived
in was reset. The Preserve boundary file itself is not a
reconstruction — it's the same file originally uploaded (same 346
vertices, same `GlobalID`), re-uploaded by the user after the reset so
this step (and Steps 3-4) could be rebuilt against the real polygon
rather than a placeholder.

## Paths

`infile` points at Step 3's full coordinate-complete output (not its
latitude-overlap output — see "Which input dataset" above). `boundary_file`
points at the shared reference boundary. Both relative, matching the
pattern used in earlier steps.
