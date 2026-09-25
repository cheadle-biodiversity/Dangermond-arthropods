# Dangermond Arthropods

This repository gathers arthropod occurrence data, source notes, literature, analysis files, and screening outputs for biodiversity work related to the Jack and Laura Dangermond Preserve.

## Repository layout

- `analysis/` - R Markdown and other analysis notebooks.
- `Apoidea/` - self-contained Python workflow for the Central Coast non-bee Apoidea checklist.
- `data/raw/gbif/` - GBIF occurrence download files.
- `data/raw/cibi/` - CIBI/source download files from the 2025-11-19 export.
- `data/raw/ecdysis/` - Ecdysis Darwin Core Archive export files.
- `data/local/` - local SQLite databases ignored by git.
- `data/reference/` - small reference tables used by analyses.
- `docs/field-logistics/` - preserve visit, directions, and overnight logistics documents.
- `docs/source-notes/` - notes and citations for merged source datasets.
- `outputs/` - generated reports and printable screening files.
- `references/papers/` - supporting literature PDFs.

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
