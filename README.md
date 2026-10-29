# Dangermond Arthropods

This repository gathers arthropod occurrence data, source notes, literature, analysis files, and screening outputs for biodiversity work related to the Jack and Laura Dangermond Preserve.

## Repository layout

- `analysis/` - R Markdown and other analysis notebooks.
- `analysis/hill-diversity/` - reproducible Hill-number profiles and record rarefaction for the saved 2026 preserve inventory.
- `Apoidea/` - self-contained Python workflow for the Central Coast non-bee Apoidea checklist.
- `data/raw/gbif/` - GBIF occurrence download files.
- `data/raw/cibi/` - CIBI/source download files from the 2025-11-19 export.
- `data/raw/ecdysis/` - Ecdysis Darwin Core Archive export files.
- `data/raw/epa/` - dated EPA ecoregion downloads and their metadata.
- `data/local/` - local SQLite databases ignored by git.
- `data/reference/` - small reference tables used by analyses.
- `docs/field-logistics/` - preserve visit, directions, and overnight logistics documents.
- `docs/source-notes/` - notes and citations for merged source datasets.
- `outputs/` - generated reports and printable screening files.
- `outputs/hill-diversity/2026-10-26/` - Hill figures, diversity tables and record-level audit.
- `references/papers/` - supporting literature PDFs.

## Current work: potential insect fauna

The [updated Beach/Upland comparison](outputs/hill-diversity/2026-10-28-beach-upland/README.md)
uses `uplandBeach` for report section 1.5, ignoring blank assignments and
including unresolved genus morphotypes. Beach has 54 identification units
and Upland 58, with 19 shared. The effort audit retains the supplied July
totals (19.83 and 27.50 person-hours) provisionally because two July 1 Beach
records overlap the same team's Upland visit. Methods, identities, effort
review records and two comparison figures accompany the results.

The [28 October dune/restoration comparison](outputs/hill-diversity/2026-10-28-restoration/README.md)
uses the new survey grouping and effort fields for report section 1.6,
including genus-only insect morphotypes. It records 20 dune identification
units in 3.92 person-hours and 47 active-restoration units in 23.58
person-hours, with nine units shared. Methods, record audits and figures are
saved alongside the results; prior species-only comparisons remain separate.

The current analysis starts with the existing California GBIF download
(`10.15468/dl.vgv5ee`) and uses the local Ecdysis inventory for the
observed fauna. It will identify insect species that may occur at Dangermond.
Recorded species and candidate species will be reported separately.
Regional occurrence records, proximity and ecological screening provide
the initial candidate pools; SDMs are not required for this phase.

The [regional filtering workflow](analysis/regional-candidate-pool/README.md)
applies the requested sequence: genus-or-below identification, usable
coordinates, Insecta, and EPA Level III ecoregions 6 or 85. It keeps
genus-only records separate from named-species counts and records the
number retained at each step. The earlier Hill results are historical;
the [new insect-only comparison](analysis/hill-diversity/README.md) uses the
recent Ecdysis survey and the union of the two Level IV candidate lists.

The 27 October 2026 filtering run retained **1,594,367 insect occurrence
records**: 797,869 in Level III region 6 and 796,498 in region 85.
The linked workflow documents the sequential counts, exact criteria,
validation and reproducible commands. These are intermediate occurrence
records, not a final species checklist.

A separate species-identified subset retains **1,417,629 occurrences**
representing **13,934 GBIF species keys**, including subspecies and
varieties resolved to species. Its selection and counts are documented
in the same workflow; the broader genus-or-below dataset remains intact.

Taxonomic name resolution uses GBIF's Species Match API v2 with the
Catalogue of Life eXtended Release checklist explicitly selected.
The user approved all species-level service candidates; twelve specific
reviewed decisions take precedence. Original names, identifiers, match
status, confidence, diagnostics and source URLs remain preserved.

The next-version dataset contains **1,408,875 occurrences**, after removing
798 original genus/placeholder/group identifications and another 7,956
records lacking a species-level resolution. The full upstream file is
`outputs/regional-candidate-pool/gbif-vgv5ee/species_identified_insect_records_v3.csv.gz`.
The two simplified final exports are in [`data/final/`](data/final/), with
[shared column definitions](data/final/column_metadata.md) and a
[provenance/checksum manifest](data/final/dataset_metadata.json).
It adds `proposed_common_name` and source/matching fields from the
Entomological Society of America Common Names of Insects list. Names
specific to subspecies are kept at that rank; unsupported common names
remain blank. The workflow documents the source download, matching rules,
applied name changes, exclusions and reproducible commands.
Version 3 also adds EPA Level IV ecoregion code, name and assignment
status, preserving the Level III fields and all earlier records.
Two derived exports separate the broader Level III pool (codes 6/85;
1,408,875 occurrences) from the Level IV pool matching Dangermond's
ecoregions (6ap/85a; 43,555 occurrences). Their filenames, species counts
and reproduction steps are in the regional filtering workflow.
The two named regional exports use an identical **60-column schema**,
combining the 70% blank cutoff with the user's restored fields and
explicit removals. Taxon naming is reduced to the original name, resolved
name and a readable resolution description; Level IV columns are omitted
after regional selection. Common names, their source and source URL remain.
The full 266-column version 3 and complete audit tables are unchanged.

- **GBIF refresh:** awaiting a new user-requested download. Save the
  original ZIP in `data/raw/gbif/2026-10-27/`, with its GBIF download
  page or DOI. The user reports that this request selects Arthropoda
  across the USA. Additional filters will be checked against the
  download metadata when it arrives. Keep the full archive and filter
  to Insecta during analysis; distinguish specimens from observations.
- **Ecdysis:** `data/raw/ecdysis/SymbOutput_2026-10-26_124013_DwC-A.zip`.
  This export contains 459 records, including 423 Insecta records.
  Other arthropods and the gastropod remain in the original archive.
- **Previous analysis:** saved outputs use the September 2026
  California Arthropoda download, DOI `10.15468/dl.vgv5ee`. They have
  not yet been refreshed with the new GBIF or Ecdysis data.

## Data sources and file handling

| Source | Location | Role |
|---|---|---|
| GBIF occurrence downloads | `data/raw/gbif/` | Regional collection and observation records; retain each download's DOI and filters. |
| Ecdysis Darwin Core Archive | `data/raw/ecdysis/` | Local survey records, identifications, collection events and associated media metadata. |
| CIBI/BOLD barcode identifications | `analysis/reference-data/cibi_barcode_identifications.csv` | Identifications used to resolve matching BOLD-placeholder records. |
| Dangermond Preserve boundary | `analysis/reference-data/jldp_boundary.geojson` | Preserve membership, distances and spatial overlap. |
| EPA Level III ecoregions | `data/raw/epa/region9_level_iii/2026-10-27/` | Fresh Region 9 shapefile, metadata and symbology; broad regional context for candidate species. |
| California arthropod database | `data/local/` | Local SQLite input for the exploratory notebook; an external fallback location is also supported. |
| Literature and source notes | `references/papers/`, `docs/source-notes/` | Ecological context, conservation screening and dataset citations. |

Keep downloaded archives unchanged in `data/raw/`, organized by source
and download date where appropriate. Large raw data, local databases,
intermediate tables and large generated spatial files are ignored by
Git. Small source notes, manifests, DOI records, scripts and summary
outputs remain versioned. See [`data/README.md`](data/README.md).

The numbered analysis currently reads GBIF alone at its merge step;
the Ecdysis input still needs to be connected. Shared reference-file
paths have been corrected for this local folder layout, and Step 9
now points to the fresh EPA download. The separate `Apoidea/` workflow has code but no saved
checklist outputs in this checkout.

## Checklist columns and supporting habitat research

All four canonical lists are in `data/final/checklists/`. Level IV lists use
six columns: common name, order, family, resolved scientific name, occurrence
count and documented preserve occurrence. The life-history and source columns
were removed at user request. Previously shared Level IV files in
`data/final/habitat-notes/` are identical copies. Level III lists retain their
seven-column layout with blank life-history notes. Species names, counts and
preserve flags are unchanged.

The first-pass habitat annotations are retained separately in
`outputs/habitat-notes/2026-10-27/archived-annotations/`, together with the
[methods and sources](analysis/habitat-notes/README.md). Raw maps and record-level
evidence remain available as supporting research. Regeneration writes to the
archive rather than adding columns back to the active checklists.

## Hill diversity analysis

The preserve-wide record-format analysis compares human observations, preserved
specimens and DNA records, using only explicit species-level determinations.
The combined GBIF + UCSB Summer 2026 survey (this project) input has 14,508
unique insect records; 797 meet the species-only rule and represent 199 species.
Unnamed barcode clusters are excluded even if GBIF supplies a species parent.
See [record-format methods and outputs](analysis/hill-diversity/README.md).


The current [insect-only comparison](analysis/hill-diversity/README.md) documents
45 of 2,550 Level IV candidates (1.76%) in the recent Ecdysis survey. The survey
contains 62 species-level identification units across 316 eligible records;
observed Hill diversities are q0=62, q1=22.34 and q2=10.62. Seventeen observed
species fall outside the candidate pool and remain in the inventory. These are
record-frequency summaries, including qualified identifications; q2 is inverse
Simpson diversity. Outputs and identity comparisons are in
`outputs/hill-diversity/2026-10-27-insects/`. See the methods for the five
user-approved original names, name harmonization and sensitivity comparisons.

The following describes the preserved historical analysis:

The Hill-number workflow and all inputs used for the earlier report
analysis have been transferred into this repository. It compares
empirical diversity in the Ecdysis inventory and a saved GBIF extract
within the preserve, with separate profiles for named species, barcode
BINs and orders. Perko's Beach and the lighthouse localities are kept
separate in the July comparison.

- **Code and instructions:** [`analysis/hill-diversity/`](analysis/hill-diversity/README.md).
- **GBIF source snapshot:** `data/raw/gbif/preserve_2026-10-26/`, including
  original JSON responses, occurrence tables, scope decisions, query
  metadata and the boundary used for that extract.
- **Ecdysis source:** the original ZIP and its extracted tables in
  `data/raw/ecdysis/`.
- **Results:** [`outputs/hill-diversity/2026-10-26/`](outputs/hill-diversity/2026-10-26/),
  including figures, summary tables, taxon frequencies and a record audit.

The relocated workflow reproduces the existing analysis of 458 Ecdysis
arthropod records and 14,601 GBIF terrestrial-associated arthropod
records. This is the October 26 preserve snapshot, separate from the
incoming USA-wide GBIF download. It calculates empirical Hill numbers
and exact record-based richness rarefaction; coverage-based iNEXT,
extrapolation and SDM-derived presumed-species profiles remain future work.

## Special-status insect screening list

| Scientific name | Order | Family | Common name | Habitat | Host plant / larval host / key resources | California status / tracking note | Adult phenology | Likely at Dangermond? | Where most likely observed |
|---|---|---|---|---|---|---|---|---|---|
| *Ammopelmatus muwu* | Orthoptera | Stenopelmatidae | Point Conception Jerusalem cricket | Coastal sandy soils, dunes, sandy scrub, loose terrace soils near Point Conception | Omnivorous/predatory; likely roots, decaying vegetation, and small arthropods | CDFW Special Animals List; G1/S1; IUCN Vulnerable | Mostly nocturnal; most likely active at surface during cool/wet periods and after rains | **Yes — high priority** | Point Conception coastal terrace, sandy scrub, dunes, under cover, pitfall traps, night road/track surveys |
| *Trimerotropis occulens* | Orthoptera | Acrididae | Lompoc grasshopper | Open sandy or sparsely vegetated coastal terrace grassland, scrub/grassland openings, road cuts | Herbivorous grasshopper; likely grasses and forbs | CDFW Special Animals List; G1G2/S1S2; IUCN Endangered | Late spring–summer; records in June–August | **Yes — high regional priority** | Open terrace grasslands, sandy openings, road cuts, Burton Mesa/Lompoc/Vandenberg-type habitats |
| *Coelus globosus* | Coleoptera | Tenebrionidae | Globose dune beetle | Coastal dunes, foredunes, backdunes, loose sand with native dune vegetation | Detritivore/scavenger; associated with dune wrack, loose sand, and dune vegetation | CDFW Special Animals List; G1G2/S1S2; IUCN Vulnerable | Detectable much of year by targeted search; often nocturnal or under sand/debris | **Yes — high priority where dunes occur** | Coastal dunes, wrack line, under driftwood/debris, dune vegetation margins |
| *Cicindela hirticollis gravida* | Coleoptera | Carabidae | Sandy beach tiger beetle | Moist sand near ocean beaches, swales behind dunes, upper beach beyond normal high tide | Predatory beetle; larvae in moist sand burrows | CDFW tracks *C. hirticollis gravida* as a special-status sandy beach tiger beetle | Spring/fall activity likely; active on warm sunny days when sand is moist | **Possible** | Moist upper beach, creek-mouth sand, dune swales, protected beach strand |
| *Cicindela latesignata* | Coleoptera | Carabidae | Western beach tiger beetle | Sandy beaches, tidal-flat/beach margins, estuary-beach transitions | Predatory beetle; larvae in sandy substrate | CDFW Special Animals List; G2G3/S1 | Warm sunny periods, especially when beach substrate is moist but exposed | **Possible** | Beach strand, estuary margins, tidal-flat edges, upper beach wrack/sand interface |
| *Cicindela senilis frosti* | Coleoptera | Carabidae | Senile tiger beetle | Coastal saltmarsh, tidal mudflats, saline flats | Predatory beetle; larvae in mud/sand burrows | CDFW tracks *C. senilis frosti* as special-status | Approx. Feb–Jun and Aug–Oct for species-level activity | **Possible if saltmarsh/tidal-flat habitat is present** | Saltmarsh openings, unvegetated mudflats, saline flats, estuary margins |
| *Bombus crotchii* | Hymenoptera | Apidae | Crotch’s bumble bee | Coastal scrub, grassland, chaparral openings, restoration areas with sustained bloom | Generalist floral resources; Fabaceae, Asteraceae, Lamiaceae, Boraginaceae, *Asclepias*, *Salvia*, *Acmispon*, *Eriogonum*, etc. | CDFW Special Animals List; G2/S2; CESA Candidate Endangered; IUCN Endangered | Queens late winter–spring; workers/males spring–late summer; best survey during abundant bloom | **Yes — high priority** | Flower-rich coastal scrub/grassland, vetch/deerweed/sage/buckwheat/milkweed patches, restoration plantings |
| *Bombus caliginosus* | Hymenoptera | Apidae | Obscure bumble bee / fog-belt bumble bee | Coastal grasslands, scrub, meadows, edge habitats; more coastal/fog-belt associated | Generalist floral resources; requires nesting/overwintering habitat and sustained bloom | CDFW Special Animals List; G2G3/S1S2; IUCN Vulnerable | Spring–fall; survey during peak coastal bloom | **Possible, but ID is difficult** | Flower-rich coastal grassland/scrub, moist/foggy coastal sites; voucher-quality photos or specimens needed |
| *Pseudocopaeodes eunus* | Lepidoptera | Hesperiidae | Alkali skipper / wandering skipper complex | Alkali meadow, saltgrass flat, saline wetland, saltmarsh transition | Larval host: saltgrass, *Distichlis spicata* | CDFW tracks *P. e. eunus* and *P. e. obscurus*; federal endangered status applies to Carson wandering skipper | Several flights Apr–Sep; adults nectar at flowers | **Habitat-dependent** | Saltgrass-dominated flats, saline meadow, saltmarsh transition zones |

## GBIF Arthropoda pipeline (analysis/scripts/)

A separate, numbered R pipeline analyzing GBIF Arthropoda occurrence
records in California relative to the Preserve boundary — download,
merge/deduplicate, coordinate and latitude-range filtering,
boundary-distance calculation, taxonomic summary tables/figures, and
per-species minimum-convex-polygon overlap. See
[`analysis/README.md`](analysis/README.md) for the full step index, run
instructions, and status. This complements `Apoidea/` (a Python
workflow scoped to non-bee Apoidea) and `analysis/CA-arthropods.Rmd`
(a SQLite-backed exploratory notebook) as a third, independent
approach within this repository, and does not modify either.

## Additional Information

This repository supports biodiversity inventory, candidate-species
screening and survey planning for the Jack and Laura Dangermond
Preserve. Collection records document where organisms were recorded;
range envelopes and shared ecoregions identify candidates for further
investigation. A candidate designation does not establish occurrence
at the preserve, and a missing record does not establish absence.

The special-status screening table is a working survey-planning list.
Its likelihood categories are hypotheses, not new specimen records or
model probabilities. Conservation status, host associations and
phenology should be checked against the cited authorities before
formal reporting. Local observations and subsequent identifications
may supersede earlier screening notes.

### Data provenance and reproducibility

- Keep original downloads unchanged and identify the source, retrieval
  date, filters and download DOI where one exists. The October 26 GBIF
  preserve extract was an API retrieval; the incoming USA-wide archive
  will have its own GBIF citation and must remain a separate snapshot.
- Preserve record identifiers and original identifications. Document
  deduplication, geographic exclusions, taxonomic changes and the
  handling of provisional or higher-taxon identifications.
- Retain checksum manifests and distinguish original source files from
  derived tables. [Data folder documentation](data/README.md), the
  [reference-source manifest](data/reference/source_manifest.json), and
  the [Hill transfer manifest](analysis/hill-diversity/migration_manifest.json)
  record the inputs currently available here.
- Consult the [numbered pipeline](analysis/README.md) and
  [Hill workflow](analysis/hill-diversity/README.md) for methods, input
  paths, dependencies, outputs and known limitations. Large data files
  are local-only and must be obtained separately when cloning the repository.

## References

### Planned Zenodo data archive

Large local data files will be deposited separately in Zenodo, with
source citations, licenses and checksums. The full repository will
remain on GitHub; automatic GitHub-release archiving is not the intended
workflow. See [the data-deposit plan](docs/zenodo-data.md). No Zenodo
deposit or DOI has been created yet. The incoming USA-wide GBIF
download must be received and documented before selecting the final
archive snapshot. MIT was selected for original code; source data
retain their own licenses.

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
  This is the source of the existing numbered-pipeline results; see
  [download metadata](analysis/scripts/01-download-gbif-arthropoda-ca/output/download_metadata.txt).
- GBIF.org. (2025). GBIF Occurrence Download, 25 November 2025.
  [https://doi.org/10.15468/dl.k85cpx](https://doi.org/10.15468/dl.k85cpx).
  Earlier USA Arthropoda source documented in
  [fauna-data-sources.txt](docs/source-notes/fauna-data-sources.txt).
- UCSB Invertebrate Zoology Collection. (2026). Ecdysis Darwin Core
  Archive export, 26 October 2026,
  `SymbOutput_2026-10-26_124013_DwC-A.zip`. User-supplied export retained
  in `data/raw/ecdysis/`; its `CITEME.txt` and `eml.xml` retain the
  source citation and metadata. Portal: [Ecdysis](https://ecdysis.org/).
- California Insect Biodiversity Initiative (CIBI) / BOLD Systems.
  User-supplied barcode-identification export, documented in the source
  notes as downloaded 19 November 2025. The pipeline uses a
  [derived identification table](analysis/reference-data/cibi_barcode_identifications.csv).
  Public portal: [BOLD Systems](https://portal.boldsystems.org/).
  A project-specific public dataset link or DOI has not been recorded.
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

Final regional species checklists are in [`data/final/checklists/`](data/final/checklists/).
They retain all resolved species-level occurrence records, including
BOLD sources, following the user's restoration instruction.
