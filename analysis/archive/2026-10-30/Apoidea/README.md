# Central Coast Non-Bee Apoidea GBIF Checklist

## Project Overview

Develop a simple, reproducible Python workflow that queries GBIF occurrence data and produces a cleaned checklist of **non-bee Apoidea** recorded from the California Central Coast.

The primary use case is biodiversity inventory and survey planning for **The Nature Conservancy's Jack and Laura Dangermond Preserve** in Santa Barbara County. The workflow should also provide regional context from adjacent Central Coast counties.

The emphasis of this project is:

* Scientific reproducibility
* Transparent data processing
* Museum-quality taxonomy
* Simple, maintainable code

This project is **not** intended to be a web application or software product.

---

# Philosophy

## Keep It Simple

This project should remain a small research pipeline.

**Do not build:**

* Web applications
* REST APIs
* Databases
* Authentication
* Docker containers
* Cloud services
* React/Vue frontends
* Complex object-oriented frameworks
* Microservices
* Enterprise software architecture

Instead, build a small collection of readable Python scripts that can be run locally.

The intended audience is biodiversity researchers—not software engineers.

Scientific transparency is more important than software sophistication.

---

# Suggested Project Structure

```text
apoidea_gbif/
│
├── README.md
├── requirements.txt
├── config.yaml
│
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
│
├── output/
│
├── src/
│   ├── query_gbif.py
│   ├── clean_occurrences.py
│   ├── build_checklist.py
│   ├── taxonomy_flags.py
│   └── utils.py
│
└── run_pipeline.py
```

Even simpler is acceptable.

Avoid unnecessary abstraction.

---

# Geographic Scope

Include records from:

* Santa Barbara County
* San Luis Obispo County
* Ventura County
* Monterey County
* San Benito County
* Santa Cruz County

Santa Barbara County is the primary area of interest.

Dangermond Preserve should receive special emphasis throughout the workflow.

County assignment should use coordinates whenever possible rather than relying exclusively on GBIF county fields.

---

# Taxonomic Scope

Include **Apoidea excluding bees**.

Current target families:

* Ammoplanidae
* Ampulicidae
* Astatidae
* Bembicidae
* Crabronidae
* Mellinidae
* Pemphredonidae
* Philanthidae
* Psenidae
* Sphecidae

Exclude all bee families.

The workflow should remain flexible enough to accommodate future taxonomic changes.

---

# GBIF Data Retrieval

Use the GBIF occurrence API during development.

The project should also document how to run the workflow using an official GBIF occurrence download for publication-quality analyses.

Retain raw GBIF values exactly as received.

Never overwrite original data.

Save all raw responses in:

```text
data/raw/
```

Retrieve (when available):

* GBIF ID
* occurrenceID
* institutionCode
* collectionCode
* catalogNumber
* scientificName
* verbatimScientificName
* acceptedScientificName
* family
* genus
* species
* taxonRank
* basisOfRecord
* identifiedBy
* eventDate
* locality
* county
* coordinates
* coordinate uncertainty
* dataset
* publisher
* references
* GBIF issue flags

Additional fields are welcome.

---

# Query Workflow

The pipeline should:

1. Resolve GBIF taxon keys
2. Query California occurrences
3. Restrict records to the target counties
4. Handle API pagination
5. Retry failed requests
6. Cache downloaded data
7. Log query parameters
8. Save query metadata

The pipeline should never silently discard failed API requests.

---

# Data Cleaning

Cleaning should be conservative.

Never overwrite original values.

Instead, create cleaned fields alongside original values.

Cleaning should include:

* Remove duplicate GBIF IDs
* Identify probable duplicate specimens
* Standardize missing values
* Standardize county names
* Assign county from coordinates when needed
* Flag county-coordinate conflicts
* Remove records outside California
* Remove records outside target counties
* Remove fossil records
* Remove absent occurrences
* Separate genus-only records
* Retain historical records
* Preserve uncertain coordinates while flagging them

Historical museum records are valuable and should not be removed simply because they are old.

---

# Species Checklist

Each row should represent one working species.

Suggested columns:

* workingScientificName
* acceptedScientificNameGBIF
* verbatimNames
* currentFamily
* genus
* species
* totalRecordCount
* uniqueOccurrenceCount
* uniqueSpecimenCount
* earliestYear
* latestYear
* Santa Barbara count
* San Luis Obispo count
* Ventura count
* Monterey count
* San Benito count
* Santa Cruz count
* counties recorded
* preserved specimen count
* human observation count
* institutions
* datasets
* nearest Dangermond occurrence
* Dangermond likelihood
* taxonomyComplexFlag
* taxonomyComplexEvidence
* taxonomyComplexNotes
* reviewNotes

---

# Dangermond Preserve

Store the preserve location in `config.yaml`.

If a preserve polygon is available:

* Determine whether records occur inside the preserve.
* Calculate distance to the preserve boundary.

Otherwise:

* Calculate geodesic distance to a reference point.

Assign a simple rule-based likelihood category:

* Confirmed at Dangermond
* Coastal Santa Barbara
* Elsewhere in Santa Barbara County
* Adjacent Central Coast
* Regionally plausible
* Unlikely

This is a survey-planning tool, **not** a species distribution model.

---

# Taxonomic Complexity

## Important

The taxonomy flag has one purpose only.

Flag taxa **only** when the name represents a known or suspected species complex or likely contains multiple cryptic species.

**Do NOT use this flag for:**

* synonyms
* outdated combinations
* family reclassification
* difficult identifications
* poor photographs
* uncertain specimens
* geographic outliers
* spelling variants

Allowed values:

* Yes
* Suspected
* No
* Unknown

Additional fields:

* taxonomyComplexEvidence
* taxonomyComplexNotes

Species-complex information should come from a manually maintained table:

```text
data/taxonomy_species_complexes.csv
```

Suggested columns:

* inputName
* acceptedName
* family
* genus
* complexFlag
* evidenceType
* citation
* notes
* dateReviewed

If a species is absent from this table, assign **Unknown** rather than assuming **No**.

---

# Taxonomic Names

Preserve three independent concepts:

1. Original verbatim name
2. GBIF accepted name
3. Working checklist name

Never silently replace names.

Generate a taxonomic crosswalk:

```text
output/taxon_name_crosswalk.csv
```

---

# Record Quality

Record-quality flags should remain separate from taxonomy.

Possible fields include:

* countyFromCoordinates
* countyFieldConflict
* coordinateMissing
* coordinateUncertaintyHigh
* probableDuplicate
* identificationRank
* GBIF issue flags
* localityReviewNeeded

These are **not** taxonomic flags.

---

# Outputs

## Raw Occurrences

```text
data/raw/gbif_occurrences_raw.csv
```

## Cleaned Occurrences

```text
data/processed/gbif_occurrences_cleaned.csv
```

## Species Checklist

```text
output/central_coast_nonbee_apoidea_checklist.csv
```

## Excel Workbook

```text
output/central_coast_nonbee_apoidea_checklist.xlsx
```

Suggested worksheets:

* Checklist
* Occurrences
* Genus Records
* Taxonomic Crosswalk
* Species Complexes
* Query Metadata
* Excluded Records
* Data Dictionary

## Query Metadata

```text
output/query_metadata.json
```

## Summary Report

```text
output/summary_report.md
```

---

# Optional Maps

Simple static maps are sufficient.

Preferred libraries:

* GeoPandas
* Matplotlib

Avoid interactive mapping frameworks.

Maps may include:

* county boundaries
* occurrence points
* Dangermond Preserve
* family-specific maps

---

# Configuration

Store configuration in:

```text
config.yaml
```

Suggested settings include:

* counties
* families
* Dangermond coordinates
* preserve boundary
* distance thresholds
* coordinate uncertainty threshold
* output directory

---

# Running the Pipeline

A single command should execute the complete workflow.

```bash
python run_pipeline.py
```

Optional examples:

```bash
python run_pipeline.py --refresh-gbif

python run_pipeline.py --skip-query

python run_pipeline.py --families Bembicidae Sphecidae

python run_pipeline.py --county "Santa Barbara"
```

Use standard `argparse`.

---

# Dependencies

Keep dependencies minimal.

Suggested packages:

* pandas
* requests
* geopandas
* shapely
* pyproj
* pyyaml
* openpyxl
* tqdm

Avoid unnecessary frameworks.

---

# Logging

Use Python's built-in logging.

Log:

* family being queried
* pages downloaded
* records retrieved
* cleaning statistics
* excluded records
* unmatched taxa
* output files
* errors

Errors should be understandable to researchers.

---

# Documentation

The README should explain:

* project purpose
* geographic scope
* taxonomic scope
* installation
* running the pipeline
* refreshing GBIF data
* configuring Dangermond
* editing taxonomy tables
* checklist fields
* GBIF limitations

Include a concise data dictionary.

---

# Data Limitations

The project should explicitly state:

* GBIF absence does not imply true absence.
* Record density reflects sampling effort.
* County fields may be incorrect.
* Coordinates may be generalized.
* Historical records may use outdated taxonomy.
* Many non-bee Apoidea remain poorly collected.
* Species-complex flags come from manual curation.
* Dangermond likelihood is a planning tool, not a predictive model.
* Voucher specimens remain the final authority.

---

# Validation

Perform simple validation checks:

* no bee families
* no records outside target counties
* no duplicate GBIF IDs
* every checklist row has a working name
* county totals match occurrence counts
* family names are valid
* taxonomy flags use allowed values
* every "Yes" or "Suspected" flag has supporting notes
* raw data remain unchanged
* outputs are successfully created

Simple assertions are sufficient.

---

# Coding Style

Use:

* short functions
* descriptive names
* docstrings
* comments
* straightforward pandas workflows
* explicit intermediate files

Avoid:

* deep inheritance
* excessive abstraction
* hidden state
* metaprogramming
* premature optimization
* enterprise software patterns

The code should read like a scientific workflow rather than a software product.

---

# Development Phases

## Phase 1

* Query GBIF
* Save raw data
* Clean records
* Build checklist
* Export CSV and Excel

## Phase 2

* County assignment
* Dangermond distances
* Summary tables
* Static maps

## Phase 3

* Species-complex support
* Taxonomic crosswalks
* Manual review fields

## Phase 4

* Validation
* Query metadata
* Summary report
* Documentation
* Reproducibility review

---

# Acceptance Criteria

The project is complete when:

* One command generates the complete workflow.
* GBIF data are retrieved correctly.
* Bees are excluded.
* Records are limited to the six target counties.
* The checklist contains one row per working species.
* County summaries are produced.
* Dangermond relevance is calculated.
* Species-complex information is supported through a manually curated table.
* Raw, cleaned, and summarized data remain separate.
* The codebase remains small, readable, and locally executable.
* No full-stack architecture has been introduced.
* Another researcher can reproduce the workflow from the README.
* CSV, Excel, metadata, and summary outputs are all produced.
* The project can later be expanded to additional insect groups with minimal modification.
