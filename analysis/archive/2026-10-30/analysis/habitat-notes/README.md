# First-pass habitat and life-history notes

This workflow annotates all species in the two Level IV checklists with separate
lines of evidence. It is a habitat-screening aid for the proposed Hill-number
comparison, not a habitat suitability model or a determination of specialization.

## Inputs and outputs

- The 43,555 regional GBIF occurrences underlying Level IV regions 6ap and 85a.
- The full upstream version 3 supplies the species roll-up, publisher `habitat`,
  field notes and remarks omitted from the simplified occurrence files.
- The October 26 Ecdysis export contributes local habitat descriptions through
  the existing approved species-name crosswalk. Only mapped named insect records
  enter these species annotations; higher-taxon records remain valid observations.
- [CDFW vegetation ds2957](https://filelib.wildlife.ca.gov/public/BDB/GIS/BIOS/metadata/DS2957.html),
  mapped from field work during 2012–2017, and the polygons associated with
  [USGS SIM 3472](https://doi.org/10.3133/sim3472),
  [data DOI 10.5066/P9FU7SJL](https://doi.org/10.5066/P9FU7SJL).
- Manually sourced accounts in `reviewed_species_notes.csv`. This is a limited
  first literature pass on beach/dune beetles and crickets; it is not a review of
  all 2,550 species.

Enriched copies were archived to
`outputs/habitat-notes/2026-10-27/archived-annotations/` when the user restored the
original seven-column checklist layout. The workflow now writes only to that
supporting archive, preserving the restored files in `data/final/habitat-notes/`
and canonical checklists in `data/final/checklists/`. Occurrence packages are
unchanged. Supporting regional and Ecdysis
record-level evidence is in `outputs/habitat-notes/2026-10-27/`.

## Method

1. Match final regional occurrences to upstream records by GBIF ID, retaining
   the approved `resolved_species_name` used to build the checklists. Verify that
   record counts and species totals reconcile with each original checklist.
2. Transform points and map polygons to NAD83 / UTM zone 10N (EPSG:26910).
   Repair invalid polygon geometries using `make_valid`, retaining the source
   downloads. Use boundary-inclusive point-in-polygon intersection. Leave points
   outside the mapped polygons unassigned; do not snap them to a nearby habitat.
   Multiple polygon hits would be flagged and excluded from class assignment.
3. Distinguish exact vegetation map classes. `Coastal Strand` provides mapped
   strand context. `Sand Dune Sedge Swaths` and `Silver Dune Lupine - Mock Heather
   Scrub` provide mapped dune-vegetation context. Do not use `CalVegType=Dune` by
   itself: that broad category also includes polygons labeled `Coastal Bluffs`.
4. Keep USGS `Qey` (Holocene beach and dune sand) combined; this unit cannot
   separate beach from backdunes. `Qeo` is Pleistocene dune substrate and does not
   establish present-day dune habitat. Other geologic units are not evidence of
   non-dune ecology. All source polygon classes remain in the record audit.
5. Check whether each positive reported coordinate-uncertainty radius lies inside
   its individual matched polygon by comparing radius to distance from its
   boundary. Missing, zero or invalid radii are unknown. A radius reaching a
   boundary is flagged. This is a conservative geometric check, not a confidence
   probability: it does not incorporate map error, coordinate-system error or
   historical habitat change. Adjacent polygons may represent the same class.
6. Retain publisher `habitat` verbatim. Locality keyword flags only identify
   records for review; a place name containing beach does not establish habitat.
7. Link Ecdysis records by ID through `preserve_occurrence_evidence.csv`. Keep
   explicit Perko's Beach localities, field-described backdunes, other beach
   localities and unspecified sites separate. Preserve original spellings and
   qualifiers in the audit. Local records and their map assignments are separate
   from regional record counts, preventing inflation from overlapping sources.
8. Aggregate evidence separately within each regional checklist. A mapped
   occurrence demonstrates an occurrence-location association, not a species'
   habitat preference, residency, reproductive habitat or obligate specialization.
   Flighted visitors and generalists can occur in mapped dunes and beaches.
9. Add life-history notes only where a cited account has been reviewed. Clearly
   mark genus-level feeding context. Unreviewed species retain blank life-history
   text and `literature_review_status=not reviewed`. Blank notes are not evidence
   that a taxon lacks a coastal association.

The maps cover local areas, not the entire Level IV regions. Occurrence dates
span different periods, while the vegetation map predates the 2022 dune
restoration. Local field descriptions may consequently be more informative about
conditions at collection than the older map. Counts are records, not independent
individuals, sampling effort, habitat-use proportions or population abundance.
Do not assign every species to beach or backdune from this first pass.

## Reproduce

Run `python3 analysis/habitat-notes/annotate_level_iv.py` from the repository root
with pandas, NumPy, GeoPandas, Shapely and pyproj available. The first run extracts
regional context from the full upstream file; later runs reuse the saved context.
Download sources and SHA256 values are recorded under `data/raw/habitat/2026-10-27/`.
Source data and large record audits are excluded from Git; annotations, methods,
reviewed notes and provenance remain versionable.

## Literature reviewed

- Craig, P. C. 1970. The behavior and distribution of the intertidal sand beetle,
  Thinopinus pictus (Coleoptera: Staphylinidae). Ecology 51:1012–1017.
  https://doi.org/10.2307/1933627.
- Moore, I. 1974. Notes on Phaleria rotundata LeConte with description of the
  larva (Coleoptera: Tenebrionidae). The Great Lakes Entomologist 7(4).
  https://doi.org/10.22543/0090-0222.1233.
- Frank, J. H., and Ahn, K.-J. 2011. Coastal Staphylinidae (Coleoptera): A worldwide
  checklist, biogeography and natural history. ZooKeys 107:1–98.
  https://doi.org/10.3897/zookeys.107.1651.
- NatureServe Explorer. Coelus globosus species account; accessed 27 October 2026.
  https://explorer.natureserve.org/Taxon/ELEMENT_GLOBAL.2.111865/Coelus_globosus.
- Sandoval, C. 2007. Survey of Globose Dune Beetle at 30732 Pacific Coast Highway
  (Broad Beach), Appendix B in the biological resources assessment filed with the
  California Coastal Commission in 2008.
  https://documents.coastal.ca.gov/reports/2008/6/W16a-6-2008-a1.pdf.
- Washington Department of Fish and Wildlife. Snowy plover recovery-plan account,
  Table 1, beach-invertebrate natural history.
  https://wdfw.wa.gov/sites/default/files/publications/01518/wdfw01518.pdf.
- CDFW. Point Conception Jerusalem cricket species account; accessed 27 October
  2026. Historical natural-history information only; old range/status statements
  are not adopted. https://nrm.dfg.ca.gov/FileHandler.ashx?DocumentID=107616.
- Rentz, D. C. F., and Weissman, D. B. 1981. Faunal affinities, systematics, and
  bionomics of the Orthoptera of the California Channel Islands. University of
  California Publications in Entomology 94. Rhachocnemis validus account.
  https://orthsoc.org/sina/i00lrw81.pdf.

No current regulatory-status inference is made from these historical accounts.
