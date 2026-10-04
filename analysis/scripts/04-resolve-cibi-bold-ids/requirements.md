# Requirements — Step 4: Resolve BOLD-Placeholder Records Against the CIBI Barcode Project

Status: Implemented (`resolve_cibi_bold_ids.R`) and verified against
the real, live-GBIF pipeline output (9,776 of 715,978 BOLD-placeholder
records matched; 3,144 resolved to a real species). See `README.md`
for full design rationale, including why only species-rank matches
replace `scientificName`.

## 1. Purpose

Recover a real taxonomic identification, where one is available from
the user's CIBI Barcode Project spreadsheet, for GBIF records whose
`scientificName` is a BOLD Systems BIN placeholder (`BOLD:XXXXXXX`)
rather than a taxonomic name — before any downstream step groups,
cleans, or counts species.

## 2. Inputs

| ID | Requirement |
|----|-------------|
| REQ-04-IN-1 | The system shall read Step 3's merged/deduplicated output (`../03-merge-deduplicate/output/dwc_merged_deduplicated.csv`). |
| REQ-04-IN-2 | The system shall read the CIBI reference identifications (`../reference-data/cibi_barcode_identifications.csv`) and verify there are no duplicate `processid` values before using it as a join key. |

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-04-F-1 | The system shall identify BOLD-placeholder records as those whose `scientificName` matches `^BOLD:` (case-sensitive, matching the literal GBIF-exported format). |
| REQ-04-F-2 | The system shall match BOLD-placeholder records to the CIBI reference by exact equality between the record's `occurrenceID` and the CIBI reference's `processid` — no fuzzy or partial matching. |
| REQ-04-F-3 | For every matched record, the system shall attach the CIBI identification and identification rank as new columns, regardless of what rank that identification is. |
| REQ-04-F-4 | The system shall replace `scientificName` with the CIBI identification ONLY for matched records whose CIBI identification rank is exactly `"species"` AND whose CIBI species value is present and non-blank. |
| REQ-04-F-5 | For every matched record NOT replaced under REQ-04-F-4 (genus/family/subfamily/tribe/other rank), the system shall leave `scientificName` unchanged (still the original `BOLD:XXXXXXX` placeholder). |
| REQ-04-F-6 | The join shall never change the row count or row order of the input dataset. |

## 4. Outputs

| ID | Requirement |
|----|-------------|
| REQ-04-OUT-1 | The system shall write every input record, with the three added columns (`cibi_matched`, `cibi_identification`, `cibi_identification_rank`) and `scientificName` updated per REQ-04-F-4/F-5, to `output/dwc_merged_cibi_resolved.csv`. |
| REQ-04-OUT-2 | The system shall write a summary table (`output/cibi_resolution_summary.csv`) reporting: total records, BOLD-placeholder count, total CIBI matches, matches broken down by identification rank, and the count of `scientificName` replacements actually made. |
| REQ-04-OUT-3 | The system shall report the same counts to the console during the run. |

## 5. Error Handling / Edge Cases

| ID | Requirement |
|----|-------------|
| REQ-04-ERR-1 | The system shall halt with an explicit error if either input file is missing, before attempting to read it. |
| REQ-04-ERR-2 | A CIBI reference row whose rank is `"species"` but whose `species` field is blank or missing shall NOT trigger a `scientificName` replacement (guarded explicitly, not assumed never to happen). |
| REQ-04-ERR-3 | An `occurrenceID` collision with a CIBI `processid` on a record that was NOT already a BOLD placeholder shall not count as a match (REQ-04-F-1 gates REQ-04-F-2) — this join is only ever meant to resolve BOLD placeholders, not to overwrite an already-present identification. |

## 6. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-04-NFR-1 | The CIBI reference data used by this step shall be a versioned file in `../reference-data/`, not a path into the session's temporary upload directory, so the step is reproducible on a fresh checkout. |
| REQ-04-NFR-2 | This step shall run before any species-name normalization (Step 5's `clean_scientific_name()`) or species-level grouping, so a resolved identification is treated identically to any other GBIF species record by every downstream step. |

## 7. Dependencies

- R packages: `readr`, `dplyr`.
- Upstream: Step 3 (`dwc_merged_deduplicated.csv`), `../reference-data/cibi_barcode_identifications.csv`.
- Downstream: Step 5 reads this step's output instead of Step 3's directly.

## 8. Out of Scope

- Resolving any BOLD-placeholder record not covered by the CIBI spreadsheet (the other ~706,000) — a BOLD Systems API-based approach was investigated and found technically feasible but deliberately deferred; see README.
- Backfilling `kingdom`/`phylum`/`class`/`order`/`family` from CIBI — GBIF's own export already carries these to family rank for every BOLD-flagged record.
- Any fuzzy, phonetic, or partial matching between `occurrenceID` and `processid` — only exact equality is used (REQ-04-F-2).

## 9. Verification Status

**Verified against the real pipeline run**: 4,658,904 records read;
715,978 BOLD-placeholder records identified (matching Step 5's
independently-reported count exactly); 9,776 matched a CIBI
`processid` (0 duplicate `processid`s in the 16,471-row reference);
matches broken down as family 1,794, genus 3,382, species 3,144,
subfamily 1,439, tribe 17; 3,144 `scientificName` replacements made
(REQ-04-F-4); 4,658,904 records written out, confirming REQ-04-F-6
(row count unchanged). The downstream ripple this produced (Step 5's
unique-species count moving from 53,632 to 53,763) is documented in
Step 5's own requirements.md, confirming the resolved identifications
flow through exactly like any other species record (REQ-04-NFR-2).
