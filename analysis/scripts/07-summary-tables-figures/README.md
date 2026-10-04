# Dangermond Project — Step 7: Summary Table & Figures

New step (no prior "other chat" version — built fresh for this project).
Picks up after Step 6 (`../06-boundary-distance/`) and produces the
requested deliverables: one summary table and two bar figures showing
how in-extent Arthropoda species break down by taxonomic order/family
and distance to the Dangermond Preserve boundary.

## What's produced

1. **`species_by_order_family_distance.csv`** — species counts
   cross-tabbed by order, family, and distance bin, plus a `Total`
   column per row and a `TOTAL` row at the bottom. One row per
   order/family combination actually present in the data.
2. **`species_by_order_and_distance.png`** — bar chart, distance bin on
   the x-axis, one bar per order within each bin (grouped, not
   stacked), bar height = species count.
3. **`species_by_order_and_family_stacked.png`** — same frame as the
   order chart (distance bin on the x-axis, one dodged bar per order
   within each bin), but each order's bar is now stacked into segments,
   one per family within that order, shaded from that order's own color
   (see "Order+family chart design" below). Replaces an earlier
   faceted-by-family design that's no longer part of this step.

## Key decisions (each one changes the actual numbers or how to read them)

**Which distance:** Step 6 produces two different "closest distance"
figures per species. This step uses output (b), "including outside
extent" — each species' true closest record to the boundary, even from
one whose own latitude falls outside the band — rather than output (a),
"within extent only." Step 6's own test case showed these can genuinely
differ for the same species, so this choice affects which bin a species
lands in, not just a cosmetic difference.

**Distance bins:** `0, 0<1 km, 1<5km, 5<10km, 10<25km, 25<50km` as
specified, plus a `50+ km` catch-all bin added so that a species farther
than 50 km still appears in the table rather than silently vanishing
from it. Bin boundaries: `0 km` is the exact point (inside the
Preserve); every other bin is `[lower, upper)`, so a species at exactly
5 km falls in `5-10 km`, not `1-5 km`. Implemented with explicit
`case_when()` logic rather than `cut()`, since the first bin (an exact
point) doesn't fit `cut()`'s usual all-open-or-all-closed convention.

**Table shape:** one combined table (order, family, then a column per
bin) rather than separate order-only and family-only tables, since both
bar charts are just different roll-ups of the same underlying counts —
one source of truth instead of three places that could drift out of
sync.

**Chart structure:** distance bin is the x-axis in both charts (per
your description), with taxonomic group forming the bars within each
bin — a grouped/clustered bar chart, not one bar per order/family and
not a stacked-by-bin bar.

**Order+family chart design:** the second figure keeps the exact same
frame as the order chart — distance bin on the x-axis, one dodged bar
per order within each bin, same colors/order assignment as the first
chart — but each order's bar is now stacked into segments, one per
family within that order, shaded from that order's own base color:
darker/fuller = more species in that family, lighter tint = fewer. E.g.
Hymenoptera's segments are all shades of Hymenoptera's blue, its most
numerous family getting the full/darkest blue and its least numerous
family the lightest tint. This replaced an earlier design that faceted
family counts by distance bin (one small panel per bin, neutral bar
color) — scrapped in favor of this segmented version, which keeps
family broken out by order (rather than just by bin) and reads as one
figure instead of a grid of small panels.

ggplot2 has no single built-in position that dodges by one grouping
(order) and stacks by another (family) within each dodge slot at the
same time — `position_dodge()`/`position_dodge2()` and
`position_stack()` each handle only one grouping. The technique used
here: compute each order's dodge offset manually as a numeric x
position (distance-bin index + a fixed per-order offset, same slot
width at every bin regardless of which orders are actually present
there — mirroring `position_dodge2(preserve = "single")`'s behavior in
the order chart), then let `geom_col()`'s default stacking handle the
family segments within each of those now-unique x positions. Axis
labels are restored afterward via `scale_x_continuous(breaks=, labels=)`
since the underlying x is numeric, not a real discrete factor.

That numeric-axis trick has one legibility cost the order chart doesn't
have: a true discrete axis automatically centers each label under its
own group of bars, but a faked one doesn't unless something marks where
each bin's "lane" begins and ends — especially with the angled label
text used here. Fixed two ways: x-axis tick marks are explicitly
re-enabled (`theme_minimal()` removes them by default) so each bin
center has a visible anchor, and a faint vertical divider line is drawn
at each bin *boundary* (half-integer positions, added as the first
layer so bars painted on top of it leave a visible gap only in the
unused space between bins). Caught by rendering the chart and looking
at it, not by reasoning about the code — the first version (no ticks,
no dividers) rendered bars that were plausibly readable as belonging to
the wrong bin when they sat near the edge of their dodge slot.

A true nested legend (an "Hymenoptera" header with its families listed
under it) isn't something ggplot2 supports natively without extra
layout tooling. The practical equivalent used here: legend entries are
labeled "Order: Family" and ordered so every family within the same
order sits adjacent to it in the legend, in the same shade sequence as
its bar segment — the grouping still reads from color + adjacency +
label, just without a literal section-header rule between orders.

## Color

The order chart uses this project's validated categorical palette (8
colorblind-safe hues, fixed order — see the `dataviz` skill's
`references/palette.md`), assigned to orders in order of descending
total species count so the most common order always reads with the same
relative visual weight. A 9th-or-beyond order folds into a neutral
"Other" gray rather than generating a new hue, per that palette's own
rule (never cycle categorical hues past their validated set). Verified
with a 10-order test case: the top 8 kept distinct colors, the remaining
2 correctly folded into "Other," and the legend rendered as expected.
Ties in total species count break alphabetically (a side effect of how
the underlying grouping works) — deterministic and reproducible, just
worth knowing if two orders' bar colors seem swapped from what you
might expect.

The order+family chart reuses the exact same order→color assignment
(including the "Other" folding), then generates each order's family
shades by blending that order's base hex toward white — not a second,
independently-chosen hue, so it still reads as "shades of one color"
per order rather than a second unrelated categorical scale. Within an
order, families are ranked by descending total species count and
assigned shades from full color (most numerous) to a lightened tint
(least numerous); ties break alphabetically, same caveat as the order
colors above. Re-verified with the same 10-order test case: the two
orders folded into "Other" correctly produced two separate "Other:
_family_" legend entries in distinct grey shades, rather than merging
or losing one. Not capped if an order has many families — with enough
families the lightest shades could become hard to tell apart, which
hadn't come up in testing against synthetic data but did come up
immediately against the real dataset — see "Real-data bug" below for
what that actually looked like and how it was fixed (not the
"other-order bucket" idea speculated here, which turned out not to be
the real constraint).

## Verified before use

- Full run against a 12-species test dataset spanning 5 orders, 8
  families, and all 7 distance bins (including a family —
  Hymenoptera/Formicidae — split across two different bins, to confirm
  the table correctly shows nonzero counts in multiple bin columns for
  the same row rather than collapsing them).
- Table output hand-checked against the test data species-by-species;
  every count matched.
- Both charts rendered and visually reviewed (not just "it ran without
  erroring") — axis labels legible, legend correct, no overlapping
  text, y-axis forced to integer-only ticks since species counts can't
  be fractional (ggplot's default tick placement can land on 0.5 etc.
  for small ranges, which reads oddly for count data).
- The order+family chart's dodge+stack positions checked by hand against
  the 12-species test data: computed each species' expected numeric x
  position from the dodge-offset formula, confirmed it landed in the
  correct bin "lane" (bounded by the divider lines), and confirmed the
  stacked segment order/colors within each bar matched the expected
  family ranking — not just eyeballed for general plausibility.
- The 8-vs-more-orders "Other" folding path specifically exercised with
  a second, dedicated test (10 orders, 1 species each) to confirm it
  actually works in both charts, not just that the code looks right —
  including that the order+family chart correctly produces two separate
  "Other: _family_" legend entries (in distinct grey shades) rather than
  merging the two folded orders' families into one.
- A real `mutate()` bug caught only by running the script (not by
  reading the code): the family-shade calculation used a scalar `if()`
  on a per-group value that's actually a vector inside a grouped
  `mutate()`, which errors for any order with more than one family.
  Fixed by switching to a vectorized `ifelse()`. This is exactly the
  kind of bug the "run it, don't just read it" testing pattern in this
  project exists to catch.
- A legibility gap caught only by rendering the chart and looking at
  it, not by reading the code: with no axis ticks (removed by
  `theme_minimal()` by default) and no discrete factor axis to anchor
  labels the way the order chart gets automatically, a bar sitting near
  the edge of its dodge slot was plausibly misreadable as belonging to
  the neighboring bin. Fixed by re-enabling x-axis tick marks and adding
  a faint vertical divider at each bin boundary.

## Missing order/family

If either column is missing from the input entirely, the script stops
with an explicit error rather than producing a broken or misleading
table — Step 3's column-header report is the place to check first if
that happens, since it would mean one of GBIF/Symbiota's exports didn't
carry those fields through. If a specific species has a blank
order/family value (present in the data but empty for that record), the
script labels it `(order not recorded)` / `(family not recorded)`
rather than dropping the species from the taxonomic breakdown.

## Real-data bug: runaway image height

Running this step against the real dataset (19,945 in-extent species)
surfaced a real scaling bug the synthetic 12-species test case was
never going to exercise: the order+family chart's height formula
(`5.5 + 0.15 inch per order:family legend row`) was sized for a
handful of families per order. Real data produced **1,031** distinct
order:family combinations, so the formula asked `ggsave()` for a
**~152-inch-tall** image (~48,000 pixels) — technically rendered, but
unusable as a figure, and rejected outright by the file-delivery tool
for being an absurd size.

**Fix:** cap the image at a fixed, always-reasonable maximum height
(22 inches) regardless of how many order:family combinations are
present, and let the legend wrap into multiple columns
(`guide_legend(ncol = ...)`, scaled to the actual number of legend
rows) so it uses the available height instead of dictating it. The
chart itself — the part that actually needs to stay readable — keeps
its intended size; with 1,000+ legend entries the legend is
necessarily dense text at any image size, which
`species_by_order_family_distance.csv` (this step's own full table) is
the better place to look up exact counts from, same relationship this
step's own earlier notes already described between the chart and the
table.

Re-run after the fix: both charts rendered successfully
(7200×6600 px for the order+family chart), 82 orders represented (top
8 keep distinct colors, 74 folded into "Other" — as designed), 19,945
species summarized across all 7 distance bins.

## Paths

`infile` points at Step 6's "including outside extent" output. Update
if you'd rather use the "within extent only" figure instead — nothing
else in the script needs to change.
