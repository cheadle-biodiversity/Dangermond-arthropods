# Dangermond Arthropods

Regional candidate insect checklists and survey diversity analyses for the Jack and Laura Dangermond Preserve, California. This repository contains the methods, code, figures and supporting documentation used in the report *Advancing Insect Conservation at Dangermond Preserve*.

## Data availability

The four regional candidate checklists, their column definitions, associated Level III and Level IV occurrence tables, and original California GBIF archive are published on [Zenodo](https://zenodo.org/records/23819517), DOI [10.5281/zenodo.23819517](https://doi.org/10.5281/zenodo.23819517). The archive contains eight data files and a README. See the [archive README](docs/zenodo/README.md) for contents, methods and reuse notes.

Analysis code, methods and supporting documentation are maintained in [this GitHub repository](https://github.com/cheadle-biodiversity/Dangermond-arthropods). Large data files are excluded from Git; download the archived files from Zenodo. The Ecdysis survey export and additional supporting inputs are retained locally and are outside this Zenodo deposit.

## Final checklists and occurrence records

The canonical checklists are in [`data/final/checklists/`](data/final/checklists/).

| EPA ecoregion | Species |
|---|---:|
| Level III 6 | 10,135 |
| Level III 85 | 8,450 |
| Level IV 6ap | 1,521 |
| Level IV 85a | 1,852 |

The combined Level III pool contains 13,634 species; the combined Level IV pool contains 2,550. Lists overlap, so their individual counts should not be added. Regional membership identifies candidates for surveys; it does not establish occurrence or habitat suitability on the preserve.

All four lists share six fields: common name, order, family, resolved scientific name, occurrence count and documented preserve occurrence. A blank preserve flag means not documented, rather than absent. Definitions and supporting preserve evidence accompany the lists.

The [final occurrence tables](data/final/README.md) contain 1,408,875 Level III records and 43,555 Level IV records, with the same 60-column schema. Level IV is a subset of Level III. See [column definitions](data/final/column_metadata.md) and [dataset metadata](data/final/dataset_metadata.json).

## Report analyses

| Analysis | Methods and code | Results |
|---|---|---|
| Regional candidate checklists | [Regional workflow](analysis/regional-candidate-pool/README.md) | [Final checklists](data/final/checklists/) |
| Survey versus regional candidates | [Hill workflow](analysis/hill-diversity/README.md) | [Species comparison](outputs/hill-diversity/2026-10-27-insects/) |
| Human observations, specimens and DNA | [Hill workflow](analysis/hill-diversity/README.md) | [Record-format comparison](outputs/hill-diversity/2026-10-27-record-formats/) |
| Perco’s Beach versus upland dunes | [Methods](outputs/hill-diversity/2026-10-28-beach-upland/README.md) | [Figures and tables](outputs/hill-diversity/2026-10-28-beach-upland/) |
| Dunes versus active restoration | [Methods](outputs/hill-diversity/2026-10-28-restoration/README.md) | [Figures and tables](outputs/hill-diversity/2026-10-28-restoration/) |

The survey documents 45 of the 2,550 Level IV candidates and 17 additional species-level units. The species-determined, deduplicated preserve inventory contains 797 records representing 199 species across human observations, preserved specimens and DNA records.

Habitat comparisons include named species and unresolved genus morphotypes. Effort uses `personHours` alone, summed once per survey window; it already includes team size. The July Beach/Upland effort overlap remains flagged in the [effort audit](outputs/hill-diversity/2026-10-28-beach-upland/effort_review.csv). Rarefaction standardizes record count, not person-hours or sampling completeness.

## Repository layout

- `analysis/regional-candidate-pool/`: filtering, taxonomic resolution, common names and final checklist preparation.
- `analysis/hill-diversity/`: active diversity comparisons and consistent figure styling.
- `analysis/ecoregions-level-iii/`: preserve/Level III overlay used by regional filtering.
- `analysis/archive/2026-10-30/`: earlier analyses and outputs retained for reference.
- `analysis/ecoregions-level-iv/`: preserve/ecoregion overlap analysis.
- `analysis/reference-data/`: preserve boundary and barcode identification reference.
- `data/final/`: canonical checklists, occurrence tables and metadata.
- `data/raw/`: original downloads and survey inputs; large files remain local.
- `docs/`: source notes, citation checks, archive documentation and cleanup record.
- `outputs/`: current results, figures and supporting audit tables.

## Additional Information

The original GBIF source is the California Arthropoda download [10.15468/dl.vgv5ee](https://doi.org/10.15468/dl.vgv5ee). The regional workflow filters to insects and resolves names using GBIF Species Match API v2 with Catalogue of Life XR plus reviewed corrections. Named species-level BOLD records are retained; unnamed barcode clusters do not enter named-species comparisons. Source identifications, identifiers and attribution are preserved. Large local vegetation-map and management-plan reference copies are excluded from Git alongside the raw data.

Use the source-specific instructions in [data/README.md](data/README.md) and [analysis/README.md](analysis/README.md) when reproducing the analyses. Original data licenses remain applicable; the intended MIT code license does not relicense third-party data.

Earlier distance and range analyses, superseded Hill comparisons, withdrawn habitat annotations and the separate Apoidea workflow are retained in the [analysis archive](analysis/archive/2026-10-30/README.md). They are outside the current report analysis. The [archive manifest](docs/repository-cleanup-2026-10-30.json) records their original paths and checksums. Raw source archives, final datasets and current workflow dependencies remain available.

## References

### Data sources

- Entomological Society of America. Common Names of Insects Database.
  [Source and spreadsheet download](https://entsoc.org/publications/common-names),
  retrieved 27 October 2026. The original file, checksum and source-date
  labels are retained in `data/raw/common-names/esa/2026-10-27/`.
- GBIF Secretariat. Species Match API v2, using Catalogue of Life
  eXtended Release checklist `7ddf754f-d193-4cc9-b351-99906754a03b`.
  [Taxonomy interpretation documentation](https://techdocs.gbif.org/en/data-processing/taxonomy-interpretation).
  Match responses and retrieval timestamps are cached locally.
- GBIF.org. (2026). California Arthropoda occurrence download, submitted
  28 September 2026. [https://doi.org/10.15468/dl.vgv5ee](https://doi.org/10.15468/dl.vgv5ee).
  This is the source of the regional candidate checklists; see
  [download metadata](data/raw/gbif/california_2026-09-28/download_metadata.json).
- UCSB Invertebrate Zoology Collection. (2026). Ecdysis Darwin Core
  Archive export, 26 October 2026,
  `SymbOutput_2026-10-26_124013_DwC-A.zip`. User-supplied export retained
  in `data/raw/ecdysis/`; its `CITEME.txt` and `eml.xml` retain the
  source citation and metadata. Portal: [Ecdysis](https://ecdysis.org/).
- U.S. Environmental Protection Agency. *Level III Ecoregions of EPA
  Region 9*. Shapefile, metadata and symbology downloaded 27 October
  2026 from [Ecoregion Download Files by Region](https://www.epa.gov/eco-research/ecoregion-download-files-region).
  Source URLs and checksums are in
  [the download manifest](data/raw/epa/region9_level_iii/2026-10-27/archive_manifest.json).
- Jack and Laura Dangermond Preserve boundary. User-supplied GeoJSON;
  original publication date and public download URL are not recorded.
  [Local boundary](analysis/reference-data/jldp_boundary.geojson) and
  [provenance notes](analysis/reference-data/README.md).

### Diversity methods and barcode units

- Chao, A., Gotelli, N. J., Hsieh, T. C., Sander, E. L., Ma, K. H.,
  Colwell, R. K., & Ellison, A. M. (2014). Rarefaction and extrapolation
  with Hill numbers: a framework for sampling and estimation in species
  diversity studies. *Ecological Monographs*, 84, 45–67.
  [https://doi.org/10.1890/13-0133.1](https://doi.org/10.1890/13-0133.1).
  The current Hill workflow implements empirical profiles and exact
  richness interpolation, rather than the paper's full estimation framework.
- Ratnasingham, S., & Hebert, P. D. N. (2013). A DNA-based registry for
  all animal species: The Barcode Index Number (BIN) system. *PLOS ONE*,
  8(7), e66213.
  [https://doi.org/10.1371/journal.pone.0066213](https://doi.org/10.1371/journal.pone.0066213).

## Document Provenance and AI Assistance Statement

This repository contains working research scripts, biodiversity
screening tables, diversity summaries and documentation prepared with
AI assistance in Codex. AI assistance has been used to inspect and
organize repository files, draft and revise code and Markdown,
retrieve public data, document source provenance, and run numerical
and file-integrity checks. Existing code and source material may have
additional contributors; this statement does not assign authorship
of all repository contents to a single person or tool.

The scientific authorities remain the cited literature, original
collection records, voucher specimens and data providers. AI-assisted
summaries and candidate lists are working materials for researcher
review. They do not constitute independent specimen identifications,
confirmed occurrence records, peer-reviewed conclusions or validated
species distribution models.

Analyses and generated documents should retain their preparation date,
input dataset versions or DOIs, filtering and identification decisions,
software dependencies, and the role of AI assistance. Record validation
checks with the outputs, and distinguish those checks from scientific
or taxonomic review. Researchers remain responsible for evaluating
the methods, verifying interpretations and approving material for
publication or management use.

This README's provenance and AI-assistance statement was added on
27 October 2026, following the structure used in the
`ai-insect-keys` repository and adapted to this project's data and analyses.
