# Dangermond Hill diversity analysis

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
