# Regional candidate pool: existing GBIF snapshot

Source: GBIF download [10.15468/dl.vgv5ee](https://doi.org/10.15468/dl.vgv5ee),
key `0010070-260921141020460`, submitted 28 September 2026.
The download contains 4,665,086 California Arthropoda records and
already excludes GBIF-flagged geospatial issues. It is not the incoming
USA-wide download.

## Filtering order

1. Keep interpreted `taxonRank` at genus or below. Retain genus-only
   identifications as valid records; do not count them as identified
   species. Exclude `UNRANKED` entries even where parent taxonomy has
   a populated genus or species field.
2. Require numeric, finite latitude and longitude within global bounds.
   Do not introduce a coordinate-uncertainty cutoff at this stage.
3. Keep `class = Insecta`.
4. Keep records whose coordinates fall within either full EPA Level III
   region 6 (Central California Foothills and Coastal Mountains) or 85
   (Southern California/Northern Baja Coast).

The spatial test uses full regional polygons, not the portions clipped
to the preserve. The source download restricts this initial pool to
California portions of those ecoregions. Each record is retained once;
shared-boundary matches receive both region labels.

No new date, basis-of-record, identification-qualifier or deduplication
filter is applied. These four-filter outputs are intermediate occurrence
tables, not final named-species checklists. The final checklists retain BOLD
records with resolved species determinations; this supersedes the earlier
source-wide exclusion. Unnamed barcode clusters remain outside named-species
lists. Spiders and other non-insect invertebrates are outside the intended
insect scope; see the release review for a resolved-classification exception.

## Run

From the repository root, with dependencies in `requirements.txt`:

```bash
python3 analysis/regional-candidate-pool/retrieve_snapshot.py
python3 analysis/regional-candidate-pool/filter_gbif.py
python3 analysis/regional-candidate-pool/species_subset.py
python3 analysis/regional-candidate-pool/resolve_taxonomy.py
python3 analysis/regional-candidate-pool/clean_species_identifications.py
```

The retrieval script resumes checked byte-range downloads, validates
the completed ZIP and records its checksum and GBIF metadata. The
filter script streams the Darwin Core occurrence table in chunks;
all original columns are retained. Source data are not overwritten.
The reader follows the archive's `meta.xml`: UTF-8 tab-delimited text,
one header row, and no quote enclosure. Quotation marks within fields
are treated literally, and malformed rows are not skipped. The final
input count must match the 4,665,086 records in GBIF's download metadata.

## Outputs

### Completed run: 27 October 2026

| Sequential stage | Records retained | Removed at this step |
|---|---:|---:|
| Original California snapshot | 4,665,086 | — |
| Identified to genus or below | 3,401,713 | 1,263,373 |
| Usable geographic coordinates | 3,401,713 | 0 |
| Insecta only | 2,935,477 | 466,236 |
| Level III region 6 or 85 | 1,594,367 | 1,341,110 |

Region 6 contains 797,869 retained occurrences and region 85 contains
796,498. No retained record matched both regions. These are occurrence
counts, not species counts. The coordinate step removed no additional
records from the genus-or-below subset.

The complete source ZIP passed its integrity check and the input total
matched GBIF's metadata. Taxon-summary counts reconciled with the final
record count. A 1,000-row output sample passed rank, coordinate, insect
class and region-label checks; all 230 source columns and the two new
region fields were present.

### Saved files

Files are written to `outputs/regional-candidate-pool/gbif-vgv5ee/`:

- `filtered_insect_records.csv.gz`: full source columns plus Level III labels.
- `filter_counts.csv`: retained and removed records at each sequential stage.
- `taxon_record_counts_by_ecoregion.csv`: record counts by rank, name and region.
- `filter_metadata.json`: source, filter rules, source-rank inventory and provenance.
- `filter_report.md`: readable methods, sequential counts and interpretation notes.
- `species_identified_insect_records.csv.gz`: separate species-resolved subset.
- `species_subset_metadata.json`: exact selection, source checksum and counts.
- `species_subset_counts.csv`: retained/excluded counts and distinct species keys.

## Species-identified subset

The separate subset starts from the regional insect records above. It
retains interpreted rank `SPECIES` or a finer rank, requires a positive
GBIF `speciesKey` and a nonblank interpreted `species` name, and keeps
all original columns. Subspecies and varieties count as identified to
species and remain included. Genus-only records and species aggregates
are excluded. The broader regional dataset is preserved unchanged.

Distinct species are summarized by GBIF species key, so different
subspecies of one species do not inflate the species total. This step
does not resolve provisional identifications, remove duplicate records,
or apply the pending BOLD eligibility rule. It describes regional
occurrences, not confirmed occurrences on Dangermond Preserve.

The 27 October 2026 run retained **1,417,629 occurrence records** with
**13,934 distinct GBIF species keys**. It excluded 176,736 genus-only
records and two species-rank records lacking a resolved species name or
key. Retained ranks were 1,374,339 species, 43,282 subspecies and eight
variety records. Region 6 contributed 696,463 occurrences and region 85
contributed 721,166. These species totals have not yet received the
project's BOLD and ecological screening.

## Current taxonomic name resolution

Service: **GBIF Species Match API v2**, endpoint
`https://api.gbif.org/v2/species/match`, explicitly querying the
**Catalogue of Life eXtended Release (COL XR)** checklist
`7ddf754f-d193-4cc9-b351-99906754a03b`. See GBIF's
[taxonomy interpretation documentation](https://techdocs.gbif.org/en/data-processing/taxonomy-interpretation)
and [Species API documentation](https://techdocs.gbif.org/en/openapi/v1/species).
The original download used the legacy GBIF Backbone; its names and
identifiers remain unchanged in the original columns.

The initial strict screen accepted only exact, high-confidence matches.
On 27 October 2026 the user explicitly approved **all species-level
service candidates**, including variants and provisional or ambiguous
taxonomic statuses. The current workflow applies those candidates
without upgrading their original service status or confidence. Twelve
specific user-reviewed decisions in
`reviewed_taxonomic_corrections.csv` take precedence over the service.
The user's approvals are the source of those decisions; they do not
represent independent literature verification.

### Matching and retained information

Each distinct `scientificName`, `taxonRank`, `order`, `family` combination
is queried once, with Animalia, Arthropoda and Insecta context. Only
names and classification are sent, not occurrence rows or coordinates.
Full responses, request URLs and UTC retrieval timestamps are cached in
`taxonomy_api_cache.jsonl`; completed queries are reused.

The resolved table retains all original columns and adds:

- `resolved_taxon_name`, `resolved_taxon_key`, `resolved_taxon_rank`:
  the accepted canonical name, COL XR identifier and rank.
- `resolved_species_name`, `resolved_species_key`: species-level roll-up.
  Infraspecific names remain at their matched rank. Keys stay blank when
  a user-reviewed name or species ancestor has no matching COL XR key;
  genus identifiers are never assigned as species identifiers.
- Resolution status, match type, confidence and source. Manual decisions
  have no numerical service confidence; the original API values remain
  in the automatic audit columns.
- Matched and accepted names/statuses, service candidate name/key/rank,
  checklist identifier, diagnostics JSON, query URL and retrieval time.
- `taxon_resolution_baseline_status`: the result of the original strict
  screen, retained even after the user accepts a candidate.

The full lookup is `taxonomy_name_resolution.csv`. The report and
`taxonomy_resolution_metadata.json` document the service, source checksum,
approval policy and outcome. Raw API responses and large datasets remain
local and excluded from Git. Common-name additions preserve these fields.

## Genus-only exclusions in the next version

`clean_species_identifications.py` excludes original genus/higher-taxon
uninomials, genus ranks, `sp.`, `spp.`, `spec.`, unnamed morphospecies,
BOLD-only labels and species groups/complexes. It checks
`verbatimScientificName` first, then `verbatimIdentification` if blank,
and finally interpreted `scientificName` if both are blank. This catches
placeholder names that GBIF had interpreted as species.

A standalone `sp.` in a secondary field does not override a named
species in the primary field. Parenthetical group placements followed
by a named epithet remain species identifications, e.g. *Nomada*
(erigeronis group) *crotchii*.

Following the user's latest instruction, this version **also excludes
records whose service result remains only genus or higher**, unless a
user-reviewed species name is supplied. This is a scope filter, not a
claim that the original identification is erroneous.

The cleanup excludes **8,754 records** from the 1,417,629-row input,
leaving **1,408,875**. Of those exclusions, 798 were original placeholder,
group or higher-taxon labels and another 7,956 lacked a species-level
resolution. All retained records have an accepted species-or-finer name.

- `excluded_genus_placeholder_identifications.csv`: original labels,
  interpreted names, reasons and excluded counts.
- `species_identification_cleanup_metadata.json`: rules, counts and source hash.
- `accepted_name_changes.csv` and `.md`: applied name changes and counts.
- `original_name_proposed_correction.csv` and `.md`: no pending
  species-level changes remain after the user's blanket approval.

## Proposed common names: ESA source

This version uses the **Entomological Society of America Common Names
of Insects Database**, not BugGuide:
https://entsoc.org/publications/common-names

The original downloadable spreadsheet and its manifest are saved in
`data/raw/common-names/esa/2026-10-27/`. The published filename is
`Common_names_list_7-2-26.xlsx`; its internal heading says "Updated
3/4/25". Both are recorded as provided rather than assuming a newer
content date. The source is third-party data; no new license is asserted.

`add_common_names.py` parses the source's genus, species, common-name
and related fields. It matches the resolved taxon exactly first, then
its parent species. If those are absent, it uses an exact ESA match to
a binomial alias from the user-approved taxonomic crosswalk or an
explicit user-provided synonym, such as *Plebejus acmon*. No fuzzy
matching or genus/family common-name transfer is used. A common name
specific to a subspecies, such as "mission blue," is not extended to
all records of its parent species.

New columns are `proposed_common_name`, `common_name_source`,
`common_name_source_url`, `common_name_source_scientific_name`,
`common_name_match_type` and `common_name_retrieved_on`. Multiple ESA
names are retained with semicolons. A blank means no match in this
ESA source, not proof that no common name exists. ESA common names
are copied from the source, not newly coined for this project.

The current final dataset is
`outputs/regional-candidate-pool/gbif-vgv5ee/species_identified_insect_records_v3.csv.gz`.
Version 3 appends Level IV geography to version 2 without removing rows.
`species_common_name_lookup.csv` records the resolved taxon, parent
species, common-name assignment, source, matching method and occurrence
count. `common_name_enrichment_metadata.json` records provenance,
checksums and coverage. All earlier datasets remain available for audit.

The completed common-name enrichment assigned ESA names to **463,959
of 1,408,875 occurrences**. Blank names are retained for records without
a source-supported match; their scientific names remain available.

## Reproduce the current next version

After the original filters and species subset, run:

```bash
python3 analysis/regional-candidate-pool/resolve_taxonomy.py
python3 analysis/regional-candidate-pool/clean_species_identifications.py
python3 analysis/regional-candidate-pool/add_common_names.py
python3 analysis/regional-candidate-pool/add_level_iv_ecoregions.py
```

Retain the downloaded ESA spreadsheet at the documented location.
The original GBIF snapshot remains California-only and these are
regional occurrences, not a checklist of confirmed preserve records.
BOLD eligibility and ecological screening remain separate steps.

## EPA Level IV ecoregion codes

`add_level_iv_ecoregions.py` assigns every version 2 occurrence to the
full EPA Region 9 Level IV polygons saved in
`data/raw/epa/region9_level_iv/2026-10-27/`. It merges disconnected
pieces sharing a code, transforms the polygons to WGS84, and matches
longitude/latitude points using the boundary-inclusive `covered_by`
predicate. No nearest-region assignment, buffer, snapping or new
coordinate-uncertainty cutoff is applied.

Version 3 adds three columns while retaining all prior columns:

- `analysis_ecoregion_l4_code`: EPA code, e.g. `6ap` or `85a`.
- `analysis_ecoregion_l4_name`: EPA region name.
- `analysis_ecoregion_l4_match_status`: `matched_single`,
  `matched_multiple` or `unmatched`.

An occurrence matching multiple regions is retained once, with matching
codes and names separated by semicolons in corresponding order.
Unmatched occurrences remain in the dataset with blank code/name.
`level_iv_assignment_issues.csv` lists these cases and any disagreement
between the Level IV polygon's parent Level III region and the earlier
Level III assignment. No original Level III code is overwritten.

The full regional pool remains available, including Level IV regions
outside Dangermond. The two Level IV regions intersecting the preserve
are `6ap` (Solomon-Purisima-Santa Ynez Hills) and `85a` (Santa Barbara
Coastal Plain and Terraces). An occurrence anywhere within either full
region is not automatically an occurrence on the preserve. These
regional polygons do not distinguish Perko's Beach from the lighthouse
backdunes.

`level_iv_ecoregion_counts.csv` summarizes occurrences and distinct
resolved species names by region. Multiple-region boundary records
contribute to each matching region's summary without duplicating rows
in version 3. `level_iv_assignment_metadata.json` records checksums,
CRS transformation, software and counts;
`level_iv_assignment_report.md` gives the readable result.

The 27 October 2026 run assigned all **1,408,875 occurrences** to a
single Level IV region, covering **55 distinct regions**. There were
no unmatched records, multiple matches or Level III disagreements.
Version 3 contains **266 columns**, including all 263 version 2 fields.
Region `6ap` contains 9,141 regional occurrences and `85a` contains
34,414; these counts cover the full regions and are not restricted to
Dangermond Preserve.

## Separate Level III and Level IV matched datasets

Run `python3 analysis/regional-candidate-pool/export_ecoregion_datasets.py`
after version 3. This first creates the two named exports with all
version 3 columns. The sparsity-trimming step below then reduces their
columns without changing their records:

| Dataset | Regional codes | Occurrences | Distinct resolved species |
|---|---|---:|---:|
| `dangermond_level_iii_matched_records.csv.gz` | `6`, `85` | 1,408,875 | 13,634 |
| `dangermond_level_iv_matched_records.csv.gz` | `6ap`, `85a` | 43,555 | 2,550 |

Both final files are saved in `data/final/`. Summary and audit tables
remain in `outputs/regional-candidate-pool/gbif-vgv5ee/`.
The Level IV file is a subset of the Level III file; these are overlapping
regional pools, not mutually exclusive groups. "Matched" means belonging
to an ecoregion that intersects Dangermond, not necessarily a record from
within the preserve. Other Level IV regions remain in the Level III file.

The script validates the Level III criterion for every version 3 row,
then makes a verified byte-identical independent copy for that export.
It filters the Level IV file to `6ap` or `85a`, retaining each source row
once even if it has multiple matching codes. Source version 3 is unchanged.
Species counts use `resolved_species_name`, including manually reviewed
names without COL XR identifiers, with subspecies rolled up to species.

`ecoregion_dataset_summary.csv` records current sizes and scope;
`ecoregion_dataset_export_metadata.json` records criteria, counts,
checksums, original full-schema columns and provenance at initial export.

## Simplified, matching schemas for the regional exports

Run `python3 analysis/regional-candidate-pool/trim_sparse_columns.py`
after the exports. It rebuilds the named files from the unchanged
266-column version 3 source, applying the user's column decisions.
Both final files in `data/final/` have the **same 60 columns in the same order**.

The starting rule is a 70% blank cutoff, retaining the union of useful
columns across the two pools. Explicit user decisions override that rule:

- Restore `collectionID`, `individualCount`, `preparations`,
  `samplingProtocol`, `county` and `locality` to Level III, and keep
  `projectID` in both to preserve a shared schema.
- Keep `proposed_common_name`, `common_name_source` and
  `common_name_source_url` in both, regardless of completeness.
- Retain three adjacent name/resolution columns:
  `verbatimScientificName`, `resolved_taxon_name` and
  `taxon_resolution_description`.
- Remove alternative full-name fields (`scientificName`, `species`,
  `acceptedScientificName`, `genericName`, `specificEpithet`), the other
  resolved-name/key/rank fields and the separate `taxon_resolution_*`
  service fields. Taxonomic classification such as order, family and
  genus, and original identification/record IDs, remain.
- Remove `analysis_ecoregion_l4_code`, `analysis_ecoregion_l4_name`
  and `analysis_ecoregion_l4_match_status` from both working exports.
- Continue removing the user's earlier list of 37 redundant/provenance
  columns. The complete cumulative exclusions are stored in the script
  and pruning metadata.

`verbatimScientificName` remains the unmodified publisher-supplied value,
including blanks where none was supplied. `resolved_taxon_name` remains
the final service/user-reviewed name. The new readable description
combines the outcome (exact accepted match, synonym, user-accepted
service candidate or manual review), provider, original API match type,
confidence and taxonomic status, the GBIF-interpreted input name used
for the match, and any user-review note. It is generated from the full
name-resolution audit; no new service queries are performed.

The Level IV records are **selected before the Level IV columns are
removed**. The exported Level IV file therefore remains restricted to
6ap/85a even though those assignment columns are no longer included.
The Level III file retains the broader 6/85 pool and its Level III columns.
Species counts are calculated from the source species roll-up before
that internal field is omitted from the exports.

No records are removed: Level III retains 1,408,875 occurrences and
13,634 resolved species; Level IV retains 43,555 occurrences and 2,550
resolved species. Retained original cell values are unchanged. Full
names, taxonomy, diagnostics and ecoregion assignments remain available
in version 3 and the complete audit tables.

- `retained_columns.md`: the shared current column list.
- `ecoregion_column_completeness.csv`: completeness, decision and reason
  for each source column, plus the generated description field.
- `ecoregion_column_pruning_metadata.json`: rules, exclusions, restored
  and derived fields, schema, record/species counts and checksums.
- `ecoregion_dataset_summary.csv`: current file dimensions.

Completeness profiles are reused only after the full source SHA-256
checksum is verified, with generated columns excluded from source
profiling. Reproduce the current working files by running the export
script followed by the trimming script.

## Final data folder and column descriptors

The named Level III and IV exports now live in **`data/final/`**, not
in the audit-output folder. Export and trimming scripts write directly
there. The existing tables were moved byte-for-byte, with checksums
verified; full version 3 and intermediate/audit tables remain in outputs.

After export and trimming, run:

```bash
python3 analysis/regional-candidate-pool/package_final_datasets.py
```

This validates matching headers, record counts and existing file
checksums, then writes the final folder README, shared
`column_metadata.csv`, readable `column_metadata.md` and
`dataset_metadata.json`. The descriptors cover every column in order,
including semantic type, meaning, units/format, provenance, source-term
URI, missing values and interpretation notes. The maintained master is
`analysis/regional-candidate-pool/final_column_definitions.csv`.

The dataset manifest records the two regional scopes, overlapping-record
relationship, upstream species-count method, processing decisions,
licenses, source DOI, sizes and SHA-256 checksums. Large data stay
Git-ignored; the descriptors and manifests are versioned.

## Regional species checklists

`create_ecoregion_checklists.py` writes one six-column species
checklist for each of Level III regions 6/85 and Level IV regions
6ap/85a in `data/final/checklists/`. Subspecies are rolled up to species.
Life-history notes and source columns have been removed. Preserve occurrence is
`Yes` only where supporting named records are documented; otherwise
blank. Supporting survey and GBIF records, mapping questions and
classification conflicts are saved in companion audit tables.

The user explicitly restored all records with resolved species
identifications, including BOLD sources. This supersedes the earlier
blanket BOLD exclusion for these checklists. All records in the full
version 3 regional pool contribute to checklist counts; named BOLD
preserve records also remain eligible for positive evidence after
boundary and name checks. Unresolved BIN or genus-only records are not
converted into species. The original occurrence datasets are unchanged.

Reproduce: `python3 analysis/regional-candidate-pool/create_ecoregion_checklists.py`.
