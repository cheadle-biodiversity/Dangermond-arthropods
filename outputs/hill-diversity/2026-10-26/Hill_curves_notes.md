# Dangermond Preserve: Hill diversity curves

These are empirical diversity profiles weighted by occurrence-record frequency. They describe the available records rather than standardized community abundance.

| Dataset / taxonomic unit | Records used | q = 0 | q = 1 | q = 2 |
|---|---:|---:|---:|---:|
| Ecdysis: named species | 324 | 66 | 24.00 | 11.14 |
| GBIF: named species assignments | 5,384 | 543 | 90.87 | 29.66 |
| GBIF: barcode BINs | 10,915 | 1083 | 208.57 | 69.45 |
| Ecdysis: orders | 456 | 11 | 4.14 | 2.94 |
| GBIF: orders | 14,590 | 28 | 5.23 | 3.51 |
| Ecdysis: named species, unqualified IDs | 298 | 50 | 18.78 | 9.50 |
| Ecdysis: named species, preserved only | 183 | 65 | 40.78 | 25.20 |
| GBIF: named species, explicit species/subspecies rank | 807 | 208 | 99.30 | 44.55 |
| Ecdysis: Perko’s Beach, July | 73 | 38 | 27.86 | 19.81 |
| Ecdysis: lighthouse area, July | 233 | 37 | 11.97 | 6.53 |

## Reading the figures

- q = 0 counts observed taxa; q = 1 is exp(Shannon entropy); q = 2 is inverse Simpson concentration. All are expressed as effective numbers of the stated taxonomic unit. Larger q gives more weight to frequently recorded taxa.
- The overview compares Ecdysis and GBIF named-species assignments, shows GBIF BINs separately, compares order-level coverage, and shows exact named-species richness rarefaction over occurrence records.
- The second figure keeps July Perko’s Beach and lighthouse localities separate. It uses named species and species-level parents of subspecies, rather than mixing ranks.

## Data and methods

- Ecdysis: 458 arthropod records from the supplied 12:40:13 archive; the single gastropod is excluded. All arthropods in that export are treated as terrestrial-associated under the project scope.
- GBIF: 14,601 terrestrial-associated arthropod records in the previously saved Preserve extract, across all years and contributing institutions. No new GBIF download was made. The original boundary and terrestrial-scope decisions remain in the GBIF project folder.
- Named GBIF units use speciesKey and species assignments already present in the saved GBIF responses. This includes unranked BIN records that GBIF places beneath a named species. The explicit species/subspecies-rank sensitivity row shows the effect of excluding those assignments. These GBIF interpretations have not all been independently validated.
- Ecdysis species use genus + specificEpithet; subspecies are rolled up to species, and the two Lasioglossum pavonotum name forms are combined. Scientific-name spellings otherwise follow the archive. Provisional identifications are included in the primary profile; a separate sensitivity row excludes every nonempty identificationQualifier.
- Genus-, family-, order- and other higher-rank identifications are valid records but cannot enter a species-only profile. No arbitrary species were assigned to them.
- BOLD BINs use the full scientificName identifier BOLD:xxxxxxx. A BIN is a molecular clustering unit, not a confirmed biological species. BIN and named-species panels overlap in records and must not be added together.
- Order profiles retain every record with an order. Isoptera is merged into Blattodea for consistent treatment. Missing orders are omitted, not counted as an artificial order.
- Each occurrence record receives equal weight; individualCount is not used because it is absent or inconsistent across the sources. Repeated observations are not necessarily different individuals.
- The two sources share 456 occurrenceIDs across the terrestrial scope. They are displayed separately, not pooled or treated as independent samples. Cross-publisher duplicate events or specimens were not independently resolved.
- Richness rarefaction uses E[S_m] = sum_i [1 - choose(N - n_i, m) / choose(N, m)], drawing records without replacement from the saved dataset. This is finite-record subsampling, not an estimate of unseen species or a guarantee of equal survey effort. No bootstrap confidence bands or extrapolation are shown.
- The GBIF pool is dominated by barcode material samples and combines different methods, dates and habitats. Curves cannot establish relative habitat health, total Preserve richness, or ecological superiority of one source or site.

## Reference

Chao, A., Gotelli, N. J., Hsieh, T. C., Sander, E. L., Ma, K. H., Colwell, R. K., & Ellison, A. M. (2014). Rarefaction and extrapolation with Hill numbers: a framework for sampling and estimation in species diversity studies. Ecological Monographs, 84, 45–67. https://doi.org/10.1890/13-0133.1

The present analysis applies empirical Hill-number definitions and exact richness interpolation only; it does not implement the full Chao et al. estimation framework.
