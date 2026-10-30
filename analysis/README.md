# Current report analyses

| Folder | Purpose | Results |
|---|---|---|
| [ecoregions-level-iii/](ecoregions-level-iii/README.md) | Identify preserve-intersecting Level III regions for regional filtering. | [Level III overlay](../outputs/ecoregions-level-iii/2026-10-27/) |
| [ecoregions-level-iv/](ecoregions-level-iv/) | Identify preserve-intersecting Level IV regions. | [Level IV overlay](../outputs/ecoregions-level-iv/2026-10-27/) |
| [regional-candidate-pool/](regional-candidate-pool/README.md) | Filter GBIF records, resolve names, add common names and prepare regional checklists. | [Final data](../data/final/README.md) |
| [hill-diversity/](hill-diversity/README.md) | Survey/candidate comparison, record-format profiles, Beach/Upland and dune/restoration comparisons. | [Diversity outputs](../outputs/hill-diversity/) |
| [reference-data/](reference-data/README.md) | Preserve boundary used by the spatial workflows. | Shared input |
| [archive/2026-10-30/](archive/2026-10-30/README.md) | Earlier analyses, drafts and outputs retained for reference. | Outside the current report analysis |

The final checklist and occurrence data are published on [Zenodo](https://zenodo.org/records/23819517), DOI [10.5281/zenodo.23819517](https://doi.org/10.5281/zenodo.23819517).

For a full rebuild, run the Level III and IV overlays before the regional candidate workflow. Follow that workflow's documented filtering, taxonomy, export and checklist steps. Generate the survey/candidate comparison before the record-format and habitat comparisons: they reuse its record-ID name crosswalk. Keep original source archives unchanged; large data files are Git-ignored.
