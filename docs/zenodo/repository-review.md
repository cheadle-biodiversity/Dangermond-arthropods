# Zenodo preparation review — 30 October 2026

## Verified

- Four six-column checklists: 10,135 / 8,450 / 1,521 / 1,852 species.
- Their occurrence totals reconcile with the two final regional tables: 1,408,875 Level III records and 43,555 Level IV records, each with 60 columns.
- Both occurrence files have unique `gbifID` values within each file.
- Checksums match the existing manifests for both occurrence tables, all four checklists and both original archives.
- The GitHub default branch is `master`. The latest local commit is `2812c3a50e4e2af3e259f84894557b0c77a950b2`; checklist/schema updates remain uncommitted. The public checklist README still describes the older schema.

## Resolve before publishing

1. **Taxonomic scope:** Level III region 85 includes *Vejovis minimus* (Scorpiones, one regional record). Region 6 retains *Apterobittacus apterus* and *Bittacus chlorostigma* (Mecoptera, 481 records), although Mecoptera were removed from report summaries. Decide the release scope and regenerate consistently if needed.
2. **Absence records:** Five records in Level III, including one in Level IV, have `occurrenceStatus = ABSENT`. They currently contribute to checklist record totals. Review presence-only treatment before calling every supporting record an observation of occurrence.
3. **Preserve evidence:** Twelve records representing six original labels remain unmapped: *Dasymutilla coccineohirta*, *Dasymutilla sackenii*, *Dinomus bachei*, *Monomorium argatogyna*, *Paropsisterna m-fuscum*, and *Simulium hippovorum*. Review mappings; no original identification was declared erroneous or altered in this review.
4. **Provenance:** Preserve flags depend on the additional 26 October GBIF preserve extract. Retain that extract and its metadata alongside the named GBIF download and Ecdysis archive. Include taxonomy crosswalks/caches so changing online services do not obscure the decisions used.
5. **Ecdysis versions:** The annotated 28 October CSV has the same 459 occurrence IDs as the original ZIP, adds 15 columns, and changes `modified` in 459 rows and `verbatimEventDate` in 155 rows. Keep both, with distinct roles. The checklist generator reads the original archive, not the annotated table.
6. **Release metadata:** Confirm creators, version, data-license presentation and redistribution terms for supporting inputs. Commit the final methods and documentation, then record that commit in the deposit. No upload, DOI reservation or publication was performed.

## Prepared documentation

- `README.md`: concise README for the data deposit.
- `deposit_file_inventory.csv`: proposed payload paths, sizes, roles, inclusion status and SHA-256 hashes.
- `validation_summary.json`: measured counts, license distributions, order summaries and hash checks.

The data files were not edited or regenerated. Legacy documentation about checklist columns and blanket BOLD exclusion was corrected where it directly affected this deposit.
