# Zenodo data archive

The intended Zenodo deposit is a standalone **dataset**, containing
large local data files and the supporting provenance needed to reuse
them. It is not a GitHub release archive of the full repository.
Do not enable GitHub-to-Zenodo automatic release archiving for this purpose.

## Archive scope

- Large occurrence extracts and original compressed source responses.
- Large generated range polygons and nearest-occurrence tables.
- Source manifests, dataset citations, license information and checksums.
- The incoming USA-wide GBIF Arthropoda download, once received and
  its actual download DOI, size and filters have been recorded.

Keep scripts, ordinary figures and project documentation on GitHub.
The data deposit should link to the exact repository commit that
produced its derived files; add the resulting Zenodo DOI to the README
after the deposit is published. Files ignored by Git are not included
automatically and must be explicitly uploaded to the dataset deposit.

## Metadata and rights

The dataset still needs an agreed creator list, a title/version,
and a data-license decision before publication. The user's MIT choice
applies to original code, not to third-party collection datasets.
Retain GBIF's download citation and each contributing dataset's
license and attribution. Preserve the Ecdysis export's citation/EML
and EPA metadata. Do not replace these rights with a blanket MIT license.

Current local source provenance is recorded in `data/README.md`,
the source-specific manifests, and
`analysis/hill-diversity/migration_manifest.json`.

## Deposit workflow

1. Receive the new GBIF ZIP and record its DOI and actual scope.
2. Select the snapshot to archive, freeze its input files and record
   SHA-256 hashes, file roles, citations and licenses in an inventory.
3. Create a standalone dataset draft in Zenodo, upload the selected
   data and inventory, and link to the corresponding GitHub commit.
4. Review the creator list, descriptions, licenses and uploaded files.
5. Publish the dataset and add its DOI and retrieval instructions to
   the repository README. A reserved draft DOI is not a published record.

Zenodo currently allows 100 files and 50 GB per record; request a
quota increase if the incoming GBIF archive exceeds the limit rather
than splitting it solely to evade the quota.

Official documentation (checked 27 October 2026):

- [Create a new upload](https://help.zenodo.org/docs/deposit/create-new-upload/)
- [Manage files](https://help.zenodo.org/docs/deposit/manage-files/)
- [Size limits](https://support.zenodo.org/help/en-gb/1-upload-deposit/80-what-are-the-size-limitations-of-zenodo)

Status: deposit planning only. No Zenodo account connection, upload,
DOI reservation or publication has been performed.
