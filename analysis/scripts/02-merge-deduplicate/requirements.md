# Requirements — Step 2: Merge & Deduplicate

Status: Implemented (`dwc_merge_deduplicate.R`) and verified against
synthetic test data. See `README.md` for design rationale and the
NA-collapse bug this step's dedup logic specifically avoids.

## 1. Purpose

Combine an arbitrary number of Darwin Core occurrence files, of
potentially different formats/delimiters, into one deduplicated table.

## 2. Inputs

| ID | Requirement |
|----|-------------|
| REQ-02-IN-1 | The system shall accept an arbitrary-length list of input files, each declared with a name, a file path, and a field delimiter — not a fixed two-file assumption. |
| REQ-02-IN-2 | Each input file shall be read using its own declared delimiter, so files of different formats (e.g. comma-delimited and tab-delimited) can be combined in a single run. |
| REQ-02-IN-3 | Each input file's provenance shall be retained per record via a `source_file` column populated from the input's declared name. |

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-02-F-1 | The system shall append all input files into one table, aligning columns by name and filling `NA` for any column absent from a given source (not requiring identical schemas across inputs). |
| REQ-02-F-2 | The system shall deduplicate the merged table in two ordered stages: (1) by `occurrenceID`, then (2) by the composite key `institutionCode` + `collectionCode` + `catalogNumber` for any records still present after stage 1 that share that composite key. |
| REQ-02-F-3 | The system shall report, per column, whether it is present in all input files, some, or none, before merging — so a source missing an expected field is visible prior to any downstream step depending on it. |
| REQ-02-F-4 | Deduplication at each stage shall be NA-safe: records missing the relevant key value(s) shall NOT be treated as duplicates of one another and shall pass through unmodified, while only records that share an actual, non-missing key value shall be collapsed to one. |

## 4. Outputs

| ID | Requirement |
|----|-------------|
| REQ-02-OUT-1 | The system shall write the merged, deduplicated table to `output/dwc_merged_deduplicated.csv`. |
| REQ-02-OUT-2 | The system shall write the per-column header comparison report to `output/column_header_report.txt`. |
| REQ-02-OUT-3 | The system shall report to the console the record count before merge, after merge, and after each deduplication stage. |

## 5. Error Handling / Edge Cases

| ID | Requirement |
|----|-------------|
| REQ-02-ERR-1 | If `occurrenceID` is absent from the merged table entirely, the system shall skip that dedup stage with an explicit warning rather than erroring or silently doing nothing. |
| REQ-02-ERR-2 | If any of the three fallback key columns is absent from the merged table entirely, the system shall skip that dedup stage with an explicit warning, naming which column(s) are missing. |
| REQ-02-ERR-3 | Records with `NA` in the relevant dedup key (partially or fully) shall never be collapsed together based on that shared `NA`, regardless of how many such records exist (see REQ-02-F-4). |

## 6. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-02-NFR-1 | The merge/dedup logic shall be format-agnostic: the same script shall handle both a same-format multi-file scenario (e.g. a GBIF download split across parts) and a mixed-format scenario (e.g. GBIF + Symbiota) without code changes, only input-list changes. |
| REQ-02-NFR-2 | Output paths shall be created automatically if they do not already exist. |

## 7. Dependencies

- R packages: `readr`, `dplyr`, `purrr`, `tibble`.
- Upstream: Step 1 (or any other Darwin Core source declared in the input list).
- Downstream: Step 3 reads `output/dwc_merged_deduplicated.csv`.

## 8. Out of Scope

- Coordinate completeness filtering — Step 3.
- Species-name normalization across sources — Step 3.
- Resolving which duplicate record is "more correct" when a true duplicate is found — the first record in input row order is kept, by design (see README, "Ties" caveat carried into Step 4).

## 9. Verification Status

Verified against a synthetic two-source test set (a simulated GBIF
export and a simulated Symbiota export) designed to exercise every
requirement above: a same-key exact-duplicate pair (correctly collapsed
to 1), a record with a missing `catalogNumber` (correctly NOT collapsed
with anything, per REQ-02-F-4/ERR-3), and distinct `occurrenceID`
values that correctly prevented stage-1 collapse even for otherwise
identical-looking records. Result: 6 input records → 5 output records,
by hand-traced expectation — confirmed exactly on the first rebuild run
after the workspace reset (see project-level note in each step's
README on the reset). The original session additionally verified the
NA-collapse bug this design avoids with a standalone R reproduction,
documented in `README.md`.
