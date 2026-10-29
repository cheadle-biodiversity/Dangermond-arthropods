"""Exploratory record-frequency diagnostics; not a field-effort estimator.

Chao et al. (2014), doi:10.1890/13-0133.1; Chao & Jost (2012),
doi:10.1890/11-1952.1. Each named occurrence counts once, not each insect.
"""
from pathlib import Path
from collections import Counter
import csv, hashlib, json, math
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'outputs/hill-diversity/2026-10-27-insects/site_record_audit.csv'
OUT = ROOT / 'outputs/hill-diversity/2026-10-27-inventory-effort'
OUT.mkdir(parents=True, exist_ok=True)
rows = list(csv.DictReader(SOURCE.open()))
summary = []
for site in ["Perko's Beach", 'Lighthouse backdunes']:
    records = [r for r in rows if r['site_group'] == site]
    counts = Counter(r['analysis_taxon_name'] for r in records)
    frequency = Counter(counts.values())
    n, s, f1, f2 = len(records), len(counts), frequency[1], frequency[2]
    if f2:
        f0 = (n-1)/n * f1*f1/(2*f2)
    else:
        f0 = (n-1)/n * f1*(f1-1)/2
    a = f1/(n*f0+f1) if f1 else 0
    extra = f0 * (-math.expm1(n*math.log1p(-a))) if f0 else 0
    coverage = 1-f1/n*(1-a)
    assert 0 <= extra <= f0 and 0 <= coverage <= 1
    summary.append(dict(site=site,named_records=n,observed_species_units=s,
                        single_record_species=f1,two_record_species=f2,
                        conditional_chao1_richness=s+f0,
                        conditional_record_coverage=coverage,
                        additional_records_in_doubling_scenario=n,
                        total_records_after_doubling=2*n,
                        conditional_additional_species_at_double_records=extra,
                        conditional_species_at_double_records=s+extra,
                        distinct_recorded_dates=len({r['eventDate'] for r in records if r['eventDate']})))
assert [(r['named_records'],r['observed_species_units'],r['single_record_species'],r['two_record_species']) for r in summary] == [(71,36,23,6),(196,28,14,4)]
with (OUT/'inventory_effort_diagnostics.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
meta = dict(source=str(SOURCE.relative_to(ROOT)),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 method='Occurrence-record-frequency Chao1 diagnostic and richness extrapolation to twice the current number of named records. No bootstrap or confidence intervals; not iNEXT.',
 formulas=dict(f0='((n-1)/n)*f1^2/(2*f2) for f2>0; bias-corrected zero-doubleton alternative otherwise',a='f1/(n*f0+f1)',additional_species='f0*(1-(1-a)^m), with m=n',coverage='1-(f1/n)*(1-a)'),
 scope='Named species-level insect units only; all identification qualifiers retained together; no arachnids or higher-rank units.',
 assumptions=['Future records follow the same recording and identification process.', 'Occurrence frequencies are used as a surrogate distribution, not individual abundance.', 'Seasonality, habitat strata, method shifts, repeated observations and taxonomic sorting can change detection probabilities.'],
 limitations=['Pooled opportunistic and targeted data do not meet a standardized community sampling design.', 'Conditional values cannot be interpreted as site-wide species totals, actual completeness, or hours/trips required.', 'Coverage is probability mass of the observed record distribution, not fraction of all species.', 'No claim that doubling records completes either inventory.'],
 proposed_budget=dict(status='Planning assumption, not statistically estimated effort to completion',visits_per_site=6,daytime_seasonal_visits=4,dusk_night_visits=2,people=2,hours_per_visit=4,field_person_hours_per_site=48,field_person_hours_two_sites=96,excludes='Travel, trap exposure/service, specimen sorting, specialist identification, curation and data entry.'),
 references=['https://doi.org/10.1890/13-0133.1','https://doi.org/10.1890/11-1952.1'])
(OUT/'methods.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(summary,indent=2))
