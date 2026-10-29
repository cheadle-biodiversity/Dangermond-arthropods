# Dune and active-restoration comparison

Section 1.6 of the report uses the UCSB Summer 2026 survey (this project),
with the grouping and effort columns supplied on 28 October 2026.
Run `python3 analysis/hill-diversity/compare_restoration_status.py` from the
repository root. Matplotlib is required for the figure.

## Selection and identification units

The source is `data/raw/ecdysis/occurrences_Effort_Habitat_28Oct2026.csv`.
Select the case-insensitive, trimmed `ResStatus` values `dune` and
`Active restoration`. The dune group includes Site 4 (high) and Site 5
(middle); active restoration includes Sites 7–13. Do not substitute a
`duneRelief` filter or assume all dune records are high-dune records.
This retains 303 source records, of which 287 are Insecta.

Use Insecta records identified to species, subspecies, genus or subgenus.
Species names reuse the approved record-ID crosswalk in
`outputs/hill-diversity/2026-10-27-insects/ecdysis_species_record_audit.csv`.
Subspecies are grouped under species. Genus and subgenus records are pooled
into one unresolved morphotype per genus, consistently across both groups.
The ten Dialictus subgenus records enter `Lasioglossum sp. (unresolved)`.
No separation is made by identification qualifier.

Named species and unresolved genus bins remain separate operational units.
A genus bin may overlap a named species in that genus: these units are not
confirmed additional species or independently established morphospecies.
Family and higher identifications remain valid observations outside this
comparison. Each eligible occurrence receives equal weight, irrespective
of `individualCount` or record format. There are 269 eligible records.

## Effort

The user confirmed that **`personHours` alone** is the effort measure;
it already includes `surveyorCount`. Every selected window was independently
checked against elapsed hours × team size. Do not multiply by team size again.

Count effort once per unique group/date/start/end/team-size survey window,
using all selected source records before taxonomic filtering. Do not sum
effort per occurrence, collection method or identification unit. On July 1,
Sites 4 and 5 share the 13:40–14:25 window and 2.25 team person-hours; count
that shared window once, not once for each site. The audit preserves both
sites. There are two dune windows and eight restoration windows, with no
missing effort in the selected data. This assumes repeated identical team
windows denote the same shared visit, rather than independent simultaneous
teams; the source does not assign effort separately within that window.

## Results

| Measure | Dune | Active restoration |
|---|---:|---:|
| Sites | 2 | 7 |
| Survey windows | 2 | 8 |
| Survey dates | 2 | 4 |
| Person-hours | 3.92 | 23.58 |
| Insect records | 70 | 217 |
| Eligible records | 68 | 201 |
| Named species | 15 | 28 |
| Unresolved genus morphotypes | 5 | 19 |
| Observed identification units (q0) | 20 | 47 |
| Exponential Shannon (q1) | 10.73 | 14.61 |
| Inverse Simpson (q2) | 6.64 | 6.90 |
| Expected units at 68 records | 20.00 | 22.87 |

Nine units are shared (eight named species and one genus morphotype),
with 11 dune-only and 38 restoration-only units, for a union of 58.
Jaccard similarity is 15.52%; Sørensen similarity is 26.87%.
Site-only means recorded only in one inventory, not habitat restriction.

Hill numbers use occurrence-record proportions: q0 counts units,
q1 = exp(−Σp ln p), q2 = 1/Σp². Exact finite-record richness interpolation
uses E[S(m)] = Σ[1 − choose(N−n_i,m)/choose(N,m)], including m=0 and m=N.
Rarefaction to 68 records standardizes recorded sample size, not field
person-hours, method, sample completeness or identification resolution.
Chronological accumulation plots use only complete survey-window endpoints;
connecting lines do not estimate discovery within visits. No equal-hour
comparison, extrapolation, confidence intervals or iNEXT run is claimed.

The higher pooled restoration richness accompanies approximately six times
the effort and more sites and dates. q2 is similar because both record
distributions are concentrated in common taxa. The largest dune count is
*Coelus ciliatus* (21/68); restoration is dominated by *Bombus vosnesenskii*
(61/201) and *Apis mellifera* (38/201). These are recorded frequencies, not
estimates of insect abundance. Habitat, method, season and identification
coverage prevent attributing the differences to restoration treatment.

## Files and checks

- `record_audit.csv`: all 303 selected records, source fields, inclusion
  decisions, units and survey-window keys.
- `survey_effort.csv`: the ten deduplicated survey windows and effort.
- `summary.csv`, `unit_overlap.csv`: metrics and identification identities.
- `hill_profiles.csv`, `record_rarefaction.csv`, `effort_accumulation.csv`:
  plotted values.
- `restoration_comparison.png`, `.pdf`, `.svg`: report figure.
- `analysis_metadata.json`: source and crosswalk SHA-256, rules and totals.

Checks enforce unique source occurrence IDs, crosswalk identity consistency,
elapsed-time/team-size agreement, valid Hill-number ordering, exact
rarefaction endpoints and overlap partitions. The original source and all
previous analyses remain intact. Raw data are already excluded by `.gitignore`.

Reference: Chao, A., et al. (2014). Rarefaction and extrapolation with Hill
numbers: a framework for sampling and estimation in species diversity
studies. *Ecological Monographs*, 84, 45–67.
https://doi.org/10.1890/13-0133.1. This analysis uses empirical Hill numbers
and finite-record interpolation, not the full estimation framework.
