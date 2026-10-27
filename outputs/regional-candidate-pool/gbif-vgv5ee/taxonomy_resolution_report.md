# Taxonomic name-resolution results

Completed (UTC): 2026-10-27T18:07:12.490502+00:00

Service: [GBIF Species Match API v2](https://techdocs.gbif.org/en/openapi/v1/species), explicitly querying Catalogue of Life eXtended Release (COL XR), checklist `7ddf754f-d193-4cc9-b351-99906754a03b`.

Input: species-identified regional insect records from GBIF DOI [10.15468/dl.vgv5ee](https://doi.org/10.15468/dl.vgv5ee). The new table retains every occurrence and original field; original taxonomy and legacy GBIF keys are unchanged.

| Resolution status | Distinct name/context combinations | Occurrence records |
|---|---:|---:|
| resolved_exact | 12,868 | 1,282,408 |
| resolved_manual | 12 | 30,146 |
| resolved_service_accepted | 615 | 11,729 |
| resolved_synonym | 2,298 | 85,351 |
| review_higher_taxon | 291 | 7,995 |

Distinct resolved COL XR species keys: **13,640**. Reviewed names without a matching COL XR species identifier remain named but have blank resolved keys.

`resolved_taxon_name` contains the accepted canonical scientific name without authorship. It preserves infraspecific detail where available. `resolved_species_name` and `resolved_species_key` provide the species-level roll-up; COL XR keys belong to a different identifier system from the original GBIF keys.

Current policy: the user approved all named species-or-below service results on 27 October 2026, including variant/higher-rank species matches and provisional, ambiguous or misapplied statuses. Those service statuses and confidence values are preserved, not upgraded. A genus-only or higher match does not replace an identified species. The initial strict-screen outcome remains in taxon_resolution_baseline_status.

User-reviewed decisions in `analysis/regional-candidate-pool/reviewed_taxonomic_corrections.csv` override automatic results and receive status `resolved_manual`. Original API status, match type and confidence are retained in the automatic audit columns. Manual decisions have no numeric service confidence; COL XR keys are supplied only when the returned canonical species name matches the reviewed name. Junonia grisea is retained; its historical association with J. coenia does not reassign other J. coenia records.

Each distinct scientificName/rank/order/family combination is queried once, with Animalia/Arthropoda/Insecta context. Full API responses, request URLs and retrieval timestamps are cached locally. Query details and occurrence weights are in `taxonomy_name_resolution.csv`; provenance and the source checksum are in `taxonomy_resolution_metadata.json`.

A flagged name indicates a taxonomic matching question, not necessarily a bad specimen identification. Name matching does not validate specimens, geographic plausibility or conservation status. BOLD eligibility remains pending. These are regional candidate occurrences and do not demonstrate occurrence on Dangermond Preserve.
