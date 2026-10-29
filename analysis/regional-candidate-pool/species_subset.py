"""Create a separate species-resolved subset of the regional insect records."""
from collections import Counter
from datetime import date
from pathlib import Path
import csv
import gzip
import hashlib
import json

import pandas as pd

from filter_gbif import RANKS

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/regional-candidate-pool/gbif-vgv5ee"
SOURCE = OUT / "filtered_insect_records.csv.gz"
TARGET = OUT / "species_identified_insect_records.csv.gz"
# Species aggregates and ranks between genus and species are not species IDs.
SPECIES_RANKS = RANKS - {
    "GENUS", "SUBGENUS", "SECTION", "SUBSECTION", "SERIES", "SUBSERIES",
    "INFRAGENERIC_NAME", "SPECIES_AGGREGATE",
}


def main():
    counts = Counter()
    ranks = Counter()
    regions = Counter()
    species = set()
    partial = TARGET.with_suffix(".gz.partial")
    first = True
    with gzip.open(partial, "wt", encoding="utf-8", newline="", compresslevel=3) as target:
        for frame in pd.read_csv(SOURCE, dtype=str, keep_default_na=False, chunksize=25000):
            counts["input_records"] += len(frame)
            rank_ok = frame.taxonRank.str.strip().str.upper().isin(SPECIES_RANKS)
            key = pd.to_numeric(frame.speciesKey, errors="coerce")
            resolved = key.gt(0) & frame.species.str.strip().ne("")
            counts["excluded_rank_above_species"] += int((~rank_ok).sum())
            counts["excluded_species_rank_without_resolved_species"] += int((rank_ok & ~resolved).sum())
            selected = frame.loc[rank_ok & resolved]
            counts["retained_records"] += len(selected)
            ranks.update(selected.taxonRank)
            regions.update(selected.analysis_ecoregion_l3_code)
            species.update(selected.speciesKey)
            selected.to_csv(target, index=False, header=first)
            first = False
            if counts["input_records"] % 250000 == 0:
                print(f"Read {counts['input_records']:,}; retained {counts['retained_records']:,}", flush=True)
    parent = json.loads((OUT / "filter_metadata.json").read_text())
    assert counts["input_records"] == parent["counts"]["4_target_level_iii_ecoregions"]
    assert sum(v for k, v in counts.items() if k != "input_records") == counts["input_records"]
    assert counts["retained_records"] > 0
    partial.replace(TARGET)
    digest = hashlib.file_digest(SOURCE.open("rb"), "sha256").hexdigest()
    metadata = {
        "created_on": date.today().isoformat(),
        "source_doi": parent["source_doi"],
        "parent_dataset": str(SOURCE.relative_to(ROOT)),
        "parent_dataset_sha256": digest,
        "output_dataset": str(TARGET.relative_to(ROOT)),
        "selection_rule": "Interpreted taxonRank SPECIES or a finer rank, positive speciesKey and nonblank species. Includes subspecies and varieties resolved to a named species; excludes genus-only and species-aggregate IDs.",
        "accepted_ranks": sorted(SPECIES_RANKS),
        "counts": dict(counts), "records_by_rank": dict(ranks),
        "records_by_ecoregion": dict(regions),
        "distinct_gbif_species_keys": len(species),
        "scope": "All parent fields and filters retained; no new deduplication, BOLD, identification-qualifier or conservation-status screening. Candidate occurrence pool, not evidence of occurrence on the preserve.",
    }
    (OUT / "species_subset_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    with (OUT / "species_subset_counts.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["measure", "count"])
        writer.writerows(counts.items())
        writer.writerow(["distinct_gbif_species_keys", len(species)])
    print(json.dumps(metadata, indent=2), flush=True)


if __name__ == "__main__":
    main()
