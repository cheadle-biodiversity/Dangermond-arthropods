"""Section 1.5: Beach/Upland inventories from uplandBeach and team person-hours."""
from collections import Counter, defaultdict
from datetime import datetime
import csv
import hashlib
import json
import math
import re

from compare_restoration_status import read, hill, rarefy, SOURCE, CROSSWALK, ROOT

OUT = ROOT / 'outputs/hill-diversity/2026-10-28-beach-upland'
GROUPS = ['Beach', 'Upland']


def write(name, rows):
    with (OUT/name).open('w', newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=read(SOURCE)
    assert len(source)==len({r['occurrenceID'] for r in source})==459
    crosswalk={r['id']:r for r in read(CROSSWALK)}
    rows=[]
    for original in source:
        group={'beach':'Beach','upland':'Upland'}.get(original['uplandBeach'].strip().lower())
        if not group:continue
        r=dict(original,analysis_group=group,analysis_unit='',unit_type='',exclusion_reason='')
        rank=r['taxonRank'].lower()
        if r['class']!='Insecta':r['exclusion_reason']='outside Insecta'
        elif rank in ('species','subspecies'):
            previous=crosswalk[r['id']]
            assert previous['occurrenceID']==r['occurrenceID']
            r['analysis_unit']=previous['analysis_taxon_name'];r['unit_type']='named species'
        elif rank in ('genus','subgenus'):
            genus=re.match(r'[A-Z][a-z]+',r['genus']).group()
            r['analysis_unit']=genus+' sp. (unresolved)';r['unit_type']='genus morphotype'
        else:r['exclusion_reason']='identified above genus'
        r['effort_available']=bool(r['personHours'] and r['eventStart'] and r['eventEnd'])
        r['window_key']='|'.join([group,r['eventDate'],r['eventStart'],r['eventEnd'],r['surveyorCount']])
        rows.append(r)
    windows=defaultdict(list)
    for r in rows:windows[r['window_key']].append(r)
    events=[]
    for key,rs in windows.items():
        first=rs[0];valid=[r for r in rs if r['analysis_unit']]
        values={r['personHours'] for r in rs};assert len(values)==1
        available=first['effort_available'];assert all(r['effort_available']==available for r in rs)
        hours=float(first['personHours']) if available else ''
        if available:
            start=datetime.strptime(first['eventStart'],'%I:%M:%S %p');end=datetime.strptime(first['eventEnd'],'%I:%M:%S %p')
            assert math.isclose(hours,(end-start).total_seconds()/3600*int(first['surveyorCount']),abs_tol=1e-8)
        events.append(dict(window_key=key,group=first['analysis_group'],date=first['eventDate'],start=first['eventStart'],end=first['eventEnd'],surveyor_count=first['surveyorCount'],person_hours=hours,effort_available=available,
                           sites='; '.join(sorted({r['siteName'] for r in rs})),all_records=len(rs),insect_records=sum(r['class']=='Insecta' for r in rs),eligible_records=len(valid),units=len({r['analysis_unit'] for r in valid})))
    events.sort(key=lambda x:(x['date'],datetime.strptime(x['start'],'%I:%M:%S %p') if x['start'] else datetime.min))
    eligible=[r for r in rows if r['analysis_unit']]
    counters={g:Counter(r['analysis_unit'] for r in eligible if r['analysis_group']==g) for g in GROUPS}
    common_n=min(sum(c.values()) for c in counters.values())
    summaries=[]
    for g,c in counters.items():
        selected=[r for r in rows if r['analysis_group']==g];valid=[r for r in eligible if r['analysis_group']==g]
        ev=[e for e in events if e['group']==g];known=[e for e in ev if e['effort_available']]
        hours=sum(e['person_hours'] for e in known)
        summaries.append(dict(group=g,sites=len({r['siteName'] for r in selected}),survey_dates=len({r['eventDate'] for r in selected}),timed_survey_windows=len(known),untimed_date_groups=len(ev)-len(known),recorded_person_hours=hours,
                              all_records=len(selected),insect_records=sum(r['class']=='Insecta' for r in selected),eligible_records=len(valid),eligible_records_with_effort=sum(r['effort_available'] for r in valid),records_without_effort=sum(not r['effort_available'] for r in selected),
                              named_species_records=sum(r['unit_type']=='named species' for r in valid),genus_morphotype_records=sum(r['unit_type']=='genus morphotype' for r in valid),
                              named_species_units=len({r['analysis_unit'] for r in valid if r['unit_type']=='named species'}),genus_morphotype_units=len({r['analysis_unit'] for r in valid if r['unit_type']=='genus morphotype'}),
                              q0=hill(c,0),q1=hill(c,1),q2=hill(c,2),eligible_records_per_recorded_person_hour=sum(r['effort_available'] for r in valid)/hours,rarefaction_records=common_n,rarefied_richness=rarefy(c,common_n)))
    a,b=[set(counters[g]) for g in GROUPS]
    overlap=dict(shared=len(a&b),beach_only=len(a-b),upland_only=len(b-a),union=len(a|b),jaccard=len(a&b)/len(a|b),sorensen=2*len(a&b)/(len(a)+len(b)))
    units=[]
    for unit in sorted(a|b):
        rs=[r for r in eligible if r['analysis_unit']==unit]
        units.append(dict(analysis_unit=unit,unit_type=rs[0]['unit_type'],order=rs[0]['order'],beach_records=counters['Beach'][unit],upland_records=counters['Upland'][unit],occurrence_group='shared' if unit in a&b else ('Beach only' if unit in a else 'Upland only')))
    accumulation=[]
    for g in GROUPS:
        seen=set();hours=0
        for event in [e for e in events if e['group']==g and e['effort_available']]:
            hours+=event['person_hours'];seen.update(r['analysis_unit'] for r in eligible if r['window_key']==event['window_key'])
            accumulation.append(dict(group=g,window_key=event['window_key'],cumulative_person_hours=hours,cumulative_units=len(seen)))
    profiles=[dict(group=g,q=i/100,diversity=hill(c,i/100)) for g,c in counters.items() for i in range(201)]
    rarefaction=[dict(group=g,records=m,expected_units=rarefy(c,m)) for g,c in counters.items() for m in range(sum(c.values())+1)]
    fields=['occurrenceID','id','catalogNumber','recordedBy','scientificName','taxonRank','class','order','genus','specificEpithet','identificationQualifier','basisOfRecord','siteName','uplandBeach','ResStatus','duneRelief','eventDate','eventStart','eventEnd','personHours','surveyorCount','samplingProtocol','analysis_group','window_key','effort_available','analysis_unit','unit_type','exclusion_reason']
    write('record_audit.csv',[{k:r[k] for k in fields} for r in rows]);write('survey_effort.csv',events);write('summary.csv',summaries);write('unit_overlap.csv',units);write('effort_accumulation.csv',accumulation);write('hill_profiles.csv',profiles);write('record_rarefaction.csv',rarefaction)
    meta=dict(source=str(SOURCE.relative_to(ROOT)),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),species_crosswalk=str(CROSSWALK.relative_to(ROOT)),crosswalk_sha256=hashlib.sha256(CROSSWALK.read_bytes()).hexdigest(),
              grouping='Trimmed, case-insensitive uplandBeach = Beach or Upland; 14 blank rows excluded. Use supplied assignments, including beach-labelled coastal slope/sea-cliff sites. No site-name reassignment.',
              effort='User confirmed personHours alone, already team hours. Count once per group/date/start/end/team-size window before taxonomic filtering. Shared high/middle dune window counted once. Missing effort stays missing, never zero.',
              units='Existing approved species crosswalk; subspecies roll to species. One unresolved morphotype per genus for genus/subgenus records, consistent across groups. Genus bins may overlap named species, so units are not confirmed species richness. No qualifier filtering.',
              weighting='Each eligible Insecta occurrence receives equal weight; no individualCount weighting. Family/higher IDs remain valid records outside diversity scope.',
              effort_missing='Nine Beach order-only records on 18 August lack effort. Included in source inventory audit/insect total, excluded by rank from diversity. All 380 diversity records have effort. Unknown August effort excluded from effort sums and accumulation; 19.83 Beach hours are known July effort, not total July–August effort.',
              effort_conflict='The same recorded team has Beach July 1 10:20–11:45 (4.25 hours, two records UCSB-IZC00079432 and UCSB-IZC00079437) overlapping Upland July 1 10:00–12:15 (6.75 hours). Values are retained as recorded, with no unsupported allocation between habitats; effort totals/accumulation are provisional. Do not sum group hours as verified total team labor.',
              curves='Empirical Hill q0–2; exact finite-record richness interpolation. Chronological accumulation at complete recorded-effort survey-window endpoints, provisional because of the cross-habitat overlap. No equal-hour interpolation, coverage-based iNEXT, extrapolation or confidence intervals.',summary=summaries,overlap=overlap)
    (OUT/'analysis_metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    issues=[dict(issue='cross-habitat team-window overlap',catalogNumber=r['catalogNumber'],occurrenceID=r['occurrenceID'],scientificName=r['scientificName'],eventDate=r['eventDate'],eventStart=r['eventStart'],eventEnd=r['eventEnd'],personHours=r['personHours'],siteName=r['siteName'],note='Same team also assigned to Site 9 Upland 10:00–12:15 on July 1; verify date, site or effort allocation. Source retained unchanged.') for r in rows if r['analysis_group']=='Beach' and r['eventDate']=='2026-07-01' and r['eventStart']=='10:20:00 AM']
    assert len(issues)==2
    write('effort_review.csv',issues)
    assert len(rows)==445 and len(eligible)==380 and len(source)-len(rows)==14
    assert len(events)==17 and sum(e['effort_available'] for e in events)==16
    assert all(r['effort_available'] for r in eligible)
    for s in summaries:
        assert s['q0']>=s['q1']>=s['q2']>=1
        c=counters[s['group']];assert math.isclose(rarefy(c,sum(c.values())),len(c))
        assert [e for e in accumulation if e['group']==s['group']][-1]['cumulative_units']==s['q0']
    assert overlap['shared']+overlap['beach_only']+overlap['upland_only']==overlap['union']
    plot(counters,summaries,overlap,accumulation,rarefaction)
    print(json.dumps(dict(summary=summaries,overlap=overlap,top_units={g:c.most_common(7) for g,c in counters.items()}),indent=2))


def plot(counters,summaries,overlap,accumulation,rarefaction):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from figure_style import apply_style,TEAL,ORANGE,GRAY
    apply_style();colors={'Beach':TEAL,'Upland':ORANGE}
    fig,axs=plt.subplots(2,1,figsize=(8.5,8.5))
    for g,c in counters.items():
        color=colors[g];qs=[i/100 for i in range(201)]
        axs[0].plot(qs,[hill(c,q) for q in qs],color=color,lw=3,label=f'{g} (n = {sum(c.values())})')
        axs[0].scatter([0,1,2],[hill(c,q) for q in [0,1,2]],color=color,zorder=3)
        for q in [0,1,2]:axs[0].annotate(f'{hill(c,q):.1f}',(q,hill(c,q)),xytext=(0,8),textcoords='offset points',ha='center',fontsize=13,color=color)
        rs=[r for r in rarefaction if r['group']==g]
        axs[1].plot([r['records'] for r in rs],[r['expected_units'] for r in rs],color=color,lw=3,label=g)
    axs[0].set(title='A. Observed Hill diversity',xlabel='Diversity order (q)',ylabel='Effective number of units',xticks=[0,1,2],ylim=(0,70));axs[0].legend(frameon=False,fontsize=13)
    common=summaries[0]['rarefaction_records'];axs[1].axvline(common,color=GRAY,linestyle=':',lw=1.5)
    axs[1].set(title='B. Record-based richness rarefaction',xlabel='Number of occurrence records',ylabel='Expected identification units',ylim=(0,65));axs[1].legend(frameon=False,fontsize=13)
    fig.suptitle('Beach and upland insect diversity',fontsize=19,fontweight='bold',y=.99)
    fig.text(.5,.945,'UCSB Summer 2026 survey',ha='center',fontsize=14)
    for ax in axs:ax.grid(axis='y',alpha=.15)
    fig.subplots_adjust(left=.14,right=.96,top=.85,bottom=.14,hspace=.5)
    for ext in ['png','pdf','svg']:fig.savefig(OUT/f'beach_upland_diversity.{ext}',dpi=240,facecolor='white')
    plt.close(fig)
    fig,axs=plt.subplots(2,1,figsize=(8.5,8.5))
    for g in GROUPS:
        a=[r for r in accumulation if r['group']==g]
        axs[0].plot([r['cumulative_person_hours'] for r in a],[r['cumulative_units'] for r in a],color=colors[g],marker='o',lw=2.5,label=g)
    axs[0].set(title='A. Discovery and recorded effort',xlabel='Cumulative recorded person-hours',ylabel='Cumulative observed units',ylim=(0,65));axs[0].legend(frameon=False)
    values=[overlap['beach_only'],overlap['shared'],overlap['upland_only']]
    axs[1].barh([2,1,0],values,color=[TEAL,GRAY,ORANGE],height=.58)
    axs[1].set(yticks=[2,1,0],yticklabels=['Beach only','Shared','Upland only'],xlabel='Observed identification units',title='B. Inventory overlap',xlim=(0,max(values)+7))
    for y,v in zip([2,1,0],values):axs[1].text(v+.5,y,str(v),va='center',fontsize=14)
    for ax in axs:ax.grid(axis='y',alpha=.15)
    fig.suptitle('Survey effort and shared insect inventory',fontsize=19,fontweight='bold',y=.99)
    fig.text(.5,.945,'UCSB Summer 2026 survey',ha='center',fontsize=14)
    fig.subplots_adjust(left=.19,right=.96,top=.85,bottom=.15,hspace=.5)
    for ext in ['png','pdf','svg']:fig.savefig(OUT/f'beach_upland_effort_overlap.{ext}',dpi=240,facecolor='white')
    plt.close(fig)


if __name__=='__main__':main()
