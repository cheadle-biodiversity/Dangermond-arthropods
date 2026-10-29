"""Deduplicated preserve-wide GBIF + Ecdysis insect record-format comparison."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,gzip,json,math,re,hashlib
from datetime import datetime,timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/hill-diversity/2026-10-27-record-formats';OUT.mkdir(parents=True,exist_ok=True)
GB=ROOT/'data/raw/gbif/preserve_2026-10-26'
EC=ROOT/'data/raw/ecdysis/extracted/SymbOutput_2026-10-26_124013_DwC-A/occurrences.csv'
NAMED=ROOT/'outputs/hill-diversity/2026-10-27-insects/ecdysis_species_record_audit.csv'
EVIDENCE=ROOT/'data/final/checklists/preserve_occurrence_evidence.csv'

def read(p,encoding='utf-8-sig'):
 with p.open(encoding=encoding,newline='') as f:return list(csv.DictReader(f))
def write(name,rows,fields=None):
 fields=fields or list(rows[0]);p=OUT/name
 op=gzip.open(p,'wt',newline='') if str(p).endswith('.gz') else p.open('w',newline='')
 with op as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def norm(s):return re.sub('[^A-Z0-9]','',(s or '').upper())
def basis(s):return {'HUMANOBSERVATION':'HUMAN_OBSERVATION','PRESERVEDSPECIMEN':'PRESERVED_SPECIMEN','MATERIALSAMPLE':'MATERIAL_SAMPLE'}.get(norm(s),s or 'UNKNOWN')
def group(s):return {'HUMAN_OBSERVATION':'Human observations','PRESERVED_SPECIMEN':'Preserved specimens','MATERIAL_SAMPLE':'DNA records'}.get(s,'Other basis of record')
def hill(rows,q):
 c=Counter(r['species_name'] for r in rows if r['species_name']);n=sum(c.values())
 if not n:return None
 p=[v/n for v in c.values()]
 if q==0:return len(c)
 if abs(q-1)<1e-9:return math.exp(-sum(v*math.log(v) for v in p))
 return sum(v**q for v in p)**(1/(1-q))
keys={int(r['key']) for r in read(GB/'terrestrial_arthropod_occurrences.csv')}
gb=[r for r in map(json.loads,gzip.open(GB/'gbif_all_arthropods_within_preserve.jsonl.gz','rt')) if int(r['key']) in keys and r.get('class')=='Insecta']
ec=[r for r in read(EC,'iso-8859-1') if r['class']=='Insecta']
accepted_ec={r['id']:r['analysis_taxon_name'] for r in read(NAMED)}
ev=read(EVIDENCE);by_key={r['record_id']:r['resolved_species_name'] for r in ev if r['source'].startswith('GBIF')}
# Reuse reviewed name relationships on matching records to harmonize GBIF
# species-parent names with the approved project taxonomy across all records.
alias_votes=defaultdict(Counter)
ec_occ={r['occurrenceID']:r for r in ec if r['occurrenceID']}
for r in gb:
 target=by_key.get(str(r['key']))
 er=ec_occ.get(r.get('occurrenceID'))
 if er and er['id'] in accepted_ec:target=accepted_ec[er['id']]
 if target and r.get('species'):alias_votes[r['species']][target]+=1
aliases={name:c.most_common(1)[0][0] for name,c in alias_votes.items() if len(c)==1}
conflicts={name:dict(c) for name,c in alias_votes.items() if len(c)>1}
rows=[]
for r in gb:
 explicit_rank=r.get('taxonRank') in {'SPECIES','SUBSPECIES'}
 bin_only=bool(re.fullmatch('BOLD:[A-Z0-9]+',r.get('scientificName','')))
 eligible=explicit_rank and bool(r.get('speciesKey') and r.get('species')) and not bin_only
 name=r.get('species') if eligible else ''
 rows.append(dict(source='GBIF',record_id=str(r['key']),occurrence_id=r.get('occurrenceID') or '',institution=r.get('institutionCode') or '',collection=r.get('collectionCode') or '',catalog_number=r.get('catalogNumber') or '',basis=basis(r.get('basisOfRecord')),species_name=(by_key.get(str(r['key'])) or aliases.get(name,name) or '') if eligible else '',name_support='Existing approved project crosswalk' if eligible and (str(r['key']) in by_key or name in aliases) else 'Explicit GBIF species/subspecies identification' if eligible else 'Excluded from species profile: no explicit named species determination',scientific_name=r.get('scientificName') or '',input_identification_rank=r.get('taxonRank') or '',gbif_species_parent=r.get('species') or '',dataset_key=r.get('datasetKey') or '',sequence_links=r.get('associatedSequences') or '',order=r.get('order') or '',source_membership='GBIF',dedup_support='',paired_record_id='',is_barcode_bin=bool(re.fullmatch('BOLD:[A-Z0-9]+',r.get('scientificName','')))))
# Exact occurrence identifiers are the primary duplicate key. A fallback requires
# institution + collection + catalog number; no coordinate/date-only merging.
occ_index=defaultdict(list);cat_index=defaultdict(list)
for i,r in enumerate(rows):
 if r['occurrence_id']:occ_index[r['occurrence_id']].append(i)
 if r['institution'] and r['collection'] and r['catalog_number']:cat_index[(norm(r['institution']),norm(r['collection']),norm(r['catalog_number']))].append(i)
pairs=[];matched=set()
for r in ec:
 hits=occ_index.get(r['occurrenceID'],[]) if r['occurrenceID'] else [];rule='Exact occurrenceID'
 if not hits and r['institutionCode'] and r['collectionCode'] and r['catalogNumber']:
  hits=cat_index.get((norm(r['institutionCode']),norm(r['collectionCode']),norm(r['catalogNumber'])),[]);rule='Exact institution + collection + catalog number'
 if len(hits)>1:raise RuntimeError('Ambiguous duplicate match')
 nr=dict(source='Ecdysis',record_id=r['id'],occurrence_id=r['occurrenceID'],institution=r['institutionCode'],collection=r['collectionCode'],catalog_number=r['catalogNumber'],basis=basis(r['basisOfRecord']),species_name=accepted_ec.get(r['id'],''),name_support='Approved Ecdysis species crosswalk/author review' if r['id'] in accepted_ec else 'Valid higher-taxon identification',scientific_name=r['scientificName'],input_identification_rank=r['taxonRank'],gbif_species_parent='',dataset_key='',sequence_links='',order=r['order'],source_membership='Ecdysis',dedup_support='',paired_record_id='',is_barcode_bin=False)
 if hits:
  i=hits[0];assert i not in matched;matched.add(i);old=rows[i]
  pairs.append(dict(gbif_id=old['record_id'],ecdysis_id=r['id'],occurrence_id=r['occurrenceID'],match_rule=rule,gbif_basis=old['basis'],ecdysis_basis=nr['basis'],gbif_species=old['species_name'],ecdysis_species=nr['species_name']))
  # Latest local determinations take precedence on the same record; preserve
  # both source identifiers and expose differences in the duplicate audit.
  nr.update(source_membership='GBIF + Ecdysis',dedup_support=rule,paired_record_id=old['record_id'],gbif_species_parent=old['gbif_species_parent'],dataset_key=old['dataset_key'],sequence_links=old['sequence_links']);rows[i]=nr
 else:rows.append(nr)
for r in rows:r['record_format']=group(r['basis'])
assert len(rows)==len(gb)+len(ec)-len(pairs)
assert len([r['occurrence_id'] for r in rows if r['occurrence_id']]) == len({r['occurrence_id'] for r in rows if r['occurrence_id']})
summary=[]
formats=['Human observations','Preserved specimens','DNA records']
for label,rs in [('All record formats',rows)]+[(f,[r for r in rows if r['record_format']==f]) for f in formats]+[(b,[r for r in rows if r['basis']==b]) for b in sorted({r['basis'] for r in rows})]:
 summary.append(dict(record_format=label,all_insect_records=len(rs),named_species_records=sum(bool(r['species_name']) for r in rs),records_without_named_species=sum(not r['species_name'] for r in rs),q0=hill(rs,0),q1=hill(rs,1),q2=hill(rs,2)))
sets={f:{r['species_name'] for r in rows if r['record_format']==f and r['species_name']} for f in formats}
all_species=set.union(*sets.values())
unique={f:sets[f]-set.union(*(sets[o] for o in formats if o!=f)) for f in formats}
shared={name for name in all_species if sum(name in sets[f] for f in formats)>=2}
species=[]
for name in sorted(all_species):
 c=Counter(r['record_format'] for r in rows if r['species_name']==name)
 memberships=[f for f in formats if name in sets[f]]
 species.append(dict(species_name=name,human_observation_records=c[formats[0]],preserved_specimen_records=c[formats[1]],dna_records=c[formats[2]],record_formats='; '.join(memberships),contribution='Shared by multiple formats' if len(memberships)>1 else memberships[0]+' only'))
overlap=[dict(format_a=a,format_b=b,shared_species=len(sets[a]&sets[b])) for i,a in enumerate(formats) for b in formats[i+1:]]
write('record_format_summary.csv',summary);write('species_contributions.csv',species);write('species_format_overlap.csv',overlap);write('duplicate_record_audit.csv',pairs);write('combined_insect_record_audit.csv.gz',rows)
write('species_determined_records.csv.gz',[r for r in rows if r['species_name']])
dataset_metadata=json.loads((GB/'dataset_and_publisher_metadata.json').read_text())
dna_keys=sorted({r['datasetKey'] for r in gb if r.get('basisOfRecord')=='MATERIAL_SAMPLE' and r.get('taxonRank') in {'SPECIES','SUBSPECIES'} and r.get('species')})
dna_sources={k:dataset_metadata[k]['dataset']['title'] for k in dna_keys}
assert set(dna_sources.values())=={'International Barcode of Life project (iBOL)','INSDC Sequences'}
meta=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),scope='Insecta in existing preserve GBIF terrestrial scope + UCSB Summer 2026 survey (this project); species-determined records only for diversity/composition comparisons.',gbif_input_records=len(gb),ecdysis_input_records=len(ec),duplicate_records=len(pairs),combined_records=len(rows),species_determined_records=sum(bool(r['species_name']) for r in rows),basis_counts=dict(Counter(r['basis'] for r in rows)),source_membership_counts=dict(Counter(r['source_membership'] for r in rows)),species_total=len(all_species),species_unique_to_format={f:len(unique[f]) for f in formats},species_shared_by_multiple_formats=len(shared),species_in_all_three=len(set.intersection(*sets.values())),pairwise_overlap=overlap,summaries=summary,name_aliases=aliases,conflicting_name_aliases_not_applied=conflicts,dna_source_datasets=dna_sources,deduplication='Exact occurrenceID, then institution+collection+catalog number; prefer local UCSB survey determination on a matched record. No approximate merging.',species_policy='Explicit SPECIES/SUBSPECIES rank plus a named species for GBIF; approved species-level survey determinations for local records. Subspecies rolled to species. No qualifier filtering. Unnamed BIN records excluded even if GBIF supplies a species parent. Higher taxa remain valid but do not enter species profiles.',format_policy='Human observations = HUMAN_OBSERVATION; preserved specimens = PRESERVED_SPECIMEN; DNA records = species-determined MATERIAL_SAMPLE records from the verified iBOL/INSDC sequence datasets. Material samples are no longer pooled with preserved specimens.',weighting='One vote per deduplicated species-determined occurrence, not individuals. Observed Hill q0 richness, q1 exponential Shannon, q2 inverse Simpson. No rarefaction/extrapolation.',limitations='Saved snapshots have different dates and unequal effort. Duplicates published under different identifiers may persist. A DNA record can derive from a physical voucher: these are occurrence record formats, not mutually exclusive biological sampling technologies.',input_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [GB/'gbif_all_arthropods_within_preserve.jsonl.gz',GB/'terrestrial_arthropod_occurrences.csv',EC,NAMED,EVIDENCE]})
(OUT/'analysis_metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
# All panels use only species-determined records.
from figure_style import apply_style, TEAL, ORANGE, GRAY, DNA
apply_style()
colors={'Human observations':TEAL,'Preserved specimens':ORANGE,'DNA records':DNA}
fig=plt.figure(figsize=(8.5,8.5));grid=fig.add_gridspec(2,2,height_ratios=[1,1.2]);axs=[fig.add_subplot(grid[0,0]),fig.add_subplot(grid[0,1]),fig.add_subplot(grid[1,:])]
counts=[sum(r['record_format']==f and bool(r['species_name']) for r in rows) for f in formats]
axs[0].bar(range(3),counts,color=[colors[f] for f in formats],width=.62)
axs[0].set_xticks(range(3),['Human\nobs.','Preserved\nspecimens','DNA'])
axs[0].set(ylabel='Records identified\nto species',title='A. Record\ncontributions',ylim=(0,max(counts)*1.2))
for i,n in enumerate(counts):axs[0].text(i,n+max(counts)*.025,str(n),ha='center',fontsize=13)
parts=[len(unique[f]) for f in formats]+[len(shared)];labels=['Human only','Preserved only','DNA only','Shared']
axs[1].barh([3,2,1,0],parts,color=[TEAL,ORANGE,DNA,GRAY],height=.6)
axs[1].set_yticks([3,2,1,0],labels);axs[1].set(xlabel='Named species',title='B. Species\ncontributions',xlim=(0,max(parts)*1.3))
for y,n in zip([3,2,1,0],parts):axs[1].text(n+1,y,str(n),va='center',fontsize=13)
qs=[i/100 for i in range(201)];curves=[]
for f,marker in zip(formats,['o','s','^']):
 rs=[r for r in rows if r['record_format']==f and r['species_name']];ys=[hill(rs,q) for q in qs]
 axs[2].plot(qs,ys,color=colors[f],lw=3,label=f+' (n = '+str(len(rs))+')')
 for q in [0,1,2]:axs[2].scatter([q],[hill(rs,q)],color=colors[f],s=40,marker=marker,zorder=3)
 axs[2].annotate(str(int(hill(rs,0))),(0,hill(rs,0)),xytext=(0,8),textcoords='offset points',ha='center',fontsize=13,color=colors[f])
 curves += [dict(record_format=f,q=q,hill_number=y) for q,y in zip(qs,ys)]
axs[2].set_xticks([0,1,2],['0\nRichness','1\nShannon','2\nInverse\nSimpson'])
axs[2].set(xlim=(-.12,2.12),ylabel='Effective number of species',title='C. Observed species-only Hill profiles',ylim=(0,max(len(v) for v in sets.values())*1.4))
axs[2].legend(frameon=False,fontsize=12,loc='upper right')
fig.suptitle('Human observations, preserved specimens and DNA\nGBIF + UCSB Summer 2026 survey',fontsize=16,y=.98)
fig.subplots_adjust(left=.12,right=.97,top=.82,bottom=.16,wspace=.95,hspace=.95)
for ext in ['png','pdf','svg']:fig.savefig(OUT/f'record_format_contributions.{ext}',dpi=250,facecolor='white')
write('hill_profiles.csv',curves)
print(json.dumps({k:v for k,v in meta.items() if k in ['combined_records','species_determined_records','duplicate_records','species_total','species_unique_to_format','species_shared_by_multiple_formats','species_in_all_three','pairwise_overlap','summaries']},indent=2))
