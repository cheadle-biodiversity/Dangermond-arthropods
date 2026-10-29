"""Exclude genus/placeholder identifications and list remaining name proposals.

The original resolved dataset remains unchanged. This step excludes
genus/placeholder and unresolved higher-taxon matches; no API calls are made.
"""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/regional-candidate-pool/gbif-vgv5ee'
SOURCE = OUT / 'species_identified_insect_records_taxonomy_resolved.csv.gz'
TARGET = OUT / 'species_identified_insect_records_taxonomy_resolved_clean.csv.gz'
INPUT = ['scientificName', 'taxonRank', 'order', 'family']
PLACEHOLDER = r'\b(?:sp|spp|spec|species|indet|unidentified|unknown|morphospecies)\b|\bBOLD\s*:'
GROUP = r'\b(?:group|complex|aggregate|agg)\b'
UNINOMIAL = r'[A-Z][A-Za-z-]+(?:\s+\([A-Z][A-Za-z-]+\))?'


def exclusion_reason(frame):
    # Prefer the actual supplied scientific name. A standalone 'sp.' in a
    # secondary label does not negate a named species in that primary field.
    original = frame.verbatimScientificName.str.strip()
    original = original.mask(original.eq(''), frame.verbatimIdentification.str.strip())
    original = original.mask(original.eq(''), frame.scientificName.str.strip())
    # Parenthetical subgenera/species-group placements do not negate a
    # named epithet, e.g. Nomada (erigeronis group) crotchii.
    check = original.str.replace(r'\([^)]*\)', '', regex=True).str.replace(r'\s+', ' ', regex=True).str.strip()
    reason = pd.Series('', index=frame.index)
    reason.loc[check.str.fullmatch(UNINOMIAL, na=False)] = 'genus_or_higher_uninomial'
    reason.loc[check.str.contains(PLACEHOLDER, case=False, regex=True)] = 'unnamed_species_placeholder'
    reason.loc[check.str.contains(GROUP, case=False, regex=True)] = 'species_group_or_complex'
    reason.loc[frame.taxonRank.str.upper().isin(['GENUS', 'SUBGENUS'])] = 'genus_rank'
    if 'resolved_taxon_name' in frame:
        species_resolved = frame.taxon_resolution_status.str.startswith('resolved_') & frame.resolved_taxon_name.ne('') & frame.resolved_taxon_rank.isin(['SPECIES', 'SUBSPECIES', 'VARIETY', 'FORM', 'SUBVARIETY', 'SUBFORM'])
        reason.loc[reason.eq('') & ~species_resolved] = 'no_species_level_resolution'
    return original, reason


def canonical_input(name, rank):
    name = re.sub(r'\s+\([A-Z][A-Za-z-]+\)', '', name)
    match = re.match(r'^([A-Z][A-Za-z-]+\s+[a-z][a-z-]+)', name)
    if not match:
        return name
    canonical = match.group(1)
    if rank in {'SUBSPECIES', 'VARIETY', 'FORM'}:
        tail = name[match.end():]
        finer = re.match(r'\s+(?:(?:var|f)\.\s+)?([a-z][a-z-]+)\b', tail)
        if finer:
            canonical += ' ' + finer.group(1)
    return canonical


def main():
    counts = Counter()
    removed = Counter()
    retained_names = Counter()
    retained_status = Counter()
    first = True
    partial = TARGET.with_suffix('.gz.partial')
    with gzip.open(partial, 'wt', encoding='utf-8', newline='', compresslevel=3) as target:
        for frame in pd.read_csv(SOURCE, dtype=str, keep_default_na=False, chunksize=25000):
            original, reason = exclusion_reason(frame)
            reject = reason.ne('')
            counts['input_records'] += len(frame)
            counts['removed_records'] += int(reject.sum())
            removed.update(zip(original[reject], frame.loc[reject, 'scientificName'], reason[reject]))
            clean = frame.loc[~reject]
            counts['retained_records'] += len(clean)
            retained_names.update(clean[INPUT].itertuples(index=False, name=None))
            retained_status.update(clean.taxon_resolution_status)
            clean.to_csv(target, index=False, header=first)
            first = False
            if counts['input_records'] % 500000 == 0:
                print(f"Read {counts['input_records']:,}; removed {counts['removed_records']:,}", flush=True)
    assert counts['input_records'] == 1417629
    assert counts['input_records'] == counts['retained_records'] + counts['removed_records']
    partial.replace(TARGET)
    pd.DataFrame([{'original_identification': key[0], 'gbif_interpreted_name': key[1], 'exclusion_reason': key[2], 'records': value} for key, value in sorted(removed.items())]).to_csv(OUT / 'excluded_genus_placeholder_identifications.csv', index=False)
    table = pd.read_csv(OUT / 'taxonomy_name_resolution.csv', dtype=str, keep_default_na=False)
    table['occurrence_records'] = [retained_names.get(tuple(row), 0) for row in table[INPUT].itertuples(index=False, name=None)]
    review = table.loc[table.occurrence_records.gt(0) & ~table.taxon_resolution_status.str.startswith('resolved_')].copy()
    review.to_csv(OUT / 'taxonomy_names_for_review_clean.csv', index=False)
    cached = {}
    with (OUT / 'taxonomy_api_cache.jsonl').open() as f:
        for line in f:
            item = json.loads(line)
            cached[tuple(item['input'])] = item.get('response', {})
    proposals = Counter()
    provenance = {}
    reasons = {}
    no_species_candidate = 0
    unchanged = 0
    for row in review.to_dict('records'):
        response = cached[tuple(row[col] for col in INPUT)]
        accepted = response.get('acceptedUsage') or response.get('usage', {})
        if accepted.get('rank') not in {'SPECIES', 'SUBSPECIES', 'VARIETY', 'FORM'}:
            no_species_candidate += row['occurrence_records']
            continue
        original = canonical_input(row['scientificName'], row['taxonRank'])
        candidate = row['candidate_taxon_name']
        if not candidate or original == candidate:
            unchanged += row['occurrence_records']
            continue
        key = (original, candidate)
        proposals[key] += row['occurrence_records']
        provenance.setdefault(key, set()).add(row['scientificName'])
        reasons.setdefault(key, set()).add(row['taxon_resolution_status'])
    rows = [{'original_name': k[0], 'proposed_correction': k[1], 'review_reason': '; '.join(sorted(reasons[k])), 'occurrence_records': v, 'original_scientific_names': '; '.join(sorted(provenance[k]))} for k, v in sorted(proposals.items())]
    pd.DataFrame(rows, columns=['original_name','proposed_correction','review_reason','occurrence_records','original_scientific_names']).to_csv(OUT / 'original_name_proposed_correction.csv', index=False)
    lines = ['# Original name — proposed correction', '', 'Current policy: all service-returned species-level candidates have been accepted by the user. Genus-only/higher matches are excluded from this version of the dataset. No species-level candidates remain awaiting approval.', '']
    lines += [f"- *{row['original_name']}* — *{row['proposed_correction']}*" for row in rows]
    (OUT / 'original_name_proposed_correction.md').write_text('\n'.join(lines) + '\n')
    changed = Counter()
    for row in table.loc[table.occurrence_records.gt(0)].to_dict('records'):
        original = canonical_input(row['scientificName'], row['taxonRank'])
        if row['resolved_taxon_name'] and original != row['resolved_taxon_name']:
            changed[(original, row['resolved_taxon_name'], row['taxon_resolution_status'])] += row['occurrence_records']
    changes = [{'original_name': k[0], 'accepted_name': k[1], 'acceptance_status': k[2], 'occurrence_records': v} for k,v in sorted(changed.items())]
    pd.DataFrame(changes, columns=['original_name','accepted_name','acceptance_status','occurrence_records']).to_csv(OUT / 'accepted_name_changes.csv', index=False)
    (OUT / 'accepted_name_changes.md').write_text('# Accepted name changes\n\nUser-approved service results and reviewed taxonomic decisions. Original diagnostics remain in the name audit and occurrence columns.\n\n' + '\n'.join(f"- *{r['original_name']}* — *{r['accepted_name']}*" for r in changes) + '\n')
    with SOURCE.open('rb') as source:
        source_sha = hashlib.file_digest(source, 'sha256').hexdigest()
    metadata = {'completed_at': datetime.now(timezone.utc).isoformat(), 'source': str(SOURCE.relative_to(ROOT)), 'source_sha256': source_sha, 'output': str(TARGET.relative_to(ROOT)), 'counts': dict(counts), 'retained_records_by_resolution_status': dict(retained_status), 'remaining_review_records': sum(v for k, v in retained_status.items() if not k.startswith('resolved_')), 'proposed_name_pairs': len(rows), 'review_occurrences_with_higher_taxon_candidate': no_species_candidate, 'review_occurrences_with_unchanged_species_candidate': unchanged, 'name_source_precedence': 'verbatimScientificName; if blank verbatimIdentification; if blank scientificName', 'exclusion_patterns': {'placeholders': PLACEHOLDER, 'group_complex': GROUP, 'uninomial': UNINOMIAL}, 'notes': 'Exclude original genus/placeholder identifications and records lacking an accepted species-level resolution, including service matches only to genus or higher. This exclusion does not assert that the original species identification was wrong. Standalone sp. in a secondary field does not override a binomial primary name. All retained source columns unchanged. All named species-level service results are user-approved. Genus-only/higher service matches are excluded from this version. Previous source and audit files retained; use the clean output for current work.'}
    (OUT / 'species_identification_cleanup_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(metadata, indent=2), flush=True)


if __name__ == '__main__':
    main()
