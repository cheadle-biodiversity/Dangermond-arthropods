# Dangermond Project — Step 9: Identify the Preserve's Shared EPA Level III Ecoregion(s)

New step, picking up a separate thread from the rest of this pipeline:
instead of asking "how close is a species to the Preserve boundary"
(Steps 5-8), this step and Step 10 ask "does a species occur on the same
broad habitat type the Preserve itself sits on, anywhere in California."

This step answers the first half: which EPA Level III ecoregion polygon(s),
from the official Region 9 ecoregion shapefile, spatially overlap the
Preserve boundary at all. Step 10 uses the result to build the actual
species list.

## Why EPA Level III Ecoregions as "habitat type"

EPA's ecoregion framework (Omernik 1995, 2004) defines areas of general
similarity in ecosystems — geology, physiography, vegetation, climate,
soils, land use, and hydrology — specifically so they can serve as "a
spatial framework for the research, assessment, management, and
monitoring of ecosystems." Level III is the finest level EPA publishes as
a single downloadable product for an EPA Administrative Region (one
shapefile covers all of Region 9: California, Nevada, Arizona, Hawaii, and
Pacific Island territories; 85 polygons). That granularity is a reasonable
match for this project's own resolution — statewide GBIF occurrence
records, not fine-grained vegetation mapping — so "same habitat type as
the Preserve" is operationalized here as "same Level III ecoregion as the
Preserve."

## Data source — why this had to be user-supplied

The three EPA files for Region 9 —

- `reg9_eco_l3.zip` (the shapefile: `.shp`/`.shx`/`.dbf`/`.prj`/`.sbn`/`.sbx`/`.shp.xml`)
- `reg9_eco_l3.htm` (FGDC metadata)
- `reg9_eco_l3.lyr` (ArcGIS symbology — colors/legend only, no geometry)

are served from an AWS S3 bucket
(`dmap-prod-oms-edc.s3.us-east-1.amazonaws.com`). This pipeline's cloud
execution environment could not reach that host directly: every direct
download attempt failed with a TLS/connection-level rejection, and the
environment's own network diagnostics confirmed this was the environment's
own egress policy denying the connection outright (not a data license,
authentication, or bot-detection issue on EPA's end). A WebFetch-based
retrieval attempt was also tried and also failed to return usable content.

Per this project's standing approach to a host blocked at the network
level (don't retry or attempt to route around it — report it and get the
file another way), the user downloaded all three files directly from the
URLs EPA publishes and supplied them to this project. They're kept in
`raw_download/` for reproducibility; `identify_preserve_ecoregions.R`
reads only the four component files `sf` actually needs
(`.shp`/`.shx`/`.dbf`/`.prj` — not the ArcGIS-specific `.sbn`/`.sbx` spatial
index caches, and not the `.lyr` symbology file, which is a Microsoft OLE2
compound-document format carrying ArcGIS display colors, not geometry).

## What this step does

1. Reads the 85-polygon Region 9 Level III ecoregion shapefile. Its native
   CRS is `USA_Contiguous_Albers_Equal_Area_Conic_USGS_version` (NAD83) —
   an equal-area projection, not the WGS84 lat/lon GBIF and the Preserve
   boundary file use elsewhere in this pipeline.
2. Reprojects the Preserve boundary (`../reference-data/jldp_boundary.geojson`,
   WGS84) into the ecoregion shapefile's own CRS — the cheaper and
   lower-risk direction, since it's one small polygon rather than 85
   national-extent ones, and it's also the right direction for computing a
   meaningful overlap *area* (an equal-area CRS is what makes that
   calculation valid).
3. Finds every ecoregion polygon that spatially intersects the
   (reprojected) boundary — not just the one containing its centroid, in
   case the Preserve straddles an ecoregion edge.
4. For each match, computes the real overlap area, both to confirm it's a
   substantial overlap rather than a boundary-precision sliver and for
   reporting.
5. Writes the matched polygon(s) back out in WGS84 (to match GBIF's own
   coordinate convention) so Step 10 can test occurrence points against
   them directly with no further reprojection.

## Result (verified against the real data)

**Two** ecoregion polygons intersect the Preserve boundary — it genuinely
straddles the edge between them, not a sliver artifact:

| US_L3CODE | US_L3NAME | Overlap (% of Preserve area) |
|---|---|---|
| 6 | Central California Foothills and Coastal Mountains | 91.94% |
| 85 | Southern California/Northern Baja Coast | 8.06% |

Both fall under the same Level II/Level I grouping
(`California Coastal Sage, Chaparral, and Oak Woodlands` /
`MEDITERRANEAN CALIFORNIA`), so while there are two distinct Level III
polygons, they're not ecologically unrelated to each other — consistent
with a single preserve that happens to sit right at a mapped habitat
boundary rather than genuinely spanning two very different ecosystems.

## What's produced

- **`output/preserve_ecoregions.csv`** — the matched ecoregion(s) with
  code, name, full Level I/II/III hierarchy, and overlap area/percentage.
- **`output/preserve_ecoregions.geojson`** — the matched polygon geometry
  itself (WGS84), for Step 10's point-in-polygon test.

## What this step does NOT do

- It does not attempt a finer habitat classification (vegetation type,
  soil type) than EPA's own Level III ecoregion product provides.
- It does not evaluate Level IV ecoregions (a finer subdivision EPA also
  publishes but not requested for this analysis).

## Paths

`infile_ecoregions` points at the unzipped shapefile in `raw_download/`.
`infile_boundary` points at the shared `../reference-data/jldp_boundary.geojson`.
