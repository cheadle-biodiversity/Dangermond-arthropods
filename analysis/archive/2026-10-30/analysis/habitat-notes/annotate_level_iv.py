"""First-pass habitat evidence for the two Level IV species checklists.

Map intersections describe occurrence locations, never species specialization.
Source downloads are retained separately in data/raw/habitat/2026-10-27.
"""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw/habitat/2026-10-27'
OUT = ROOT / 'outputs/habitat-notes/2026-10-27'
FINAL = OUT / 'archived-annotations'
UPSTREAM = ROOT / 'outputs/regional-candidate-pool/gbif-vgv5ee/species_identified_insect_records_v3.csv.gz'
FIELDS = ['gbifID', 'resolved_species_name', 'analysis_ecoregion_l4_code', 'habitat',
          'fieldNotes', 'eventRemarks', 'occurrenceRemarks', 'associatedTaxa', 'lifeStage']


def overlay(records, polygons, attributes, prefix):
    """Boundary-inclusive point match, with conservative uncertainty check."""
    polys = polygons.to_crs(26910).reset_index(drop=True)
    invalid = ~polys.is_valid
    polys.loc[invalid, 'geometry'] = polys.loc[invalid, 'geometry'].make_valid()
    points = gpd.GeoSeries(gpd.points_from_xy(records.decimalLongitude.astype(float),
                                           records.decimalLatitude.astype(float)), crs=4326).to_crs(26910)
    pi, gi = shapely.STRtree(polys.geometry.to_numpy()).query(points.to_numpy(), predicate='covered_by')
    hits = np.bincount(pi, minlength=len(records))
    records[prefix + '_match'] = np.where(hits == 0, 'outside mapped polygons',
                                        np.where(hits == 1, 'single polygon', 'multiple polygons'))
    for name in attributes:
        records[prefix + '_' + name] = ''
    records[prefix + '_uncertainty_check'] = 'not applicable'
    single = hits[pi] == 1
    sp, sg = pi[single], gi[single]
    for name in attributes:
        records.loc[sp, prefix + '_' + name] = polys.iloc[sg][name].fillna('').astype(str).to_numpy()
    radius = pd.to_numeric(records.coordinateUncertaintyInMeters, errors='coerce').to_numpy()[sp]
    distance = shapely.distance(points.to_numpy()[sp], shapely.boundary(polys.geometry.to_numpy()[sg]))
    # Darwin Core does not support zero as a known coordinate uncertainty.
    known = np.isfinite(radius) & (radius > 0)
    status = np.where(~known, 'uncertainty unknown',
                      np.where(radius < distance, 'reported radius inside polygon', 'reported radius reaches boundary'))
    records.loc[sp, prefix + '_uncertainty_check'] = status
    return {'features': len(polys), 'invalid_geometries_repaired': int(invalid.sum()),
            'record_matches': records[prefix + '_match'].value_counts().to_dict(),
            'uncertainty': records[prefix + '_uncertainty_check'].value_counts().to_dict()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FINAL.mkdir(parents=True, exist_ok=True)
    records = pd.read_csv(ROOT / 'data/final/dangermond_level_iv_matched_records.csv.gz', dtype=str, keep_default_na=False)
    assert len(records) == 43555 and records.gbifID.is_unique
    cache = OUT / 'regional_record_context.csv.gz'
    if not cache.exists():
        selected = set(records.gbifID)
        parts = []
        for frame in pd.read_csv(UPSTREAM, usecols=FIELDS, dtype=str, keep_default_na=False, chunksize=50000):
            hit = frame[frame.gbifID.isin(selected)]
            if len(hit):
                parts.append(hit)
        context = pd.concat(parts, ignore_index=True)
        assert len(context) == len(records) and context.gbifID.is_unique
        context.to_csv(cache, index=False)
    context = pd.read_csv(cache, dtype=str, keep_default_na=False)
    records = records.drop(columns=['lifeStage']).merge(context, on='gbifID', how='left', validate='one_to_one')
    assert records.resolved_species_name.notna().all()
    vegetation = gpd.read_file(RAW / 'cdfw_extracted/ds2957.gdb')
    geology = gpd.read_file(RAW / 'usgs_extracted/SMPtC_Shapefiles/MapUnitPolys.shp')
    stats = {'vegetation': overlay(records, vegetation, ['MapClass', 'MCVName', 'CalVegType'], 'vegetation'),
             'geology': overlay(records, geology, ['MapUnit', 'Label'], 'geology')}
    # Do not use the broad CalVegType='Dune': it also includes Coastal Bluffs.
    dune_classes = {'Sand Dune Sedge Swaths', 'Silver Dune Lupine - Mock Heather Scrub'}
    records['mapped_dune_vegetation'] = records.vegetation_MapClass.isin(dune_classes)
    records['mapped_coastal_strand'] = records.vegetation_MapClass.eq('Coastal Strand')
    records['mapped_beach_and_dune_sand'] = records.geology_MapUnit.eq('Qey')
    records['mapped_old_dune_substrate'] = records.geology_MapUnit.eq('Qeo')
    # Locality names alone are explicitly weaker evidence; e.g. a town called Beach.
    for label, pattern in [('dune', r'\b(?:back[ -]?dunes?|fore[ -]?dunes?|dunes?)\b'),
                           ('beach_wrack', r'\b(?:beach|beaches|wrack|seaweed|kelp)\b')]:
        records['publisher_habitat_mentions_' + label] = records.habitat.str.contains(pattern, case=False, regex=True)
        records['locality_mentions_' + label] = (records.locality + ' ' + records.verbatimLocality).str.contains(pattern, case=False, regex=True)
    records['inside_preserve'] = shapely.covered_by(
        shapely.points(records.decimalLongitude.astype(float), records.decimalLatitude.astype(float)),
        gpd.read_file(ROOT / 'analysis/reference-data/jldp_boundary.geojson').to_crs(4326).geometry.union_all())
    # Add local field descriptions through the existing, reviewed name crosswalk.
    # These records establish site evidence, not extra regional GBIF counts.
    local = pd.read_csv(ROOT / 'data/raw/ecdysis/extracted/SymbOutput_2026-10-26_124013_DwC-A/occurrences.csv',
                        encoding='ISO-8859-1', dtype=str, keep_default_na=False)
    crosswalk = pd.read_csv(ROOT / 'data/final/checklists/preserve_occurrence_evidence.csv', dtype=str, keep_default_na=False)
    crosswalk = crosswalk[crosswalk.source.eq('Ecdysis local survey')][['record_id', 'resolved_species_name', 'name_support']]
    local = local.merge(crosswalk, left_on='id', right_on='record_id', how='inner', validate='one_to_one')
    local['site_context'] = np.select([
        local.locality.str.contains(r'\bper(?:ko|cos|kos|co)[\W_]*s?\s*beach\b', case=False, regex=True),
        (local.locality + ' ' + local.habitat).str.contains(r'\bback[ -]?dunes?\b', case=False, regex=True),
        (local.locality + ' ' + local.habitat).str.contains(r'\bbeach\b|\bwrack\b', case=False, regex=True)],
        ["Perko's Beach", 'backdune (field description)', 'other beach/wrack locality'], default='other/unspecified')
    assert pd.to_numeric(local.decimalLatitude, errors='coerce').notna().all()
    assert pd.to_numeric(local.decimalLongitude, errors='coerce').notna().all()
    stats['local_vegetation'] = overlay(local, vegetation, ['MapClass', 'MCVName', 'CalVegType'], 'vegetation')
    stats['local_geology'] = overlay(local, geology, ['MapUnit', 'Label'], 'geology')
    local.to_csv(OUT / 'ecdysis_habitat_evidence.csv', index=False)
    local_groups = {name: group for name, group in local.groupby('resolved_species_name')}
    review = pd.read_csv(Path(__file__).with_name('reviewed_species_notes.csv'), dtype=str, keep_default_na=False).set_index('resolved_scientific_name')
    summaries = []
    for code in ['6ap', '85a']:
        checklist = pd.read_csv(ROOT / f'data/final/checklists/checklist_level_iv_{code}.csv', dtype=str, keep_default_na=False)
        region = records[records.analysis_ecoregion_l4_code.eq(code)]
        assert len(region) == int(checklist.occurrence_count.astype(int).sum())
        grouped = {name: group for name, group in region.groupby('resolved_species_name')}
        enriched = []
        for row in checklist.to_dict('records'):
            name = row['resolved_scientific_name']
            group = grouped[name]
            assert len(group) == int(row['occurrence_count'])
            categories = [('mapped_dune_vegetation', 'mapped dune vegetation'),
                          ('mapped_coastal_strand', 'mapped coastal strand'),
                          ('mapped_beach_and_dune_sand', 'USGS Qey beach/dune substrate'),
                          ('mapped_old_dune_substrate', 'USGS Qeo old dune substrate')]
            notes = []
            for key, label in categories:
                n = int(group[key].sum())
                row[key + '_records'] = n
                if n:
                    prefix = 'vegetation' if key in ['mapped_dune_vegetation', 'mapped_coastal_strand'] else 'geology'
                    secure = int((group[key] & group[prefix + '_uncertainty_check'].eq('reported radius inside polygon')).sum())
                    notes.append(f'{label}: {n} records ({secure} with reported uncertainty radius inside the matched polygon)')
            row['vegetation_mapped_records'] = int(group.vegetation_match.eq('single polygon').sum())
            row['geology_mapped_records'] = int(group.geology_match.eq('single polygon').sum())
            row['geology_unit_names'] = ', '.join(sorted(set(group.loc[
                group.geology_match.eq('single polygon') & group.geology_Label.ne(''), 'geology_Label'])))
            row['mapped_vegetation_classes'] = '; '.join(f'{k}: {v}' for k, v in Counter(group.loc[group.vegetation_MapClass.ne(''), 'vegetation_MapClass']).most_common())
            row['publisher_habitat_notes'] = ' | '.join(sorted(set(group.loc[group.habitat.ne(''), 'habitat'])))
            row['publisher_dune_habitat_records'] = int(group.publisher_habitat_mentions_dune.sum())
            row['publisher_beach_wrack_habitat_records'] = int(group.publisher_habitat_mentions_beach_wrack.sum())
            row['habitat_notes'] = '; '.join(notes)
            row['habitat_interpretation'] = 'Occurrence-location evidence; does not establish habitat specialization' if notes else ''
            local_group = local_groups.get(name)
            row['ecdysis_local_records'] = 0 if local_group is None else len(local_group)
            row['ecdysis_site_contexts'] = '' if local_group is None else '; '.join(f'{k}: {v}' for k, v in Counter(local_group.site_context).most_common())
            row['ecdysis_field_habitat_notes'] = '' if local_group is None else ' | '.join(sorted(set(local_group.loc[local_group.habitat.ne(''), 'habitat'])))
            row['ecdysis_mapped_vegetation_classes'] = '' if local_group is None else '; '.join(f'{k}: {v}' for k, v in Counter(local_group.loc[local_group.vegetation_MapClass.ne(''), 'vegetation_MapClass']).most_common())
            row['published_habitat_association'] = ''
            row['life_history_sources'] = ''
            row['literature_review_status'] = 'not reviewed'
            row['habitat_map_sources'] = ('https://filelib.wildlife.ca.gov/public/BDB/GIS/BIOS/metadata/DS2957.html; https://doi.org/10.5066/P9FU7SJL') if row['vegetation_mapped_records'] or row['geology_mapped_records'] else ''
            if name in review.index:
                item = review.loc[name]
                row['published_habitat_association'] = item.published_habitat_association
                row['life_history_notes'] = item.life_history_notes
                row['life_history_sources'] = item.sources
                row['literature_review_status'] = item.review_status
            enriched.append(row)
        result = pd.DataFrame(enriched)
        result.to_csv(FINAL / f'checklist_level_iv_{code}_habitat_notes.csv', index=False)
        summaries.append({'level_iv_code': code, 'species': len(result), 'records': len(region),
                          'species_with_regional_priority_map_evidence': int(result.habitat_notes.ne('').sum()),
                          'species_with_any_vegetation_match': int(result.vegetation_mapped_records.gt(0).sum()),
                          'species_with_publisher_habitat': int(result.publisher_habitat_notes.ne('').sum()),
                          'species_with_publisher_dune_habitat': int(result.publisher_dune_habitat_records.gt(0).sum()),
                          'species_with_publisher_beach_wrack_habitat': int(result.publisher_beach_wrack_habitat_records.gt(0).sum()),
                          'species_with_ecdysis_field_habitat': int(result.ecdysis_field_habitat_notes.ne('').sum()),
                          'species_with_literature_notes': int(result.life_history_notes.ne('').sum())})
    records.to_csv(OUT / 'occurrence_habitat_evidence.csv.gz', index=False)
    pd.DataFrame(summaries).to_csv(FINAL / 'habitat_annotation_summary.csv', index=False)
    stats['checklists'] = summaries
    stats['unique_species'] = records.resolved_species_name.nunique()
    stats['unique_species_with_publisher_habitat'] = records.loc[records.habitat.ne(''), 'resolved_species_name'].nunique()
    stats['unique_species_with_publisher_dune_habitat'] = records.loc[records.publisher_habitat_mentions_dune, 'resolved_species_name'].nunique()
    stats['unique_species_with_publisher_beach_wrack_habitat'] = records.loc[records.publisher_habitat_mentions_beach_wrack, 'resolved_species_name'].nunique()
    candidates = set(records.resolved_species_name)
    stats['candidate_species_with_ecdysis_evidence'] = len(set(local.resolved_species_name) & candidates)
    stats['candidate_species_with_literature_notes'] = len(set(review.index) & candidates)
    stats['ecdysis_records_mapped_to_species'] = len(local)
    stats['ecdysis_site_context_records'] = local.site_context.value_counts().to_dict()
    stats['ecdysis_named_species'] = local.resolved_species_name.nunique()
    stats['unique_species_with_priority_map_evidence'] = records.loc[records[['mapped_dune_vegetation', 'mapped_coastal_strand', 'mapped_beach_and_dune_sand', 'mapped_old_dune_substrate']].any(axis=1), 'resolved_species_name'].nunique()
    stats['map_category_records'] = {key: int(records[key].sum()) for key in ['mapped_dune_vegetation', 'mapped_coastal_strand', 'mapped_beach_and_dune_sand', 'mapped_old_dune_substrate']}
    stats['record_count'] = len(records)
    stats['created_at_utc'] = datetime.now(timezone.utc).isoformat()
    stats['checksums_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(FINAL.glob('*.csv'))}
    (FINAL / 'habitat_annotation_metadata.json').write_text(json.dumps(stats, indent=2) + '\n')
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    main()
