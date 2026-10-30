from __future__ import annotations

import logging
import re
from typing import Any

import pandas as pd

from src.utils import extract_year, resolve_path


LOGGER = logging.getLogger(__name__)

MISSING_STRINGS = {"", " ", "na", "n/a", "nan", "none", "null", "unknown"}


def clean_string(value: Any) -> str | None:
    """Normalize a single string-like value without changing source columns."""
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if text.lower() in MISSING_STRINGS:
        return None
    return text


def normalize_county(value: Any, aliases: dict[str, str]) -> str | None:
    """Standardize a county name using configured aliases."""
    text = clean_string(value)
    if not text:
        return None
    key = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    key = re.sub(r"\s+", " ", key).strip()
    return aliases.get(key)


def normalize_family(value: Any) -> str | None:
    """Normalize a family value for comparisons."""
    text = clean_string(value)
    if not text:
        return None
    return text.strip()


def build_working_name(row: pd.Series) -> str | None:
    """Create a conservative working species name from GBIF fields."""
    species = clean_string(row.get("species"))
    if species and " " in species:
        return species

    genus = clean_string(row.get("genus"))
    if genus and species and " " not in species:
        return f"{genus} {species}"

    for field in ["acceptedScientificName", "scientificName", "verbatimScientificName"]:
        name = clean_string(row.get(field))
        if not name:
            continue
        words = re.findall(r"[A-Z][a-z-]+|[a-z-]+", name)
        if len(words) >= 2:
            return f"{words[0]} {words[1]}"
    return None


def make_specimen_key(row: pd.Series) -> str | None:
    """Create a specimen-like key for duplicate review."""
    parts = [
        clean_string(row.get("institutionCode")),
        clean_string(row.get("collectionCode")),
        clean_string(row.get("catalogNumber")),
        clean_string(row.get("scientificName")),
    ]
    if not any(parts[:3]):
        return None
    return "|".join(part or "" for part in parts)


def add_clean_fields(raw_df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """Add cleaned and review fields alongside original GBIF values."""
    df = raw_df.copy()
    aliases = config.get("county_aliases", {})
    target_families = set(config["families"])
    bee_families = set(config.get("bee_families", []))
    uncertainty_limit = config["quality"]["coordinate_uncertainty_threshold_m"]

    for column in raw_df.columns:
        if raw_df[column].dtype == object:
            df[column] = raw_df[column].map(clean_string)

    df["familyWorking"] = df.apply(
        lambda row: normalize_family(row.get("family"))
        or normalize_family(row.get("queryFamily")),
        axis=1,
    )
    df["countyOriginal"] = df.get("county")
    df["countyClean"] = df.get("county").map(lambda value: normalize_county(value, aliases))
    df["countyFromCoordinates"] = False
    df["countyFieldConflict"] = False
    df["countyAssignmentMethod"] = df["countyClean"].map(
        lambda value: "gbif county field" if value else None
    )

    df["decimalLatitude"] = pd.to_numeric(df.get("decimalLatitude"), errors="coerce")
    df["decimalLongitude"] = pd.to_numeric(df.get("decimalLongitude"), errors="coerce")
    df["coordinateUncertaintyInMeters"] = pd.to_numeric(
        df.get("coordinateUncertaintyInMeters"), errors="coerce"
    )
    df["coordinateMissing"] = (
        df["decimalLatitude"].isna() | df["decimalLongitude"].isna()
    )
    df["coordinateUncertaintyHigh"] = (
        df["coordinateUncertaintyInMeters"].fillna(0) > uncertainty_limit
    )

    year_from_event = df.get("eventDate", pd.Series(index=df.index, dtype=object)).map(
        extract_year
    )
    df["eventYearClean"] = pd.to_numeric(df.get("year"), errors="coerce").fillna(
        year_from_event
    )
    df["eventYearClean"] = pd.to_numeric(df["eventYearClean"], errors="coerce").astype(
        "Int64"
    )

    df["specimenKey"] = df.apply(make_specimen_key, axis=1)
    df["probableDuplicate"] = False
    specimen_has_value = df["specimenKey"].notna()
    df.loc[specimen_has_value, "probableDuplicate"] = df.loc[
        specimen_has_value, "specimenKey"
    ].duplicated(keep=False)

    occurrence_has_value = df.get("occurrenceID", pd.Series(index=df.index)).notna()
    df.loc[occurrence_has_value, "probableDuplicate"] = (
        df.loc[occurrence_has_value, "probableDuplicate"]
        | df.loc[occurrence_has_value, "occurrenceID"].duplicated(keep=False)
    )

    df["identificationRank"] = df.get("taxonRank")
    df["workingScientificName"] = df.apply(build_working_name, axis=1)
    df["isGenusOnly"] = (
        df.get("taxonRank", pd.Series(index=df.index, dtype=object))
        .fillna("")
        .str.upper()
        .eq("GENUS")
        | df.get("species", pd.Series(index=df.index, dtype=object)).isna()
    )
    df["targetFamily"] = df["familyWorking"].isin(target_families)
    df["beeFamily"] = df["familyWorking"].isin(bee_families)
    df["localityReviewNeeded"] = (
        df["countyClean"].isna()
        | df["coordinateMissing"]
        | df["coordinateUncertaintyHigh"]
        | df["countyFieldConflict"]
    )
    return df


def exclusion_reasons(row: pd.Series, target_counties: set[str]) -> list[str]:
    """Identify reasons a record should be excluded from the cleaned dataset."""
    reasons: list[str] = []

    if bool(row.get("duplicateGbifID")):
        reasons.append("duplicate GBIF ID")
    if bool(row.get("beeFamily")):
        reasons.append("bee family")
    if not bool(row.get("targetFamily")):
        reasons.append("outside target non-bee Apoidea families")

    country = clean_string(row.get("countryCode"))
    if country and country.upper() not in {"US", "USA"}:
        reasons.append("outside United States")

    state = clean_string(row.get("stateProvince"))
    if state and state.lower() != "california":
        reasons.append("outside California")

    county = clean_string(row.get("countyClean"))
    if not county or county not in target_counties:
        reasons.append("county missing or outside target counties")

    basis = clean_string(row.get("basisOfRecord"))
    if basis and "FOSSIL" in basis.upper():
        reasons.append("fossil record")

    status = clean_string(row.get("occurrenceStatus"))
    if status and status.upper() == "ABSENT":
        reasons.append("absent occurrence")

    return reasons


def clean_occurrences(
    raw_df: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Clean raw GBIF rows and split excluded records for review."""
    if raw_df.empty:
        empty = add_clean_fields(raw_df, config)
        return empty, empty.copy(), {"rawRecords": 0, "cleanedRecords": 0}

    df = add_clean_fields(raw_df, config)
    target_counties = set(config["counties"])

    df["duplicateGbifID"] = df.get("gbifID").duplicated(keep="first")
    df["exclusionReason"] = df.apply(
        lambda row: "; ".join(exclusion_reasons(row, target_counties)),
        axis=1,
    )

    excluded = df[df["exclusionReason"].ne("")].copy()
    cleaned = df[df["exclusionReason"].eq("")].copy()

    stats = {
        "rawRecords": int(len(raw_df)),
        "cleanedRecords": int(len(cleaned)),
        "excludedRecords": int(len(excluded)),
        "duplicateGbifIDs": int(df["duplicateGbifID"].sum()),
        "genusOnlyRecords": int(cleaned["isGenusOnly"].sum()),
        "recordsNeedingLocalityReview": int(cleaned["localityReviewNeeded"].sum()),
    }
    LOGGER.info("Cleaning stats: %s", stats)
    return cleaned, excluded, stats


def write_cleaned_outputs(
    cleaned: pd.DataFrame,
    excluded: pd.DataFrame,
    config: dict[str, Any],
) -> None:
    """Write cleaned and excluded occurrence tables."""
    cleaned_path = resolve_path(config, config["paths"]["cleaned_occurrences_csv"])
    excluded_path = resolve_path(config, config["paths"]["excluded_records_csv"])
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    excluded_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(cleaned_path, index=False)
    excluded.to_csv(excluded_path, index=False)
    LOGGER.info("Wrote cleaned occurrences: %s", cleaned_path)
    LOGGER.info("Wrote excluded records: %s", excluded_path)

