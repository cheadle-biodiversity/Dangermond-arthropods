# Level IV habitat annotations — first pass

`checklist_level_iv_6ap_habitat_notes.csv` and
`checklist_level_iv_85a_habitat_notes.csv` retain all original species and columns
and add mapped habitat evidence, original publisher habitat descriptions, local
Ecdysis context, cited life-history notes and review status. The original
seven-column checklists are preserved separately.

`geology_unit_names` lists distinct mapped geologic unit names for each species
in one comma-separated field, without codes or counts. Blank means no unit names
were assigned from the regional occurrence coordinates.

Read `analysis/habitat-notes/README.md` for methods and limitations. In particular:

- Spatial overlays describe the locations of records, not habitat specialization.
- USGS Qey combines beach and dune sand; Qeo is old dune substrate.
- Perko's Beach and lighthouse backdunes remain separate local contexts.
- Local preserve evidence is preserve-wide, regardless of which regional list
  contains the species. It is not evidence of occurrence inside that ecoregion.
- Maps cover only local portions of the regional candidate pool; no match does
  not mean non-coastal habitat or biological absence.
- Publisher habitat text is retained verbatim and may need ecological review.
- Life-history review is limited to a first set of coastal beetles and crickets. Unreviewed
  entries have blank life-history notes and an explicit review status.
- Regional and local record counts are separate, not independent totals to add.

`habitat_annotation_summary.csv` and `habitat_annotation_metadata.json` provide
counts, overlay diagnostics and checksums. Record-level evidence is retained at
`outputs/habitat-notes/2026-10-27/`.
