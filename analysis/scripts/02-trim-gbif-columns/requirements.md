# Requirements — Step 2: Trim GBIF Columns

Status: Implemented (`trim_gbif_columns.R`, plus an equivalent
`trim_gbif_columns.py`) and verified against both synthetic test data
and the real, live-GBIF Step 1 output. See `README.md` for design
rationale and why this step exists.

## 1. Purpose

Reduce a raw GBIF Darwin Core Archive `occurrence.txt` export to just
the columns later pipeline steps actually use, so the file is small
enough to transfer and process, without discarding any row or any
column those later steps need.

## 2. Inputs

| ID | Requirement |
|----|-------------|
| REQ-02-IN-1 | The system shall read Step 1's extracted Darwin Core occurrence file (`../01-download-gbif-arthropoda-ca/output/dwca/occurrence.txt`, or an equivalent path when run in a different environment than Step 1). |
| REQ-02-IN-2 | The system shall check the input file's header for the presence of every column it intends to keep BEFORE reading the full file, and shall halt with an explicit, actionable error naming the missing column(s) if any are absent. |

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-02-F-1 | The system shall select columns to keep BY NAME, not by fixed position, so it stays correct if a different GBIF export's column order differs from this one's. |
| REQ-02-F-2 | The system shall keep exactly these 14 columns, in this order: `gbifID`, `occurrenceID`, `institutionCode`, `collectionCode`, `catalogNumber`, `basisOfRecord`, `decimalLatitude`, `decimalLongitude`, `scientificName`, `kingdom`, `phylum`, `class`, `order`, `family`. |
| REQ-02-F-3 | The system shall preserve every row from the input file (no filtering), reordering only columns, not rows. |
| REQ-02-F-4 | The system shall read and write the file without requiring the full, untrimmed file to be materialized in memory all at once (column-selective / streaming read), so it remains practical on a multi-gigabyte input. |

## 4. Outputs

| ID | Requirement |
|----|-------------|
| REQ-02-OUT-1 | The system shall write the trimmed table to `output/occurrence_trimmed.txt`, tab-delimited, with a header row. |
| REQ-02-OUT-2 | The system shall report to the console the input column count, the kept column count and names, and the final row count written. |

## 5. Error Handling / Edge Cases

| ID | Requirement |
|----|-------------|
| REQ-02-ERR-1 | If the input file does not exist at the configured path, the system shall halt with an explicit error. |
| REQ-02-ERR-2 | (Python implementation only) A row with fewer fields than the header (malformed/truncated line) shall be skipped and counted, with a warning if the count is large, rather than crashing the whole run. |

## 6. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-02-NFR-1 | The original input file shall never be modified or deleted by this script — read-only access only. |
| REQ-02-NFR-2 | The kept columns shall be exactly the set later steps' join keys (`occurrenceID`, `institutionCode`, `collectionCode`, `catalogNumber`) and analysis fields depend on, so full record detail can be rejoined later from the untouched original file without needing to re-run this step. |

## 7. Dependencies

- R package: `readr` (R implementation); Python standard library only (`csv`, `sys`, `time`) for the Python implementation.
- Upstream: Step 1 (`output/dwca/occurrence.txt`).
- Downstream: Step 3 reads `output/occurrence_trimmed.txt` as one of its merge inputs.

## 8. Out of Scope

- Any further filtering (coordinate completeness, latitude range, etc.) — deferred to Step 4.
- Deduplication or merging with other sources — Step 3.
- Compression of the output file for transfer — a one-off environment-specific workaround used on this project (see README), not part of this script.
- Rejoining full record detail onto final outputs — a separate, not-yet-written utility script (see top-level `analysis/README.md` "Status").

## 9. Verification Status

Verified against synthetic test data (both the success path and the
missing-expected-column error path) in both the R and Python
implementations before either was run against real data.

**Also verified against the real pipeline run** (R implementation
only — Python was not available on the machine that ran this step for
real): run against the real 6.84 GB, 230-column `occurrence.txt`,
producing a 914,209,952-byte (≈872 MB) output with exactly 4,665,086
rows — matching the live GBIF download's total record count exactly —
and all 14 expected columns present and correctly ordered. No
discrepancies from the synthetic-test-verified behavior were found at
this step when run against the real file.
