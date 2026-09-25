# Dangermond Project — Step 4: Distance to Preserve Boundary

New step (no prior "other chat" version — built fresh for this project).
Picks up after Step 3 (`../03-filter-latrange-overlap/`) and the
Preserve boundary file (`../reference-data/jldp_boundary.geojson`).

## What's actually wanted

Two outputs, both scoped to species that qualify for the Preserve's
latitudinal extent (Step 3's overlap list) — **never** a species that
doesn't occur anywhere in that band, and **never** a single global row
across the whole dataset:

**(a) Within extent** — for each in-extent species, its closest record
considering only that species' records whose *own* latitude falls
inside the Preserve's band.

**(b) Including outside extent** — for the same set of species, its
closest record considering *all* of that species' records, even ones
whose own latitude falls outside the band. This answers "how close does
this species actually get, period" rather than "how close does it get
while staying inside the coarse latitude filter."

Both keep every original column from the merged dataset, not just
summary statistics.

This went through two revisions before landing here, worth recording
since it shapes how to read the outputs:

- First version only computed distance for species that had already
  passed Step 3's filter, and only using their in-band records — so it
  had no way to produce (b) at all.
- Second version added a *global* "closest record overall, any species"
  output, which turned out to be a misreading — "closest overall" meant
  "closest overall **for each in-extent species**," not "the single
  closest record across the entire dataset regardless of whether the
  species occurs in the latitudinal extent at all." Corrected here: both
  outputs are per-species tables over the same in-extent species set:
  (a) restricts each species' candidate records to ones inside the
  band, (b) doesn't.

**Verified with a purpose-built test case:** a species with one record
inside the latitude band (14.5 km from the boundary) and a second record
outside the band but only 5.0 km from the boundary. (a) correctly
reports the in-band record (14.5 km); (b) correctly reports the
out-of-band record (5.0 km) for the same species. A second species in
the same test, with no closer out-of-band record, correctly came back
identical in both outputs (6.4 km either way). A third species with no
record anywhere in the latitude band correctly appeared in neither
output.

## What the script does

1. **Reads** Step 3's full coordinate-complete output (every record with
   usable coordinates, regardless of latitude) — needed so that (b) can
   see records Step 3's overlap file would have excluded.
2. **Reads** Step 3's latitude-overlap output, only to get the list of
   in-extent species — reusing Step 3's own (already-fixed) species-name
   normalization rather than re-implementing it here.
3. **Reads** the authoritative Preserve boundary polygon, checks its
   validity (`sf::st_is_valid()`), and derives the latitude band from
   its bounding box (same approach as Step 3, not hardcoded).
4. **Computes distance** from every coordinate-complete record to the
   boundary — 0 if the point falls inside the Preserve, otherwise the
   true geodesic distance to the nearest edge — and flags whether each
   record's own latitude falls in the band.
5. **Writes three outputs:**
   - `dwc_distance_to_boundary.csv` — every record, all original
     columns, plus distance columns, sorted nearest-first (a byproduct,
     useful on its own).
   - `nearest_record_per_species_within_extent.csv` — output (a).
   - `nearest_record_per_species_including_outside_extent.csv` —
     output (b).
   A console table also prints (a) vs (b) side by side per species with
   a `differs` flag, so it's immediately visible which species' true
   closest approach comes from outside the band.

## Distance method

Uses `sf::st_distance()` directly on unprojected WGS84 (lon/lat)
geometry. As of `sf` ≥ 1.0 this uses the S2 spherical geometry engine
(`sf_use_s2()` is `TRUE` by default) to compute true geodesic distances —
**not** naive Euclidean distance on raw latitude/longitude degrees, which
would be measurably wrong here: at this latitude (~34.5°N) one degree of
longitude is roughly 17% shorter than one degree of latitude (~91.7 km vs
~111.3 km).

Also verified directly against the real boundary polygon: the Preserve's
own centroid came back inside (0 m), a point shifted ~0.15° east came
back measurably outside (~6.0 km), and downtown Santa Barbara came back
at 61.2 km (~38 mi), consistent with its known real-world distance from
the Point Conception area.

## Ties

If more than one record shares the exact minimum distance within a
group, one is kept — first in the input's row order, **not** chosen by
any data-quality criterion — but `n_tied_at_min` records how many
records shared that minimum, so a tie is visible rather than silently
resolved. Same caveat as Step 2's duplicate-resolution order.

## Performance note

This computes distance for every coordinate-complete record (needed for
(b) — see above), not a pre-filtered subset — for the full
Arthropoda-in-California dataset that could be a large number of
records. S2-based distance against a single polygon is efficient, but if
this becomes slow in practice, a first-pass longitude-window filter
would be the natural place to optimize — not attempted here since it
hasn't been shown to be necessary yet.

## No distance threshold applied

Neither output filters to "within X km" — no such threshold has been
decided, and picking one arbitrarily seemed worse than surfacing the
actual nearest records for review. Easy to add later once a value is
chosen.

## Note on this copy (rebuilt after a workspace reset)

This script was reconstructed from conversation history after the
cloud workspace it originally lived in was reset. The scoping logic
described above (both outputs restricted to in-extent species,
diverging correctly between (a) and (b)) was verified with a real test
run in the original session — this rebuild restores that same,
already-verified logic rather than re-deriving it from scratch.

## Paths

`infile_coords` and `infile_overlap` both point at Step 3's output
folder, `boundary_file` at the shared reference boundary. All relative,
matching the pattern used in earlier steps.
