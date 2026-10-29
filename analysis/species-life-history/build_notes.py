"""Apply bounded, attributable species-account evidence to Level IV checklists.

No geography-derived habitat assignments, taxonomy edits, or absence claims.
Short account quotations are explicitly marked and capped at 25 words per URL.
"""
from pathlib import Path
from html import unescape
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw/species-literature/2026-10-27'
OUT = ROOT / 'outputs/species-life-history/2026-10-27'
FINAL = ROOT / 'data/final/checklists'
DATE = '2026-10-27'
CDFW_URL = 'https://nrm.dfg.ca.gov/FileHandler.ashx?DocumentID=109406&inline='


def clean(text):
    text = re.sub(r'<[^>]*>', ' ', text or '')
    return re.sub(r'\s+', ' ', unescape(text)).strip(' \t–-')


def read_csv(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def cached(kind, name):
    path = RAW / kind / (hashlib.sha256(name.encode()).hexdigest()[:24] + '.json.gz')
    return json.load(gzip.open(path, 'rt')) if path.exists() else {}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    species = json.loads((RAW / 'species_input.json').read_text())
    reviewed = {r['resolved_scientific_name']: r for r in read_csv(ROOT / 'analysis/habitat-notes/reviewed_species_notes.csv')}
    extra = {r['resolved_scientific_name']: r for r in read_csv(ROOT / 'analysis/species-life-history/reviewed_additions.csv')}
    statuses = defaultdict(list)
    for row in json.loads((RAW / 'cdfw_matched_rows.json').read_text()):
        statuses[row['checklist_species']].append(row)
    results, audit = {}, []
    for name in sorted(species):
        notes, sources, evidence = [], [], []
        quoted = Counter()
        seen_excerpt_text = set()

        def add(note, url, kind, title='', raw=''):
            if not note or not url:
                return
            notes.append(note)
            if url not in sources:
                sources.append(url)
            evidence.append(dict(kind=kind, source_title=title, url=url, selected_text=note, account_text=raw))

        def excerpt(text, url, label, title, maximum=25):
            text = clean(text)
            if not text or text.casefold() in {'unknown', 'none', 'n/a', 'not available', 'no information', 'not reported'}:
                return
            remaining = min(maximum, 25 - quoted[url])
            if remaining < 6 or text.casefold() in seen_excerpt_text:
                return
            seen_excerpt_text.add(text.casefold())
            words = text.split()
            snippet = ' '.join(words[:remaining])
            quoted[url] += min(remaining, len(words))
            if len(words) > remaining:
                snippet += ' …'
            add(f'{label} (account excerpt): “{snippet}”', url, 'account_excerpt', title, text)

        if name in reviewed:
            row = reviewed[name]
            add(row['published_habitat_association'] + ' ' + row['life_history_notes'], row['sources'], 'reviewed_note', row['review_status'])
        if name in extra:
            row = extra[name]
            add(row['life_history_notes'], row['source'], 'reviewed_note', row['review_status'])

        gbif = cached('gbif', name)
        descriptions = gbif.get('descriptions', {}).get('data', {}).get('results', [])
        # Structured European traits are not evidence of Californian specialization.
        traits = [r for r in descriptions if r.get('source') == 'Northwestern European arthropod life histories and ecological traits']
        if traits:
            positive = sorted({r['type'].removeprefix('Habitat_').replace('_', ' ') for r in traits if r['type'].startswith('Habitat_') and clean(r['description']) == '1'})
            feeding = sorted({r['type'].removeprefix('Feeding_guild_') + ': ' + clean(r['description']) for r in traits if r['type'].startswith('Feeding_guild_') and clean(r['description']) not in {'', 'NA', '0'}})
            facts = []
            if positive:
                facts.append('habitat flags = ' + ', '.join(positive))
            if feeding:
                facts.append('feeding guilds = ' + ', '.join(feeding))
            if facts:
                url = 'https://www.gbif.org/species/' + str(traits[0]['sourceTaxonKey'])
                add('Northwestern European trait dataset: ' + '; '.join(facts) + '. Geographic context is Europe; these flags do not establish California habitat use or dune specialization.', url, 'structured_traits', traits[0]['source'])

        # Up to two original account sources; exclude secondary Wikipedia copies,
        # conservation prose, and descriptions not explicitly ecological.
        ecological = []
        for row in descriptions:
            typ = row.get('type', '').lower()
            title = row.get('source', '')
            if 'wikipedia' in title.lower() or title == 'Northwestern European arthropod life histories and ecological traits':
                continue
            if typ in {'habitat', 'eunis habitat', 'biology_ecology', 'biology', 'ecology', 'host', 'bionomics', 'lifecycle', 'life history', 'taxon_biology', 'biotope', 'ecología'}:
                if row.get('language') not in {'', 'eng', 'en', None}:
                    continue
                if len(clean(row.get('description', '')).split()) < 2:
                    continue
                ecological.append(row)
        ecological.sort(key=lambda r: (0 if 'habitat' in r.get('type', '').lower() else 1, r.get('source', '')))
        chosen = []
        chosen_titles = {}
        for row in ecological:
            url = 'https://www.gbif.org/species/' + str(row.get('sourceTaxonKey') or row['taxonKey'])
            title = row.get('source', '')
            if title in chosen_titles and chosen_titles[title] != url:
                continue
            if url not in chosen:
                if len(chosen) == 2:
                    continue
                chosen.append(url)
                chosen_titles[title] = url
            title = row.get('source', '')
            context = ' [European evidence]' if 'Europe' in title or title.startswith('DAISIE') else ''
            label = row['type'].replace('_', '/') + context + ' — ' + title
            excerpt(row.get('description'), url, label, title, maximum=15 if 'habitat' in row['type'].lower() else 25)

        bamona = cached('bamona', name)
        text = bamona.get('text', '') if bamona.get('status') == 200 else ''
        # The requested binomial must occur in the page title, not merely a
        # navigation/similar-species link elsewhere in the page.
        page_title = clean(' '.join(re.findall(r'<title[^>]*>(.*?)</title>', text, re.S | re.I)))
        valid_bamona = name.casefold() in page_title.casefold()
        if valid_bamona:
            fields = [('habitat', 'Habitat', 15), ('caterpillarhosts', 'Larval hosts', 10), ('lifehistory', 'Life history', 25), ('adultfood', 'Adult food', 25)]
            for field, label, maximum in fields:
                match = re.search(r'views-field-field-' + field + r'\"[^>]*>(.*?)</div>', text, re.S)
                if match:
                    content = re.search(r'<span class="field-content">(.*?)</span>', match[1], re.S)
                    if content:
                        excerpt(content[1], bamona['url'], 'BAMONA ' + label, 'Butterflies and Moths of North America', maximum)

        for row in statuses.get(name, []):
            ranks = ', '.join(x for x in [row.get('global_rank'), row.get('state_rank')] if x and x != 'None')
            entry = row['scientific_name']
            if row['scope'] == 'species':
                statement = f'CDFW Special Animals List (October 2026): species tracked; ranks {ranks}.'
            else:
                statement = f'CDFW Special Animals List (October 2026) tracks {entry} ({ranks}); this applies to that subspecies/population, not automatically to every {name} record.'
            if row.get('esa') not in {'', 'None', None}:
                statement += ' Federal ESA status for that listed entity: ' + row['esa'] + '.'
            if row.get('cesa') not in {'', 'None', None}:
                statement += ' California CESA status for that listed entity: ' + row['cesa'] + '.'
            if name == 'Danaus plexippus':
                statement += ' The tracked entry is the California overwintering population; the proposed federal threatened listing concerns the species and is a proposal, not a final listing.'
            add(statement, CDFW_URL + '#page=' + str(row['pdf_page']), 'conservation', 'CDFW Special Animals List, October 2026')

        red = gbif.get('redlist', {}).get('data', {})
        category = red.get('code')
        if category in {'CR', 'EN', 'VU', 'NT'} and gbif.get('exact_species_lookup'):
            statement = f'Global IUCN category reported by GBIF: {red.get("category", category)} ({category}), retrieved {DATE}; assessment date not supplied by this endpoint.'
            add(statement, gbif['redlist']['url'], 'conservation', 'GBIF IUCN Red List category endpoint')
        results[name] = dict(life_history_notes=' '.join(notes), source='; '.join(sources))
        audit.append(dict(resolved_scientific_name=name, note_present=bool(notes), evidence=evidence,
                          gbif_exact_species_lookup=gbif.get('exact_species_lookup', False),
                          gbif_match=gbif.get('match', {}).get('data', {}),
                          gbif_match_http_status=gbif.get('match', {}).get('status'),
                          gbif_descriptions_http_status=gbif.get('descriptions', {}).get('status'),
                          bamona_http_status=bamona.get('status'), bamona_title_validated=valid_bamona,
                          selected_quote_word_counts=dict(quoted),
                          review_status='Source excerpts and structured flags; not a comprehensive manual literature review' if notes else 'No usable evidence in the queried accounts; blank does not imply no information exists',
                          retrieved_on=DATE))

    summary = {'retrieved_on': DATE, 'unique_species_queried': len(species), 'species_with_notes': sum(bool(r['life_history_notes']) for r in results.values()), 'species_without_notes': sum(not r['life_history_notes'] for r in results.values()), 'checklists': []}
    for code in ['6ap', '85a']:
        path = FINAL / f'checklist_level_iv_{code}.csv'
        rows = read_csv(path)
        fields = [f for f in rows[0] if f != 'source']
        fields.insert(fields.index('life_history_notes') + 1, 'source')
        originals = [{k: v for k, v in r.items() if k not in {'source', 'life_history_notes'}} for r in rows]
        for row in rows:
            row.update(results[row['resolved_scientific_name']])
        assert originals == [{k: v for k, v in r.items() if k not in {'source', 'life_history_notes'}} for r in rows]
        assert all(bool(r['source']) == bool(r['life_history_notes']) for r in rows)
        write_csv(path, rows, fields)
        alias = ROOT / f'data/final/habitat-notes/checklist_level_iv_{code}_habitat_notes.csv'
        alias.write_bytes(path.read_bytes())
        summary['checklists'].append(dict(code=code, species=len(rows), species_with_notes=sum(bool(r['life_history_notes']) for r in rows), file=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    write_csv(OUT / 'species_lookup_coverage.csv', [dict(resolved_scientific_name=name, has_notes=bool(result['life_history_notes']), source_count=len(result['source'].split('; ')) if result['source'] else 0) for name, result in results.items()], ['resolved_scientific_name', 'has_notes', 'source_count'])
    with gzip.open(OUT / 'species_source_audit.jsonl.gz', 'wt') as stream:
        for row in audit:
            stream.write(json.dumps(row) + '\n')
    summary['evidence_types'] = dict(Counter(e['kind'] for row in audit for e in row['evidence']))
    summary['species_with_conservation_flags'] = sum(any(e['kind'] == 'conservation' for e in row['evidence']) for row in audit)
    summary['gbif_exact_species_lookups'] = sum(row['gbif_exact_species_lookup'] for row in audit)
    summary['bamona_http_status_counts'] = dict(Counter(row['bamona_http_status'] for row in audit if row['bamona_http_status'] is not None))
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    metadata_path = FINAL / 'checklist_metadata.json'
    metadata = json.loads(metadata_path.read_text())
    metadata['blank_rule'] = 'Blank preserve flag means not documented, not absent. Blank Level IV life-history note means no usable evidence found in the bounded source lookup; Level III notes remain blank.'
    metadata['life_history_notes'] = 'Level IV annotations: analysis/species-life-history/README.md; source column follows notes. Level III unchanged.'
    metadata['life_history_annotation'] = summary
    for entry in summary['checklists']:
        metadata['output_checksums_sha256'][Path(entry['file']).name] = entry['sha256']
    metadata_path.write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    raise SystemExit('Retired at user request: life_history_notes and source were removed from active Level IV checklists. Historical source evidence remains in outputs/species-life-history/.')
