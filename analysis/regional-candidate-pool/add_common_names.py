"""Add attributed ESA common names to the species-only next-version table.

Uses ESA's unchanged public spreadsheet, parsed as OOXML with the Python
standard library. No genus-level common labels or fuzzy name matches.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import gzip
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile

import pandas as pd

from clean_species_identifications import canonical_input

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/regional-candidate-pool/gbif-vgv5ee'
RAW = ROOT / 'data/raw/common-names/esa/2026-10-27'
ESA = RAW / 'Common_names_list_7-2-26.xlsx'
SOURCE = OUT / 'species_identified_insect_records_taxonomy_resolved_clean.csv.gz'
TARGET = OUT / 'species_identified_insect_records_v2.csv.gz'
ESA_PAGE = 'https://entsoc.org/publications/common-names'
ESA_URL = json.loads((RAW / 'archive_manifest.json').read_text())['download_url']
NEW = ['proposed_common_name', 'common_name_source', 'common_name_source_url', 'common_name_source_scientific_name', 'common_name_match_type', 'common_name_retrieved_on']
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def read_esa():
    with zipfile.ZipFile(ESA) as archive:
        shared = [''.join(t.text or '' for t in si.findall('.//s:t', NS)) for si in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        root = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        records = []
        for row in root.findall('.//s:sheetData/s:row', NS):
            cells = {}
            for cell in row.findall('s:c', NS):
                column = re.sub(r'\d+', '', cell.get('r'))
                value = cell.find('s:v', NS)
                text = value.text or '' if value is not None else ''.join(t.text or '' for t in cell.findall('.//s:t', NS))
                if cell.get('t') == 's':
                    text = shared[int(text)]
                cells[column] = text.strip()
            common, genus, epithet = cells.get('A', ''), cells.get('E', ''), cells.get('F', '')
            if not common or not re.fullmatch(r'[A-Z][A-Za-z-]+', genus) or not re.fullmatch(r'[a-z][a-z-]+(?: [a-z][a-z-]+)?', epithet) or epithet in {'sp', 'spp', 'species'}:
                continue
            records.append({'scientific_name': genus + ' ' + epithet, 'common_name': common, 'source_scientific_name': cells.get('B', ''), 'order': cells.get('C', ''), 'family': cells.get('D', ''), 'notes': cells.get('H', ''), 'taxonomy_last_updated': cells.get('I', '')})
    return records


def main():
    esa_rows = read_esa()
    pd.DataFrame(esa_rows).to_csv(RAW / 'parsed_species_common_names.csv', index=False)
    esa = defaultdict(set)
    for row in esa_rows:
        esa[row['scientific_name']].add(row['common_name'])
    aliases = defaultdict(set)
    audit = pd.read_csv(OUT / 'taxonomy_name_resolution.csv', dtype=str, keep_default_na=False)
    for row in audit.to_dict('records'):
        species = row['resolved_species_name']
        if not species or not row['taxon_resolution_status'].startswith('resolved_'):
            continue
        original = canonical_input(row['scientificName'], 'SPECIES')
        if re.fullmatch(r'[A-Z][A-Za-z-]+ [a-z][a-z-]+', original):
            aliases[species].add(original)
        if re.fullmatch(r'[A-Z][A-Za-z-]+ [a-z][a-z-]+', row['resolved_taxon_name']):
            aliases[species].add(row['resolved_taxon_name'])
    with (ROOT / 'analysis/regional-candidate-pool/reviewed_taxonomic_corrections.csv').open() as f:
        for row in csv.DictReader(f):
            if row['synonym_or_alternative']:
                aliases[' '.join(row['resolved_name'].split()[:2])].add(row['synonym_or_alternative'])
    lookup = {}
    for taxon, species in set(zip(audit.resolved_taxon_name, audit.resolved_species_name)):
        if not taxon or not species:
            continue
        match_names = {taxon} if taxon in esa else {species} if species in esa else {name for name in aliases[species] if name in esa}
        common_names = sorted({common for name in match_names for common in esa[name]})
        method = 'exact_resolved_taxon' if taxon in esa else 'exact_resolved_species' if species in esa else 'approved_taxonomic_alias' if common_names else 'not_found_in_ESA'
        lookup[(taxon, species)] = dict(zip(NEW, ['; '.join(common_names), 'Entomological Society of America (ESA)' if common_names else '', ESA_URL if common_names else '', '; '.join(sorted(match_names)), method, '2026-10-27' if common_names else '']))
    counts = Counter()
    species_counts = Counter()
    resolution_counts = Counter()
    first = True
    partial = TARGET.with_suffix('.gz.partial')
    with gzip.open(partial, 'wt', encoding='utf-8', newline='', compresslevel=3) as target:
        for frame in pd.read_csv(SOURCE, dtype=str, keep_default_na=False, chunksize=25000):
            assert frame.resolved_species_name.ne('').all()
            assert frame.taxon_resolution_status.str.startswith('resolved_').all()
            assert frame.resolved_taxon_rank.isin(['SPECIES','SUBSPECIES','VARIETY','FORM','SUBVARIETY','SUBFORM']).all()
            addition = pd.DataFrame([lookup[key] for key in zip(frame.resolved_taxon_name, frame.resolved_species_name)], index=frame.index)
            counts['records'] += len(frame)
            counts['records_with_common_name'] += int(addition.proposed_common_name.ne('').sum())
            species_counts.update(zip(frame.resolved_taxon_name, frame.resolved_species_name))
            resolution_counts.update(frame.taxon_resolution_status)
            pd.concat([frame, addition], axis=1).to_csv(target, index=False, header=first)
            first = False
            if counts['records'] % 500000 == 0:
                print(f"Added ESA name fields to {counts['records']:,} records", flush=True)
    assert counts['records'] == json.loads((OUT / 'species_identification_cleanup_metadata.json').read_text())['counts']['retained_records']
    partial.replace(TARGET)
    rows = [{'resolved_taxon_name': key[0], 'resolved_species_name': key[1], **lookup[key], 'occurrence_records': count} for key, count in sorted(species_counts.items())]
    pd.DataFrame(rows).to_csv(OUT / 'species_common_name_lookup.csv', index=False)
    with SOURCE.open('rb') as source:
        source_sha = hashlib.file_digest(source, 'sha256').hexdigest()
    metadata = {'completed_at': datetime.now(timezone.utc).isoformat(), 'source_dataset': str(SOURCE.relative_to(ROOT)), 'source_sha256': source_sha, 'output': str(TARGET.relative_to(ROOT)), 'common_name_source': 'Entomological Society of America Common Names of Insects Database', 'source_page': ESA_PAGE, 'source_download_url': ESA_URL, 'source_file': str(ESA.relative_to(ROOT)), 'source_file_sha256': hashlib.sha256(ESA.read_bytes()).hexdigest(), 'source_file_label': 'Filename 7-2-26; internal heading Updated 3/4/25, retained as supplied.', 'source_retrieved_on': '2026-10-27', 'source_species_name_rows': len(esa_rows), 'counts': dict(counts), 'resolved_species_names': len({row['resolved_species_name'] for row in rows}), 'resolved_taxon_names': len(rows), 'taxon_names_with_common_name': sum(bool(row['proposed_common_name']) for row in rows), 'species_with_a_common_name_at_some_rank': len({row['resolved_species_name'] for row in rows if row['proposed_common_name']}), 'occurrence_records_by_resolution_status': dict(resolution_counts), 'match_rule': 'Exact resolved taxon name first, then exact parent species; otherwise exact ESA match to a binomial alias from the approved GBIF/COL XR crosswalk or explicit user synonym. Subspecies-only names are not generalized to the parent species. No fuzzy, genus or family name transfer. Multiple ESA names retained with semicolons. No source match leaves proposed_common_name blank.', 'coverage_note': 'ESA only for this version; BugGuide was not used. A blank means no match in this downloaded ESA list, not proof that no common name exists.', 'matching_service_provenance': 'All prior scientific-name match columns, original names, statuses, confidence, identifiers, request URLs and diagnostics are preserved. Full API responses remain cached locally.'}
    (OUT / 'common_name_enrichment_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(metadata, indent=2), flush=True)


if __name__ == '__main__':
    main()
