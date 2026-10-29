# Final dataset column descriptor

Shared schema for both final regional datasets: 60 columns in the order shown. All files are UTF-8, comma-delimited CSV with a header, standard double-quote escaping and gzip compression. Semantic types below describe intended interpretation; identifiers should be read as text. Blank/whitespace-only cells represent missing information, not zero.

| Column | Semantic type | Definition and interpretation |
|---|---|---|
| `gbifID` | string | GBIF identifier for the source occurrence record. Format/units: Identifier. Read as text; records in the two regional pools intentionally overlap. |
| `license` | string | Reuse license attached to the source occurrence. Format/units: URI or source license text. Record-level rights remain applicable; this package does not relicense source records. |
| `modified` | string | Source record modification date or timestamp. Format/units: Date/time text. Not the creation date of this final package. |
| `publisher` | string | Organization or agent publishing the source record. Format/units: Text. Preserved from the GBIF archive. |
| `references` | string | Links or citations associated with the source record. Format/units: URI or text. May contain more than one reference. |
| `rightsHolder` | string | Person or organization holding rights in the record. Format/units: Text. Preserved source attribution. |
| `collectionID` | string | Identifier for the collection holding or documenting the material. Format/units: Identifier or URI. Not a collecting-event identifier; preserve as text. |
| `institutionCode` | string | Source institution abbreviation or code. Format/units: Text. Use alongside collectionCode and catalogNumber. |
| `collectionCode` | string | Source collection abbreviation or code. Format/units: Text. Codes need not be globally unique. |
| `datasetName` | string | Name of the dataset containing the source record. Format/units: Text. See datasetKey for the GBIF dataset identifier. |
| `basisOfRecord` | string | Record category, such as preserved specimen or human observation. Format/units: GBIF/Darwin Core vocabulary. The final tables contain multiple record categories; they are not specimen-only. |
| `occurrenceID` | string | Occurrence identifier supplied with the source record. Format/units: Identifier or URI. Distinct from the GBIF-assigned gbifID; retain leading zeros and punctuation. |
| `catalogNumber` | string | Catalog identifier assigned within the source collection. Format/units: Identifier. May repeat between collections; do not coerce to a number. |
| `recordedBy` | string | Collectors or observers associated with the occurrence. Format/units: Names or source identifiers. Multiple agents may be represented in one cell. |
| `individualCount` | integer | Number of individuals reported by the source record. Format/units: Individuals. Blank is missing, not zero; observation counts are not standardized sampling effort. |
| `lifeStage` | string | Developmental stage reported for the organism. Format/units: Source vocabulary. Examples may include adult or larva; source terms are preserved. |
| `occurrenceStatus` | string | Source or GBIF interpretation of presence or absence. Format/units: GBIF occurrence-status vocabulary. No additional presence-only filter was introduced during final packaging. |
| `preparations` | string | Preparation or preservation methods for the material. Format/units: Text. May list multiple preparations. |
| `eventDate` | string | Date, time or interval assigned to the collecting or observation event. Format/units: Date/time or interval text. Precision and any interval are preserved; do not assume every value identifies a single day. |
| `eventTime` | string | Time or time interval associated with the event. Format/units: Time text. No timezone is inferred when the source omits one. |
| `startDayOfYear` | integer | First ordinal day associated with the event. Format/units: Day of year, nominally 1–366. Useful for event intervals; blank remains missing. |
| `endDayOfYear` | integer | Last ordinal day associated with the event. Format/units: Day of year, nominally 1–366. Useful for event intervals; blank remains missing. |
| `year` | integer | Event year interpreted in the source archive. Format/units: Calendar year. Not the publication or download year. |
| `month` | integer | Event month interpreted in the source archive. Format/units: Month, nominally 1–12. Missing precision remains blank. |
| `day` | integer | Event day of month interpreted in the source archive. Format/units: Day of month, nominally 1–31. Missing precision remains blank. |
| `verbatimEventDate` | string | Original event-date wording provided by the publisher. Format/units: Unstandardized text. May differ in precision or format from eventDate. |
| `samplingProtocol` | string | Collecting or observation method reported by the source. Format/units: Text. Retained even where sparse to keep the regional schemas identical. |
| `continent` | string | Continent assigned to the occurrence location. Format/units: Text. Source geographic interpretation is preserved. |
| `countryCode` | string | Two-letter country code associated with the occurrence. Format/units: ISO 3166-1 alpha-2. Preserved as text. |
| `stateProvince` | string | State or equivalent administrative unit for the occurrence. Format/units: Text. The source download was restricted to California. |
| `county` | string | County or equivalent administrative unit for the occurrence. Format/units: Text. Retained in both tables, including blanks. |
| `locality` | string | Source locality description associated with the occurrence. Format/units: Text. Not a determination that the record lies on Dangermond Preserve. |
| `verbatimLocality` | string | Original locality wording supplied with the source record. Format/units: Unstandardized text. Source wording is preserved. |
| `decimalLatitude` | number | Latitude used in the geographic overlays. Format/units: Decimal degrees, WGS84 / EPSG:4326. Point coordinate; not an uncertainty envelope. |
| `decimalLongitude` | number | Longitude used in the geographic overlays. Format/units: Decimal degrees, WGS84 / EPSG:4326. Point coordinate; not an uncertainty envelope. |
| `coordinateUncertaintyInMeters` | number | Reported radial uncertainty associated with the location. Format/units: Meters. Blank means unavailable, not zero; uncertainty was not used to buffer ecoregion assignments. |
| `identificationID` | string | Source identifier for an identification assertion. Format/units: Identifier or URI. Not the occurrence identifier. |
| `identifiedBy` | string | People or agents associated with the source identification. Format/units: Names or source identifiers. Does not necessarily identify the provider of this project’s later name resolution. |
| `dateIdentified` | string | Date or interval of the source identification. Format/units: Date/time or source date text. Distinct from service-query and user-review dates. |
| `taxonID` | string | Identifier attached to the taxon in the source record. Format/units: Identifier or URI. Identifier namespace is source-dependent; do not equate with a COL XR key. |
| `kingdom` | string | Kingdom in the original GBIF-interpreted classification. Format/units: Scientific classification name. Not recalculated after the project’s taxon-name changes. |
| `phylum` | string | Phylum in the original GBIF-interpreted classification. Format/units: Scientific classification name. Not recalculated after the project’s taxon-name changes. |
| `class` | string | Class in the original GBIF-interpreted classification. Format/units: Scientific classification name. The regional candidate analysis retained Insecta. |
| `order` | string | Order in the original GBIF-interpreted classification. Format/units: Scientific classification name. Not recalculated after the project’s taxon-name changes. |
| `family` | string | Family in the original GBIF-interpreted classification. Format/units: Scientific classification name. Not recalculated after the project’s taxon-name changes. |
| `genus` | string | Genus in the original GBIF-interpreted classification. Format/units: Scientific classification name. May differ from the genus of resolved_taxon_name following a name change. |
| `taxonRank` | string | Rank of the original GBIF-interpreted identification. Format/units: GBIF rank vocabulary. Not necessarily the rank of resolved_taxon_name after user-approved changes. |
| `taxonomicStatus` | string | Taxonomic status recorded in the original GBIF interpretation. Format/units: Source status vocabulary. Not the final project acceptance status; see taxon_resolution_description. |
| `datasetKey` | string | GBIF identifier for the dataset contributing the occurrence. Format/units: UUID. Can be used to retrieve source dataset provenance from GBIF. |
| `taxonKey` | string | Legacy GBIF taxon key assigned in the original download. Format/units: GBIF Backbone identifier. Preserved source key; not updated to the resolved COL XR name. |
| `acceptedTaxonKey` | string | Legacy GBIF accepted-taxon key in the original download. Format/units: GBIF Backbone identifier. Preserved source key; not a new resolved-name identifier. |
| `verbatimScientificName` | string | Scientific-name text originally supplied by the publisher. Format/units: Original scientific-name text. Preserved without replacement; can be blank and may differ from the GBIF-interpreted name sent to the service. |
| `resolved_taxon_name` | string | Final project-accepted canonical scientific name. Format/units: Scientific name without authorship. Uses GBIF Species Match API v2 / COL XR results and explicit user decisions; may retain subspecies or other finer ranks. |
| `taxon_resolution_description` | string | Readable account of the name match and acceptance decision. Format/units: Semicolon-separated descriptive text. Includes provider, original match type/confidence/status, GBIF-interpreted service input and any user-review note. Confidence is a matching score, not a probability that a specimen identification is correct. |
| `projectID` | string | Project identifier or identifiers supplied with the source occurrence. Format/units: Source identifier list. Not an identifier created for this repository; original archive allows semicolon-separated values. |
| `analysis_ecoregion_l3_code` | string | EPA Level III code assigned by the project’s geographic overlay. Format/units: EPA code: 6 or 85; semicolons supported. Represents full regional membership, not preserve membership; both exports retain this field. |
| `analysis_ecoregion_l3_name` | string | EPA Level III name corresponding to the assigned code. Format/units: EPA region name. Codes and names correspond in order when multiple labels occur. |
| `proposed_common_name` | string | ESA common name matched to the resolved taxon, parent species or approved binomial alias. Format/units: English common name; semicolon-separated alternatives. No source match leaves a blank. Subspecies-only common names are not generalized to the parent species. |
| `common_name_source` | string | Organization supplying the proposed common name. Format/units: Entomological Society of America (ESA), or blank. This package used the ESA list, not BugGuide. |
| `common_name_source_url` | string | Exact ESA spreadsheet download used for the assignment. Format/units: HTTPS URL, or blank. Source spreadsheet and checksum are retained in data/raw/common-names/esa/2026-10-27/. |

The CSV companion also records provenance and the exact source-term URI taken from the GBIF archive schema where applicable. Field descriptions are project-specific summaries, informed by [Darwin Core](https://dwc.tdwg.org/terms/) and [GBIF download documentation](https://techdocs.gbif.org/en/data-use/download-formats).

Classification and legacy taxon keys remain from the original GBIF interpretation; only resolved_taxon_name and its description reflect the later name-resolution decisions. The original publisher name can be blank. Full machine-readable resolution diagnostics, species roll-ups and Level IV assignments remain in the upstream version 3 dataset and audit tables.
