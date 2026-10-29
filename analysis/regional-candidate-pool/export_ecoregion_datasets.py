"""Export occurrence pools matching Dangermond's Level III and IV regions.

Level III: codes 6/85. Level IV: codes 6ap/85a. These are full regional
occurrence pools, not occurrences clipped to the preserve boundary.
"""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json
import shutil

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/regional-candidate-pool/gbif-vgv5ee'
SOURCE = OUT / 'species_identified_insect_records_v3.csv.gz'
FINAL = ROOT / 'data/final'
III = FINAL / 'dangermond_level_iii_matched_records.csv.gz'
IV = FINAL / 'dangermond_level_iv_matched_records.csv.gz'


def checksum(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    FINAL.mkdir(parents=True, exist_ok=True)
    iv_partial = IV.with_suffix('.gz.partial')
    counts = Counter()
    species = {'III': set(), 'IV': set()}
    codes_iii, codes_iv = Counter(), Counter()
    first = True
    columns = None
    with gzip.open(iv_partial, 'wt', encoding='utf-8', newline='', compresslevel=3) as target:
        for frame in pd.read_csv(SOURCE, dtype=str, keep_default_na=False, chunksize=25000):
            if columns is None:
                columns = list(frame.columns)
            match_iii = frame.analysis_ecoregion_l3_code.str.contains(r'(?:^|;)(?:6|85)(?:;|$)', regex=True)
            # Version 3 is already the Level III regional pool. Assert this
            # before making a byte-identical independent copy for that pool.
            assert match_iii.all(), 'Source includes records outside the intended Level III pool'
            match_iv = frame.analysis_ecoregion_l4_code.str.contains(r'(?:^|;)(?:6ap|85a)(?:;|$)', regex=True)
            selected = frame.loc[match_iv]
            counts['level_iii_records'] += len(frame)
            counts['level_iv_records'] += len(selected)
            species['III'].update(frame.resolved_species_name)
            species['IV'].update(selected.resolved_species_name)
            codes_iii.update(frame.analysis_ecoregion_l3_code)
            codes_iv.update(selected.analysis_ecoregion_l4_code)
            selected.to_csv(target, index=False, header=first)
            first = False
    assert counts['level_iii_records'] == json.loads((OUT / 'level_iv_assignment_metadata.json').read_text())['records']
    assert counts['level_iv_records'] > 0
    iv_partial.replace(IV)
    iii_partial = III.with_suffix('.gz.partial')
    shutil.copyfile(SOURCE, iii_partial)
    source_sha = checksum(SOURCE)
    assert checksum(iii_partial) == source_sha
    iii_partial.replace(III)
    rows = [
        {'dataset': 'Level III regional pool', 'codes': '6;85', 'occurrence_records': counts['level_iii_records'], 'distinct_resolved_species_names': len(species['III']), 'columns': len(columns), 'file': III.name},
        {'dataset': 'Level IV regional pool', 'codes': '6ap;85a', 'occurrence_records': counts['level_iv_records'], 'distinct_resolved_species_names': len(species['IV']), 'columns': len(columns), 'file': IV.name},
    ]
    pd.DataFrame(rows).to_csv(OUT / 'ecoregion_dataset_summary.csv', index=False)
    metadata = {
        'created_at': datetime.now(timezone.utc).isoformat(), 'source': str(SOURCE.relative_to(ROOT)),
        'source_sha256': source_sha, 'datasets': rows,
        'level_iii_label_counts': dict(codes_iii), 'level_iv_label_counts': dict(codes_iv),
        'level_iv_output_sha256': checksum(IV),
        'selection': 'Level III: any assigned code 6 or 85. Level IV: any assigned code 6ap or 85a. Semicolon-separated boundary labels supported; no occurrence duplicated.',
        'species_count_rule': 'Distinct resolved_species_name; subspecies rolled up to species. Reviewed names without COL XR keys remain included.',
        'scope': 'Full ecoregions that intersect Dangermond, not preserve-clipped records. The Level IV dataset is a subset of the Level III dataset; records may appear in both files.',
        'columns': columns,
        'provenance': 'All version 3 fields preserved, including source identifiers, scientific names, service diagnostics, common-name attribution and Level III/IV geography. Source remains unchanged. The Level III file is a verified byte-identical independent copy after checking all source rows meet the Level III criterion.',
    }
    (OUT / 'ecoregion_dataset_export_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(pd.DataFrame(rows).to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
