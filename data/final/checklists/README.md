# Ecoregion species checklists

Four species-level regional checklists. All four lists use the same six columns; life-history notes and sources have been removed. Preserve occurrence is Yes only where a supporting record was found, and blank otherwise.

| Level | Code | Species | Regional occurrences | Species documented on preserve |
|---|---|---:|---:|---:|
| III | 6 | 10,135 | 691,304 | 189 |
| III | 85 | 8,450 | 717,571 | 160 |
| IV | 6ap | 1,521 | 9,141 | 165 |
| IV | 85a | 1,852 | 34,414 | 115 |

Subspecies are rolled up to species; common names specific to a subspecies are not generalized. Counts represent regional records, not individuals or preserve-only records. The Level III/IV lists overlap. A preserve-wide Yes does not locate that species in a specific ecoregion or habitat; blank does not imply absence.

The evidence table includes the local Ecdysis survey and named GBIF preserve records, including BOLD with name-matching provenance. Coordinate checks use the supplied preserve boundary; local species records also carry an explicit Dangermond locality. Higher-taxon identifications are valid but do not establish a named species. All resolved species-level regional records are included regardless of source, following the user’s restoration instruction. Unresolved BIN and genus-only records do not establish named species; final occurrence datasets are unchanged.

See column_metadata.csv and checklist_metadata.json for definitions, sources and exact methods. The evidence, unmapped-record and classification-conflict tables permit review; all four checklists share the six-column schema.

Reproduce the base lists: `python3 analysis/regional-candidate-pool/create_ecoregion_checklists.py`. Life-history and source enrichment is retired at user request.
