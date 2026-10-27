# Preserve GBIF snapshot — 26 October 2026

Complete source folder transferred from the report workspace for the
Hill-number analysis. This snapshot was retrieved through the GBIF
occurrence search API; it is not the incoming USA-wide DOI download.

- `gbif_bounding_box_source.jsonl.gz`: original bounding-box responses.
- `gbif_all_arthropods_within_preserve.jsonl.gz`: boundary-clipped responses.
- `all_arthropods_within_preserve.csv`: tabular boundary-clipped records.
- `terrestrial_arthropod_occurrences.csv`: 14,601 records selected for analysis.
- `excluded_or_unresolved_arthropods.csv`: excluded records and scope decisions.
- `preserve_boundary.geojson`: exact boundary used for this snapshot.
- `initial_query.json`, `download_manifest.json`,
  `dataset_and_publisher_metadata.json`, `checksums_sha256.json`:
  retrieval, attribution and provenance details.
- Summary CSVs, `summary_tables.json` and `GBIF_summary.md`: original
  summaries retained alongside their source data.

The Hill script reads the compressed clipped responses and uses the
terrestrial CSV's record identifiers to select its analysis set.
The separate reference boundary in `analysis/reference-data/` is used
by the regional candidate-species pipeline; this snapshot's boundary
is retained independently so the historical analysis can be audited.
