from pathlib import Path
import csv, json, gzip, re, hashlib
from collections import Counter
import numpy as np
from scipy.special import gammaln
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/hill-diversity/2026-10-26'
OUT.mkdir(parents=True,exist_ok=True)
SRC=ROOT/'data/raw/gbif/preserve_2026-10-26'
def readcsv(p,encoding='utf-8-sig'):
    return list(csv.DictReader(open(p,encoding=encoding,newline='')))
ec=readcsv(ROOT/'data/raw/ecdysis/extracted/SymbOutput_2026-10-26_124013_DwC-A/occurrences.csv','iso-8859-1')
ec=[r for r in ec if r['phylum']=='Arthropoda']
scope=readcsv(SRC/'terrestrial_arthropod_occurrences.csv')
keys={int(r['key']) for r in scope}
gb=[r for r in map(json.loads,gzip.open(SRC/'gbif_all_arthropods_within_preserve.jsonl.gz','rt')) if int(r['key']) in keys]
assert len(gb)==14601 and len({r['key'] for r in gb})==14601
def ec_species(r):
    if r['taxonRank'] not in ('Species','Subspecies'): return None
    return (r['genus']+' '+r['specificEpithet']).strip() if r['genus'] and r['specificEpithet'] else None
def gb_species(r):
    return str(r['speciesKey']) if r.get('speciesKey') and r.get('species') else None
def bin_key(r):
    return r.get('scientificName') if re.fullmatch(r'BOLD:[A-Z0-9]+',r.get('scientificName','')) else None
def order_key(r):
    x=r.get('order','')
    return 'Blattodea' if x=='Isoptera' else (x or None)
def count(rows,fn): return Counter(k for r in rows if (k:=fn(r)))
series={
 'Ecdysis: named species':count(ec,ec_species),
 'GBIF: named species assignments':count(gb,gb_species),
 'GBIF: barcode BINs':count(gb,bin_key),
 'Ecdysis: orders':count(ec,order_key),
 'GBIF: orders':count(gb,order_key),
 'Ecdysis: named species, unqualified IDs':count([r for r in ec if not r['identificationQualifier'].strip()],ec_species),
 'Ecdysis: named species, preserved only':count([r for r in ec if r['basisOfRecord']=='PreservedSpecimen'],ec_species),
 'GBIF: named species, explicit species/subspecies rank':count([r for r in gb if r.get('taxonRank') in ('SPECIES','SUBSPECIES')],gb_species),
 'Ecdysis: Perko’s Beach, July':count([r for r in ec if r['month']=='7' and ('percos' in r['locality'].lower() or "perco's" in r['locality'].lower())],ec_species),
 'Ecdysis: lighthouse area, July':count([r for r in ec if r['month']=='7' and 'lighthouse' in r['locality'].lower()],ec_species),
}
def hill(c,q):
    p=np.asarray(list(c.values()),dtype=float);p=p/p.sum()
    if q==0:return float(len(p))
    if abs(q-1)<1e-10:return float(np.exp(-np.sum(p*np.log(p))))
    return float(np.sum(p**q)**(1/(1-q)))
def rarefaction(c,m):
    n=np.asarray(list(c.values()),dtype=int);N=int(n.sum())
    if m==0:return 0.
    if m==N:return float(len(n))
    good=(N-n)>=m
    absent=np.zeros(len(n))
    base=gammaln(N+1)-gammaln(m+1)-gammaln(N-m+1)
    absent[good]=np.exp(gammaln(N-n[good]+1)-gammaln(m+1)-gammaln(N-n[good]-m+1)-base)
    return float(np.sum(1-absent))
def writecsv(name,rows,fields):
    with open(OUT/name,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
qs=np.linspace(0,3,151)
summary=[dict(series=k,records=sum(v.values()),taxa=len(v),q0=hill(v,0),q1=hill(v,1),q2=hill(v,2)) for k,v in series.items()]
writecsv('hill_summary.csv',summary,list(summary[0]))
profile=[dict(series=k,q=float(q),diversity=hill(v,q)) for k,v in series.items() for q in qs]
writecsv('hill_profiles.csv',profile,['series','q','diversity'])
rar=[]
for k in ['Ecdysis: named species','GBIF: named species assignments','GBIF: barcode BINs']:
    c=series[k];N=sum(c.values());ms=np.unique(np.r_[0,np.linspace(1,N,220,dtype=int),min(324,N),N])
    vals=[rarefaction(c,int(m)) for m in ms]
    assert np.all(np.diff(vals)>=-1e-6) and abs(vals[-1]-len(c))<1e-8
    rar.extend(dict(series=k,records=int(m),expected_taxa=x) for m,x in zip(ms,vals))
writecsv('record_rarefaction.csv',rar,['series','records','expected_taxa'])
names={str(r['speciesKey']):r['species'] for r in gb if r.get('speciesKey') and r.get('species')}
freq=[dict(series=k,taxon_key=tax,taxon_name=names.get(tax,tax) if k.startswith('GBIF: named') else tax,records=n) for k,c in series.items() for tax,n in sorted(c.items())]
writecsv('taxon_record_frequencies.csv',freq,['series','taxon_key','taxon_name','records'])
audit=[]
for source,rows,fn in [('Ecdysis',ec,ec_species),('GBIF',gb,gb_species)]:
    for r in rows:
        audit.append(dict(source=source,record_id=r.get('occurrenceID') or str(r.get('key')),scientific_name=r.get('scientificName',''),rank=r.get('taxonRank',''),named_species_key=fn(r) or '',bin=bin_key(r) or '',order=order_key(r) or '',basis=r.get('basisOfRecord',''),qualifier=r.get('identificationQualifier',''),locality=r.get('locality',''),event_date=r.get('eventDate','')))
writecsv('analysis_record_audit.csv',audit,list(audit[0]))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','savefig.facecolor':'white'})
colors=['#007C91','#C05A2B','#7754A3']
def plot_profile(ax,items,title,unit):
    for i,k in enumerate(items):
        c=series[k];ax.plot(qs,[hill(c,q) for q in qs],lw=2.5,color=colors[i],label=f'{k}\n{sum(c.values()):,} records; {len(c):,} taxa')
        ax.scatter([0,1,2],[hill(c,q) for q in [0,1,2]],color=colors[i],s=25,zorder=3)
    ax.set(title=title,xlabel='Diversity order q',ylabel=unit,xticks=[0,1,2,3]);ax.grid(alpha=.16);ax.legend(frameon=False,fontsize=8.5)
fig,axs=plt.subplots(2,2,figsize=(14,10.5))
plot_profile(axs[0,0],['Ecdysis: named species','GBIF: named species assignments'],'A  Named-species profiles','Effective number of named species')
plot_profile(axs[0,1],['GBIF: barcode BINs'],'B  GBIF molecular units (separate analysis)','Effective number of barcode BINs')
plot_profile(axs[1,0],['Ecdysis: orders','GBIF: orders'],'C  Broad taxonomic coverage','Effective number of orders')
ax=axs[1,1]
for i,k in enumerate(['Ecdysis: named species','GBIF: named species assignments']):
    a=[r for r in rar if r['series']==k];ax.plot([r['records'] for r in a],[r['expected_taxa'] for r in a],lw=2.5,color=colors[i],label=k)
ax.set(title='D  Named-species record rarefaction (q = 0)',xlabel='Number of occurrence records',ylabel='Expected number of named species');ax.grid(alpha=.16);ax.legend(frameon=False,fontsize=8.5)
fig.suptitle('Dangermond Preserve — Hill diversity curves',fontsize=19,fontweight='bold',y=.99)
fig.text(.5,.945,'Ecdysis: July–August 2026  |  GBIF: all years in the saved Preserve terrestrial-arthropod extract',ha='center',fontsize=11)
fig.text(.5,.018,'Record-frequency diversity, not individual abundance. Higher-rank identifications remain valid but are excluded from species profiles.\nBINs are molecular units, not confirmed species; sources overlap and differ in sampling methods and identification coverage.',ha='center',fontsize=9,color='#454545')
fig.tight_layout(rect=[0,.065,1,.92])
for ext in ['png','pdf','svg']:fig.savefig(OUT/f'Hill_diversity_overview.{ext}',dpi=220)
plt.close(fig)
fig,ax=plt.subplots(figsize=(10,6.5))
plot_profile(ax,['Ecdysis: Perko’s Beach, July','Ecdysis: lighthouse area, July'],'July 2026 — locality-specific named-species profiles','Effective number of named species')
fig.text(.5,.025,'Perko’s Beach and lighthouse localities are separate. Record frequencies include provisional species identifications.\nUnequal effort and methods prevent interpretation as a standardized habitat-quality comparison.',ha='center',fontsize=9)
fig.tight_layout(rect=[0,.09,1,1])
for ext in ['png','pdf','svg']:fig.savefig(OUT/f'Hill_profiles_Perkos_vs_lighthouse.{ext}',dpi=220)
plt.close(fig)
overlap=len({r['occurrenceID'] for r in ec if r['occurrenceID']} & {r.get('occurrenceID') for r in gb if r.get('occurrenceID')})
meta={'ecdysis_arthropod_records':len(ec),'ecdysis_gastropod_excluded':1,'gbif_terrestrial_records':len(gb),'shared_occurrence_ids':overlap,'summary':summary,'sources':['SymbOutput_2026-10-26_124013_DwC-A.zip','saved GBIF extract dated 2026-10-26'],'weighting':'one vote per occurrence record; individualCount not used','scope':'terrestrial-associated Arthropoda within the saved Preserve boundary; aquatic juvenile insects included as in original GBIF extract','method':'empirical Hill profiles q=0..3 and exact finite-record richness rarefaction; no extrapolation, confidence intervals, unseen-diversity estimates, or population inference'}
(OUT/'analysis_metadata.json').write_text(json.dumps(meta,indent=2))
lines=['# Dangermond Preserve: Hill diversity curves','', 'These are empirical diversity profiles weighted by occurrence-record frequency. They describe the available records rather than standardized community abundance.','', '| Dataset / taxonomic unit | Records used | q = 0 | q = 1 | q = 2 |','|---|---:|---:|---:|---:|']
for s in summary:lines.append(f"| {s['series']} | {s['records']:,} | {s['q0']:.0f} | {s['q1']:.2f} | {s['q2']:.2f} |")
lines += ['', '## Reading the figures','', '- q = 0 counts observed taxa; q = 1 is exp(Shannon entropy); q = 2 is inverse Simpson concentration. All are expressed as effective numbers of the stated taxonomic unit. Larger q gives more weight to frequently recorded taxa.', '- The overview compares Ecdysis and GBIF named-species assignments, shows GBIF BINs separately, compares order-level coverage, and shows exact named-species richness rarefaction over occurrence records.', '- The second figure keeps July Perko’s Beach and lighthouse localities separate. It uses named species and species-level parents of subspecies, rather than mixing ranks.', '', '## Data and methods','', f'- Ecdysis: {len(ec)} arthropod records from the supplied 12:40:13 archive; the single gastropod is excluded. All arthropods in that export are treated as terrestrial-associated under the project scope.', f'- GBIF: {len(gb):,} terrestrial-associated arthropod records in the previously saved Preserve extract, across all years and contributing institutions. No new GBIF download was made. The original boundary and terrestrial-scope decisions remain in the GBIF project folder.', '- Named GBIF units use speciesKey and species assignments already present in the saved GBIF responses. This includes unranked BIN records that GBIF places beneath a named species. The explicit species/subspecies-rank sensitivity row shows the effect of excluding those assignments. These GBIF interpretations have not all been independently validated.', '- Ecdysis species use genus + specificEpithet; subspecies are rolled up to species, and the two Lasioglossum pavonotum name forms are combined. Scientific-name spellings otherwise follow the archive. Provisional identifications are included in the primary profile; a separate sensitivity row excludes every nonempty identificationQualifier.', '- Genus-, family-, order- and other higher-rank identifications are valid records but cannot enter a species-only profile. No arbitrary species were assigned to them.', '- BOLD BINs use the full scientificName identifier BOLD:xxxxxxx. A BIN is a molecular clustering unit, not a confirmed biological species. BIN and named-species panels overlap in records and must not be added together.', '- Order profiles retain every record with an order. Isoptera is merged into Blattodea for consistent treatment. Missing orders are omitted, not counted as an artificial order.', '- Each occurrence record receives equal weight; individualCount is not used because it is absent or inconsistent across the sources. Repeated observations are not necessarily different individuals.', f'- The two sources share {overlap} occurrenceIDs across the terrestrial scope. They are displayed separately, not pooled or treated as independent samples. Cross-publisher duplicate events or specimens were not independently resolved.', '- Richness rarefaction uses E[S_m] = sum_i [1 - choose(N - n_i, m) / choose(N, m)], drawing records without replacement from the saved dataset. This is finite-record subsampling, not an estimate of unseen species or a guarantee of equal survey effort. No bootstrap confidence bands or extrapolation are shown.', '- The GBIF pool is dominated by barcode material samples and combines different methods, dates and habitats. Curves cannot establish relative habitat health, total Preserve richness, or ecological superiority of one source or site.', '', '## Reference','', 'Chao, A., Gotelli, N. J., Hsieh, T. C., Sander, E. L., Ma, K. H., Colwell, R. K., & Ellison, A. M. (2014). Rarefaction and extrapolation with Hill numbers: a framework for sampling and estimation in species diversity studies. Ecological Monographs, 84, 45–67. https://doi.org/10.1890/13-0133.1', '', 'The present analysis applies empirical Hill-number definitions and exact richness interpolation only; it does not implement the full Chao et al. estimation framework.']
(OUT/'Hill_curves_notes.md').write_text('\n'.join(lines)+'\n')
assert all(s['q0']+1e-9>=s['q1']>=s['q2']-1e-9>=1 for s in summary)
print(json.dumps(meta,indent=2))
