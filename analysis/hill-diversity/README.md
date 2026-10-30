# Dangermond Hill diversity analysis

## Beach and Upland comparison — 28 October 2026

Report section 1.4 uses the supplied `uplandBeach` assignments, excluding all
14 blank rows. Run `python3 analysis/hill-diversity/compare_beach_upland.py`.
The [full methods and results](../../outputs/hill-diversity/2026-10-28-beach-upland/README.md)
document the broader groups (Beach Sites 1–3; Upland Sites 4, 5, 7–13),
genus/subgenus morphotypes, record-ID species crosswalk, effort audit,
Hill profiles, record rarefaction and shared identities.

Beach has 54 units in 111 eligible records, and Upland 58 in 269; 19 are
shared. q1 is 39.62 versus 18.17, q2 is 29.27 versus 8.56, and richness
at 111 records is 54.00 versus 33.42. Units mix named species and unresolved
genus bins, which can overlap species within the same genus.

The user confirmed `personHours` alone, already team effort. Sum once per
group/date/start/end/team-size window: 19.83 recorded July hours for Beach,
27.50 for Upland. Nine order-only August Beach records lack effort and none
enters genus/species diversity. All eligible diversity records have effort.
**Effort is provisional:** two July 1 Beach records overlap the same team's
Upland visit. The source values are retained and the affected records listed
in `effort_review.csv`; no unsupported effort allocation is made. Record
rarefaction standardizes record count, not person-hours. Superseded species-only site results and doubling projections were removed from the active repository.

## Dune and active-restoration comparison — 28 October 2026

Report section 1.5 uses `ResStatus` from the 28 October survey CSV: `dune`
(high and middle dune sites) versus `Active restoration` (Sites 7–13).
Run `python3 analysis/hill-diversity/compare_restoration_status.py`.
The [full methods, results and output descriptions](../../outputs/hill-diversity/2026-10-28-restoration/README.md)
document selection, genus morphotypes, source hashes, effort aggregation,
observed Hill numbers, exact record rarefaction and inventory overlap.

The user confirmed that `personHours` already includes team size. Sum it
once per group/date/start/end/team-size window, including only once for the
shared July 1 high/middle dune window. Effort is 3.92 versus 23.58 person-hours.
Species and subspecies use the existing approved name crosswalk; genus and
subgenus identifications form one unresolved unit per genus across both groups.
These mixed identification units may overlap within genera and are not a
count of confirmed species. Family and higher IDs are outside this comparison.
No identification-qualifier filter is applied.

Dune has 68 eligible records and 20 units (15 named species + 5 genus bins);
active restoration has 201 records and 47 units (28 + 19). Nine units are
shared. q1 is 10.73 versus 14.61; q2 is 6.64 versus 6.90. Richness at 68
records is 20.00 versus 22.87. Rarefaction equalizes record count, not field
hours or methods. Chronological effort curves use complete-window endpoints.
The two groups differ in sites, dates, effort and collection emphasis, so this
describes their inventories rather than testing a causal restoration effect.
The species-only record-format analysis remains separate.

## Current species-only record-format comparison — 27 October 2026

The report compares **human observations, preserved specimens and DNA records**
from the saved GBIF preserve snapshot plus **UCSB Summer 2026 survey**. Run `python3 analysis/hill-diversity/compare_record_formats.py`
(matplotlib required). Outputs are in
`outputs/hill-diversity/2026-10-27-record-formats/`.

Only explicit named-species determinations enter any of the three figure panels.
GBIF records require SPECIES or SUBSPECIES rank and a named species/species key;
unnamed BOLD BINs are excluded even when GBIF assigns a species parent. Local
records require the approved species-level survey crosswalk. Subspecies roll
up to species; all species-level identifications are retained together without
qualifier filtering. Existing single-target name relationships are reused;
no new taxonomic matching service was called.

Of 14,508 distinct insect records in the combined input, **797** meet this
species-determination rule and represent **199 species**. All 423 local insect
records match GBIF by exact occurrenceID and are counted once, with local
reviewed determinations preferred. The deduplication audit preserves both source
IDs and name/basis differences. Institution + collection + catalog number is a
fallback that was not needed. Different identifiers can still conceal duplicate
biological events. No coordinate/date-only merging is performed.

| Record type | Species-determined records | Species (q0) | q1 | q2 |
|---|---:|---:|---:|---:|
| Human observations | 240 | 66 | 16.42 | 6.46 |
| Preserved specimens | 510 | 147 | 94.95 | 63.72 |
| DNA records | 47 | 24 | 21.66 | 19.90 |

DNA records are the explicitly species-determined MATERIAL_SAMPLE records from
verified source datasets: **44 iBOL records** (dataset
`040c5662-da76-4782-a48e-cdea1892d14c`, DOI `10.15468/inygc6`) and **three INSDC
Sequences records** (`d8cd16ba-bb74-4420-821e-083f2bac17c2`, DOI
`10.15468/sbmztx`). The three INSDC records have sequence links; iBOL provenance
supports the barcode classification for the other 44. Physical vouchers can
underlie DNA records; groups describe published occurrence formats, not mutually
exclusive laboratory technologies. PRESERVED_SPECIMEN is kept separate from DNA.

Fifty-one species occur only in human observations, 110 only in preserved
specimens, one only in DNA records (Ammopelmatus muwu), and 37 in at least two
formats. The pairwise overlaps are 15 human/preserved, one human/DNA and 23
preserved/DNA; one species appears in all three. Those overlapping counts must
not be added. The combined Hill values are q0=199, q1=95.47 and q2=43.46.

Each distinct species-determined occurrence contributes one vote, not
individualCount. These are observed frequency profiles, without rarefaction,
extrapolation or effort/completeness standardization. Taxon assignments are not
a new comprehensive validation of every GBIF identification. The previous
species-parent comparison (532 species, including GBIF species parents of
unnamed BIN records) is superseded and archived locally under
`data/raw/hill-analysis-history/2026-10-27-species-parent-assignments/`.

`record_format_summary.csv`, `species_contributions.csv`,
`species_format_overlap.csv`, `duplicate_record_audit.csv`, `hill_profiles.csv`
and `analysis_metadata.json` support the figure. Full-input and species-only
record audits are compressed and ignored by Git; source hashes identify inputs.
All plot panels use the eligible species-determined subset; full-input counts
in the audit/summary metadata are provenance, not the plotted comparison.

## Survey versus regional candidate species — 27 October 2026

Run `python3 analysis/hill-diversity/compare_candidate_pool.py` from the repository
root. This separate analysis answers two questions: how much of the regional
candidate list the recent survey documents, and how diverse/uneven the survey
records are. It uses pandas and Python's standard library.

The candidate pool is the union of the Level IV 6ap and 85a species checklists:
2,550 species, counting the 823 species shared between the lists once. All are
assumed potentially able to occur somewhere on Dangermond for this first pass;
there is no habitat filter, abundance weighting, fitted SDM or requirement for
previous preserve evidence. The observed sample uses only the recent Ecdysis
archive, not regional or historical GBIF records.

Of 423 insect records, 316 have species/subspecies identifications and 107 have
valid higher-taxon identifications. The latter do not enter the species profile.
Names follow the previously approved species crosswalk by Ecdysis ID; subspecies
roll up to species. On 27 October the user confirmed five previously unmatched
names in eight records as valid. They are retained exactly as written, with
identification qualifiers, through `reviewed_ecdysis_names.csv`. This is recorded
as user review rather than a new service match. The main profile contains 62
species-level identification units, including qualified identifications. A
service-crosswalk-only sensitivity has 308 records and 57 species, but is not the
primary result. Source IDs and occurrence IDs are unique; no GBIF records are
pooled into the observed sample, avoiding overlap between sources.

The list comparison records 45 shared species, 17 observed species outside the candidate pool, no pending
names, and 2,505 candidates not documented by a survey identification. Shared
species / candidate species is 45/2,550 = 1.7647%; it is not an estimate of sample
coverage, detection probability or the fraction of resident species sampled.
Candidate mismatches remain in the observed inventory. All species-level identifications are analyzed together; original identification
qualifiers remain in the record audit as source data.

For each observed taxon, p is its number of occurrence records divided by all
eligible records. Empirical Hill values are q0 = number of units,
q1 = exp(-sum(p * ln(p))), q2 = 1/sum(p²), following Chao et al. (2014), cited
below. The primary profile gives q0=62, q1=22.3364 and q2=10.6207. Each occurrence
receives equal weight; individualCount is not used. Repeated records need not be
different individuals, and these values do not estimate population abundance.
Species-level preserved specimens and human observations are also summarized
separately because source-specific recording emphasis affects evenness. No separate qualified/unqualified comparison is made.

Outputs in `outputs/hill-diversity/2026-10-27-insects/` contain the summary,
record audit, taxon frequencies, shared identities, observed taxa outside the
pool, pending names, candidate taxa not documented, and source SHA256 values. Superseded locality-based site outputs are no longer generated; use the Beach/Upland and restoration comparisons above.
All totals are checked against the source records and set partitions. These are
empirical descriptive values: no rarefaction, unseen-richness estimation,
extrapolation, confidence intervals or coverage standardization is claimed.
An equally weighted candidate list would have q0=q1=q2=2,550, so candidate
comparison uses richness and identities, not an invented abundance distribution.

## References

Chao et al. (2014). Rarefaction and extrapolation with Hill numbers. https://doi.org/10.1890/13-0133.1
