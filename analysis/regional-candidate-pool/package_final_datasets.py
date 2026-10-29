"""Document and verify the two final, identical-schema regional datasets.

Run after export_ecoregion_datasets.py and trim_sparse_columns.py.
Datasets are produced directly in data/final; full source/audits stay in outputs.
"""
from datetime import datetime, timezone
from pathlib import Path
import csv
import gzip
import hashlib
import json
import shutil

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FINAL = ROOT / 'data/final'
AUDITS = ROOT / 'outputs/regional-candidate-pool/gbif-vgv5ee'
DEFINITIONS = Path(__file__).with_name('final_column_definitions.csv')
FILES = {'III': 'dangermond_level_iii_matched_records.csv.gz', 'IV': 'dangermond_level_iv_matched_records.csv.gz'}


def checksum(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    FINAL.mkdir(parents=True, exist_ok=True)
    definitions = pd.read_csv(DEFINITIONS, dtype=str, keep_default_na=False)
    assert definitions.column_name.is_unique and len(definitions) == 60
    prune = json.loads((AUDITS / 'ecoregion_column_pruning_metadata.json').read_text())
    datasets = []
    headers = []
    for level, filename in FILES.items():
        path = FINAL / filename
        with gzip.open(path, 'rt', encoding='utf-8', newline='') as source:
            columns = next(csv.reader(source))
        assert columns == definitions.column_name.tolist() == prune['datasets'][level]['retained_columns']
        headers.append(columns)
        digest = checksum(path)
        assert digest == prune['datasets'][level]['sha256']
        count = 0
        names = set()
        for frame in pd.read_csv(path, usecols=['gbifID', 'resolved_taxon_name'], dtype=str, keep_default_na=False, chunksize=100000):
            assert frame.gbifID.ne('').all() and frame.resolved_taxon_name.ne('').all()
            count += len(frame)
            names.update(frame.resolved_taxon_name)
        expected = prune['datasets'][level]
        assert count == expected['records']
        datasets.append({'file': filename, 'path': str(path.relative_to(ROOT)), 'ecoregion_level': level,
                         'selected_codes': ['6','85'] if level == 'III' else ['6ap','85a'],
                         'records': count, 'columns': len(columns),
                         'species_count_from_upstream_rollup': expected['distinct_resolved_species_names'],
                         'distinct_resolved_taxon_names_including_infraspecific': len(names),
                         'bytes': path.stat().st_size, 'sha256': digest})
    assert headers[0] == headers[1]
    shutil.copyfile(DEFINITIONS, FINAL / 'column_metadata.csv')
    dictionary = ['# Final dataset column descriptor', '',
                  'Shared schema for both final regional datasets: 60 columns in the order shown. All files are UTF-8, comma-delimited CSV with a header, standard double-quote escaping and gzip compression. Semantic types below describe intended interpretation; identifiers should be read as text. Blank/whitespace-only cells represent missing information, not zero.', '',
                  '| Column | Semantic type | Definition and interpretation |', '|---|---|---|']
    for row in definitions.to_dict('records'):
        text = row['description'] + ' Format/units: ' + row['units_or_format'] + '. ' + row['notes']
        dictionary.append(f"| `{row['column_name']}` | {row['semantic_data_type']} | {text.replace('|', ' / ')} |")
    dictionary += ['', 'The CSV companion also records provenance and the exact source-term URI taken from the GBIF archive schema where applicable. Field descriptions are project-specific summaries, informed by [Darwin Core](https://dwc.tdwg.org/terms/) and [GBIF download documentation](https://techdocs.gbif.org/en/data-use/download-formats).', '',
                   'Classification and legacy taxon keys remain from the original GBIF interpretation; only resolved_taxon_name and its description reflect the later name-resolution decisions. The original publisher name can be blank. Full machine-readable resolution diagnostics, species roll-ups and Level IV assignments remain in the upstream version 3 dataset and audit tables.']
    (FINAL / 'column_metadata.md').write_text('\n'.join(dictionary) + '\n')
    metadata = {'packaged_at_utc': datetime.now(timezone.utc).isoformat(),
                'title': 'Dangermond candidate insect occurrence pools: EPA Level III and IV',
                'source_doi': '10.15468/dl.vgv5ee', 'source_gbif_download_key': '0010070-260921141020460',
                'source_scope': 'Existing California Arthropoda snapshot, submitted 2026-09-28; filtered to named insects with coordinates and regional matches.',
                'datasets': datasets, 'shared_column_count': 60, 'column_descriptor': 'column_metadata.csv',
                'descriptor_sha256': checksum(FINAL / 'column_metadata.csv'),
                'format': {'compression': 'gzip', 'text_encoding': 'UTF-8', 'delimiter': ',', 'header': True,
                           'quote_character': '"', 'quote_escaping': 'doubled quote',
                           'missing_values': 'Empty or whitespace-only strings; literal NA/unknown labels not automatically recoded.'},
                'selection': 'Level III includes codes 6/85. Level IV includes 6ap/85a. Full matching regions, not clipped to Dangermond. Level IV is a subset of Level III; the same occurrence can appear in both files.',
                'geographic_interpretation': 'Coordinates treated as WGS84/EPSG:4326 points; boundaries included, no uncertainty buffering or nearest-region assignment. Level IV selection was applied before Level IV columns were omitted.',
                'taxonomy': 'GBIF Species Match API v2 with COL XR checklist 7ddf754f-d193-4cc9-b351-99906754a03b; user approved named species-level service candidates and twelve specific corrections. Preserve original publisher name and readable match description. Original classification and legacy GBIF taxon IDs were not recalculated.',
                'species_count_method': 'Upstream distinct resolved_species_name, rolling subspecies to species and including reviewed names without COL XR keys. That internal roll-up column is not retained here; distinct resolved_taxon_name can include subspecies and is not the same richness statistic.',
                'common_names': 'ESA Common Names of Insects spreadsheet retrieved 2026-10-27; exact taxon/parent-species or approved-binomial-alias matching. No BugGuide names used. Unsupported names left blank; subspecies-only names not generalized.',
                'column_selection': 'Identical schema after a 70% blank screening rule, shared-field restorations, protected common-name fields and explicit user deletions; one readable matching-description column derived. Final simplification changed columns only, not records.',
                'record_handling': 'No additional final-stage deduplication, date, coordinate-uncertainty, conservation-status or BOLD eligibility filter. BOLD eligibility and ecological screening remain pending for subsequent analyses.',
                'rights': 'Source record licenses and rights holders remain in their columns. Third-party data are not relicensed by this package.',
                'upstream_full_dataset': 'outputs/regional-candidate-pool/gbif-vgv5ee/species_identified_insect_records_v3.csv.gz',
                'upstream_pruning_metadata': 'outputs/regional-candidate-pool/gbif-vgv5ee/ecoregion_column_pruning_metadata.json',
                'reproduction_script': 'analysis/regional-candidate-pool/package_final_datasets.py',
                'references': ['https://doi.org/10.15468/dl.vgv5ee', 'https://dwc.tdwg.org/terms/', 'https://techdocs.gbif.org/en/data-use/download-formats', 'https://techdocs.gbif.org/en/data-processing/taxonomy-interpretation', 'https://www.epa.gov/eco-research/ecoregion-download-files-region', 'https://entsoc.org/publications/common-names']}
    (FINAL / 'dataset_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    readme = ['# Final regional insect occurrence datasets', '',
              '| File | Ecoregion codes | Occurrences | Species (upstream roll-up) | Columns |',
              '|---|---|---:|---:|---:|']
    for entry in datasets:
        readme.append(f"| [{entry['file']}]({entry['file']}) | {', '.join(entry['selected_codes'])} | {entry['records']:,} | {entry['species_count_from_upstream_rollup']:,} | {entry['columns']} |")
    readme += ['', 'These are full regional occurrence pools, not records restricted to Dangermond Preserve. The Level IV dataset is a subset of the Level III dataset, so the files overlap. Regions 6ap (Solomon-Purisima-Santa Ynez Hills) and 85a (Santa Barbara Coastal Plain and Terraces) intersect the preserve. Level IV assignment columns were deliberately removed after selecting those records; the Level III code/name remain.', '',
               '- [Column descriptor — readable](column_metadata.md)',
               '- [Column descriptor — CSV](column_metadata.csv)',
               '- [Dataset provenance, counts and SHA-256 checksums](dataset_metadata.json)', '',
               'Both files have the same 60-column schema. Each is a gzip-compressed, UTF-8 CSV with a header; read identifier fields as text. Blank values are not zero. Original names, final resolved names and match descriptions are retained. Original GBIF classification and taxon keys may differ from the subsequently resolved name. Species counts above use the upstream species-level roll-up; do not substitute a count of distinct resolved_taxon_name because that field can retain subspecies.', '',
               'Source: [GBIF download 10.15468/dl.vgv5ee](https://doi.org/10.15468/dl.vgv5ee). Scientific-name matching used GBIF / Catalogue of Life XR plus user-reviewed decisions; common names used the [ESA list](https://entsoc.org/publications/common-names). Record-level licenses and rights holders remain applicable. BOLD eligibility and ecological screening remain future analysis steps.', '',
               'The large compressed files are ignored by Git; descriptors and manifests are versioned. Full 266-column data and audit tables remain in outputs/regional-candidate-pool/gbif-vgv5ee/. These final files were relocated byte-for-byte from the working exports.', '',
               'Reproduce from repository root:', '', '```bash',
               'python3 analysis/regional-candidate-pool/export_ecoregion_datasets.py',
               'python3 analysis/regional-candidate-pool/trim_sparse_columns.py',
               'python3 analysis/regional-candidate-pool/package_final_datasets.py', '```', '',
               'Full filtering, source and name-resolution methods: [workflow README](../../analysis/regional-candidate-pool/README.md).']
    (FINAL / 'README.md').write_text('\n'.join(readme) + '\n')
    print(pd.DataFrame(datasets)[['file','records','columns','bytes']].to_string(index=False), flush=True)
    print('Column descriptors cover every shared field; dataset checksums and record counts verified.', flush=True)


if __name__ == '__main__':
    main()
