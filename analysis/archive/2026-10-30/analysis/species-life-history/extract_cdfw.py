"""Read CDFW table columns without collapsing names and listing categories."""
from pathlib import Path
import csv
import json
import re
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw/species-literature/2026-10-27'


def main():
    reader = PdfReader(RAW / 'cdfw_special_animals.pdf')
    records = []
    for page_index, page in enumerate(reader.pages):
        text = page.extract_text(extraction_mode='layout')
        columns = None
        current = None
        def finish():
            nonlocal current
            if current:
                current = {k: ' '.join(v.split()) if isinstance(v, str) else v for k, v in current.items()}
                if re.match(r'^[A-Z][a-z]+ [a-z]', current['scientific_name']):
                    records.append(current)
                current = None
        for line in text.splitlines():
            if 'Scientific Name' in line and 'Common' in line and 'Global' in line and 'ESA' in line:
                finish()
                labels = ['Scientific Name', 'Common', 'Comments', 'Global', 'State', 'ESA', 'CESA', 'Other', 'Records', 'End']
                names = ['scientific_name', 'common_name', 'comments', 'global_rank', 'state_rank', 'esa', 'cesa', 'other', 'records', 'end_notes']
                columns = [(name, line.index(label)) for name, label in zip(names, labels)]
                continue
            if not columns:
                continue
            if re.search(r'^[A-Z]+(?:,|\s+Order)|^October 21|Special Animals List', line.strip()):
                finish()
                continue
            sci = line[:columns[1][1]].strip()
            if sci in ['Rank', 'Status', 'in', 'CNDDB?', '']:
                pass
            elif re.match(r'^[A-Z][a-z]+(?:\s|$)', sci):
                finish()
                current = {name: '' for name, _ in columns}
                current['pdf_page'] = page_index + 1
            elif not re.match(r'^[a-z][a-z0-9 .?\-]*$', sci):
                continue
            if current is not None:
                for i, (name, start) in enumerate(columns):
                    end = columns[i + 1][1] if i + 1 < len(columns) else len(line)
                    value = line[start:end].strip()
                    current[name] += ' ' + value
        finish()
    pool = {}
    for code in ['6ap', '85a']:
        for row in csv.DictReader((ROOT / f'data/final/checklists/checklist_level_iv_{code}.csv').open()):
            pool[row['resolved_scientific_name']] = row
    matched = []
    for row in records:
        full = row['scientific_name']
        parent = ' '.join(full.split()[:2])
        if full in pool:
            matched.append({**row, 'checklist_species': full, 'scope': 'species'})
        elif parent in pool:
            matched.append({**row, 'checklist_species': parent, 'scope': 'subspecies/population only'})
    (RAW / 'cdfw_matched_rows.json').write_text(json.dumps(matched, indent=2) + '\n')
    print(json.dumps(matched, indent=2))


if __name__ == '__main__':
    main()
