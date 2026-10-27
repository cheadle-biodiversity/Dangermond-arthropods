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

The next analysis will use a fresh GBIF download and the local Ecdysis
inventory to identify insect species that may occur at Dangermond.
Recorded species and candidate species will be reported separately.
The existing range-envelope and ecoregion results provide starting
points for screening; fitted species distribution models are a later
stage of the work.

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

## Hill diversity analysis

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
