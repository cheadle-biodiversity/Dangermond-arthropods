"""Build identical regional schemas using the cutoff and user overrides.

Profile the unchanged full version 3 once, including its Level IV subset.
Replace only the two named exports; version 3 and full name audits remain.
"""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/regional-candidate-pool/gbif-vgv5ee'
SOURCE = OUT / 'species_identified_insect_records_v3.csv.gz'
FINAL = ROOT / 'data/final'
FILES = {'III': FINAL / 'dangermond_level_iii_matched_records.csv.gz', 'IV': FINAL / 'dangermond_level_iv_matched_records.csv.gz'}
CUTOFF_PERCENT = 70
ALWAYS_RETAIN = {'proposed_common_name', 'common_name_source', 'common_name_source_url', 'verbatimScientificName', 'resolved_taxon_name'}
RESTORE_FOR_SHARED_SCHEMA = {'collectionID', 'individualCount', 'preparations', 'samplingProtocol', 'county', 'locality', 'projectID'}
EXPLICIT_REMOVE = set('''acceptedNameUsageID publishingCountry lastInterpreted issue taxonomicIssue nonTaxonomicIssue mediaType hasCoordinate hasGeospatialIssues kingdomKey phylumKey classKey orderKey familyKey genusKey speciesKey protocol lastParsed lastCrawled repatriated isSequenced gbifRegion publishedByGbifRegion level0Gid level0Name level1Gid level1Name level2Gid level2Name taxon_resolution_diagnostics_json taxon_resolution_query_url taxon_resolution_retrieved_at taxon_resolution_checklist_key taxon_resolution_baseline_status common_name_source_scientific_name common_name_match_type common_name_retrieved_on'''.split())

# Replace alternative full taxon-name/resolution columns with the three
# user-selected fields. Classification (order/family/genus) and record IDs stay.
EXPLICIT_REMOVE |= {'scientificName', 'species', 'acceptedScientificName', 'genericName', 'specificEpithet', 'resolved_taxon_key', 'resolved_taxon_rank', 'resolved_species_name', 'resolved_species_key', 'analysis_ecoregion_l4_code', 'analysis_ecoregion_l4_name', 'analysis_ecoregion_l4_match_status'}
DESCRIPTION = 'taxon_resolution_description'
MATCH_INPUT = ['scientificName', 'taxonRank', 'order', 'family']


def resolution_description(row):
    labels = {'resolved_exact': 'Exact accepted-name match',
              'resolved_synonym': 'Synonym resolved to accepted name',
              'resolved_service_accepted': 'Service candidate accepted by user',
              'resolved_manual': 'User-reviewed resolution'}
    outcome = labels.get(row['taxon_resolution_status'], row['taxon_resolution_status'])
    match = row['taxon_resolution_automatic_match_type']
    confidence = row['taxon_resolution_automatic_confidence']
    parts = [outcome, 'GBIF Species Match v2 / Catalogue of Life XR',
             'Match type: ' + match, 'Confidence: ' + confidence,
             'Matched taxonomic status: ' + row['matched_taxonomic_status'],
             'Service input (GBIF-interpreted): ' + row['scientificName']]
    if row.get('taxon_resolution_note'):
        parts.append(row['taxon_resolution_note'])
    return '; '.join(parts)


def iv_mask(frame):
    return frame.analysis_ecoregion_l4_code.str.contains(r'(?:^|;)(?:6ap|85a)(?:;|$)', regex=True)


def main():
    FINAL.mkdir(parents=True, exist_ok=True)
    populated = {'III': Counter(), 'IV': Counter()}
    totals = Counter()
    with SOURCE.open('rb') as source:
        source_sha = hashlib.file_digest(source, 'sha256').hexdigest()
    columns = list(pd.read_csv(SOURCE, nrows=0).columns)
    profile_file = OUT / 'ecoregion_column_completeness.csv'
    metadata_file = OUT / 'ecoregion_column_pruning_metadata.json'
    reused = False
    if profile_file.exists() and metadata_file.exists():
        old = json.loads(metadata_file.read_text())
        if old.get('source_sha256') == source_sha:
            profile = pd.read_csv(profile_file, keep_default_na=False)
            profile = profile.loc[profile.column.isin(columns)]
            if all(set(profile.loc[profile.dataset_level.eq(level), 'column']) == set(columns) for level in FILES):
                for level in FILES:
                    rows = profile.loc[profile.dataset_level.eq(level)]
                    assert rows.total_records.nunique() == 1 and rows.column.nunique() == len(columns)
                    totals[level] = int(rows.total_records.iloc[0])
                    populated[level].update({r.column: int(r.nonblank_records) for r in rows.itertuples()})
                reused = True
                print('Reusing full-column completeness counts after verifying the unchanged source checksum.', flush=True)
    if not reused:
        for frame in pd.read_csv(SOURCE, dtype=str, keep_default_na=False, chunksize=25000):
            present = frame.apply(lambda col: col.str.strip().ne(''))
            selected = iv_mask(frame)
            populated['III'].update(present.sum().to_dict())
            populated['IV'].update(present.loc[selected].sum().to_dict())
            totals['III'] += len(frame)
            totals['IV'] += int(selected.sum())
            if totals['III'] % 500000 == 0:
                print(f"Profiled {totals['III']:,} regional records", flush=True)
    EXPLICIT_REMOVE.update(c for c in columns if c.startswith('taxon_resolution_'))
    assert EXPLICIT_REMOVE <= set(columns)
    audit = pd.read_csv(OUT / 'taxonomy_name_resolution.csv', dtype=str, keep_default_na=False)
    descriptions = {tuple(row[col] for col in MATCH_INPUT): resolution_description(row) for row in audit.to_dict('records')}
    common_schema = [column for column in columns if column not in EXPLICIT_REMOVE and (column in ALWAYS_RETAIN | RESTORE_FOR_SHARED_SCHEMA or any((totals[level] - populated[level][column]) * 100 < totals[level] * CUTOFF_PERCENT for level in FILES))]
    name_position = common_schema.index('verbatimScientificName')
    common_schema.remove('verbatimScientificName')
    common_schema.remove('resolved_taxon_name')
    common_schema[name_position:name_position] = ['verbatimScientificName', 'resolved_taxon_name', DESCRIPTION]
    retained = {level: common_schema.copy() for level in FILES}
    audit_rows = []
    for level in FILES:
        for column in columns:
            blank = totals[level] - populated[level][column]
            keep = column in common_schema
            reason = ('user_requested_removal' if column in EXPLICIT_REMOVE else
                      'user_requested_retained_fields' if column in ALWAYS_RETAIN else
                      'restored_for_shared_schema' if column in RESTORE_FOR_SHARED_SCHEMA else
                      'below_blank_cutoff' if blank * 100 < totals[level] * CUTOFF_PERCENT else
                      'shared_schema_kept_from_other_dataset' if keep else 'at_or_above_blank_cutoff')
            audit_rows.append({'dataset_level': level, 'column': column, 'total_records': totals[level], 'nonblank_records': populated[level][column], 'blank_records': blank, 'percent_blank': 100 * blank / totals[level], 'action': 'retained' if keep else 'removed', 'retention_reason': reason})
        audit_rows.append({'dataset_level': level, 'column': DESCRIPTION, 'total_records': totals[level], 'nonblank_records': totals[level], 'blank_records': 0, 'percent_blank': 0.0, 'action': 'retained', 'retention_reason': 'derived_readable_matching_description'})
        print(f"Level {level}: {len(retained[level])} retained, {sum(c not in retained[level] for c in columns)} source columns removed, one description added", flush=True)
    pd.DataFrame(audit_rows).to_csv(OUT / 'ecoregion_column_completeness.csv', index=False)
    # Read only the union of retained columns, plus the subset selector.
    needed = [c for c in columns if c in set(retained['III']) | set(retained['IV']) | {'analysis_ecoregion_l4_code', 'resolved_species_name', *MATCH_INPUT}]
    partials = {level: path.with_suffix('.gz.partial') for level,path in FILES.items()}
    first = True
    written = Counter()
    species = {'III': set(), 'IV': set()}
    with gzip.open(partials['III'], 'wt', encoding='utf-8', newline='', compresslevel=3) as iii, gzip.open(partials['IV'], 'wt', encoding='utf-8', newline='', compresslevel=3) as iv:
        for frame in pd.read_csv(SOURCE, usecols=needed, dtype=str, keep_default_na=False, chunksize=25000):
            frame[DESCRIPTION] = [descriptions[key] for key in frame[MATCH_INPUT].itertuples(index=False, name=None)]
            selected = frame.loc[iv_mask(frame)]
            frame[retained['III']].to_csv(iii, index=False, header=first)
            selected[retained['IV']].to_csv(iv, index=False, header=first)
            written['III'] += len(frame)
            written['IV'] += len(selected)
            species['III'].update(frame.resolved_species_name)
            species['IV'].update(selected.resolved_species_name)
            first = False
            if written['III'] % 500000 == 0:
                print(f"Wrote trimmed fields for {written['III']:,} records", flush=True)
    assert totals == written
    assert totals['III'] == 1408875 and totals['IV'] == 43555
    assert len(species['III']) == 13634 and len(species['IV']) == 2550
    for level in FILES:
        partials[level].replace(FILES[level])
    metadata = {'completed_at': datetime.now(timezone.utc).isoformat(), 'source': str(SOURCE.relative_to(ROOT)), 'source_sha256': source_sha, 'cutoff_percent_blank': CUTOFF_PERCENT, 'blank_definition': 'Empty or whitespace-only string; nonblank labels such as unknown, NA and null are not silently recoded.', 'rule': f'Use an identical schema for both datasets: union of columns below {CUTOFF_PERCENT}% blank in either pool plus explicitly restored columns and common name/source/URL. Explicit user deletions take precedence. Taxon-name/resolution fields are reduced to verbatimScientificName, resolved_taxon_name and a derived description; Level IV assignment columns are omitted after selecting records. No rows removed and no retained original values changed.', 'completeness_profile_reused_after_source_checksum_check': reused, 'always_retained_columns': sorted(ALWAYS_RETAIN), 'restored_for_shared_schema': sorted(RESTORE_FOR_SHARED_SCHEMA), 'explicit_removed_columns': sorted(EXPLICIT_REMOVE), 'identical_schema': True, 'derived_columns': {DESCRIPTION: 'Readable service outcome, provider, original API match type/confidence/status, GBIF-interpreted input name and user-review note. Based on full taxonomy_name_resolution.csv, not a fresh name query.'}, 'filtering_before_column_removal': 'Level IV 6ap/85a selection and species-count rollup use full version 3 internal fields before they are omitted from exports.', 'source_column_count': len(columns), 'datasets': {}, 'full_provenance': 'The full 266-column source v3 and taxonomy/common-name audit tables remain unchanged. Matching-service fields removed for sparsity remain available there.'}
    summary = []
    for level, path in FILES.items():
        with path.open('rb') as result:
            sha = hashlib.file_digest(result, 'sha256').hexdigest()
        metadata['datasets'][level] = {'file': str(path.relative_to(ROOT)), 'records': totals[level], 'distinct_resolved_species_names': len(species[level]), 'retained_column_count': len(retained[level]), 'removed_column_count': sum(c not in retained[level] for c in columns), 'derived_column_count': 1, 'retained_columns': retained[level], 'removed_columns': [c for c in columns if c not in retained[level]], 'sha256': sha}
        summary.append({'dataset': f'Level {level} regional pool', 'codes': '6;85' if level=='III' else '6ap;85a', 'occurrence_records': totals[level], 'distinct_resolved_species_names': len(species[level]), 'columns': len(retained[level]), 'file': path.name})
    (OUT / 'ecoregion_column_pruning_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    pd.DataFrame(summary).to_csv(OUT / 'ecoregion_dataset_summary.csv', index=False)
    export_file = OUT / 'ecoregion_dataset_export_metadata.json'
    if export_file.exists():
        old = json.loads(export_file.read_text())
        old['subsequent_column_pruning'] = {'metadata': 'ecoregion_column_pruning_metadata.json', 'note': 'This export manifest describes initial full-schema creation. Named export files were subsequently trimmed; use column-pruning metadata and current summary for their present schemas/checksums.'}
        export_file.write_text(json.dumps(old, indent=2) + '\n')
    column_lines = ['# Retained columns — identical Level III and Level IV schemas', '', f'{len(common_schema)} columns in each dataset. Explicit user removals override the 70% blank rule; common name, source and URL are retained.', '']
    column_lines += [f'- `{column}`' for column in common_schema]
    (OUT / 'retained_columns.md').write_text('\n'.join(column_lines) + '\n')
    print(pd.DataFrame(summary).to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
