from __future__ import annotations

from typing import Any

import pandas as pd

from src.taxonomy_flags import ALLOWED_COMPLEX_FLAGS
from src.utils import resolve_path


def validate_outputs(
    raw: pd.DataFrame,
    cleaned: pd.DataFrame,
    checklist: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, list[str]]:
    """Run simple validation checks from the README."""
    errors: list[str] = []
    warnings: list[str] = []
    target_counties = set(config["counties"])
    target_families = set(config["families"])
    bee_families = set(config.get("bee_families", []))

    if cleaned["familyWorking"].isin(bee_families).any():
        errors.append("Cleaned records include bee families.")

    outside_counties = cleaned[~cleaned["countyClean"].isin(target_counties)]
    if not outside_counties.empty:
        errors.append("Cleaned records include rows outside target counties.")

    if cleaned["gbifID"].duplicated().any():
        errors.append("Cleaned records include duplicate GBIF IDs.")

    if not checklist.empty and checklist["workingScientificName"].isna().any():
        errors.append("Checklist has rows without a working scientific name.")

    if not checklist.empty and ~checklist["currentFamily"].isin(target_families).all():
        errors.append("Checklist includes family names outside configured target families.")

    if not checklist.empty:
        flags = set(checklist["taxonomyComplexFlag"].dropna().astype(str))
        invalid_flags = flags - ALLOWED_COMPLEX_FLAGS
        if invalid_flags:
            errors.append(f"Invalid taxonomy complex flags: {sorted(invalid_flags)}")

        needs_evidence = checklist[
            checklist["taxonomyComplexFlag"].isin(["Yes", "Suspected"])
            & checklist["taxonomyComplexEvidence"].fillna("").str.strip().eq("")
            & checklist["taxonomyComplexNotes"].fillna("").str.strip().eq("")
        ]
        if not needs_evidence.empty:
            errors.append(
                "Taxonomy flags Yes/Suspected require evidence or notes."
            )

        county_columns = [f"{county} count" for county in config["counties"]]
        missing_county_columns = [col for col in county_columns if col not in checklist]
        if missing_county_columns:
            errors.append(f"Missing county count columns: {missing_county_columns}")
        else:
            county_totals = checklist[county_columns].sum(axis=1)
            mismatches = county_totals.ne(checklist["totalRecordCount"])
            if mismatches.any():
                errors.append("Checklist county totals do not match totalRecordCount.")

    raw_path = resolve_path(config, config["paths"]["raw_occurrences_csv"])
    expected_paths = [
        raw_path,
        resolve_path(config, config["paths"]["cleaned_occurrences_csv"]),
        resolve_path(config, config["paths"]["checklist_csv"]),
        resolve_path(config, config["paths"]["query_metadata_json"]),
    ]
    missing_outputs = [str(path) for path in expected_paths if not path.exists()]
    if missing_outputs:
        warnings.append(f"Expected output files are not present yet: {missing_outputs}")

    if raw.empty:
        warnings.append("Raw occurrence table is empty.")
    if cleaned.empty:
        warnings.append("Cleaned occurrence table is empty.")
    if checklist.empty:
        warnings.append("Checklist is empty.")

    return {"errors": errors, "warnings": warnings}


def write_summary_report(
    raw: pd.DataFrame,
    cleaned: pd.DataFrame,
    excluded: pd.DataFrame,
    checklist: pd.DataFrame,
    cleaning_stats: dict[str, int],
    validation: dict[str, list[str]],
    metadata: dict[str, Any],
    config: dict[str, Any],
) -> None:
    """Write a concise Markdown summary for researchers."""
    path = resolve_path(config, config["paths"]["summary_report_md"])
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Central Coast Non-Bee Apoidea Summary",
        "",
        f"Created: {metadata.get('createdAt', '')}",
        "",
        "## Scope",
        "",
        f"Families: {', '.join(config['families'])}",
        "",
        f"Counties: {', '.join(config['counties'])}",
        "",
        "## Record Counts",
        "",
        f"* Raw GBIF records: {len(raw)}",
        f"* Cleaned records retained: {len(cleaned)}",
        f"* Excluded records: {len(excluded)}",
        f"* Checklist species rows: {len(checklist)}",
        f"* Genus-only records: {cleaning_stats.get('genusOnlyRecords', 0)}",
        f"* Records needing locality review: {cleaning_stats.get('recordsNeedingLocalityReview', 0)}",
        "",
        "## Validation",
        "",
    ]

    if validation["errors"]:
        lines.append("Errors:")
        lines.extend(f"* {error}" for error in validation["errors"])
    else:
        lines.append("* No validation errors.")

    if validation["warnings"]:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"* {warning}" for warning in validation["warnings"])

    lines.extend(
        [
            "",
            "## Data Limitations",
            "",
            "* GBIF absence does not imply true absence.",
            "* Record density reflects sampling effort.",
            "* County fields may be incorrect or missing.",
            "* Coordinates may be generalized.",
            "* Historical records may use outdated taxonomy.",
            "* Species-complex flags come from manual curation.",
            "* Dangermond likelihood is a planning tool, not a predictive model.",
            "* Voucher specimens remain the final authority.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
