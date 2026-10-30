"""Four species-level regional checklists with preserve evidence and blank notes."""
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json
import re
import xml.etree.ElementTree as ET

import pandas as pd
import shapely
from shapely.geometry import shape

from clean_species_identifications import canonical_input
from resolve_taxonomy import query, evaluate

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / 'outputs/regional-candidate-pool/gbif-vgv5ee'
SOURCE = AUDIT / 'species_identified_insect_records_v3.csv.gz'
DEST = ROOT / 'data/final/checklists'
BOUNDARY = ROOT / 'analysis/reference-data/jldp_boundary.geojson'
ECDYSIS = ROOT / 'data/raw/ecdysis/extracted/SymbOutput_2026-10-26_124013_DwC-A'
OLDER = ROOT / 'data/raw/gbif/preserve_2026-10-26/gbif_all_arthropods_within_preserve.jsonl.gz'
INPUT = ['scientificName','taxonRank','order','family']
REGIONS = {('III','6'):'Central California Foothills and Coastal Mountains', ('III','85'):'Southern California/Northern Baja Coast', ('IV','6ap'):'Solomon-Purisima-Santa Ynez Hills', ('IV','85a'):'Santa Barbara Coastal Plain and Terraces'}
COLS = ['common_name','order','family','resolved_scientific_name','occurrence_count','collected_or_observed_on_dangermond']
BOLD_KEYS = {'040c5662-da76-4782-a48e-cdea1892d14c'}


def is_bold(key, institution='', title=''):
    return key in BOLD_KEYS or institution.upper() in {'BIOUG','BOLD','CBG'} or bool(re.search(r'\b(?:BOLD|iBOL)\b|Barcode of Life', title, re.I))


def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    taxa = pd.read_csv(AUDIT/'taxonomy_name_resolution.csv',dtype=str,keep_default_na=False)
    raw = {}
    with (AUDIT/'taxonomy_api_cache.jsonl').open() as f:
        for line in f:
            r=json.loads(line);raw[tuple(r['input'])]=r.get('response',{})
    direct={}; aliases=defaultdict(set); classification=defaultdict(Counter); classification_sources=defaultdict(set)
    for r in taxa.to_dict('records'):
        target=r['resolved_species_name']
        if not target or not r['taxon_resolution_status'].startswith('resolved_'):continue
        key=tuple(r[x] for x in INPUT);direct[key]=target
        aliases[canonical_input(r['scientificName'],'SPECIES')].add(target)
        response=raw.get(key,{})
        classes={v['rank']:v['name'] for v in response.get('classification',[])}
        pair=(classes.get('ORDER',''),classes.get('FAMILY',''))
        origin='GBIF/COL XR classification'
        if not all(pair):pair=(r['order'],r['family']);origin='Original GBIF classification fallback'
        classification[target][pair]+=int(r['occurrence_records'])
        classification_sources[target].add(origin)
    common=defaultdict(set)
    lookup=pd.read_csv(AUDIT/'species_common_name_lookup.csv',dtype=str,keep_default_na=False)
    for r in lookup.to_dict('records'):
        # Subspecies-specific common names must not label the whole species.
        source_names=r['common_name_source_scientific_name'].split('; ')
        if r['proposed_common_name'] and all(len(n.split())==2 for n in source_names):
            common[r['resolved_species_name']].update(r['proposed_common_name'].split('; '))
    boundary=json.loads(BOUNDARY.read_text())
    geometry=shapely.union_all([shape(f['geometry']) for f in boundary['features']])
    assert shapely.is_valid(geometry);shapely.prepare(geometry)
    region_counts={r:Counter() for r in REGIONS}
    evidence=[];source_counts=Counter();excluded=Counter();retained_bold=Counter()
    fields=['gbifID','scientificName','taxonRank','order','family','resolved_species_name','analysis_ecoregion_l3_code','analysis_ecoregion_l4_code','decimalLongitude','decimalLatitude','basisOfRecord','occurrenceStatus','occurrenceID','catalogNumber','datasetKey','datasetName','institutionCode','identificationQualifier']
    total=0
    for frame in pd.read_csv(SOURCE,usecols=fields,dtype=str,keep_default_na=False,chunksize=100000):
        total+=len(frame)
        assert frame.resolved_species_name.ne('').all()
        bold=pd.Series([is_bold(k,i,t) for k,i,t in zip(frame.datasetKey,frame.institutionCode,frame.datasetName)],index=frame.index)
        retained_bold['regional_records']+=int(bold.sum())
        # All v3 rows already have accepted species-level determinations.
        # Source membership, including BOLD, does not exclude these rows.
        for region in REGIONS:
            col='analysis_ecoregion_l3_code' if region[0]=='III' else 'analysis_ecoregion_l4_code'
            hit=frame[col].str.split(';').map(lambda codes:region[1] in codes)
            region_counts[region].update(frame.loc[hit,'resolved_species_name'])
        points=shapely.points(pd.to_numeric(frame.decimalLongitude),pd.to_numeric(frame.decimalLatitude))
        inside=shapely.covers(geometry,points)&~frame.occurrenceStatus.str.upper().eq('ABSENT').to_numpy()
        for r in frame.loc[inside].to_dict('records'):
            evidence.append({'resolved_species_name':r['resolved_species_name'],'source':'GBIF regional snapshot point in preserve boundary','record_id':r['gbifID'],'occurrence_id':r['occurrenceID'],'catalog_number':r['catalogNumber'],'basis_of_record':r['basisOfRecord'],'original_name':r['scientificName'],'identification_qualifier':r['identificationQualifier'],'location_support':'Point covered by supplied preserve boundary','name_support':'Existing approved name resolution'})
    assert total==1408875
    # Survey archive explicitly identifies Dangermond in each species-rank
    # locality; use the encoding specified in its Darwin Core meta.xml.
    meta=ET.parse(ECDYSIS/'meta.xml').getroot();core=meta.find('{http://rs.tdwg.org/dwc/text/}core')
    local=pd.read_csv(ECDYSIS/'occurrences.csv',encoding=core.get('encoding'),dtype=str,keep_default_na=False)
    observed=[]
    for r in local.to_dict('records'):
        if r['class']!='Insecta' or r['taxonRank'].casefold() not in {'species','subspecies','variety','form'}:continue
        if not re.search('Dangermond',r['locality'],re.I):continue
        observed.append({'source':'Ecdysis local survey','record_id':r['id'],'occurrence_id':r['occurrenceID'],'catalog_number':r['catalogNumber'],'basis_of_record':r['basisOfRecord'],'original_name':r['scientificName'],'identification_qualifier':r['identificationQualifier'],'location_support':'Publisher locality explicitly names Dangermond Preserve','key':(r['scientificName'],r['taxonRank'].upper(),r['order'],r['family'])})
    # The prior extract is already boundary-clipped. Recheck its coordinates
    # against the current supplied boundary; named BOLD records remain eligible.
    with gzip.open(OLDER,'rt',encoding='utf-8') as f:
        for line in f:
            r=json.loads(line)
            if r.get('class')!='Insecta' or r.get('taxonRank') not in {'SPECIES','SUBSPECIES','VARIETY','FORM'} or str(r.get('occurrenceStatus','')).upper()=='ABSENT':continue
            if is_bold(r.get('datasetKey',''),r.get('institutionCode','') or '',r.get('datasetName','') or ''):
                retained_bold['preserve_extract_records']+=1
            try:point=shapely.Point(float(r['decimalLongitude']),float(r['decimalLatitude']))
            except (KeyError,ValueError,TypeError):continue
            if not shapely.covers(geometry,point):continue
            observed.append({'source':'GBIF preserve extract 2026-10-26','record_id':str(r.get('gbifID',r.get('key',''))),'occurrence_id':r.get('occurrenceID',''),'catalog_number':r.get('catalogNumber',''),'basis_of_record':r.get('basisOfRecord',''),'original_name':r.get('scientificName',''),'identification_qualifier':r.get('identificationQualifier',''),'location_support':'Point rechecked inside supplied preserve boundary','key':tuple(r.get(c,'') or '' for c in INPUT)})
    unresolved=set();observed_mapping={}
    for item in observed:
        key=item['key'];canonical=canonical_input(key[0],'SPECIES')
        if key in direct:observed_mapping[key]=(direct[key],'Existing exact input/classification crosswalk')
        elif len(aliases.get(canonical,set()))==1:observed_mapping[key]=(next(iter(aliases[canonical])),'Unique approved original-binomial crosswalk')
        else:unresolved.add(key)
    cache_file=AUDIT/'checklist_observed_name_matches.json'
    cache=json.loads(cache_file.read_text()) if cache_file.exists() else {}
    pending=[key for key in unresolved if json.dumps(key) not in cache]
    if pending:
        print(f'Matching {len(pending)} additional observed names with GBIF/COL XR.',flush=True)
        with ThreadPoolExecutor(max_workers=6) as pool:
            for item in pool.map(query,pending):cache[json.dumps(item['input'])]=item
        cache_file.write_text(json.dumps(cache,indent=2)+'\n')
    for key in unresolved:
        result=evaluate(cache[json.dumps(key)])
        if result['resolved_species_name']:
            observed_mapping[key]=(result['resolved_species_name'],'Additional GBIF/COL XR match; same user-approved species-level policy')
    unresolved_rows=[]
    for item in observed:
        key=item.pop('key')
        if key not in observed_mapping:
            unresolved_rows.append({**item,'reason':'No unique species-level name mapping'});continue
        name,support=observed_mapping[key]
        evidence.append({'resolved_species_name':name,**item,'name_support':support})
    evidence=pd.DataFrame(evidence).drop_duplicates(subset=['resolved_species_name','source','record_id'])
    evidence.to_csv(DEST/'preserve_occurrence_evidence.csv',index=False)
    present=set(evidence.resolved_species_name)
    summary=[];conflicts=[]
    for name,pairs in classification.items():
        if len(pairs)>1:conflicts.append({'resolved_species_name':name,'classification_counts':json.dumps({str(k):v for k,v in pairs.items()})})
    pd.DataFrame(conflicts,columns=['resolved_species_name','classification_counts']).to_csv(DEST/'taxonomy_classification_conflicts.csv',index=False)
    for (level,code),counts in region_counts.items():
        rows=[]
        for name,n in counts.items():
            pair=sorted(classification[name].items(),key=lambda x:(-x[1],x[0]))[0][0]
            rows.append({'common_name':'; '.join(sorted(common[name])),'order':pair[0],'family':pair[1],'resolved_scientific_name':name,'occurrence_count':n,'collected_or_observed_on_dangermond':'Yes' if name in present else ''})
        table=pd.DataFrame(rows,columns=COLS).sort_values(['order','family','resolved_scientific_name'])
        assert table.resolved_scientific_name.is_unique
        filename=f'checklist_level_{level.lower()}_{code}.csv'
        table.to_csv(DEST/filename,index=False)
        summary.append({'level':level,'ecoregion_code':code,'ecoregion_name':REGIONS[(level,code)],'checklist_species':len(table),'regional_occurrences':int(table.occurrence_count.sum()),'species_documented_on_preserve':int(table.collected_or_observed_on_dangermond.eq('Yes').sum()),'file':filename})
    pd.DataFrame(summary).to_csv(DEST/'checklist_summary.csv',index=False)
    all_candidates=set().union(*(set(c) for c in region_counts.values()))
    evidence.loc[~evidence.resolved_species_name.isin(all_candidates)].to_csv(DEST/'documented_preserve_taxa_not_in_candidate_pool.csv',index=False)
    pd.DataFrame(unresolved_rows).to_csv(DEST/'unmapped_preserve_records.csv',index=False)
    columns=[('common_name','ESA-derived species common name; blank if unavailable. Subspecies-specific common names are not promoted to the whole species.'),('order','Service classification where available; otherwise original GBIF classification. Weighted modal pair resolves conflicting classifications; conflicts are logged.'),('family','Same classification policy as order.'),('resolved_scientific_name','Resolved species-level canonical name; subspecies rolled up to species.'),('occurrence_count','Number of eligible regional occurrence records, not individuals. The same record contributes separately to its Level III and IV checklists.'),('collected_or_observed_on_dangermond','Yes when a named record supports occurrence on the property; otherwise blank, not evidence of absence. Includes qualified identifications, with qualifiers in evidence table.')]
    pd.DataFrame(columns,columns=['column','description']).to_csv(DEST/'column_metadata.csv',index=False)
    metadata={'created_at_utc':datetime.now(timezone.utc).isoformat(),'source':str(SOURCE.relative_to(ROOT)),'source_sha256':sha(SOURCE),'final_occurrence_package':'data/final/dataset_metadata.json','checklists':summary,'species_unit':'resolved_species_name from upstream full v3, not subspecies-level resolved_taxon_name','preserve_boundary':str(BOUNDARY.relative_to(ROOT)),'boundary_sha256':sha(BOUNDARY),'local_survey_encoding':core.get('encoding'),'preserve_positive_rule':'Positive supporting GBIF point in supplied boundary or Ecdysis named-species record with locality explicitly naming Dangermond. Genus/higher IDs do not create species flags; ABSENT records do not establish presence. A positive flag is preserve-wide, not evidence of occurrence in that checklist ecoregion or a particular dune habitat. Coordinate uncertainty not buffered.','blank_rule':'Blank preserve flag means not documented in the records checked, not absence.','bold_policy':'User explicitly restored all records with resolved species determinations, including BOLD/iBOL/BIOUG/CBG sources. All v3 regional records retained. Named preserve BOLD records can support a positive flag after boundary/name checks; genus-only and unresolved BIN records do not establish species. This supersedes the earlier blanket BOLD exclusion for these checklists.','excluded_records':dict(excluded),'retained_identifiable_BOLD_records':dict(retained_bold),'preserve_evidence_records':len(evidence),'preserve_named_taxa_in_evidence':len(present),'unmapped_preserve_records':len(unresolved_rows),'classification_rule':'Prefer service ORDER/FAMILY; missing service values fall back to original GBIF. Choose weighted modal pair over regional source records, with ties sorted lexically. Conflicts logged separately.','notes':'Regional candidate lists, not lists of confirmed preserve species. Candidate occurrence counts use source records, not individualCount; no new date/deduplication filter. Local surveys mark presence without increasing regional GBIF record counts. Preserve evidence may contain overlapping sources; its rows must not be summed as independent biological events.'}
    (DEST/'checklist_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    lines=['# Ecoregion species checklists','', 'Four species-level regional checklists. All four lists use the same six columns; life-history notes and sources have been removed. Preserve occurrence is Yes only where a supporting record was found, and blank otherwise.','', '| Level | Code | Species | Regional occurrences | Species documented on preserve |','|---|---|---:|---:|---:|']
    lines += [f"| {r['level']} | {r['ecoregion_code']} | {r['checklist_species']:,} | {r['regional_occurrences']:,} | {r['species_documented_on_preserve']:,} |" for r in summary]
    lines += ['', 'Subspecies are rolled up to species; common names specific to a subspecies are not generalized. Counts represent regional records, not individuals or preserve-only records. The Level III/IV lists overlap. A preserve-wide Yes does not locate that species in a specific ecoregion or habitat; blank does not imply absence.','', 'The evidence table includes the local Ecdysis survey and named GBIF preserve records, including BOLD with name-matching provenance. Coordinate checks use the supplied preserve boundary; local species records also carry an explicit Dangermond locality. Higher-taxon identifications are valid but do not establish a named species. All resolved species-level regional records are included regardless of source, following the user’s restoration instruction. Unresolved BIN and genus-only records do not establish named species; final occurrence datasets are unchanged.','', 'See column_metadata.csv and checklist_metadata.json for definitions, sources and exact methods. The evidence, unmapped-record and classification-conflict tables permit review; all four checklists share the six-column schema.','', 'Reproduce: `python3 analysis/regional-candidate-pool/create_ecoregion_checklists.py`.']
    (DEST/'README.md').write_text('\n'.join(lines)+'\n')
    print(pd.DataFrame(summary).to_string(index=False),flush=True)
    print('Retained BOLD:',dict(retained_bold),'Exclusions:',dict(excluded),'Preserve named taxa:',len(present),'Unmapped records:',len(unresolved_rows),flush=True)


if __name__=='__main__':main()
