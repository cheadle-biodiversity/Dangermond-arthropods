# Dangermond Preserve regional candidate insect checklists

This dataset contains regional candidate species checklists and their supporting occurrence records for the Jack and Laura Dangermond Preserve, California. Candidate species are drawn from EPA ecoregions intersecting the preserve; inclusion does not confirm that a species occurs on the property.

**GitHub repository:** https://github.com/cheadle-biodiversity/Dangermond-arthropods

## Files

| File | Description |
|---|---|
| `0010070-260921141020460.zip` | Original GBIF Darwin Core Archive containing 4,665,086 California Arthropoda records. |
| `checklist_column_metadata.csv` | Definitions of the six checklist columns. |
| `checklist_level_iii_6.csv` | Level III region 6: 10,135 species. |
| `checklist_level_iii_85.csv` | Level III region 85: 8,450 species. |
| `checklist_level_iv_6ap.csv` | Level IV region 6ap: 1,521 species. |
| `checklist_level_iv_85a.csv` | Level IV region 85a: 1,852 species. |
| `dangermond_level_iii_matched_records.csv.gz` | 1,408,875 regional occurrence records; 60 columns. |
| `dangermond_level_iv_matched_records.csv.gz` | 43,555 regional occurrence records; 60 columns. |

The combined Level III checklists contain **13,634 species** and the combined Level IV checklists contain **2,550 species**. Species lists overlap; do not add their individual totals. The Level IV occurrence table is a subset of the Level III table.

## Geographic scope

| EPA code | Ecoregion |
|---|---|
| III 6 | Central California Foothills and Coastal Mountains |
| III 85 | Southern California/Northern Baja Coast |
| IV 6ap | Solomon-Purisima-Santa Ynez Hills |
| IV 85a | Santa Barbara Coastal Plain and Terraces |

Records represent the California portions of these regions, rather than only Dangermond Preserve. No habitat or vegetation filter was applied.

## Methods

The original [GBIF download](https://doi.org/10.15468/dl.vgv5ee) was requested on 28 September 2026 and retrieved on 27 October 2026. It selected California Arthropoda records without GBIF-flagged geospatial issues. Records were filtered sequentially to genus-or-finer identifications, usable coordinates, Insecta and the selected Level III regions. Subsequent species-level filtering and name resolution retained 1,408,875 records; selection of the two Level IV regions retained 43,555.

Names were resolved using **GBIF Species Match API v2 / Catalogue of Life eXtended Release**, with project-reviewed corrections. Subspecies were grouped under species for the checklists. Common names were matched against the Entomological Society of America list. Named species-level BOLD records were retained; genus-only identifications and unnamed barcode clusters were excluded from named-species lists.

The preserve-occurrence flag also used the UCSB Summer 2026 survey, exported from Ecdysis, and a separate GBIF preserve extract. These additional sources establish local evidence without increasing regional checklist record counts. They are not included among this deposit's eight data files.

[Detailed methods and scripts](https://github.com/cheadle-biodiversity/Dangermond-arthropods/tree/master/analysis/regional-candidate-pool) and [occurrence-column definitions](https://github.com/cheadle-biodiversity/Dangermond-arthropods/blob/master/data/final/column_metadata.md) are maintained on GitHub.

## Reading the tables

- Checklist columns are `common_name`, `order`, `family`, `resolved_scientific_name`, `occurrence_count` and `collected_or_observed_on_dangermond`.
- `occurrence_count` counts regional records, not individuals. A preserve flag of `Yes` indicates supporting local evidence; blank means not documented, not absent.
- Read identifiers as text. CSV files use UTF-8; `.csv.gz` files require gzip decompression or a compatible reader.
- Occurrence tables retain `verbatimScientificName`, `resolved_taxon_name` and `taxon_resolution_description`. The resolved name can retain subspecies even though checklist names are species-level.
- Level IV membership was selected before its assignment columns were removed. Both occurrence tables retain Level III codes and names.

## Limitations

Regional membership does not demonstrate habitat suitability or assign an occurrence probability. Taxonomic matching does not independently validate identifications. The current tables retain five Level III absence records, including one in Level IV; use `occurrenceStatus` for presence-only analyses. The Level III checklists also retain one Scorpiones classification and two Mecoptera species. Twelve supporting preserve records remain unmapped, so local flags may be incomplete.

## Citation and rights

Cite this Zenodo dataset using the creator list, version and DOI shown on its record, and retain the source citation:

GBIF.org. (2026, September 28). *GBIF occurrence download*. https://doi.org/10.15468/dl.vgv5ee

Source records retain their CC0, CC BY or CC BY-NC terms in the `license` field. Preserve contributor attribution and the original archive's citation and rights files. These data are not relicensed under the repository's intended MIT code license.

## Document Provenance and AI Assistance Statement

Prepared with AI assistance in Codex on 30 October 2026 from repository methods, metadata and file checks. Researchers remain responsible for scientific review and publication decisions. Supporting code and documentation are available in the [GitHub repository](https://github.com/cheadle-biodiversity/Dangermond-arthropods).
