# Dangermond Project — Step 8: Species Minimum Convex Polygons & Preserve Overlap

New step (no prior "other chat" version — built fresh for this
project). A different kind of analysis from Steps 5-6: instead of
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

**Which input dataset:** this uses Step 5's full coordinate-complete
output (`dwc_coords_complete.csv` — every species, any latitude), not
the latitude-band-restricted overlap file. That band was a coarse
pre-filter built for a different question (does this species' raw
latitude range even reach this far), not a real range boundary — using
it here would silently drop occurrence points a species' true range
hull needs, which could hide real overlaps or distort hull shape. This
step re-derives which species overlap the Preserve from each species'
full known range, independently of Step 5's filter.

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
geometry, consistent with Step 6's distance calculation — with `sf`'s
S2 spherical engine (`sf_use_s2()` is `TRUE` by default) this is true
geodesic area, not naive planar area on raw lon/lat degrees.

## This is a real 2D convex hull, not a latitude (or bounding-box) test

Worth stating explicitly, since it's easy to misread from a plot: the
hull is built with `sf::st_convex_hull()` on each species' full
`(decimalLongitude, decimalLatitude)` point set, so both east-west and
north-south spread shape the polygon — it is not derived from a
latitude range the way Step 5's coarse filter is.

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
near the Preserve" is the real question, Step 6's boundary-distance
output and Step 7's distance-bin breakdown answer that directly; this
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
with potentially many thousands of species, this takes a while to run
for real — confirmed against the real dataset (53,763 species to
process): roughly 25-30 minutes for the per-species loop itself.
Memory stayed flat throughout (~2.7 GB RSS), so this part scales fine;
the real bottleneck turned out to be somewhere else entirely — see
below.

## Real-data bug: `do.call(rbind, ...)` on ~27,000 hulls never finishes

The per-species loop above completed fine against the real data
(27,348 species got a valid hull), and the two CSV summary outputs
wrote successfully in seconds. But the final step — combining all
~27,000 individual single-feature `sf` hull objects into one file with
`do.call(rbind, valid_hulls)` — ran at 100% CPU with flat memory for
over 10 minutes and never completed. This is a classic R anti-pattern:
`rbind()`'s S3 dispatch recombines its arguments pairwise internally,
so a single `do.call(rbind, <list of thousands>)` call re-copies the
growing result over and over — an `O(n²)` blowup that isn't visible
from reading the code, only from running it at real scale.

**Fix:** combine the attribute columns and the geometries separately,
using operations that are actually vectorized across the whole list —
`dplyr::bind_rows()` for the attributes (the same function already
used successfully for the two CSV outputs) and `c()` for the `sfc`
geometry list (concatenates in one pass, not pairwise) — then
reassemble with `st_sf()`. Benchmarked directly against ~27,000
single-feature `sf` objects: ~7 seconds this way vs. not completing in
10+ minutes the original way.

**Also added:** a checkpoint (`output/_checkpoint_after_loop.rds`)
saved immediately after the per-species loop finishes, before the
assembly/write step runs. The loop is the expensive part (tens of
minutes); everything after it is just reformatting and writing that
same result. A future bug in the assembly step — like this one — now
costs a reload of that checkpoint, not a 25-30 minute re-run of the
whole loop.

## Real-data problem: the per-species loop itself got killed mid-run

The checkpoint above protects against a bug *after* the loop, but on
one real run (in a memory-constrained environment, ~7.8 GB total, no
swap) the R process was killed mid-loop, with no error message —
consistent with an out-of-memory kill, though not confirmed via a
kernel log in that environment. Without any checkpoint during the loop
itself, that would mean losing the entire 25-30 minute loop, not just
the assembly step.

**Fix:** an in-progress checkpoint (`output/_checkpoint_in_progress.rds`)
is now saved every 2,000 species processed, holding the species list
(to confirm it still matches the current input) plus everything
accumulated so far. On the next run, if this file exists and its
species list matches, the loop resumes right after the last checkpoint
instead of restarting from species 1. The file is removed once the
loop finishes normally — the after-loop checkpoint above then takes
over. Confirmed working on the real run that triggered this fix: after
being killed partway through, a resumed run picked up from the last
saved checkpoint and completed the remaining species, rather than
reprocessing all 53,763 from scratch.

## Paths

`infile` points at Step 5's full coordinate-complete output (not its
latitude-overlap output — see "Which input dataset" above). `boundary_file`
points at the shared reference boundary. Both relative, matching the
pattern used in earlier steps.
