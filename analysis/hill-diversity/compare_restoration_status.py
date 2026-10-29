"""Section 1.6: ResStatus comparison with audited survey-window effort.

Species and genus-only operational units describe records, not estimated fauna.
Run from any directory with Python; matplotlib is needed for the report figure.
"""
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import csv
import hashlib
import json
import math
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'data/raw/ecdysis/occurrences_Effort_Habitat_28Oct2026.csv'
CROSSWALK = ROOT / 'outputs/hill-diversity/2026-10-27-insects/ecdysis_species_record_audit.csv'
OUT = ROOT / 'outputs/hill-diversity/2026-10-28-restoration'
GROUPS = ['Dune', 'Active restoration']


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write(name, rows):
    with (OUT / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def hill(c, q):
    p = [n / sum(c.values()) for n in c.values()]
    if q == 0:
        return len(c)
    if q == 1:
        return math.exp(-sum(x * math.log(x) for x in p))
    return sum(x ** q for x in p) ** (1 / (1 - q))


def rarefy(c, m):
    n = sum(c.values())
    return sum(1 - (math.comb(n - x, m) / math.comb(n, m) if n - x >= m else 0)
               for x in c.values())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = read(SOURCE)
    assert len(source) == len({r['occurrenceID'] for r in source}) == 459
    crosswalk = {r['id']: r for r in read(CROSSWALK)}
    rows = []
    for original in source:
        group = {'dune': 'Dune', 'active restoration': 'Active restoration'}.get(original['ResStatus'].strip().lower())
        if not group:
            continue
        r = dict(original, analysis_group=group, analysis_unit='', unit_type='', exclusion_reason='')
        rank = r['taxonRank'].lower()
        if r['class'] != 'Insecta':
            r['exclusion_reason'] = 'outside Insecta'
        elif rank in ('species', 'subspecies'):
            previous = crosswalk[r['id']]
            assert previous['occurrenceID'] == r['occurrenceID']
            r['analysis_unit'] = previous['analysis_taxon_name']
            r['unit_type'] = 'named species'
        elif rank in ('genus', 'subgenus'):
            genus = re.match(r'[A-Z][a-z]+', r['genus']).group()
            r['analysis_unit'] = genus + ' sp. (unresolved)'
            r['unit_type'] = 'genus morphotype'
        else:
            r['exclusion_reason'] = 'identified above genus'
        # Effort belongs to a team survey window, not each occurrence or method.
        r['window_key'] = '|'.join([group, r['eventDate'], r['eventStart'], r['eventEnd'], r['surveyorCount']])
        rows.append(r)

    windows = defaultdict(list)
    for r in rows:
        windows[r['window_key']].append(r)
    event_rows = []
    for key, rs in windows.items():
        values = {float(r['personHours']) for r in rs}
        assert len(values) == 1
        effort = values.pop()
        first = rs[0]
        start = datetime.strptime(first['eventStart'], '%I:%M:%S %p')
        end = datetime.strptime(first['eventEnd'], '%I:%M:%S %p')
        calculated = (end - start).total_seconds() / 3600 * int(first['surveyorCount'])
        assert math.isclose(effort, calculated, abs_tol=1e-8)
        valid = [r for r in rs if r['analysis_unit']]
        event_rows.append(dict(window_key=key, analysis_group=first['analysis_group'],
                               date=first['eventDate'], start=first['eventStart'], end=first['eventEnd'],
                               surveyor_count=first['surveyorCount'], person_hours=effort,
                               sites='; '.join(sorted({r['siteName'] for r in rs})),
                               all_records=len(rs), insect_records=sum(r['class']=='Insecta' for r in rs),
                               eligible_records=len(valid), units=len({r['analysis_unit'] for r in valid}),
                               protocols='; '.join(sorted({r['samplingProtocol'] or '(blank)' for r in rs}))))
    event_rows.sort(key=lambda x: (x['date'], datetime.strptime(x['start'], '%I:%M:%S %p')))
    eligible = [r for r in rows if r['analysis_unit']]
    counters = {g: Counter(r['analysis_unit'] for r in eligible if r['analysis_group'] == g) for g in GROUPS}
    common_n = min(sum(c.values()) for c in counters.values())
    summaries = []
    for group, c in counters.items():
        selected = [r for r in rows if r['analysis_group'] == group]
        valid = [r for r in selected if r['analysis_unit']]
        es = [e for e in event_rows if e['analysis_group'] == group]
        hours = sum(e['person_hours'] for e in es)
        summary = dict(group=group, sites=len({r['siteName'] for r in selected}), survey_windows=len(es),
                       survey_dates=len({e['date'] for e in es}), person_hours=hours,
                       all_records=len(selected), insect_records=sum(r['class']=='Insecta' for r in selected),
                       eligible_records=len(valid), named_species_records=sum(r['unit_type']=='named species' for r in valid),
                       genus_morphotype_records=sum(r['unit_type']=='genus morphotype' for r in valid),
                       named_species_units=len({r['analysis_unit'] for r in valid if r['unit_type']=='named species'}),
                       genus_morphotype_units=len({r['analysis_unit'] for r in valid if r['unit_type']=='genus morphotype'}),
                       q0=hill(c, 0), q1=hill(c, 1), q2=hill(c, 2),
                       eligible_records_per_person_hour=len(valid)/hours,
                       rarefaction_records=common_n, rarefied_richness=rarefy(c, common_n))
        assert summary['q0'] >= summary['q1'] >= summary['q2'] >= 1
        summaries.append(summary)
    sets = [set(c) for c in counters.values()]
    overlap = dict(shared=len(sets[0] & sets[1]), dune_only=len(sets[0]-sets[1]),
                   restoration_only=len(sets[1]-sets[0]), union=len(sets[0]|sets[1]),
                   jaccard=len(sets[0]&sets[1])/len(sets[0]|sets[1]),
                   sorensen=2*len(sets[0]&sets[1])/(len(sets[0])+len(sets[1])))
    unit_rows = []
    for unit in sorted(sets[0] | sets[1]):
        records = [r for r in eligible if r['analysis_unit'] == unit]
        unit_rows.append(dict(analysis_unit=unit, unit_type=records[0]['unit_type'], order=records[0]['order'],
                              dune_records=counters['Dune'][unit], restoration_records=counters['Active restoration'][unit],
                              occurrence_group='shared' if unit in sets[0]&sets[1] else ('Dune only' if unit in sets[0] else 'Active restoration only')))
    accumulation = []
    for group in GROUPS:
        seen = set()
        hours = 0
        for e in [e for e in event_rows if e['analysis_group'] == group]:
            hours += e['person_hours']
            seen.update(r['analysis_unit'] for r in eligible if r['window_key'] == e['window_key'])
            accumulation.append(dict(group=group, window_key=e['window_key'], cumulative_person_hours=hours, cumulative_units=len(seen)))
    profiles = [dict(group=g, q=i/100, diversity=hill(c, i/100)) for g,c in counters.items() for i in range(201)]
    rarefaction = [dict(group=g, records=m, expected_units=rarefy(c,m)) for g,c in counters.items() for m in range(sum(c.values())+1)]
    fields = ['occurrenceID','id','scientificName','taxonRank','class','order','genus','specificEpithet','identificationQualifier','basisOfRecord','siteName','ResStatus','duneRelief','eventDate','eventStart','eventEnd','personHours','surveyorCount','samplingProtocol','analysis_group','window_key','analysis_unit','unit_type','exclusion_reason']
    write('record_audit.csv', [{k:r[k] for k in fields} for r in rows])
    write('survey_effort.csv',event_rows)
    write('summary.csv',summaries)
    write('unit_overlap.csv',unit_rows)
    write('effort_accumulation.csv',accumulation)
    write('hill_profiles.csv',profiles)
    write('record_rarefaction.csv',rarefaction)
    metadata = dict(source=str(SOURCE.relative_to(ROOT)), source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                    species_crosswalk=str(CROSSWALK.relative_to(ROOT)), crosswalk_sha256=hashlib.sha256(CROSSWALK.read_bytes()).hexdigest(),
                    grouping='Case-insensitive exact ResStatus values dune and Active restoration; no additional relief or habitat filter.',
                    effort='personHours alone, confirmed by user; already equals elapsed hours times surveyorCount. Unique group/date/start/end/team-size windows counted once, including the shared July 1 high/middle dune window.',
                    units='Species follow approved existing record-ID crosswalk; subspecies roll to species. Genus and subgenus identifications become one unresolved morphotype per genus across both groups, separate from named species; possible overlap is not resolved. Qualifiers retained without filtering.',
                    weighting='One occurrence record per vote; individualCount not used. Family and higher IDs excluded, not errors.',
                    effort_comparison='Chronological discovery at actual complete-window effort endpoints; no within-window interpolation, hour-based rarefaction, extrapolation or confidence intervals.',
                    rarefaction='Exact finite-record richness interpolation, not field-effort or coverage standardization.',
                    summary=summaries, overlap=overlap)
    (OUT/'analysis_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    assert len(rows)==303 and len(eligible)==269
    assert overlap['shared'] + overlap['dune_only'] + overlap['restoration_only'] == overlap['union']
    assert len(event_rows)==10
    for group in GROUPS:
        c=counters[group]
        assert math.isclose(rarefy(c,sum(c.values())),len(c))
        assert accumulation[[a['group'] for a in accumulation].index(group)]['cumulative_units'] > 0
    plot(counters,summaries,overlap,accumulation,rarefaction)
    print(json.dumps(dict(summary=summaries,overlap=overlap,top_units={g:c.most_common(6) for g,c in counters.items()}),indent=2))


def plot(counters, summaries, overlap, accumulation, rarefaction):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from figure_style import apply_style, TEAL, ORANGE, GRAY
    apply_style()
    colors={'Dune':TEAL,'Active restoration':ORANGE}
    fig,axs=plt.subplots(2,2,figsize=(12,9))
    for group,c in counters.items():
        color=colors[group]
        qs=[i/100 for i in range(201)]
        axs[0,0].plot(qs,[hill(c,q) for q in qs],color=color,lw=3,label=group)
        axs[0,0].scatter([0,1,2],[hill(c,q) for q in [0,1,2]],color=color,zorder=3)
        for q in [0,1,2]:
            offset = -18 if group == 'Dune' and q > 0 else 7
            axs[0,0].annotate(f'{hill(c,q):.1f}',(q,hill(c,q)),xytext=(0,offset),textcoords='offset points',ha='center',fontsize=12,color=color)
        a=[r for r in rarefaction if r['group']==group]
        axs[0,1].plot([r['records'] for r in a],[r['expected_units'] for r in a],color=color,lw=3)
        a=[r for r in accumulation if r['group']==group]
        axs[1,0].plot([r['cumulative_person_hours'] for r in a],[r['cumulative_units'] for r in a],color=color,marker='o',lw=2,label=group)
    axs[0,0].set(title='A. Observed Hill diversity',xlabel='Diversity order (q)',ylabel='Effective number of units',xticks=[0,1,2],ylim=(0,57))
    axs[0,0].legend(frameon=False,loc='upper right')
    axs[0,1].axvline(68,color=GRAY,linestyle=':',lw=1.5)
    axs[0,1].set(title='B. Record-based richness rarefaction',xlabel='Number of occurrence records',ylabel='Expected units',ylim=(0,55))
    axs[1,0].set(title='C. Discovery and recorded effort',xlabel='Cumulative person-hours',ylabel='Cumulative observed units',ylim=(0,55))
    axs[1,0].text(.02,.96,'Complete survey-window endpoints\nLines show chronological visit order',transform=axs[1,0].transAxes,va='top',fontsize=11)
    values=[overlap['dune_only'],overlap['shared'],overlap['restoration_only']]
    axs[1,1].barh([2,1,0],values,color=[TEAL,GRAY,ORANGE],height=.58)
    axs[1,1].set(yticks=[2,1,0],yticklabels=['Dune only','Shared','Restoration only'],xlabel='Observed identification units',title='D. Inventory overlap',xlim=(0,max(values)+6))
    for y,v in zip([2,1,0],values):axs[1,1].text(v+.4,y,str(v),va='center',fontsize=14)
    for ax in axs.flat:ax.grid(axis='y',alpha=.15)
    fig.suptitle('Dune and active-restoration insect inventories',fontsize=20,fontweight='bold',y=.99)
    fig.text(.5,.94,'UCSB Summer 2026 survey',ha='center',fontsize=15)
    fig.subplots_adjust(left=.08,right=.98,top=.85,bottom=.15,hspace=.5,wspace=.5)
    for ext in ['png','pdf','svg']:fig.savefig(OUT/f'restoration_comparison.{ext}',dpi=240,facecolor='white')
    plt.close(fig)


if __name__=='__main__':
    main()
