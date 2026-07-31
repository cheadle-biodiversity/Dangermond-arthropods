from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from src.build_checklist import build_checklist, write_checklist_outputs
from src.clean_occurrences import clean_occurrences, write_cleaned_outputs
from src.query_gbif import load_raw_occurrences, query_gbif
from src.utils import configure_logging, ensure_directories, load_config, save_json
from src.validation import validate_outputs, write_summary_report


LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line options for the local research workflow."""
    parser = argparse.ArgumentParser(
        description="Build the Central Coast non-bee Apoidea GBIF checklist."
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to the workflow YAML config file.",
    )
    parser.add_argument(
        "--refresh-gbif",
        action="store_true",
        help="Ignore cached per-family GBIF JSONL files and query GBIF again.",
    )
    parser.add_argument(
        "--skip-query",
        action="store_true",
        help="Use data/raw/gbif_occurrences_raw.csv instead of querying GBIF.",
    )
    parser.add_argument(
        "--families",
        nargs="+",
        help="Limit the run to one or more target families.",
    )
    parser.add_argument(
        "--county",
        action="append",
        help="Limit the run to one or more counties. Repeat for multiple counties.",
    )
    return parser.parse_args()


def apply_overrides(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    """Apply command-line family and county filters to the loaded config."""
    result = dict(config)
    if args.families:
        unknown = sorted(set(args.families) - set(config["families"]))
        if unknown:
            raise ValueError(f"Requested families are not in config.yaml: {unknown}")
        result["families"] = args.families

    if args.county:
        unknown = sorted(set(args.county) - set(config["counties"]))
        if unknown:
            raise ValueError(f"Requested counties are not in config.yaml: {unknown}")
        result["counties"] = args.county

    return result


def run() -> int:
    """Run the complete local workflow."""
    args = parse_args()
    config = apply_overrides(load_config(args.config), args)
    configure_logging(config)
    ensure_directories(config)

    LOGGER.info("Starting Central Coast non-bee Apoidea workflow")
    LOGGER.info("Families: %s", ", ".join(config["families"]))
    LOGGER.info("Counties: %s", ", ".join(config["counties"]))

    if args.skip_query:
        LOGGER.info("Skipping GBIF query and loading cached raw occurrence CSV")
        raw_df = load_raw_occurrences(config)
        metadata = {
            "createdAt": "",
            "querySkipped": True,
            "recordCount": int(len(raw_df)),
            "families": {},
        }
    else:
        raw_df, metadata = query_gbif(
            config=config,
            families=config["families"],
            refresh=args.refresh_gbif,
        )

    cleaned, excluded, cleaning_stats = clean_occurrences(raw_df, config)
    write_cleaned_outputs(cleaned, excluded, config)

    checklist, genus_records, crosswalk = build_checklist(cleaned, config)
    write_checklist_outputs(
        checklist=checklist,
        cleaned=cleaned,
        genus_records=genus_records,
        crosswalk=crosswalk,
        excluded=excluded,
        metadata=metadata,
        config=config,
    )

    validation = validate_outputs(raw_df, cleaned, checklist, config)
    write_summary_report(
        raw=raw_df,
        cleaned=cleaned,
        excluded=excluded,
        checklist=checklist,
        cleaning_stats=cleaning_stats,
        validation=validation,
        metadata=metadata,
        config=config,
    )

    metadata["cleaningStats"] = cleaning_stats
    metadata["validation"] = validation
    save_json(
        metadata,
        Path(config["_project_root"]) / config["paths"]["query_metadata_json"],
    )

    if validation["errors"]:
        LOGGER.error("Validation failed:")
        for error in validation["errors"]:
            LOGGER.error("  %s", error)
        return 1

    for warning in validation["warnings"]:
        LOGGER.warning(warning)

    LOGGER.info("Pipeline complete")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception as exc:
        LOGGER.exception("Pipeline failed: %s", exc)
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

