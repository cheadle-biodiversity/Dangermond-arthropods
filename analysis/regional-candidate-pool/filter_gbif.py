"""Filter the existing GBIF snapshot in the requested, audited order.

No source records are overwritten. All original columns are retained in
the filtered CSV; genus-only records are not treated as identified species.
"""
from pathlib import Path
from collections import Counter
import argparse
import csv
import gzip
import hashlib
import json
import platform
import zipfile

import numpy as np
import pandas as pd
import shapely
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
DOI = "10.15468/dl.vgv5ee"
KEY = "0010070-260921141020460"
RANKS = {
    "GENUS", "SUBGENUS", "SECTION", "SUBSECTION", "SERIES", "SUBSERIES",
    "INFRAGENERIC_NAME", "SPECIES_AGGREGATE", "SPECIES", "INFRASPECIFIC_NAME",
    "GREX", "SUBSPECIES", "CULTIVAR_GROUP", "CONVARIETY", "INFRASUBSPECIFIC_NAME",
    "PROLES", "NATIO", "ABERRATION", "VARIETY", "SUBVARIETY", "FORM", "SUBFORM",
    "PATHOVAR", "BIOVAR", "CHEMOVAR", "MORPHOVAR", "PHAGOVAR", "SEROVAR",
    "CHEMOFORM", "FORMA_SPECIALIS", "CULTIVAR", "STRAIN",
}


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / f"data/raw/gbif/california_2026-09-28/{KEY}.zip")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/regional-candidate-pool/gbif-vgv5ee")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    regions_file = ROOT / "outputs/ecoregions-level-iii/2026-10-27/preserve_ecoregions.geojson"
    regions = json.loads(regions_file.read_text())["features"]
    regions = [f for f in regions if str(f["properties"]["US_L3CODE"]) in {"6", "85"}]
    assert len(regions) == 2
    regions.sort(key=lambda x: str(x["properties"]["US_L3CODE"]))
    region_shapes = [(feature, shape(feature["geometry"])) for feature in regions]
    for _, geometry in region_shapes:
        assert shapely.is_valid(geometry)
        shapely.prepare(geometry)
    counts = Counter()
    rank_counts = Counter()
    region_counts = Counter()
    taxon_counts = Counter()
    final_file = args.output / "filtered_insect_records.csv.gz"
    partial_file = final_file.with_suffix(final_file.suffix + ".partial")
    first = True
    with zipfile.ZipFile(args.archive) as archive, gzip.open(partial_file, "wt", encoding="utf-8", newline="", compresslevel=3) as target:
        member = next(n for n in archive.namelist() if n == "occurrence.txt" or n.endswith("/occurrence.txt"))
        with archive.open(member) as source:
            # meta.xml specifies fieldsEnclosedBy="": quotes are literal data.
            for chunk in pd.read_csv(source, sep="\t", quoting=csv.QUOTE_NONE, dtype=str, keep_default_na=False, chunksize=25000, low_memory=False):
                required = {"taxonRank", "decimalLatitude", "decimalLongitude", "class", "scientificName"}
                assert required <= set(chunk), required - set(chunk)
                counts["0_original_records"] += len(chunk)
                ranks = chunk["taxonRank"].str.strip().str.upper()
                rank_counts.update(ranks)
                chunk = chunk.loc[ranks.isin(RANKS)].copy()
                counts["1_genus_or_below"] += len(chunk)
                lat = pd.to_numeric(chunk["decimalLatitude"], errors="coerce")
                lon = pd.to_numeric(chunk["decimalLongitude"], errors="coerce")
                valid = np.isfinite(lat) & np.isfinite(lon) & lat.between(-90, 90) & lon.between(-180, 180)
                chunk = chunk.loc[valid].copy()
                counts["2_usable_coordinates"] += len(chunk)
                chunk = chunk.loc[chunk["class"].str.strip().str.casefold().eq("insecta")].copy()
                counts["3_insecta"] += len(chunk)
                if chunk.empty:
                    continue
                points = shapely.points(pd.to_numeric(chunk["decimalLongitude"]), pd.to_numeric(chunk["decimalLatitude"]))
                codes = np.full(len(chunk), "", dtype=object)
                names = np.full(len(chunk), "", dtype=object)
                for feature, geometry in region_shapes:
                    hit = shapely.covers(geometry, points)
                    code = str(feature["properties"]["US_L3CODE"])
                    # Retain each occurrence once; label rare shared-boundary hits.
                    both = hit & (codes != "")
                    only = hit & (codes == "")
                    codes[both] = np.array([x + ";" + code for x in codes[both]])
                    names[both] = np.array([x + ";" + feature["properties"]["US_L3NAME"] for x in names[both]])
                    codes[only] = code
                    names[only] = feature["properties"]["US_L3NAME"]
                    region_counts[code] += int(hit.sum())
                chunk["analysis_ecoregion_l3_code"] = codes
                chunk["analysis_ecoregion_l3_name"] = names
                chunk = chunk.loc[codes != ""].copy()
                counts["4_target_level_iii_ecoregions"] += len(chunk)
                taxon_counts.update(zip(chunk["analysis_ecoregion_l3_code"], chunk["taxonRank"], chunk["order"], chunk["family"], chunk["genus"], chunk["scientificName"]))
                chunk.to_csv(target, index=False, header=first)
                first = False
                if counts["0_original_records"] % 250000 == 0:
                    print(f"Read {counts['0_original_records']:,}; retained {counts['4_target_level_iii_ecoregions']:,}", flush=True)
    assert counts["0_original_records"] == 4665086, "Source snapshot record count differs from DOI metadata"
    assert counts["4_target_level_iii_ecoregions"] > 0
    partial_file.replace(final_file)
    with (args.output / "filter_counts.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["stage", "records_retained", "records_removed_at_stage"])
        previous = counts["0_original_records"]
        for name in sorted(counts):
            writer.writerow([name, counts[name], previous - counts[name]])
            previous = counts[name]
    with (args.output / "taxon_record_counts_by_ecoregion.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ecoregion_l3_code", "taxon_rank", "order", "family", "genus", "scientific_name", "records"])
        for key, value in sorted(taxon_counts.items()):
            writer.writerow([*key, value])
    metadata = {
        "source_doi": DOI, "source_download_key": KEY,
        "input_format": "UTF-8, tab-delimited, no quote enclosure, header row; per archive meta.xml. Literal quotes are preserved; malformed rows are not skipped.",
        "software_versions": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "shapely": shapely.__version__},
        "source_archive": str(args.archive.relative_to(ROOT)) if args.archive.is_relative_to(ROOT) else str(args.archive),
        "ecoregion_file": str(regions_file.relative_to(ROOT)),
        "ecoregion_file_sha256": hashlib.sha256(regions_file.read_bytes()).hexdigest(),
        "counts": dict(sorted(counts.items())), "source_taxon_ranks": dict(rank_counts),
        "records_by_ecoregion": dict(region_counts), "accepted_ranks": sorted(RANKS),
        "coordinate_rule": "Finite latitude/longitude, within valid global coordinate bounds; no new uncertainty cutoff",
        "taxonomic_rule": "GBIF taxonRank genus or below; UNRANKED records excluded even if a parent genus is populated",
        "geographic_rule": "Coordinates covered by full EPA Level III region 6 or 85; not restricted to preserve boundary",
        "record_handling": "All source columns retained; no deduplication, date, basis-of-record or identificationQualifier filter added",
        "bold_policy": "These are the four requested filters only. BOLD eligibility must be applied before final candidate lists; local-trap exceptions require verified locations.",
        "scope_limit": "Source download is California-only; results are California portions of the two ecoregions, not their complete USA-wide fauna",
    }
    source_manifest = args.archive.parent / "archive_manifest.json"
    if source_manifest.exists():
        metadata["source_archive_sha256"] = json.loads(source_manifest.read_text())["sha256"]
    (args.output / "filter_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    labels = {
        "0_original_records": "Original GBIF download",
        "1_genus_or_below": "1. Identified to genus or below",
        "2_usable_coordinates": "2. Usable geographic coordinates",
        "3_insecta": "3. Insecta only",
        "4_target_level_iii_ecoregions": "4. EPA Level III ecoregion 6 or 85",
    }
    report = [
        "# GBIF regional filtering results", "",
        f"Source DOI: https://doi.org/{DOI}; download key `{KEY}`.", "",
        "Filters were applied in the order shown. The original archive was retained unchanged.", "",
        "The occurrence table was read as UTF-8 tab-delimited text without quote enclosure, as specified in the archive's meta.xml. Literal quotation marks are data; no malformed rows were skipped.", "",
        "| Stage | Records retained | Records removed at this step |",
        "|---|---:|---:|",
    ]
    previous = counts["0_original_records"]
    for key in sorted(counts):
        report.append(f"| {labels[key]} | {counts[key]:,} | {previous - counts[key]:,} |")
        previous = counts[key]
    report += [
        "", "## Exact criteria", "",
        "1. Use GBIF's interpreted taxonRank at GENUS or a finer named rank. The full allowed-rank list and input rank counts are in filter_metadata.json. UNRANKED records are excluded; a populated parent genus alone is not sufficient.",
        "2. Require finite numeric decimalLatitude and decimalLongitude within [-90, 90] and [-180, 180]. Coordinate uncertainty is preserved and no new uncertainty threshold is applied.",
        "3. Require class to equal Insecta (ignoring case and surrounding whitespace). This excludes spiders and other non-insect invertebrates from this analysis, not from the separate report inventory.",
        "4. Test points against the full EPA Level III polygons for region 6 (Central California Foothills and Coastal Mountains) and region 85 (Southern California/Northern Baja Coast). Points on a polygon boundary are included; a point matching both regions is retained once with both labels.",
        "", "## Interpretation and next steps", "",
        "- The source snapshot contains California records only. This is not a complete USA-wide inventory of either ecoregion.",
        "- Genus-only records are valid and retained; taxon-name groups are not automatically species counts.",
        "- No deduplication, year, basis-of-record or provisional-identification filter was added. The source download already excluded GBIF-flagged geospatial issues.",
        "- These are the four requested initial filters. Apply the project's BOLD exclusion, including only verified local-trap exceptions, before producing final candidate lists or recomputing insect Hill diversity.",
        "- All 230 original source fields are retained in the compressed output, with ecoregion code and name appended. Software versions, source identifiers and the ecoregion-file checksum are recorded in filter_metadata.json.",
    ]
    (args.output / "filter_report.md").write_text("\n".join(report) + "\n")
    print(json.dumps(metadata["counts"], indent=2), flush=True)


if __name__ == "__main__":
    run()
