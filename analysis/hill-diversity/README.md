# Dangermond Hill diversity analysis

## Beach and Upland comparison — 28 October 2026

Section 1.5 now uses the supplied `uplandBeach` assignments, excluding all
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
rarefaction standardizes record count, not person-hours. Earlier species-only
site results and doubling projections are historical, not the current 1.5.

## Dune and active-restoration comparison — 28 October 2026

Section 1.6 now uses `ResStatus` from the 28 October survey CSV: `dune`
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
The older species-only site and record-format analyses remain unchanged.

## Current species-only record-format comparison — 27 October 2026

The report compares **human observations, preserved specimens and DNA records**
from the saved GBIF preserve snapshot plus **UCSB Summer 2026 survey (this
project)**. Run `python3 analysis/hill-diversity/compare_record_formats.py`
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

## Recent-survey insect-only comparison — 27 October 2026

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
pool, pending names, candidate taxa not documented, and source SHA256 values.
All totals are checked against the source records and set partitions. These are
empirical descriptive values: no rarefaction, unseen-richness estimation,
extrapolation, confidence intervals or coverage standardization is claimed.
An equally weighted candidate list would have q0=q1=q2=2,550, so candidate
comparison uses richness and identities, not an invented abundance distribution.

### Perko's Beach and explicitly recorded lighthouse backdunes

The current script also assigns a site group from the recorded locality and
habitat text. Beach-name variants identify Perko's Beach; an explicit
backdune description identifies the backdunes. Lighthouse coordinates alone
do not assign a habitat. Other/unspecified localities remain preserve-wide.
Of 316 species-level records, 71 are assigned to Perko's, 196 to explicit
backdunes, and 49 remain other/unspecified. The two named sites share seven
units, with 29 unique to Perko's and 21 unique to backdunes (union 57).

| Site | Named records | q0 | q1 | q2 |
|---|---:|---:|---:|---:|
| Perko's Beach | 71 | 36 | 26.37 | 18.88 |
| Lighthouse backdunes | 196 | 28 | 8.93 | 5.04 |

The site comparison combines record formats within each site. Seven of 57
species-level units are shared; 29 occur only in the Perko's inventory and 21
only in the backdune inventory. Jaccard similarity is 7/57 = 12.28%; Sorensen
similarity is 14/64 = 21.875%. The Perko's record distribution is more even;
backdune records are more concentrated in a few species. These are observed
inventory differences; site-only records do not demonstrate habitat restriction.
Unequal effort, dates and identification completeness limit ecological ranking.
The outputs `site_hill_summary.csv`, `site_species_overlap.csv` and
`site_record_audit.csv` retain calculations, identities and site assignments.

## Historical analysis — 26 October 2026

Empirical Hill diversity profiles and exact richness rarefaction for
the Ecdysis and GBIF preserve data snapshot used in the October 2026
report. The complete workflow, inputs and results were transferred
from the report workspace on 27 October 2026.

## Run

From the repository root, using Python with the packages in
`requirements.txt` installed:

```bash
python3 -m pip install -r analysis/hill-diversity/requirements.txt
python3 analysis/hill-diversity/make_hill_curves.py
```

The script resolves paths from its own location, so it can also be
called from another working directory. This is a reproducible, fixed
snapshot: its record-count assertions protect against silently mixing
in the incoming USA-wide GBIF download. A new data snapshot requires an
explicitly revised scope and output directory.

## Inputs

| Source | Path | Use |
|---|---|---|
| Ecdysis ZIP and all extracted tables | `data/raw/ecdysis/` | The workflow reads `extracted/SymbOutput_2026-10-26_124013_DwC-A/occurrences.csv` (ISO-8859-1). |
| Preserve GBIF snapshot | `data/raw/gbif/preserve_2026-10-26/` | Reads `terrestrial_arthropod_occurrences.csv` to select records from `gbif_all_arthropods_within_preserve.jsonl.gz`. |
| Original GBIF retrieval and spatial provenance | Same GBIF folder | Bounding-box responses, query, download manifest, dataset metadata, scope exclusions and the boundary used are retained for audit. |

The Ecdysis archive has 459 records, of which 458 are arthropods; its
gastropod record is excluded. The GBIF analysis has 14,601
terrestrial-associated arthropod records. Neither input is limited to
Insecta. These sources share 456 occurrence identifiers and are shown
separately rather than pooled.

## Methods

- q = 0: observed taxon richness.
- q = 1: exponential Shannon diversity.
- q = 2: inverse Simpson diversity.
- Profiles span q = 0–3. Richness rarefaction samples occurrence
  records without replacement using the exact finite-sample formula.
- Each occurrence record has equal weight; individual counts are not
  used. These are record-frequency summaries, not population abundance.
- Named species, BOLD BINs and orders are separate units of analysis.
  BINs and named-species assignments can overlap and must not be added.
- Higher-taxon identifications remain valid records but are excluded
  from species-only profiles. Provisional IDs and explicit species-rank
  subsets are examined in separate sensitivity summaries.
- Perko's Beach and lighthouse records remain separate in the July
  site comparison. Raw locality spellings are retained in source files;
  figure labels use Perko's Beach.

The workflow does not calculate coverage-based iNEXT estimates,
extrapolation, confidence intervals, unseen richness, or SDM-derived
presumed-species diversity. See the generated `Hill_curves_notes.md`
for interpretation and the Chao et al. (2014) reference.

## Outputs and transfer verification

Outputs are written to `outputs/hill-diversity/2026-10-26/`: PNG/PDF/SVG
figures, Hill summaries and profiles, rarefaction values, taxon
frequencies, a record-level audit and analysis metadata.

Transferred inputs were checked with SHA-256 hashes. The relocated
script was rerun and its numerical diversity/rarefaction results
compared with the original outputs. `migration_manifest.json` retains
the original transfer paths and hashes; originals remain in the report
workspace as a backup. The displayed beach spelling and local file
paths were updated during relocation.

### Current comparison figures

Run `python3 analysis/hill-diversity/plot_site_comparison.py` after the comparison
script; matplotlib is required. Outputs `hill_survey_comparison` and
`hill_site_comparison` are saved as PNG/PDF/SVG beside the current summaries.
Profiles span q=0–2 with the observed frequency distribution; all species-level
identifications are included together. The site figure combines all records within each site and shows overall Hill
profiles alongside site-only/shared species counts. It does not separate methods.
Seven of the 57 units in the combined site inventory are shared (Jaccard
similarity = 7/57 = 12.28%; Sorensen similarity = 14/64 = 21.875%). These are
observed inventory similarities, not estimates corrected for incomplete sampling.

### Survey display name

In the report and figure labels, the local inventory is named **UCSB Summer 2026
survey (this project)**. Ecdysis remains the original publishing portal and source
archive provenance. `rename_archived_figure_labels.py` renders older figures from
saved frequencies with this display name, without changing archived numerical
results. The current record-format figure uses the same display name.

### Report graph style

`figure_style.py` uses Times throughout and a palette drawn from the report’s
cover photographs and Cheadle Center logo: leaf green (`#59784D`), rust brown
(`#9C502F`), slate blue (`#6A7FA8`), gray-green (`#626B61`) and navy
(`#173C60`). Human observations and Perko’s Beach use green; preserved specimens
and lighthouse backdunes use rust; DNA records use blue; shared categories and
totals use gray-green. In source comparisons, the UCSB Summer 2026 survey uses
green and GBIF uses rust. Labels identify every grouping. The regional order
chart uses the same four-color palette; hatch patterns distinguish orders when
colors repeat. Barcode-cluster panels use the DNA blue consistently. These styling changes
do not change the input records, calculations or reported diversity values.

The site figure now stacks its panels for larger labels at report size. Axis
labels, legends and count annotations are enlarged across current and archived
plots. `restyle_regional_distance.py` applies the report styling to the existing
regional distance summary. These changes affect presentation only.

### Inventory expansion and exploratory effort scenario

Run `python3 analysis/hill-diversity/estimate_inventory_effort.py`. Results and
assumptions are saved in `outputs/hill-diversity/2026-10-27-inventory-effort/`.
The existing species-only site audit is unchanged. Single-record species number
23/36 at Perko’s Beach and 14/28 in the lighthouse backdunes. A Chao-style
record-frequency projection to twice the current number of named records gives
about 18 and 11 additional species-level units, respectively (approximately 54
and 39 total units). It uses f0=((n−1)/n)*f1²/(2*f2), a=f1/(n*f0+f1), and
S(n+m)=Sobs+f0*(1−(1−a)^m), with m=n. The zero-doubleton branch uses the
bias-corrected f0 alternative. This is a direct exploratory calculation, not an
iNEXT run; confidence intervals were not estimated.

These mixed, targeted occurrence records are not standardized individual
abundance samples. Repeated sightings, identification effort, season, microhabitat
and method affect the record distribution. The projected additions assume the
same recording process and cannot estimate the full fauna, true completeness,
or hours required to finish. Coverage diagnostics in the local CSV are
probability mass of the surrogate record distribution, not percent of species
found. The Level IV candidate pool is not a site-specific denominator.

The report proposes a first-phase budget of four seasonal daytime visits and
two dusk/night visits per site, with two people for four hours per visit:
48 field person-hours/site, 96 for both. These are explicit planning assumptions,
not an estimated completion threshold. Travel, trap servicing, identification,
curation and data entry require separate budgeting. Record person-hours,
protocol-specific effort, replicated sampling units and species incidence;
update completeness and discovery curves after each seasonal round. Continue
expert specimen identification alongside photo recording and BioBlitz events.

References: Chao & Jost (2012), https://doi.org/10.1890/11-1952.1;
Chao et al. (2014), https://doi.org/10.1890/13-0133.1;
Katzer et al. (2025), https://doi.org/10.1111/csp2.70016;
Lowe et al. (2026), https://doi.org/10.1002/2688-8319.70173;
Turley et al. (2024), https://doi.org/10.1093/aesa/saae014.
