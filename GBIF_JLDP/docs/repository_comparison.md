# Full data flow comparison

How OBIS-SEAMAP, KNB and PANGAEA handle data submission, and whether submitted occurrence data reach GBIF. Appendix to the TNC report on Dangermond Preserve data accessibility, October 2026.

| | OBIS-SEAMAP | KNB/Dangermond | PANGAEA |
| --- | --- | --- | --- |
| Scope | Narrow: marine mammals, seabirds, sea turtles | Broad: any ecological or environmental data | Broad: earth and environmental science |
| Who standardizes the data | Curators. You send raw files and they map them to their schema. | Researcher/Author. Self-service upload through an online form. | Curators. Expert data editors work with you through a ticket system. |
| Formats accepted | Nearly anything except device-dependent binary | Any file type, described with EML metadata | Any format; editors convert it to PANGAEA's format |
| Minimum content | Species, lat/lon, date/time, count | An EML metadata record and an ORCID for the submitter | Data plus metadata compiled with the editor |
| Curation depth | Records are loaded into one queryable database; effort data become tracklines | Files are archived as submitted; no record-level standardization | Basic (metadata only) or enhanced (data converted, quality-checked, harmonized and loaded into a relational database) |
| Researcher effort | Low: send files and a species-code key, then review metadata online | Highest: you write the EML (attributes, units, coverage) yourself | Moderate: back-and-forth with the editor, but they do the conversion |
| Turnaround | Not published; you approve before it goes public | Immediate once you publish | About 6–8 weeks after the submission is accepted |
| Cost to depositor | Free (no fee stated) | Free | Free, but €500 is requested when project funds cover publication; large projects negotiate |
| Cost to the host | Not published; appears to run on a small team at Duke's Marine Geospatial Ecology Lab | Low marginal cost per dataset because there are no curators; Metacat software is open source | About €1M a year and ~24 staff, over two-thirds on curation (2017 figures) |
| Onward to GBIF/OBIS | Automatic by default (minimum fields only) | KNB is a GBIF publisher, but nothing flows unless the data are restructured as Darwin Core | PANGAEA is a registered GBIF publisher |
| Access control | CC0, CC BY, CC BY-NC, plus "permission required" | License chosen at upload; embargo possible | Password protection until the related paper is published |

## Sources

- OBIS-SEAMAP, Contributing Data (Contributor FAQ): https://seamap.env.duke.edu/content/provider_faq
- About the KNB: https://knb.ecoinformatics.org/js/themes/knb/templates/about.html
- KNB on GBIF: https://www.gbif.org/publisher/7879e569-4a13-4643-b833-d1a564675b86
- PANGAEA, Data submission: https://wiki.pangaea.de/wiki/Submit
- PANGAEA, Submit Data: https://pangaea.de/submit/
- PANGAEA, Costs: https://wiki.pangaea.de/wiki/Costs
- PANGAEA, Curation levels: https://wiki.pangaea.de/wiki/Curation_levels
- Diepenbroek, PANGAEA presentation, DINI 2017 (host costs and staffing): https://dini.de/fileadmin/jahrestagungen/2017/2017-10-05--08-diepenbroek-PANGEA.pdf
- PANGAEA on GBIF (organization key d5778510-eb28-11da-8629-b8a03c50a862): https://www.gbif.org/publisher/d5778510-eb28-11da-8629-b8a03c50a862
