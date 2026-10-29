"""Assign EPA Level IV regions to version 2, preserving all rows and columns.

Use full Region 9 polygons, not preserve-clipped polygons. Boundary
points are included; multiple matches are labeled, not duplicated.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json

import geopandas as gpd
import numpy as np
import pandas as pd
import pyproj
import shapely

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/regional-candidate-pool/gbif-vgv5ee'
SOURCE = OUT / 'species_identified_insect_records_v2.csv.gz'
TARGET = OUT / 'species_identified_insect_records_v3.csv.gz'
EPA = ROOT / 'data/raw/epa/region9_level_iv/2026-10-27'
SHAPEFILE = EPA / 'extracted/reg9_eco_l4.shp'
NEW = ['analysis_ecoregion_l4_code', 'analysis_ecoregion_l4_name', 'analysis_ecoregion_l4_match_status']


def main():
    eco = gpd.read_file(SHAPEFILE)
    original_crs = str(eco.crs)
    original_features = len(eco)
    assert eco.crs and eco.is_valid.all() and eco.US_L4CODE.notna().all()
    for code, group in eco.groupby('US_L4CODE'):
        assert group.US_L4NAME.nunique() == group.US_L3CODE.nunique() == 1
    # Merge disconnected pieces of one region so repeated code hits never
    # create duplicate occurrence rows or false multiple-region labels.
    eco = eco[['US_L4CODE', 'US_L4NAME', 'US_L3CODE', 'geometry']].dissolve(by='US_L4CODE', as_index=False).to_crs(4326)
    eco = eco.sort_values('US_L4CODE').reset_index(drop=True)
    assert eco.is_valid.all()
    tree = shapely.STRtree(eco.geometry.to_numpy())
    poly_codes = eco.US_L4CODE.astype(str).to_numpy()
    poly_names = eco.US_L4NAME.astype(str).to_numpy()
    poly_l3 = eco.US_L3CODE.astype(str).to_numpy()
    names = dict(zip(poly_codes, poly_names))
    preserve_codes = set(pd.read_csv(ROOT / 'outputs/ecoregions-level-iv/2026-10-27/preserve_ecoregions_level_iv.csv').US_L4CODE)
    statuses = Counter()
    labels = Counter()
    species = defaultdict(set)
    issue_rows = []
    total = 0
    first = True
    partial = TARGET.with_suffix('.gz.partial')
    with gzip.open(partial, 'wt', encoding='utf-8', newline='', compresslevel=3) as output:
        for frame in pd.read_csv(SOURCE, dtype=str, keep_default_na=False, chunksize=25000):
            assert not set(NEW) & set(frame)
            lat = pd.to_numeric(frame.decimalLatitude, errors='raise').to_numpy()
            lon = pd.to_numeric(frame.decimalLongitude, errors='raise').to_numpy()
            assert np.isfinite(lat).all() and np.isfinite(lon).all()
            points = shapely.points(lon, lat)
            point_idx, polygon_idx = tree.query(points, predicate='covered_by')
            hits = np.bincount(point_idx, minlength=len(frame))
            codes = np.full(len(frame), '', dtype=object)
            region_names = np.full(len(frame), '', dtype=object)
            parents = np.full(len(frame), '', dtype=object)
            codes[point_idx] = poly_codes[polygon_idx]
            region_names[point_idx] = poly_names[polygon_idx]
            parents[point_idx] = poly_l3[polygon_idx]
            multiple = np.flatnonzero(hits > 1)
            for index in multiple:
                matched = polygon_idx[point_idx == index]
                codes[index] = ';'.join(poly_codes[matched])
                region_names[index] = ';'.join(poly_names[matched])
                parents[index] = ';'.join(sorted(set(poly_l3[matched])))
            status = np.where(hits == 0, 'unmatched', np.where(hits == 1, 'matched_single', 'matched_multiple'))
            frame[NEW[0]], frame[NEW[1]], frame[NEW[2]] = codes, region_names, status
            statuses.update(status)
            labels.update(codes)
            for code, name in zip(codes, frame.resolved_species_name):
                if code:
                    for component in code.split(';'):
                        species[component].add(name)
            # Keep discrepancies explicit; never snap to a nearest region.
            mismatches = np.array([bool(parent) and not (set(parent.split(';')) & set(prior.split(';'))) for parent, prior in zip(parents, frame.analysis_ecoregion_l3_code)])
            problematic = (hits != 1) | mismatches
            if problematic.any():
                audit = frame.loc[problematic, ['gbifID','decimalLatitude','decimalLongitude','analysis_ecoregion_l3_code',*NEW]].copy()
                audit['level_iv_parent_level_iii_code'] = parents[problematic]
                audit['level_iii_disagrees'] = mismatches[problematic]
                issue_rows.append(audit)
            frame.to_csv(output, index=False, header=first)
            first = False
            total += len(frame)
            if total % 500000 == 0:
                print(f"Assigned Level IV fields to {total:,} records; unmatched {statuses['unmatched']:,}", flush=True)
    assert total == json.loads((OUT / 'common_name_enrichment_metadata.json').read_text())['counts']['records']
    assert total == sum(statuses.values()) == sum(labels.values())
    partial.replace(TARGET)
    region_counts = Counter()
    for label, count in labels.items():
        if label:
            for code in label.split(';'):
                region_counts[code] += count
    rows = [{'ecoregion_l4_code': code, 'ecoregion_l4_name': names[code], 'occurrence_records': count, 'distinct_resolved_species_names': len(species[code]), 'ecoregion_intersects_preserve': code in preserve_codes} for code, count in sorted(region_counts.items())]
    pd.DataFrame(rows).to_csv(OUT / 'level_iv_ecoregion_counts.csv', index=False)
    issues = pd.concat(issue_rows, ignore_index=True) if issue_rows else pd.DataFrame(columns=['gbifID','decimalLatitude','decimalLongitude','analysis_ecoregion_l3_code',*NEW,'level_iv_parent_level_iii_code','level_iii_disagrees'])
    issues.to_csv(OUT / 'level_iv_assignment_issues.csv', index=False)
    with SOURCE.open('rb') as source:
        source_sha = hashlib.file_digest(source, 'sha256').hexdigest()
    with (EPA / 'reg9_eco_l4.zip').open('rb') as archive:
        epa_sha = hashlib.file_digest(archive, 'sha256').hexdigest()
    metadata = {
        'completed_at': datetime.now(timezone.utc).isoformat(),
        'source_dataset': str(SOURCE.relative_to(ROOT)), 'source_dataset_sha256': source_sha,
        'output_dataset': str(TARGET.relative_to(ROOT)), 'records': total, 'columns_added': NEW,
        'epa_source': str(SHAPEFILE.relative_to(ROOT)), 'epa_archive_sha256': epa_sha,
        'epa_source_manifest': str((EPA / 'archive_manifest.json').relative_to(ROOT)),
        'source_crs': original_crs, 'assignment_crs': 'EPSG:4326',
        'source_polygon_features': original_features, 'distinct_level_iv_regions': len(eco),
        'assignment_rule': 'Dissolve disconnected pieces by US_L4CODE; transform full EPA Region 9 polygons to WGS84; point covered_by polygon includes boundary. No nearest-neighbor, buffer, snapping or uncertainty threshold. No rows filtered.',
        'multiple_match_rule': 'Retain each occurrence once; semicolon-separated codes/names in corresponding order. Regional summary counts credit a boundary occurrence to each matching region.',
        'match_status_counts': dict(statuses), 'distinct_assigned_region_codes': len(region_counts),
        'level_iii_disagreement_records': int(issues.level_iii_disagrees.sum()) if not issues.empty else 0,
        'preserve_ecoregion_codes': sorted(preserve_codes),
        'preserve_ecoregion_occurrence_counts': {code: region_counts[code] for code in sorted(preserve_codes)},
        'interpretation': 'Assigns actual Level IV location to the complete regional pool. It does not restrict records to the two Level IV regions intersecting Dangermond. A regional assignment does not establish occurrence on the preserve or identify beach/backdune habitat. Coordinate uncertainty remains in original columns and is not propagated into region assignment.',
        'software_versions': {'pandas': pd.__version__, 'geopandas': gpd.__version__, 'shapely': shapely.__version__, 'pyproj': pyproj.__version__},
    }
    (OUT / 'level_iv_assignment_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    lines = ['# Level IV ecoregion assignment', '', f"Input records: {total:,}. All retained; three fields appended to version 2.", '', 'Source: EPA Region 9 Level IV polygons, downloaded 27 October 2026; original archive and checksum retained locally.', '', '| Assignment | Occurrences |', '|---|---:|']
    lines += [f'| {key} | {value:,} |' for key, value in sorted(statuses.items())]
    lines += ['', '| Level IV region intersecting Dangermond | Regional occurrences |', '|---|---:|']
    lines += [f'| {code}: {names[code]} | {region_counts[code]:,} |' for code in sorted(preserve_codes)]
    lines += ['', 'These are occurrences throughout the full ecoregions, not counts restricted to the preserve. All Level IV regions in the regional pool remain available for comparison. Points are matched directly to polygons with boundaries included; unmatched records retain blank codes. Multiple matches retain all codes without duplicating rows. No nearest-region assignment or coordinate-uncertainty buffer is used.', '', 'The count table summarizes each assigned region. The issues table lists unmatched, multiple and Level III disagreement cases. Metadata records source checksums, rules and software versions.']
    (OUT / 'level_iv_assignment_report.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(metadata, indent=2), flush=True)


if __name__ == '__main__':
    main()
