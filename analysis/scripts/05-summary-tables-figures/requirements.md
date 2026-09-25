# Requirements — Step 5: Summary Table & Figures

Status: Implemented (`summarize_taxon_distance.R`) and verified against
synthetic test data. See `README.md` for the full design rationale
behind the order+family chart and the two bugs its build process
caught.

## 1. Purpose

Summarize in-extent species by taxonomic order/family and distance-to-
Preserve bin, as one table and two bar figures, all produced by the
script itself when run (not a manual post-processing step).

## 2. Inputs

| ID | Requirement |
|----|-------------|
| REQ-05-IN-1 | The system shall read Step 4's output (b) — `../04-boundary-distance/output/nearest_record_per_species_including_outside_extent.csv` — each in-extent species' true closest record, including ones outside the latitude band. |
| REQ-05-IN-2 | The system shall require `order`, `family`, and a species-name column (`scientificName_clean` if present, else `scientificName`) plus `distance_to_preserve_km` to be present in the input, and shall halt with an explicit, actionable error if any are missing. |

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-05-F-1 | The system shall bin each species' distance into exactly these bins, in this order: `0 km (inside)`, `0-1 km`, `1-5 km`, `5-10 km`, `10-25 km`, `25-50 km`, `50+ km`. |
| REQ-05-F-2 | Bin boundaries shall be `[lower, upper)` for every bin except the first, which is the exact point `distance == 0`; a species at exactly a bin boundary (e.g. 5 km) shall fall into the higher bin. |
| REQ-05-F-3 | A species whose distance is `NA` or otherwise unbinnable shall be excluded from the table and both figures, with the excluded count reported as a warning. |
| REQ-05-F-4 | A record with a missing/blank `order` or `family` shall be labeled `(order not recorded)` / `(family not recorded)` rather than dropped from the taxonomic breakdown. |
| REQ-05-F-5 | The system shall build one cross-tabulated table of species counts by `order`, `family`, and distance bin, with a `Total` column per row and a `TOTAL` row across all rows. |
| REQ-05-F-6 | The system shall build Chart 1: distance bin on the x-axis, one dodged (not stacked) bar per order within each bin, bar height = species count. |
| REQ-05-F-7 | The system shall build Chart 2: the same frame as Chart 1 (distance bin on x-axis, one dodged bar per order per bin), but each order's bar shall be stacked into segments, one per family within that order. |
| REQ-05-F-8 | In Chart 2, family segment color shall be a shade of that order's base color — full/darkest for the most numerous family in that order, progressively lighter for less numerous families — not an independently chosen hue. |
| REQ-05-F-9 | Both charts shall assign each order the same color, using this project's fixed 8-hue categorical palette, ordered by descending total species count. |
| REQ-05-F-10 | If more than 8 orders are present, orders beyond the top 8 (by total species count) shall fold into a single neutral "Other" category in both charts, rather than generating additional hues. |
| REQ-05-F-11 | In Chart 2, "Other"-folded orders shall still have their own families broken out as separate, distinctly shaded legend entries (e.g. "Other: FamilyX", "Other: FamilyY"), not merged into one undifferentiated segment. |
| REQ-05-F-12 | The y-axis of both charts shall use integer-only tick breaks, since species counts cannot be fractional. |

## 4. Outputs

| ID | Requirement |
|----|-------------|
| REQ-05-OUT-1 | The system shall write the summary table to `output/species_by_order_family_distance.csv`. |
| REQ-05-OUT-2 | The system shall write Chart 1 to `output/species_by_order_and_distance.png`. |
| REQ-05-OUT-3 | The system shall write Chart 2 to `output/species_by_order_and_family_stacked.png`. |
| REQ-05-OUT-4 | All three outputs (table + two figures) shall be produced by a single execution of the script — no separate manual step required. |

## 5. Error Handling / Edge Cases

| ID | Requirement |
|----|-------------|
| REQ-05-ERR-1 | If, after binning, no species remain to summarize, the system shall halt with an explicit error rather than producing an empty or misleading table/chart. |
| REQ-05-ERR-2 | If the input contains more than one row for the same species (violating the expected one-row-per-species shape of Step 4's output b), the system shall warn explicitly rather than silently inflating counts. |

## 6. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-05-NFR-1 | Chart 2's x-axis, though numerically computed (to allow the combined dodge+stack layout), shall present bin labels and visual anchors (tick marks, bin-boundary divider lines) equivalent in legibility to Chart 1's true discrete axis — a bar shall not be visually ambiguous as to which bin it belongs to. |
| REQ-05-NFR-2 | Any per-group scalar computation used to derive Chart 2's family shading shall be implemented in a way that is correct when a group contains more than one row (i.e. vectorized, not a scalar `if()` inside a grouped `mutate()`). |

## 7. Dependencies

- R packages: `readr`, `dplyr`, `tidyr`, `ggplot2`, `forcats`.
- Upstream: Step 4 (output b).
- Downstream: none (terminal output for this branch of the pipeline).

## 8. Out of Scope

- A family-only chart (an earlier faceted-by-bin design was built, reviewed, and explicitly replaced by Chart 2 per user direction — see README).
- Any distance bin finer than 25-50 km / coarser than the "50+ km" catch-all.

## 9. Verification Status

Verified against a 12-species synthetic dataset spanning 5 orders, 8
families, and all 7 distance bins (including one family split across
two bins, to confirm REQ-05-F-5 doesn't collapse multi-bin counts).
Table output hand-checked species-by-species against the test data;
every count matched. Both charts rendered and visually reviewed, not
just checked for successful execution. The "Other" folding path
(REQ-05-F-10/F-11) was separately exercised with a 10-order,
1-species-each test case, confirming both charts fold correctly and
Chart 2 produces two distinct "Other: _family_" legend entries. Two
real bugs were caught only by running the script, not by reading the
code: a `mutate()` crash from a non-vectorized `if()` (REQ-05-NFR-2),
and a legibility gap from missing axis anchors on Chart 2's numeric
x-axis (REQ-05-NFR-1) — both are now fixed in the current
implementation. Fully re-confirmed on the first rebuild run after the
workspace reset (identical table and pixel-identical chart output).
