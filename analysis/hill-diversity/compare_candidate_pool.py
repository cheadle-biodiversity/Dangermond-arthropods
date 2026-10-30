"""Empirical Ecdysis insect Hill numbers and Level IV candidate overlap.

No habitat filtering, candidate weighting, unseen-richness estimation or iNEXT.
Unreconciled species-level names remain as explicit provisional analysis units.
"""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import math
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/hill-diversity/2026-10-27-insects'
ECDYSIS = ROOT / 'data/raw/ecdysis/extracted/SymbOutput_2026-10-26_124013_DwC-A/occurrences.csv'
CHECKLISTS = ROOT / 'data/final/checklists'
REVIEWED = Path(__file__).with_name('reviewed_ecdysis_names.csv')


def hill(names):
    counts = Counter(names)
    n = sum(counts.values())
    p = [v / n for v in counts.values()]
    return {'records': n, 'q0': len(counts),
            'q1': math.exp(-sum(v * math.log(v) for v in p)),
            'q2': 1 / sum(v * v for v in p)}


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    local = pd.read_csv(ECDYSIS, encoding='ISO-8859-1', dtype=str, keep_default_na=False)
    assert len(local) == 459 and local.id.is_unique and local.occurrenceID.is_unique
    insects = local[local['class'].eq('Insecta')].copy()
    rank_ok = insects.taxonRank.str.casefold().isin(['species', 'subspecies', 'variety', 'form'])
    named = insects[rank_ok].copy()
    evidence = pd.read_csv(CHECKLISTS / 'preserve_occurrence_evidence.csv', dtype=str, keep_default_na=False)
    mapping = evidence[evidence.source.eq('Ecdysis local survey')][['record_id', 'resolved_species_name', 'name_support']]
    named = named.merge(mapping, left_on='id', right_on='record_id', how='left', validate='one_to_one')
    named['service_crosswalk_available'] = named.resolved_species_name.notna()
    named['user_reviewed_original_name'] = False
    approved = pd.read_csv(REVIEWED, dtype=str, keep_default_na=False).set_index('original_name')
    for name, row in approved.iterrows():
        hit = named.resolved_species_name.isna() & named.scientificName.eq(name)
        named.loc[hit, 'resolved_species_name'] = row.approved_species_name
        named.loc[hit, 'name_support'] = row.review_source + '; ' + row.reviewed_on
        named.loc[hit, 'user_reviewed_original_name'] = True
    named['name_reconciled'] = named.resolved_species_name.notna()
    # The five unreconciled original names are already binomials; no invented
    # accepted name or arbitrary genus-to-species assignment is made.
    assert named.loc[~named.name_reconciled, 'scientificName'].str.split().str.len().eq(2).all()
    named['analysis_taxon_name'] = named.resolved_species_name.fillna(named.scientificName)
    named['analysis_name_status'] = named.name_reconciled.map({True: 'approved species-name crosswalk', False: 'original species-level name; reconciliation pending'})
    named.loc[named.user_reviewed_original_name, 'analysis_name_status'] = 'original name accepted by user review; no service species match'
    named = named.fillna('')
    pools = {}
    paths = [ECDYSIS, CHECKLISTS / 'preserve_occurrence_evidence.csv', REVIEWED]
    for code in ['6ap', '85a']:
        path = CHECKLISTS / f'checklist_level_iv_{code}.csv'
        paths.append(path)
        table = pd.read_csv(path, dtype=str, keep_default_na=False)
        assert table.resolved_scientific_name.is_unique
        pools[code] = set(table.resolved_scientific_name)
    candidates = pools['6ap'] | pools['85a']
    resolved = set(named.loc[named.name_reconciled, 'analysis_taxon_name'])
    shared = resolved & candidates
    outside = resolved - candidates
    pending = set(named.loc[~named.name_reconciled, 'analysis_taxon_name'])
    assert len(candidates) == 2550 and len(named) == 316 and len(insects) == 423
    assert not pending & resolved
    named['candidate_match'] = named.apply(lambda r: 'pending name reconciliation' if not r.name_reconciled
                                          else ('in Level IV pool' if r.analysis_taxon_name in candidates else 'outside Level IV pool'), axis=1)
    named.to_csv(OUT / 'ecdysis_species_record_audit.csv', index=False)
    excluded = insects[~rank_ok].copy()
    excluded['analysis_scope_note'] = 'Valid higher-taxon identification; excluded from species-level Hill profile'
    excluded.to_csv(OUT / 'higher_taxon_records.csv', index=False)
    units = []
    for name, group in named.groupby('analysis_taxon_name', sort=True):
        units.append({'analysis_taxon_name': name, 'occurrence_records': len(group),
                      'candidate_match': group.candidate_match.iloc[0],
                      'original_names': '; '.join(sorted(set(group.scientificName))),
                      'preserved_specimen_records': int(group.basisOfRecord.eq('PreservedSpecimen').sum()),
                      'human_observation_records': int(group.basisOfRecord.eq('HumanObservation').sum())})
    unit_table = pd.DataFrame(units)
    unit_table.to_csv(OUT / 'observed_species_comparison.csv', index=False)
    for category, filename in [('in Level IV pool', 'shared_species.csv'),
                               ('outside Level IV pool', 'observed_outside_candidate_pool.csv'),
                               ('pending name reconciliation', 'unreconciled_species_names.csv')]:
        unit_table[unit_table.candidate_match.eq(category)].to_csv(OUT / filename, index=False)
    pd.DataFrame([{'resolved_scientific_name': name,
                   'level_iv_regions': ', '.join(code for code in pools if name in pools[code])}
                  for name in sorted(candidates - shared)]).to_csv(OUT / 'candidates_not_documented.csv', index=False)
    subsets = [('All species-level records (primary)', named),
               ('Service-crosswalk names only', named[named.service_crosswalk_available]),
               ('Preserved specimens only', named[named.basisOfRecord.eq('PreservedSpecimen')]),
               ('Human observations only', named[named.basisOfRecord.eq('HumanObservation')])]
    summaries = [{'subset': label, **hill(frame.analysis_taxon_name)} for label, frame in subsets]
    pd.DataFrame(summaries).to_csv(OUT / 'observed_hill_summary.csv', index=False)
    observed_lookup = dict(zip(unit_table.analysis_taxon_name, unit_table.occurrence_records))
    pd.DataFrame([{'resolved_scientific_name': name,
                   'level_iv_regions': ', '.join(code for code in pools if name in pools[code]),
                   'ecdysis_records': observed_lookup.get(name, 0),
                   'documented_in_recent_survey': 'Yes' if name in shared else ''}
                  for name in sorted(candidates)]).to_csv(OUT / 'candidate_species_comparison.csv', index=False)
    primary = summaries[0]
    meta = {'created_at_utc': datetime.now(timezone.utc).isoformat(),
            'assumption': 'All species in the union of Level IV 6ap and 85a could occur somewhere on Dangermond; no habitat filter or fitted SDM.',
            'source_archive_records': len(local), 'insect_records': len(insects),
            'species_rank_records': len(named), 'higher_rank_insect_records': len(excluded),
            'observed_species_level_units': primary['q0'], 'reconciled_species': len(resolved),
            'reconciled_records': int(named.name_reconciled.sum()),
            'user_approved_original_names': int(named.loc[named.user_reviewed_original_name, 'analysis_taxon_name'].nunique()),
            'user_approved_original_name_records': int(named.user_reviewed_original_name.sum()),
            'pending_species_names': len(pending), 'pending_records': int((~named.name_reconciled).sum()),
            'candidate_species': len(candidates), 'shared_between_level_iv_lists': len(pools['6ap'] & pools['85a']),
            'candidate_species_documented': len(shared), 'candidate_species_not_documented': len(candidates - shared),
            'candidate_percentage_documented': 100 * len(shared) / len(candidates),
            'reconciled_observed_outside_pool': len(outside), 'hill_summaries': summaries,
            'two_most_recorded_species': named.analysis_taxon_name.value_counts().head(2).to_dict(),
            'weighting': 'One unique Ecdysis occurrence record per count, not individualCount or population abundance. No GBIF records are pooled into the observed survey.',
            'pending_name_policy': 'User confirmed five previously unmatched names on 2026-10-27; retain them exactly, with qualifiers. This is user review, not a new service match. Any remaining unresolved names would remain explicit pending units.',
            'uncertainty': 'All species-level identifications are analyzed together. These are empirical record-frequency Hill values, not unseen-richness estimates, coverage-standardized estimates, occupancy probabilities or habitat-health scores.',
            'reference': 'Chao et al. 2014; https://doi.org/10.1890/13-0133.1',
            'input_sha256': {str(path.relative_to(ROOT)): sha(path) for path in paths}}
    (OUT / 'analysis_metadata.json').write_text(json.dumps(meta, indent=2) + '\n')
    (OUT / 'latest_run_summary.json').write_text(json.dumps(meta, indent=2) + '\n')
    assert sum(unit_table.occurrence_records) == len(named)
    assert len(unit_table) == len(shared) + len(outside) + len(pending)
    assert len(candidates) == len(shared) + len(candidates - shared)
    assert all(row['q0'] >= row['q1'] >= row['q2'] >= 1 for row in summaries)
    print(json.dumps(meta, indent=2))


if __name__ == '__main__':
    main()
