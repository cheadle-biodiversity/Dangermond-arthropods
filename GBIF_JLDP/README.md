# GBIF_JLDP: Dangermond Preserve data accessibility in GBIF

Assessment of how much biodiversity occurrence data from the Jack and Laura Dangermond Preserve (JLDP) reaches GBIF, prepared for The Nature Conservancy (TNC) in September–October 2026. It supports the report section *Occurrence data accessibility*.

## Questions addressed

1. Which datasets in the Dangermond Preserve Research Repository (DPRR), hosted on KNB/DataONE, contain organism occurrence data, and what would it take to publish them to GBIF?
2. How many GBIF occurrence records fall inside the Preserve footprint, and which publishers contribute them?
3. How do repositories with curator-led models (OBIS-SEAMAP, PANGAEA) compare with KNB's self-service model?

## Contents

| Path | Description |
| --- | --- |
| [`inputs/Dangermond_DataOne_datasets_25Sept2026_reformatted3.xlsx`](inputs/) | DataONE catalog search results for "Dangermond Preserve", 25 September 2026. Three sheets (`DataOnePortalSearch`, `DangermondPortalSearch`, `OnlyOnOneList`); 50 unique entries after removing duplicates by identifier. |
| [`../analysis/reference-data/jldp_boundary.geojson`](../analysis/reference-data/jldp_boundary.geojson) | TNC Preserve boundary (EPSG:4326, GIS_Acres 24,458.6). Shared with the other spatial workflows; identical to the file used here. |
| [`outputs/Dangermond_KNB_triage_GBIF_footprint_25Sept2026.xlsx`](outputs/) | Main output workbook (sheets described below). |
| [`docs/repository_comparison.md`](docs/repository_comparison.md) | Full data flow comparison of OBIS-SEAMAP, KNB and PANGAEA, with sources. Report appendix. |
| [`docs/dataone_schemaorg_repositories.csv`](docs/dataone_schemaorg_repositories.csv) | The 23 schema.org repositories DataONE federates, as listed by Ian Nesbitt (NCEAS) after a call on 11 August 2026. |
| [`requirements.txt`](requirements.txt) | Python package requirements. |

## Method

### 1. KNB dataset triage

- Metadata for each KNB entry were retrieved from the KNB member-node Solr index (`https://knb.ecoinformatics.org/knb/d1/mn/v2/query/solr/`): title, abstract, EML attribute names, bounding box, temporal coverage, license, obsolescence (`obsoletedBy`) and the list of data files.
- Small tabular data files (CSV/XLSX) were downloaded from `https://knb.ecoinformatics.org/knb/d1/mn/v2/object/<pid>` and inspected for taxon names, coordinates and dates.
- Large radar track files (~0.5 GB each) and large zip archives were not opened. Two entries hosted outside KNB (OpenTopography lidar, HydroShare hydrology) were classified from their titles.
- Where data held coordinates, points were tested against the Preserve polygon and a 500 m buffer (UTM coordinates converted to WGS84 first).
- Each entry was assigned to one tier by researcher review:

| Tier | Definition |
| --- | --- |
| A | Occurrence-ready: taxon, coordinates and date present in the data |
| B | Organism data; needs georeferencing or restructuring |
| C | Checklist only; no per-record location |
| D | Organism detections without taxon IDs, or derived products |
| E | No organism data |

### 2. GBIF records in the Preserve footprint

- The boundary was projected to UTM zone 10N (EPSG:32610), simplified at 20 m tolerance (area change < 0.1%) and converted to counter-clockwise WKT for the GBIF API. A second polygon used a 500 m buffer, because the boundary follows the shoreline and coastal records (cliff nests, haulouts, intertidal) fall just outside it.
- Queried `https://api.gbif.org/v1/occurrence/search` with the `geometry` filter and `limit=0`, faceting on `publishingOrg`, `datasetKey`, `basisOfRecord`, `kingdomKey` and `year`.
- Publisher and dataset names were resolved through the GBIF `organization` and `dataset` endpoints.
- Taxon gaps: for species documented in DPRR datasets, the GBIF backbone key (`/species/match`) was used to count in-footprint records.
- GBIF's dataset index was searched for Dangermond-related terms (Dangermond, Point Conception, Jalama, Cojo, Point Blue, VTM, Western Monarch Thanksgiving Count) to check whether any DPRR dataset had been published to GBIF.

GBIF counts are a snapshot of the live index on 25 September 2026.

### 3. Repository comparison

OBIS-SEAMAP, KNB and PANGAEA were compared using each repository's published submission documentation and conversations with DataONE/NCEAS staff. GBIF publisher status and DataONE member-node status were confirmed through the GBIF organization API and the DataONE node list on 30 October 2026.

## Output workbook

| Sheet | Contents |
| --- | --- |
| README | Methods summary and the footprint WKT |
| KNB_Triage | All 50 entries with tier, organism fields, location detail, estimated convertible records, footprint relation, license, obsolescence and publishing hurdles |
| GBIF_by_Publisher | Records in parcel and in parcel + 500 m, by publisher, with basis-of-record breakdown and year span |
| GBIF_by_Dataset | Records by GBIF dataset, with license and dataset link |
| Taxon_Gaps | GBIF records in the footprint for species documented in DPRR datasets |

## Key results (25 September 2026)

- GBIF holds 25,591 records inside the Preserve boundary (49,203 within 500 m) from 63 publishers. iBOL (13,453) and eBird (8,663) account for 86% of in-boundary records.
- No GBIF dataset corresponds to any of the 50 DPRR entries.
- DPRR triage: 5 Tier A, 6 Tier B, 8 Tier C (4 of them superseded versions), 5 Tier D and 26 Tier E.
- Several species documented in DPRR datasets have few or no GBIF records in the Preserve, including Western snowy plover, harbor seal, Mexican free-tailed bat and California red-legged frog.

## Reproduction

```
pip install -r requirements.txt
```

Python 3.12. The analysis was run interactively; scripts were not retained. The steps above, the API endpoints and the query date are sufficient to repeat it. Tier assignments are researcher judgement and will not be reproduced by code alone.

## Caveats

- GBIF counts change as records are added or reprocessed; rerun the queries before reusing the numbers.
- A first pass used a copy of the boundary from the NASA VITALS workshop repository; it differed from the TNC boundary by < 10 acres and changed in-parcel counts by 5 records.
- Some DPRR datasets include threatened or endangered species. How their locations should be published is an open question for TNC and the data owners (CDFW, Point Blue Conservation Science, Vandenberg Space Force Base).

## Data sources and licenses

- KNB Data Repository (NCEAS), via the DataONE network: https://knb.ecoinformatics.org. DPRR packages are licensed CC0 or CC BY 4.0, as recorded per dataset in the `KNB_Triage` sheet.
- GBIF.org occurrence search API, queried 25 September 2026: https://api.gbif.org/v1/occurrence/search. Counts only; no records were downloaded. Individual records retain their publishers' licenses.
- Repository comparison sources are listed in [`docs/repository_comparison.md`](docs/repository_comparison.md).
- I. Nesbitt, NCEAS, personal communication, 11 August 2026 (DataONE schema.org federation list).

## Document Provenance and AI Assistance Statement

The triage workbook, repository comparison and this documentation were prepared with AI assistance (Claude, Anthropic) in September–October 2026. AI assistance was used to query the KNB and GBIF APIs, inspect dataset files, compute footprint overlaps and record counts, draft tables and Markdown, and check citations against source pages. Dataset tier assignments and interpretations were reviewed by the researcher.

The scientific authorities remain the original data providers, repository documentation and cited literature. These materials are working documents for researcher review and do not constitute independent validation of the underlying datasets. Researchers remain responsible for verifying interpretations and approving material for publication or management use.
