# Project data

| Folder | Contents |
|---|---|
| `raw/gbif/` | Original GBIF download ZIPs, grouped by request date, with DOI and query metadata. |
| `raw/ecdysis/` | Original Ecdysis Darwin Core Archive ZIPs and checksum manifests. |
| `raw/epa/` | Dated EPA ecoregion archives, metadata, symbology and extracted GIS files. |
| `raw/cibi/` | Original CIBI/BOLD exports, when available locally. |
| `local/` | Local SQLite databases. |
| `reference/` | Small reference tables used by the exploratory notebook. |

Shared spatial and barcode reference inputs currently live in
`analysis/reference-data/`. The numbered scripts retain their existing
per-step `output/` folders; moving those outputs would break their
current input dependencies.

## New GBIF download

Save the new ZIP in `raw/gbif/2026-10-27/`. Keep the original filename.
Save its download page/DOI with it so the query can be cited and checked.
The previous GBIF download and its saved analysis outputs describe a
different data snapshot and should not be overwritten or relabeled as
the new run.

## Ecdysis inventory

The 26 October 2026 export is in `raw/ecdysis/` and contains:

| Class | Records |
|---|---:|
| Insecta | 423 |
| Arachnida | 31 |
| Crustacea | 4 |
| Gastropoda | 1 |
| Total | 459 |

The ZIP retains occurrence, identification, multimedia and identifier
tables, the Darwin Core schema, ecological metadata and citation text.
Its SHA-256 checksum is recorded in `archive_manifest.json`.
Filter to Insecta for the insect prediction analysis without changing
the original archive. Identifications above species remain valid
records and should be handled separately from species-level lists.

## Git policy

Raw data and archives remain local. Git retains source documentation,
small manifests, query definitions and DOI records. Large generated
tables and spatial files are also ignored; their scripts and smaller
summary outputs remain available for reproducibility.

## Hill-analysis source snapshot

`raw/gbif/preserve_2026-10-26/` contains the complete earlier preserve
extract: bounding-box GBIF responses, boundary-clipped responses,
terrestrial-scope decisions, occurrence tables, dataset metadata,
summary tables, checksums and the exact boundary used. It is separate
from the incoming USA-wide download in `raw/gbif/2026-10-27/`.

The Ecdysis tables used by that analysis are in
`raw/ecdysis/extracted/SymbOutput_2026-10-26_124013_DwC-A/`.
`analysis/hill-diversity/migration_manifest.json` records the transferred
files and their source checksums. `reference/source_manifest.json`
records the existing CIBI extract and preserve boundary; those two
inputs were already present and have not been represented as new downloads.
