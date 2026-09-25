# Dangermond Project — Step 3: Coordinate Filtering & Latitude-Range Overlap

Picks up after Step 2 (`../02-merge-deduplicate/`) and the Preserve
boundary file (`../reference-data/jldp_boundary.geojson`).

## What's produced

1. **`output/dwc_coords_complete.csv`** — every merged record that has
   both `decimalLatitude` and `decimalLongitude`, regardless of
   latitude. This is the "cleaned" dataset later steps (4 and 6) build
   from — not the latitude-restricted file below.
2. **`output/dwc_latrange_overlap.csv`** — the subset of (1) restricted
   to species whose overall latitude range overlaps the Dangermond
   Preserve's own latitude band. A coarse, fast first-pass filter, not
   a precise spatial test.

## Key decisions

**Species-name normalization before grouping.** Confirmed with a test
case before this fix was written, not just suspected: grouping directly
on the raw `scientificName` string silently fragments a single species
into multiple groups when sources format names differently — GBIF's
interpreted export typically includes full authorship ("Formica rufa
Linnaeus, 1758") while a Symbiota-network export is often the bare
binomial ("Formica rufa"). In a test case with the same species present
in both sources (one record at 34.5°, one at 34.6°, spanning the
Dangermond boundary), the un-normalized version fragmented it into two
"species," one of which was silently dropped from the overlap results
entirely — not for any biological reason, just a naming-format
difference between sources.

Fix: derive `scientificName_clean` (genus + specific epithet only,
authorship/year stripped) via `clean_scientific_name()`, and group on
that instead. The original `scientificName` is kept in the output for
reference/audit, and every distinct raw name folded into a group is
listed in the console summary so nothing is hidden by the
normalization. Scope note: this operates at the species level by
design — a trinomial (subspecies/variety) folds up to its parent
species, and a name that doesn't start with a capitalized genus-like
token (blank, a hybrid-formula name, an OCR artifact) is left unchanged
rather than guessed at, simply forming its own group.

**`regmatches()` vector-misalignment bug**, caught while prototyping
the name-cleaning fix above, before it shipped: `regmatches(x,
regexpr(pattern, x))` silently **drops** non-matching elements from its
result vector instead of returning `NA`/the original value in their
place — which shifts every subsequent element out of alignment with
the input. A test case with a parenthetical-authorship name came back
`NA` incorrectly because of this misalignment, not because the pattern
itself was wrong. Fixed by switching to `sub()` with a capture group
instead, which is always one-to-one with its input — no realignment
possible.

**Boundary source reconciliation.** `lat_min`/`lat_max` used to be
hardcoded as `34.442106`/`34.574661`. Once the authoritative boundary
file for the Preserve became available, those hardcoded numbers turned
out to be close but not exact — off by roughly 20-50 meters on each
end from the polygon's true bounding box (`34.442303`/`34.574189`).
This script now derives `lat_min`/`lat_max` directly from
`../reference-data/jldp_boundary.geojson`'s bounding box every run, so
there's one authoritative source instead of two slightly different
numbers, and it stays correct if the boundary geometry is ever revised.

## What "latitude-range overlap" means (and doesn't)

A species passes this filter if its *overall* latitude range (min to
max across every record) overlaps the Preserve's latitude band at all
— a coarse, one-dimensional test, not a real spatial check. It ignores
longitude entirely, and it says nothing about whether any specific
record actually falls near the Preserve. It exists purely as a fast
first-pass filter for later steps that need one; Step 4's
boundary-distance calculation and Step 6's minimum-convex-polygon
overlap test are the places to look for actual spatial relationships to
the Preserve. Step 6 in particular reads Step 3's *full*
coordinate-complete output rather than this latitude-restricted file,
specifically to avoid inheriting this coarse filter's blind spots.

## Note on this copy (rebuilt after a workspace reset)

This script was reconstructed from conversation history after the
cloud workspace it originally lived in was reset. Both bugs described
above (the cross-source name-fragmentation issue and the
`regmatches()` misalignment issue) were caught and fixed with real test
data in the original session — this rebuild restores that same,
already-verified logic rather than re-deriving it from scratch.

## Paths

`infile` points at Step 2's merged/deduplicated output. `boundary_file`
points at the shared reference boundary.
