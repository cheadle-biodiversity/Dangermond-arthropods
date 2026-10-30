# Final regional insect occurrence datasets

| File | Ecoregion codes | Occurrences | Species (upstream roll-up) | Columns |
|---|---|---:|---:|---:|
| [dangermond_level_iii_matched_records.csv.gz](dangermond_level_iii_matched_records.csv.gz) | 6, 85 | 1,408,875 | 13,634 | 60 |
| [dangermond_level_iv_matched_records.csv.gz](dangermond_level_iv_matched_records.csv.gz) | 6ap, 85a | 43,555 | 2,550 | 60 |

These are full regional occurrence pools, not records restricted to Dangermond Preserve. The Level IV dataset is a subset of the Level III dataset, so the files overlap. Regions 6ap (Solomon-Purisima-Santa Ynez Hills) and 85a (Santa Barbara Coastal Plain and Terraces) intersect the preserve. Level IV assignment columns were deliberately removed after selecting those records; the Level III code/name remain.

- [Column descriptor — readable](column_metadata.md)
- [Column descriptor — CSV](column_metadata.csv)
- [Dataset provenance, counts and SHA-256 checksums](dataset_metadata.json)

Both files have the same 60-column schema. Each is a gzip-compressed, UTF-8 CSV with a header; read identifier fields as text. Blank values are not zero. Original names, final resolved names and match descriptions are retained. Original GBIF classification and taxon keys may differ from the subsequently resolved name. Species counts above use the upstream species-level roll-up; do not substitute a count of distinct resolved_taxon_name because that field can retain subspecies.

Source: [GBIF download 10.15468/dl.vgv5ee](https://doi.org/10.15468/dl.vgv5ee). Scientific-name matching used GBIF / Catalogue of Life XR plus user-reviewed decisions; common names used the [ESA list](https://entsoc.org/publications/common-names). Record-level licenses and rights holders remain applicable. BOLD eligibility and ecological screening remain future analysis steps.

The large compressed files are ignored by Git; descriptors and manifests are versioned. Full 266-column data and audit tables remain in outputs/regional-candidate-pool/gbif-vgv5ee/. These final files were relocated byte-for-byte from the working exports.

Reproduce from repository root:

```bash
python3 analysis/regional-candidate-pool/export_ecoregion_datasets.py
python3 analysis/regional-candidate-pool/trim_sparse_columns.py
python3 analysis/regional-candidate-pool/package_final_datasets.py
```

Full filtering, source and name-resolution methods: [workflow README](../../analysis/regional-candidate-pool/README.md).

## Species checklists

The [checklists/](checklists/) folder contains separate checklists for
regions 6, 85, 6ap and 85a, with a `Yes` preserve flag only when documented.
All four lists have six columns following removal of life-history notes and sources.
All resolved species-level source
records, including BOLD, are retained under the user's latest instruction.
Companion files document preserve evidence and checklist methods.
