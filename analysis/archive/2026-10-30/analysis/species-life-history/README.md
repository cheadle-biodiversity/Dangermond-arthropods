# Retired: Level IV species habitat and natural-history accounts

**Withdrawn at user request on 27 October 2026.** The life-history and source
columns have been removed from active Level IV lists and their duplicate copies.
The lookup evidence remains archived for provenance. The following describes
the withdrawn enrichment, not the current checklist layout.

The user requested habitat/life-history information and conservation or other
notable traits for every species in the Level IV candidate lists. This is a
bounded species-account lookup, not a complete manual literature review.
Retrieval date: **27 October 2026**.

Both Level IV checklists now have `source` immediately after
`life_history_notes`. No spatial/geology columns are added. Original names,
classifications, common names, occurrence counts, preserve flags and row order
are preserved. Level III lists are unchanged. The files in
`data/final/habitat-notes/` are identical copies retained for old links.

## Coverage

All **2,550 unique species** were queried. **502** have usable sourced notes;
**2,048** remain blank. Blank means the queried accounts did not provide usable
evidence, not that nothing is known about the species. The 6ap list has notes
for **265/1,521** species; 85a has notes for **425/1,852**. Lists overlap.
Conservation-related flags occur for **24** unique species, including explicit
warnings when the status applies only to a subspecies or population.

## Sources and selection

1. **GBIF Species API v1** strict name match: all 2,550 requests succeeded;
   2,518 matched the exact canonical binomial at species/subspecies rank in
   Insecta. Only those matches were used to retrieve account descriptions and
   IUCN categories. Synonym/accepted-name responses are retained in the audit;
   they support source retrieval and do not change checklist names. Thirty-two
   nonexact matches were rejected for automatic account annotation.
2. **Original accounts indexed by GBIF**, including taxonomic papers and Species
   File accounts: ecological, habitat, host and biology fields only. Morphology,
   specimen localities and taxonomy-only descriptions are not habitat evidence.
   Source links identify the originating GBIF source-taxon account, whose source
   dataset/publication is named in the note. Up to two distinct original account
   sources are selected per species. This selection does not exhaust every
   description supplied by GBIF.
3. **Northwestern European arthropod life histories and ecological traits**:
   positive habitat flags and feeding guilds are identified as European evidence.
   A zero is not a habitat association. These data do not establish California
   habitat use or dune specialization. DAISIE habitat accounts likewise carry
   an explicit European qualifier.
4. **Butterflies and Moths of North America (BAMONA)**: all 594 Lepidoptera
   names were requested; 460 pages returned HTTP 200 and 134 returned 404.
   The binomial must occur in the page title. Only populated habitat, larval-host,
   life-history and adult-food fields are used. Empty accounts are not evidence.
   Historical conservation text/NCGR values are not promoted to current legal
   status.
5. **CDFW October 2026 Special Animals List**, inspected as a PDF with its column
   layout: the list's 26 matching entries include species, subspecies and a
   population. Species-level checklist entries can carry a note about a tracked
   subspecies, but the note explicitly limits that status to the named entity.
   Tracked status does not itself mean federally/state listed or CDFW Species
   of Special Concern. Rank codes are retained as reported. Proposed and
   candidate listings remain labeled as such. The listed-animals PDF was also
   downloaded for reference; the annotated flags use the Special Animals List.
6. **Reviewed species accounts** in `reviewed_additions.csv` and the earlier
   `analysis/habitat-notes/reviewed_species_notes.csv`: 16 checklist species have
   these notes. The four Cafius notes based on genus-level feeding context say
   so explicitly. These reviewed notes supplement the automatic excerpts.
7. Wikipedia was queried in 128 batches as exploratory reference discovery;
   its extracts are cached but **not used to populate final notes**. Direct
   BugGuide batch access returned 403; no access restriction was bypassed.
   The separately reviewed Bombus californicus account was available through
   web retrieval and is attributed to that account.

Automatic account wording is clearly marked **account excerpt**; quotations are
capped at 25 words per source URL per species and may end in an ellipsis.
They are reference leads, not newly written comprehensive species biographies.
Structured trait/status facts and separately reviewed paraphrases are labeled
separately. Geographic context in original account titles must be respected.
Neither a regional occurrence nor a nearby mapped unit is used to call a species
a beach/dune specialist. No additional species-presence claims are made.

The GBIF IUCN endpoint reports a global category but not its assessment date.
CR, EN, VU and NT are flagged with that limitation and retrieval date. No absence
of a flag is interpreted as absence of conservation concern. Legal status can
change and must be checked again before management decisions.

## Reproduce and audit

From the repository root:

```sh
python3 analysis/species-life-history/collect_sources.py
# extract_cdfw.py requires pypdf; source PDFs are retained in the raw folder.
python3 analysis/species-life-history/extract_cdfw.py
python3 analysis/species-life-history/build_notes.py
```

The collector uses requests and Python's standard library, a research User-Agent,
six workers, timeout/retry handling and resumable compressed caches. The compiler
uses only the standard library. Run the compiler **after** regenerating the base
checklists with `create_ecoregion_checklists.py`, which creates blank base notes.
The CDFW extraction expects the two downloaded PDFs; their source URLs are below.

`outputs/species-life-history/2026-10-27/summary.json` records coverage and final
checksums. `species_lookup_coverage.csv` lists all 2,550 species. The compressed
`species_source_audit.jsonl.gz` retains selected text, unabridged account fields,
name-match diagnostics, source identity, HTTP statuses and quote counts. The audit
and raw HTML/JSON/PDF caches are local-only and ignored by Git. They contain
reference material, not redistributable newly licensed project prose.

## References

- [GBIF Species API](https://techdocs.gbif.org/en/openapi/v1/species).
- [Butterflies and Moths of North America](https://www.butterfliesandmoths.org/).
- [CDFW Special Animals List, October 2026](https://nrm.dfg.ca.gov/FileHandler.ashx?DocumentID=109406&inline=).
- [CDFW State and Federally Listed Animals, October 2026](https://nrm.dfg.ca.gov/FileHandler.ashx?DocumentID=109405&inline=).
- Exact species-account URLs are provided in each annotated checklist row and
  the source audit; original data retain their source licenses.
