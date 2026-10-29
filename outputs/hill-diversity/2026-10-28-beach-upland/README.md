# Beach and Upland insect inventories

Report section 1.5 uses the UCSB Summer 2026 survey (this project).
Run `python3 analysis/hill-diversity/compare_beach_upland.py` from the
repository root with matplotlib installed. It imports the existing Hill
definitions, exact record-rarefaction function and input paths from
`compare_restoration_status.py`; it does not rerun or change section 1.6.

## Scope and identification units

The source is `data/raw/ecdysis/occurrences_Effort_Habitat_28Oct2026.csv`.
Select trimmed, case-insensitive `uplandBeach` values Beach and Upland.
Ignore all 14 rows with blank assignments. There are 445 selected source
records, including 419 Insecta. Beach includes Sites 1–3 (including the
coastal-slope/sea-cliff site labelled Beach in the supplied data); Upland
includes Sites 4, 5 and 7–13. Do not recode sites from names or coordinates.
The new groups therefore differ from the earlier Perco’s Beach versus
explicit lighthouse-backdune comparison.

Include insect Species, Subspecies, Genus and Subgenus determinations.
Species names reuse the approved record-ID crosswalk in
`outputs/hill-diversity/2026-10-27-insects/ecdysis_species_record_audit.csv`.
Subspecies roll to species. Pool genus/subgenus determinations as one
unresolved morphotype per genus, consistently across both habitats. This
includes the Dialictus subgenus records under Lasioglossum. All qualifiers
are retained together. Family and higher IDs remain valid records outside
this analysis, and non-insects are excluded. Each eligible occurrence
receives one vote; `individualCount` is not used.

Unresolved genus bins may duplicate named species within the same genus.
They are operational identification units rather than independently
validated morphospecies or confirmed additional species.

## Effort and unresolved source conflict

The user confirmed **personHours alone** for this comparison, consistent
with section 1.6. The field already equals elapsed time × surveyorCount.
Every complete window was checked against that calculation. Count effort
once per habitat/date/start/end/team-size window using source records before
taxonomic filtering. Do not multiply again by team size or sum per record,
method or site. The shared July 1 high/middle dune window counts once.

Beach has six timed July windows, with **19.83 recorded person-hours**.
Upland has ten, with **27.50 recorded person-hours**. Nine order-only Beach
records from August 18 lack time/effort. They remain in the source and insect
totals, but none qualifies for genus/species diversity. All 380 diversity
records have recorded effort. Unknown effort is not zero, and 19.83 hours
is not a complete July–August effort total.

**Effort remains provisional.** Two July 1 Perco’s Beach records
(`UCSB-IZC00079432`, *Blaesoxipha*; `UCSB-IZC00079437`, Tenebrionidae)
have a 10:20–11:45 window and 4.25 person-hours for the same named team
recorded at Upland Site 9 from 10:00–12:15 (6.75 person-hours). The source
does not establish how to allocate that overlap or which fields need
correction. Values are retained as recorded, not silently corrected or
summed as verified total team labor. `effort_review.csv` lists these records.
The diversity and overlap results do not depend on effort values.

## Results

| Measure | Beach | Upland |
|---|---:|---:|
| Sites | 3 | 9 |
| Timed survey windows | 6 | 10 |
| Recorded person-hours (provisional) | 19.83 | 27.50 |
| Insect records | 132 | 287 |
| Records used for diversity | 111 | 269 |
| Named species | 42 | 35 |
| Unresolved genus morphotypes | 12 | 23 |
| Identification units (q0) | 54 | 58 |
| Exponential Shannon (q1) | 39.62 | 18.17 |
| Inverse Simpson (q2) | 29.27 | 8.56 |
| Expected units at 111 records | 54.00 | 33.42 |

Nineteen units are shared (14 named species and five genus bins), 35 are
Beach-only and 39 Upland-only; union = 93. Jaccard similarity is 20.43%
and Sørensen similarity is 33.93%. Group-only means recorded in just one
inventory, not demonstrated habitat restriction. Shared genus bins do not
establish that the same biological species occurs in both habitats.

Beach records are more evenly distributed. Coleoptera contribute 66/111
eligible Beach records, with *Phaleria rotundata* the most frequent named
species (10). Upland records emphasize Hymenoptera (186/269);
*Bombus vosnesenskii* (68) and *Apis mellifera* (50) together contribute
43.9% of Upland records. These are occurrence frequencies, not standardized
abundance or habitat-health measures.

Hill definitions are q0 = observed units, q1 = exp(−Σp ln p), q2 = 1/Σp².
Exact finite-record richness interpolation uses
E[S(m)] = Σ[1 − choose(N−n_i,m)/choose(N,m)]. Rarefaction to 111 records
equalizes record count, not field hours, methods, identification resolution
or sample completeness. The chronological discovery plot shows actual
complete-window endpoints with provisional recorded effort; it does not
interpolate within visits, standardize hours or estimate completion time.
No coverage-based iNEXT, unseen richness, extrapolation, confidence intervals
or causal habitat-quality comparison is claimed.

The old 71-record/196-record species-only comparison and its exploratory
doubling projections remain in historical outputs. They are replaced in
the current report section, not reused for the new group definitions.

## Outputs and provenance

- `summary.csv`: group totals, effort availability and Hill metrics.
- `record_audit.csv`: all 445 selected records and inclusion decisions.
- `survey_effort.csv`: six Beach and ten Upland timed windows plus the
  untimed August Beach date group.
- `effort_review.csv`: the two records with overlapping team assignments.
- `unit_overlap.csv`: identities, group frequencies and overlap class.
- `hill_profiles.csv`, `record_rarefaction.csv`, `effort_accumulation.csv`:
  plotted data.
- `beach_upland_diversity.*`, `beach_upland_effort_overlap.*`: report figures.
- `analysis_metadata.json`: source and crosswalk hashes and explicit rules.

Checks enforce occurrence-ID uniqueness, crosswalk identity, complete-window
elapsed-time/team-size agreement, all eligible records having effort,
taxonomic-unit partitions, rarefaction endpoints and final accumulation
totals. Original data and previous outputs are preserved. The source CSV
is already ignored by Git; no new large data files are introduced.

Reference: Chao, A., et al. (2014). Rarefaction and extrapolation with Hill
numbers: a framework for sampling and estimation in species diversity
studies. *Ecological Monographs*, 84, 45–67.
https://doi.org/10.1890/13-0133.1. Only empirical Hill numbers and exact
finite-record richness interpolation are applied here.
