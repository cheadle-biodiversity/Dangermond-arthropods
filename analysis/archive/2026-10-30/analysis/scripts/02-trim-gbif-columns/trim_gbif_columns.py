#!/usr/bin/env python3
# ============================================================
# Trim GBIF Occurrence Columns (Arthropoda, California)
# ============================================================
# Dangermond Project — proposed Step 2 (column reduction)
#
# Purpose: Steps 2-10 of this pipeline only ever use a small subset of
# the ~230 columns a GBIF Darwin Core occurrence.txt export contains
# (dedup identifiers, taxonomy, and coordinates) — everything else
# (citation/rights metadata, event remarks, geological context,
# free-text locality notes, media links, etc.) is dead weight for this
# pipeline's purposes, but dominates the file's actual byte size.
#
# This script streams the full occurrence.txt line by line (it never
# loads the whole file into memory, so it works fine even on a file
# many gigabytes in size) and writes out just the needed columns,
# selected BY NAME rather than by fixed column position — GBIF's
# column order can differ across different downloads/export settings,
# so matching by header name (same philosophy as Step 1 resolving the
# taxon key by name rather than a hardcoded ID) is what keeps this
# robust if re-run against a different export later.
#
# WHY THIS EXISTS: the raw download for this project's real GBIF
# query came back as a single ~6.8 GB, 230-column file — far too large
# to move through a browser upload (30 MB limit) or even most
# device-to-cloud bridges (typically capped well under 1 GB per file).
# Trimming to just the needed columns first, before any transfer or
# processing, was the practical fix.
#
# WHAT'S NOT LOST: the full original file is untouched by this script
# (it only ever reads it, never modifies or deletes it) — a later step
# rejoins full record detail back onto the small, final per-species
# outputs using the same occurrenceID / institutionCode+collectionCode+
# catalogNumber matching keys Step 3 (merge/dedup) already uses, so
# nothing is permanently discarded, only deferred until the data is
# small enough that carrying every column is no longer a problem.
# ============================================================

import csv
import sys
import time

# ------------------------------------------------------------
# USER INPUTS — update if needed
# ------------------------------------------------------------
input_path = "occurrence.txt"
output_path = "occurrence_trimmed.txt"

# Columns to keep, in this order. Must match the exact header names in
# the input file (case-sensitive, standard Darwin Core term names).
columns_to_keep = [
    "gbifID",
    "occurrenceID",
    "institutionCode",
    "collectionCode",
    "catalogNumber",
    "basisOfRecord",
    "decimalLatitude",
    "decimalLongitude",
    "scientificName",
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
]

progress_every_n_rows = 500_000
# ------------------------------------------------------------

# csv.field_size_limit default (~131072 bytes) can be too small for a
# handful of long free-text DwC fields elsewhere in the row even
# though we're discarding them — raise it so csv.reader doesn't choke
# parsing a row before we get the chance to select columns out of it.
csv.field_size_limit(sys.maxsize if sys.maxsize < 2**31 else 2**31 - 1)


def main():
    start_time = time.time()

    with open(input_path, "r", encoding="utf-8", errors="replace", newline="") as infile:
        reader = csv.reader(infile, delimiter="\t", quoting=csv.QUOTE_NONE)

        try:
            header = next(reader)
        except StopIteration:
            sys.exit(f"ERROR: input file '{input_path}' appears to be empty.")

        # Map each wanted column name to its position in the actual
        # header — never assume a fixed column order.
        header_index = {name: i for i, name in enumerate(header)}

        missing = [c for c in columns_to_keep if c not in header_index]
        if missing:
            sys.exit(
                "ERROR: the following expected column(s) were not found in "
                f"'{input_path}' header: {missing}\n"
                "This usually means the export's column set differs from what "
                "this script expects — check the header and update "
                "columns_to_keep above, or investigate why they're missing "
                "before proceeding."
            )

        keep_indices = [header_index[name] for name in columns_to_keep]
        n_input_cols = len(header)

        print(f"Input:  {input_path}")
        print(f"Output: {output_path}")
        print(f"Keeping {len(columns_to_keep)} of {n_input_cols} columns: {columns_to_keep}")
        print()

        with open(output_path, "w", encoding="utf-8", newline="") as outfile:
            writer = csv.writer(
                outfile, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\", lineterminator="\n"
            )
            writer.writerow(columns_to_keep)

            n_rows = 0
            n_short_rows = 0

            for row in reader:
                n_rows += 1

                # Defensive: a row with fewer fields than the header
                # (malformed/truncated line) shouldn't crash the whole
                # run — skip it, but count and report how many so it's
                # never a silent data-quality issue.
                if len(row) < n_input_cols:
                    n_short_rows += 1
                    continue

                writer.writerow([row[i] for i in keep_indices])

                if n_rows % progress_every_n_rows == 0:
                    elapsed = time.time() - start_time
                    print(f"  ...{n_rows:,} rows processed ({elapsed:.0f}s elapsed)")

    elapsed = time.time() - start_time
    print()
    print(f"Done. {n_rows:,} rows processed in {elapsed:.0f}s.")
    if n_short_rows:
        print(
            f"WARNING: {n_short_rows:,} row(s) had fewer fields than the header "
            "and were skipped — investigate if this count is large relative to "
            "total rows, since it may indicate a parsing or export issue rather "
            "than a handful of genuinely malformed records."
        )
    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    main()
