# Preserve Level III ecoregions

Run `Rscript analysis/ecoregions-level-iii/identify_preserve_ecoregions.R` from the repository root. Requires R packages `sf`, `dplyr` and `readr`.

Inputs are the preserve boundary in `analysis/reference-data/jldp_boundary.geojson` and the EPA Region 9 Level III shapefile in `data/raw/epa/region9_level_iii/2026-10-27/extracted/`. Source metadata remain in that raw-data folder.

The script intersects the boundary in the EPA source CRS, reports overlap areas and exports the full intersecting regional polygons in WGS84 to `outputs/ecoregions-level-iii/2026-10-27/`. The regional filtering workflow reads these polygons. Codes 6 and 85 intersect the preserve; regional boundaries do not delineate beach or dune habitats.

This retains the spatial calculation used in the report while replacing its dependency on the archived numbered pipeline.
