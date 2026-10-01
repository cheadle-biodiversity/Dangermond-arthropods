# Requirements — Step 4: Coordinate Filtering & Latitude-Range Overlap

Status: Implemented (`filter_coords_latrange.R`) and verified against
both synthetic test data and the real, live-GBIF pipeline output. See
`README.md` for design rationale, the cross-source name-fragmentation
bug, the `regmatches()` bug, and the real-data BOLD BIN collapse bug
this step's implementation specifically avoids.

## 1. Purpose

Produce the coordinate-complete dataset that later steps build from,
and a coarse, fast first-pass list of species whose overall latitude
range overlaps the Dangermond Preserve's latitude band.

## 2. Inputs

| ID | Requirement |
|----|-------------|
| REQ-04-IN-1 | The system shall read Step 3's merged/deduplicated output (`../03-merge-deduplicate/output/dwc_merged_deduplicated.csv`). |
| REQ-04-IN-2 | The system shall read the authoritative Preserve boundary polygon (`../reference-data/jldp_boundary.geojson`) and derive the Preserve's latitude band from that file's bounding box — never from a hardcoded latitude range. |

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-04-F-1 | The system shall coerce `decimalLatitude`/`decimalLongitude` to numeric and remove any record missing either value. |
| REQ-04-F-2 | The system shall derive a normalized species name, `scientificName_clean`, by stripping authorship/year/rank text down to genus + specific epithet, so records of the same species formatted differently by different sources (e.g. full authorship vs. bare binomial) group together correctly. |
| REQ-04-F-3 | Names that do not match the expected "capitalized genus + lowercase epithet" pattern shall be left unchanged by REQ-04-F-2, rather than guessed at, and shall form their own group. |
| REQ-04-F-4 | The system shall compute, per normalized species, the minimum and maximum `decimalLatitude` across all of that species' coordinate-complete records. |
| REQ-04-F-5 | The system shall retain a species in the latitude-overlap output if and only if its latitude range `[lat_min_sp, lat_max_sp]` overlaps the Preserve's latitude band `[lat_min, lat_max]`, using the standard interval-overlap test (`lat_min_sp <= lat_max AND lat_max_sp >= lat_min`). |

## 4. Outputs

| ID | Requirement |
|----|-------------|
| REQ-04-OUT-1 | The system shall write every coordinate-complete record (all original columns, plus `scientificName_clean`) to `output/dwc_coords_complete.csv`, regardless of latitude. |
| REQ-04-OUT-2 | The system shall write the subset of (OUT-1) belonging to latitude-overlap species to `output/dwc_latrange_overlap.csv`. |
| REQ-04-OUT-3 | The system shall print a per-species console summary of the overlap species, including each species' latitude range, record count, and the distinct raw `scientificName` values folded into it. |

## 5. Error Handling / Edge Cases

| ID | Requirement |
|----|-------------|
| REQ-04-ERR-1 | Records with unusable (non-numeric or missing) coordinates shall be excluded from `dwc_coords_complete.csv`, with the dropped count reported to the console. |
| REQ-04-ERR-2 | Records with `scientificName_clean = NA` shall be excluded from the per-species latitude-range computation, so they cannot silently form a bogus "NA species" group. |

## 6. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-04-NFR-1 | The Preserve's latitude band shall always be derived from the current boundary file at run time, never hardcoded, so the result stays correct if the boundary geometry is ever revised. |
| REQ-04-NFR-2 | The name-normalization step (REQ-04-F-2) shall be implemented using an approach that preserves one-to-one alignment between input and output vectors (i.e. not `regexpr()`+`regmatches()`, which can silently drop non-matching elements) — see README for the specific bug this avoids. |

## 7. Dependencies

- R packages: `readr`, `dplyr`, `sf`.
- Upstream: Step 3 (`dwc_merged_deduplicated.csv`), `../reference-data/jldp_boundary.geojson`.
- Downstream: Step 5 reads both outputs; Step 7 reads `dwc_coords_complete.csv` only (deliberately bypassing `dwc_latrange_overlap.csv` — see Step 7 requirements, REQ-07-IN-1).

## 8. Out of Scope

- True spatial (2D) overlap testing against the Preserve polygon — this step is a 1D latitude-only pre-filter by design; see Step 5 (point distance) and Step 7 (convex-hull overlap) for actual spatial tests.
- Subspecies/variety-level resolution — trinomials are folded to their parent species (REQ-04-F-2).

## 9. Verification Status

Verified against a synthetic merged dataset containing: the same
species recorded under two differently-formatted raw names (one with
full authorship, one bare binomial) with coordinates spanning the
Preserve's latitude band — confirmed correctly merged into one
`scientificName_clean` group and correctly flagged as overlapping; a
species entirely outside the band — confirmed excluded; and a record
with missing coordinates — confirmed dropped from `dwc_coords_complete.csv`
with the drop counted and reported. The `regmatches()` misalignment bug
(REQ-04-NFR-2) was additionally verified with a standalone
reproduction, documented in `README.md`.

**Also verified against the real pipeline run**: 4,658,904
coordinate-complete records, 53,632 unique species, 19,894 overlapping
the Preserve's latitude band. This run surfaced the real BOLD BIN
collapse bug described in `README.md` — found only because real GBIF
data includes ~716K DNA-barcode records that no synthetic test case
had modeled; fixed and re-verified (species count rose from 36,638 to
53,632 once BOLD codes were no longer wrongly merged).
