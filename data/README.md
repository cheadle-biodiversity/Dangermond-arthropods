# Project data

| Folder | Contents |
|---|---|
| [final/](final/README.md) | Canonical six-column checklists, Level III/IV occurrence tables and column/provenance metadata. |
| `raw/gbif/california_2026-09-28/` | Original California Arthropoda GBIF archive, DOI 10.15468/dl.vgv5ee. |
| [raw/gbif/preserve_2026-10-26/](raw/gbif/preserve_2026-10-26/README.md) | Preserve GBIF API snapshot used for record-format analysis and local occurrence evidence. |
| `raw/ecdysis/` | Original 26 October archive and annotated 28 October survey CSV; 459 records, including 423 insects. |
| `raw/epa/` | Original Level III/IV ecoregion sources and metadata. |
| `raw/common-names/` | ESA common-name source and attribution. |
| `raw/ant-conservation/`, `raw/beach-assessment/`, `raw/species-literature/`, `raw/habitat/` | Supporting sources and literature. |
| `reference/` | Shared boundary provenance. The boundary itself is in `analysis/reference-data/`. |

## Published data

The original California GBIF archive, four final regional checklists, checklist column definitions and two regional occurrence tables are available from [Zenodo](https://zenodo.org/records/23819517), DOI [10.5281/zenodo.23819517](https://doi.org/10.5281/zenodo.23819517). See the [archive README](../docs/zenodo/README.md). Ecdysis and other supporting raw inputs are outside that deposit.

## Source handling

Keep original downloads unchanged, with citations, licenses and checksum manifests. The annotated survey CSV adds habitat and effort fields; it does not replace the original Ecdysis archive used for species-name provenance. Identifications above species are valid records and are handled separately from species-only comparisons.

Large raw files, compressed regional occurrence tables and intermediate outputs are Git-ignored. Small manifests, source notes, final checklists and audit summaries are versioned. Archived analyses and their old outputs are retained in [analysis/archive/2026-10-30/](../analysis/archive/2026-10-30/README.md).
