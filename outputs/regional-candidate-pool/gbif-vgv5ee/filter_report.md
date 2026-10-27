# GBIF regional filtering results

Source DOI: https://doi.org/10.15468/dl.vgv5ee; download key `0010070-260921141020460`.

Filters were applied in the order shown. The original archive was retained unchanged.

The occurrence table was read as UTF-8 tab-delimited text without quote enclosure, as specified in the archive's meta.xml. Literal quotation marks are data; no malformed rows were skipped.

| Stage | Records retained | Records removed at this step |
|---|---:|---:|
| Original GBIF download | 4,665,086 | 0 |
| 1. Identified to genus or below | 3,401,713 | 1,263,373 |
| 2. Usable geographic coordinates | 3,401,713 | 0 |
| 3. Insecta only | 2,935,477 | 466,236 |
| 4. EPA Level III ecoregion 6 or 85 | 1,594,367 | 1,341,110 |

## Exact criteria

1. Use GBIF's interpreted taxonRank at GENUS or a finer named rank. The full allowed-rank list and input rank counts are in filter_metadata.json. UNRANKED records are excluded; a populated parent genus alone is not sufficient.
2. Require finite numeric decimalLatitude and decimalLongitude within [-90, 90] and [-180, 180]. Coordinate uncertainty is preserved and no new uncertainty threshold is applied.
3. Require class to equal Insecta (ignoring case and surrounding whitespace). This excludes spiders and other non-insect invertebrates from this analysis, not from the separate report inventory.
4. Test points against the full EPA Level III polygons for region 6 (Central California Foothills and Coastal Mountains) and region 85 (Southern California/Northern Baja Coast). Points on a polygon boundary are included; a point matching both regions is retained once with both labels.

## Interpretation and next steps

- The source snapshot contains California records only. This is not a complete USA-wide inventory of either ecoregion.
- Genus-only records are valid and retained; taxon-name groups are not automatically species counts.
- No deduplication, year, basis-of-record or provisional-identification filter was added. The source download already excluded GBIF-flagged geospatial issues.
- These are the four requested initial filters. Apply the project's BOLD exclusion, including only verified local-trap exceptions, before producing final candidate lists or recomputing insect Hill diversity.
- All 230 original source fields are retained in the compressed output, with ecoregion code and name appended. Software versions, source identifiers and the ecoregion-file checksum are recorded in filter_metadata.json.
