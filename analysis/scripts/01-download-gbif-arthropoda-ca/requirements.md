# Requirements — Step 1: GBIF Download (Arthropoda, California)

Status: Implemented (`download_arthropoda_ca.R`). Not yet executed against
live GBIF in this environment (requires user-supplied credentials — see
REQ-01-IN-2). Formalizes requirements already satisfied by the current
implementation; see `README.md` for design rationale and discussion.

## 1. Purpose

Retrieve a Darwin Core Archive (DwC-A) of every GBIF-mediated Arthropoda
occurrence record in California, and record the DOI GBIF assigns to
that specific download request, as the entry point of the Dangermond
pipeline.

## 2. Inputs

| ID | Requirement |
|----|-------------|
| REQ-01-IN-1 | The system shall resolve the taxon "Arthropoda" to a GBIF backbone `taxonKey` at run time via `rgbif::name_backbone()`, rather than a hardcoded numeric key. |
| REQ-01-IN-2 | The system shall authenticate to the GBIF API using credentials supplied via the standard `rgbif` environment variables (`GBIF_USER`, `GBIF_PWD`, `GBIF_EMAIL`). Credentials shall never be hardcoded in the script or requested through any other channel. |
| REQ-01-IN-3 | No other data file inputs are required — this step originates the pipeline. |

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-01-F-1 | The system shall submit a single GBIF occurrence download request scoped to the resolved Arthropoda `taxonKey`. |
| REQ-01-F-2 | The system shall scope the request to California using a geometric boundary match (`gadmGid = "USA.5_1"`), not a free-text `stateProvince` match. |
| REQ-01-F-3 | The system shall NOT filter by `basisOfRecord` — all record types (preserved specimen, human observation, machine observation, living specimen, fossil specimen, etc.) shall be included. |
| REQ-01-F-4 | The system shall exclude records GBIF's own quality checks have flagged via `hasGeospatialIssue = TRUE`. |
| REQ-01-F-5 | The system shall request the download in Darwin Core Archive (`DWCA`) format. |
| REQ-01-F-6 | The system shall capture the download's DOI via `occ_download_meta()` immediately after submission, without waiting for the archive itself to finish preparing. |
| REQ-01-F-7 | The system shall wait for the download to finish processing (`occ_download_wait()`) before attempting to fetch it. |
| REQ-01-F-8 | The system shall fetch and unzip the completed archive into a dedicated output subdirectory. |

## 4. Outputs

| ID | Requirement |
|----|-------------|
| REQ-01-OUT-1 | The system shall write the resolved DOI to `output/doi.txt` as a single value, if a DOI was returned. |
| REQ-01-OUT-2 | The system shall write a metadata record to `output/download_metadata.txt` containing, at minimum: download key, DOI, resolved taxon name and key, the predicates used, and a submission timestamp. |
| REQ-01-OUT-3 | The system shall extract the downloaded Darwin Core Archive to `output/dwca/`. |

## 5. Error Handling / Edge Cases

| ID | Requirement |
|----|-------------|
| REQ-01-ERR-1 | If "Arthropoda" cannot be resolved to a backbone taxon key (no match), the system shall halt with an explicit error rather than proceeding with an undefined key. |
| REQ-01-ERR-2 | If `occ_download_meta()` does not yet return a DOI at submission time, the system shall emit an explicit warning rather than writing an empty or missing DOI file silently. |

## 6. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| REQ-01-NFR-1 | GBIF credentials shall never appear in the script, in chat, or in any committed file. |
| REQ-01-NFR-2 | Output paths shall be created automatically if they do not already exist. |
| REQ-01-NFR-3 | Large downloaded artifacts (`output/*.zip`, `output/dwca/`) shall be excluded from version control via `.gitignore`; the DOI and metadata files shall be explicitly retained. |

## 7. Dependencies

- R package: `rgbif`.
- Upstream: none (pipeline entry point).
- Downstream: Step 2 reads `output/dwca/occurrence.txt` (or the equivalent DwC-A occurrence file) as one of its merge inputs.

## 8. Out of Scope

- Any coordinate or data-quality filtering beyond `hasGeospatialIssue` — deferred to Step 3.
- Deduplication or merging with other sources — Step 2.
- Retry/resume logic for interrupted downloads.

## 9. Verification Status

Design and code reviewed; script is syntactically valid (`Rscript -e
'parse(...)'` passes). **Not executed against the live GBIF API** in
any session to date, since that requires live user credentials that
were deliberately never shared in chat (REQ-01-IN-2, REQ-01-NFR-1). All
other pipeline steps have been verified with synthetic test data that
assumes this step's documented output shape; if GBIF's actual DwC-A
column names or `occurrence.txt` structure differ from that
assumption when this step is finally run for real, Step 2's column-
header report (REQ-02-F-3) is the intended place to catch that
discrepancy.
