"""Cache species-account lookups for every unique Level IV checklist species.

Public sources only. Taxon lookups support literature retrieval and do not change
the approved checklist taxonomy. HTTP failures are recorded, never treated as
negative habitat/conservation evidence. Resume by rerunning this script.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import csv
import gzip
import hashlib
import json
import threading
import time

import requests

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw/species-literature/2026-10-27'
UA = 'DangermondSpeciesNotes/1.0 (https://github.com/cheadle-biodiversity/Dangermond-arthropods; biodiversity research)'
TLS = threading.local()


def session():
    if not hasattr(TLS, 'session'):
        TLS.session = requests.Session()
        TLS.session.headers['User-Agent'] = UA
    return TLS.session


def fetch(url, params=None):
    result = {'url': url, 'params': params or {}, 'retrieved_at': datetime.now(timezone.utc).isoformat()}
    for attempt in range(3):
        try:
            response = session().get(url, params=params, timeout=25)
            result.update(status=response.status_code, final_url=response.url)
            if response.status_code == 429:
                time.sleep(min(30, float(response.headers.get('Retry-After', 3 + attempt * 3))))
                continue
            if response.status_code >= 500 and attempt < 2:
                time.sleep(attempt + 1)
                continue
            if response.ok:
                if 'json' in response.headers.get('Content-Type', ''):
                    result['data'] = response.json()
                else:
                    result['text'] = response.text
            return result
        except (requests.RequestException, ValueError) as error:
            result['error'] = str(error)
            if attempt < 2:
                time.sleep(attempt + 1)
    return result


def cache_path(kind, name):
    path = RAW / kind / (hashlib.sha256(name.encode()).hexdigest()[:24] + '.json.gz')
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save(path, data):
    temporary = path.with_suffix('.partial')
    with gzip.open(temporary, 'wt', encoding='utf-8') as stream:
        json.dump(data, stream)
    temporary.replace(path)


def gbif_account(name):
    path = cache_path('gbif', name)
    if path.exists():
        return
    match = fetch('https://api.gbif.org/v1/species/match', {'name': name, 'strict': 'true'})
    data = match.get('data', {})
    result = {'name': name, 'match': match}
    # Reject genus/fuzzy matches. A species synonym may retrieve its accepted
    # species account, with that relationship retained in the original response.
    exact = (data.get('matchType') == 'EXACT' and data.get('canonicalName', '').casefold() == name.casefold()
             and data.get('rank') in ['SPECIES', 'SUBSPECIES'] and data.get('class') == 'Insecta')
    result['exact_species_lookup'] = exact
    key = data.get('speciesKey') or data.get('acceptedUsageKey') or data.get('usageKey')
    if exact and key:
        result['descriptions'] = fetch(f'https://api.gbif.org/v1/species/{key}/descriptions', {'limit': 300})
        result['redlist'] = fetch(f'https://api.gbif.org/v1/species/{key}/iucnRedListCategory')
    save(path, result)


def bamona_account(name):
    path = cache_path('bamona', name)
    if path.exists():
        return
    url = 'https://www.butterfliesandmoths.org/species/' + name.replace(' ', '-')
    save(path, {'name': name, **fetch(url)})


def wikipedia_batch(names):
    key = '|'.join(names)
    path = cache_path('wikipedia', key)
    if path.exists():
        return
    data = fetch('https://en.wikipedia.org/w/api.php', {
        'action': 'query', 'format': 'json', 'prop': 'extracts', 'explaintext': 1,
        'exlimit': 20, 'redirects': 1, 'titles': '|'.join(names), 'maxlag': 5})
    save(path, {'names': names, **data})


def main():
    species = {}
    for code in ['6ap', '85a']:
        with (ROOT / f'data/final/checklists/checklist_level_iv_{code}.csv').open() as stream:
            for row in csv.DictReader(stream):
                species[row['resolved_scientific_name']] = row
    assert len(species) == 2550
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / 'species_input.json').write_text(json.dumps(species, indent=2) + '\n')
    jobs = [('gbif', name) for name in sorted(species)]
    jobs += [('bamona', name) for name, row in sorted(species.items()) if row['order'] == 'Lepidoptera']
    names = sorted(species)
    jobs += [('wikipedia', names[i:i + 20]) for i in range(0, len(names), 20)]
    functions = {'gbif': gbif_account, 'bamona': bamona_account, 'wikipedia': wikipedia_batch}
    counts = {'completed': 0, 'errors': 0, 'jobs': len(jobs)}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(functions[kind], value): kind for kind, value in jobs}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as error:
                counts['errors'] += 1
                print('ERROR', futures[future], str(error), flush=True)
            counts['completed'] += 1
            if counts['completed'] % 100 == 0:
                print(json.dumps(counts), flush=True)
                (RAW / 'lookup_progress.json').write_text(json.dumps(counts, indent=2) + '\n')
    (RAW / 'lookup_progress.json').write_text(json.dumps(counts, indent=2) + '\n')
    print(json.dumps(counts), flush=True)


if __name__ == '__main__':
    main()
