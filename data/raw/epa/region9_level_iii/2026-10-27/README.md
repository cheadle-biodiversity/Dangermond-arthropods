# EPA Region 9 Level III ecoregions

Downloaded 27 October 2026 from the links on the
[EPA regional download page](https://www.epa.gov/eco-research/ecoregion-download-files-region).

- `reg9_eco_l3.zip`: original GIS archive.
- `reg9_eco_l3.htm`: source metadata.
- `reg9_eco_l3.lyr`: ArcGIS symbology.
- `extracted/`: all shapefile components from the original ZIP.
- `archive_manifest.json`: source URLs, download date, sizes and SHA-256 hashes.

Validation: the ZIP passed its integrity check; the extracted dataset
opens with `sf` and contains 85 features. Two features intersect the
existing preserve boundary. The numbered Step 9 script now reads this
copy. The older tracked `raw_download/` copy remains as a historical
input; it has not been silently overwritten.
