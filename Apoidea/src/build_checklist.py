from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from src.taxonomy_flags import add_taxonomy_flags, load_species_complexes
from src.utils import haversine_km, resolve_path, unique_join


LOGGER = logging.getLogger(__name__)


DATA_DICTIONARY = [
    ("workingScientificName", "Working checklist name used for grouping records."),
    ("acceptedScientificNameGBIF", "GBIF accepted scientific name, when available."),
    ("verbatimNames", "Unique verbatim or scientific names seen among source records."),
    ("currentFamily", "Family used for the working checklist row."),
    ("totalRecordCount", "Number of cleaned records assigned to this species."),
    ("uniqueOccurrenceCount", "Unique occurrence identifiers, falling back to GBIF IDs."),
    ("uniqueSpecimenCount", "Unique specimen-like keys built from collection fields."),
    ("earliestYear", "Earliest interpreted event year."),
    ("latestYear", "Latest interpreted event year."),
    ("nearestDangermondOccurrenceKm", "Nearest geodesic distance to the configured Dangermond point."),
    ("dangermondLikelihood", "Rule-based planning category, not a species distribution model."),
    ("taxonomyComplexFlag", "Manual species-complex flag from data/taxonomy_species_complexes.csv."),
]


def mode_or_first(series: pd.Series) -> Any:
    """Return the most common non-empty value from a series."""
    cleaned = series.dropna()
    cleaned = cleaned[cleaned.astype(str).str.strip().ne("")]
    if cleaned.empty:
        return ""
    modes = cleaned.mode()
    if not modes.empty:
        return modes.iloc[0]
    return cleaned.iloc[0]


def add_dangermond_distance(df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """Add distance from each record to the configured Dangermond point."""
    result = df.copy()
    point = config.get("dangermond", {}).get("reference_point", {})
    latitude = point.get("latitude")
    longitude = point.get("longitude")

    if latitude is None or longitude is None or result.empty:
        result["distanceKmToDangermond"] = pd.NA
        return result

    def distance(row: pd.Series) -> float | None:
        lat = row.get("decimalLatitude")
        lon = row.get("decimalLongitude")
        if pd.isna(lat) or pd.isna(lon):
            return None
        return haversine_km(float(lat), float(lon), float(latitude), float(longitude))

    result["distanceKmToDangermond"] = result.apply(distance, axis=1)
    return result


def dangermond_likelihood(group: pd.DataFrame, config: dict[str, Any]) -> str:
    """Assign a simple planning category for Dangermond relevance."""
    thresholds = config.get("dangermond", {}).get("distance_thresholds_km", {})
    confirmed_km = float(thresholds.get("confirmed", 1))
    coastal_km = float(thresholds.get("coastal_santa_barbara", 35))
    regional_km = float(thresholds.get("regionally_plausible", 150))

    distances = pd.to_numeric(group["distanceKmToDangermond"], errors="coerce")
    min_distance = distances.min(skipna=True)
    counties = set(group["countyClean"].dropna().astype(str))

    if pd.notna(min_distance) and min_distance <= confirmed_km:
        return "Confirmed at Dangermond"
    if "Santa Barbara" in counties and pd.notna(min_distance) and min_distance <= coastal_km:
        return "Coastal Santa Barbara"
    if "Santa Barbara" in counties:
        return "Elsewhere in Santa Barbara County"
    if counties:
        return "Adjacent Central Coast"
    if pd.notna(min_distance) and min_distance <= regional_km:
        return "Regionally plausible"
    return "Unlikely"


def count_unique_identifiers(group: pd.DataFrame) -> int:
    """Count unique occurrence IDs with GBIF ID fallback."""
    ids = group["occurrenceID"].copy()
    ids = ids.where(ids.notna(), group["gbifID"])
    return int(ids.dropna().astype(str).nunique())


def build_species_row(
    working_name: str,
    group: pd.DataFrame,
    counties: list[str],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Build one checklist row from grouped occurrence records."""
    occurrence_ids = count_unique_identifiers(group)
    specimen_count = int(group["specimenKey"].dropna().astype(str).nunique())
    years = pd.to_numeric(group["eventYearClean"], errors="coerce").dropna()
    distances = pd.to_numeric(group["distanceKmToDangermond"], errors="coerce")
    min_distance = distances.min(skipna=True)

    row: dict[str, Any] = {
        "workingScientificName": working_name,
        "acceptedScientificNameGBIF": unique_join(group["acceptedScientificName"]),
        "verbatimNames": unique_join(
            pd.concat(
                [
                    group["verbatimScientificName"],
                    group["scientificName"],
                ],
                ignore_index=True,
            )
        ),
        "currentFamily": mode_or_first(group["familyWorking"]),
        "genus": mode_or_first(group["genus"]),
        "species": mode_or_first(group["species"]),
        "totalRecordCount": int(len(group)),
        "uniqueOccurrenceCount": occurrence_ids,
        "uniqueSpecimenCount": specimen_count,
        "earliestYear": int(years.min()) if not years.empty else "",
        "latestYear": int(years.max()) if not years.empty else "",
        "counties recorded": unique_join(group["countyClean"]),
        "preserved specimen count": int(
            group["basisOfRecord"].fillna("").str.upper().eq("PRESERVED_SPECIMEN").sum()
        ),
        "human observation count": int(
            group["basisOfRecord"].fillna("").str.upper().eq("HUMAN_OBSERVATION").sum()
        ),
        "institutions": unique_join(group["institutionCode"]),
        "datasets": unique_join(group["datasetName"]),
        "nearestDangermondOccurrenceKm": (
            round(float(min_distance), 2) if pd.notna(min_distance) else ""
        ),
        "dangermondLikelihood": dangermond_likelihood(group, config),
        "reviewNotes": "",
    }

    for county in counties:
        row[f"{county} count"] = int(group["countyClean"].eq(county).sum())

    return row


def build_taxon_crosswalk(cleaned: pd.DataFrame) -> pd.DataFrame:
    """Build the taxonomic crosswalk table."""
    columns = [
        "verbatimScientificName",
        "scientificName",
        "acceptedScientificName",
        "workingScientificName",
        "familyWorking",
        "genus",
        "species",
    ]
    if cleaned.empty:
        return pd.DataFrame(columns=columns)
    return cleaned[columns].drop_duplicates().sort_values(
        ["workingScientificName", "scientificName"],
        na_position="last",
    )


def build_checklist(
    cleaned: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create checklist, genus-only records, and taxonomic crosswalk tables."""
    cleaned = add_dangermond_distance(cleaned, config)
    genus_records = cleaned[cleaned["isGenusOnly"]].copy()
    species_records = cleaned[
        ~cleaned["isGenusOnly"] & cleaned["workingScientificName"].notna()
    ].copy()

    rows = [
        build_species_row(working_name, group, config["counties"], config)
        for working_name, group in species_records.groupby("workingScientificName")
    ]
    checklist = pd.DataFrame(rows)

    if not checklist.empty:
        county_columns = [f"{county} count" for county in config["counties"]]
        base_columns = [
            "workingScientificName",
            "acceptedScientificNameGBIF",
            "verbatimNames",
            "currentFamily",
            "genus",
            "species",
            "totalRecordCount",
            "uniqueOccurrenceCount",
            "uniqueSpecimenCount",
            "earliestYear",
            "latestYear",
            *county_columns,
            "counties recorded",
            "preserved specimen count",
            "human observation count",
            "institutions",
            "datasets",
            "nearestDangermondOccurrenceKm",
            "dangermondLikelihood",
            "reviewNotes",
        ]
        checklist = checklist[base_columns].sort_values(
            ["currentFamily", "workingScientificName"]
        )

    species_complexes = load_species_complexes(config)
    checklist = add_taxonomy_flags(checklist, species_complexes)
    crosswalk = build_taxon_crosswalk(cleaned)
    return checklist, genus_records, crosswalk


def write_checklist_outputs(
    checklist: pd.DataFrame,
    cleaned: pd.DataFrame,
    genus_records: pd.DataFrame,
    crosswalk: pd.DataFrame,
    excluded: pd.DataFrame,
    metadata: dict[str, Any],
    config: dict[str, Any],
) -> None:
    """Write checklist, crosswalk, genus records, and workbook outputs."""
    checklist_csv = resolve_path(config, config["paths"]["checklist_csv"])
    xlsx_path = resolve_path(config, config["paths"]["checklist_xlsx"])
    crosswalk_path = resolve_path(config, config["paths"]["taxon_crosswalk_csv"])
    genus_path = resolve_path(config, config["paths"]["genus_records_csv"])

    checklist_csv.parent.mkdir(parents=True, exist_ok=True)
    checklist.to_csv(checklist_csv, index=False)
    crosswalk.to_csv(crosswalk_path, index=False)
    genus_records.to_csv(genus_path, index=False)
    LOGGER.info("Wrote checklist CSV: %s", checklist_csv)
    LOGGER.info("Wrote taxon crosswalk: %s", crosswalk_path)
    LOGGER.info("Wrote genus records: %s", genus_path)

    metadata_rows = [
        {"key": key, "value": str(value)}
        for key, value in metadata.items()
        if key != "families"
    ]
    family_rows = []
    for family, details in metadata.get("families", {}).items():
        resolution = details.get("resolution", {})
        query = details.get("query", {})
        family_rows.append(
            {
                "family": family,
                "taxonKey": resolution.get("usageKey"),
                "matchType": resolution.get("matchType"),
                "confidence": resolution.get("confidence"),
                "records": query.get("records"),
                "cacheUsed": query.get("cacheUsed"),
                "cachePath": query.get("cachePath"),
            }
        )

    data_dictionary = pd.DataFrame(DATA_DICTIONARY, columns=["field", "description"])
    species_complexes = load_species_complexes(config)

    try:
        with pd.ExcelWriter(xlsx_path) as writer:
            checklist.to_excel(writer, sheet_name="Checklist", index=False)
            cleaned.to_excel(writer, sheet_name="Occurrences", index=False)
            genus_records.to_excel(writer, sheet_name="Genus Records", index=False)
            crosswalk.to_excel(writer, sheet_name="Taxonomic Crosswalk", index=False)
            species_complexes.to_excel(writer, sheet_name="Species Complexes", index=False)
            pd.DataFrame(metadata_rows).to_excel(
                writer, sheet_name="Query Metadata", index=False
            )
            pd.DataFrame(family_rows).to_excel(
                writer, sheet_name="Family Queries", index=False
            )
            excluded.to_excel(writer, sheet_name="Excluded Records", index=False)
            data_dictionary.to_excel(writer, sheet_name="Data Dictionary", index=False)
        LOGGER.info("Wrote Excel workbook: %s", xlsx_path)
    except ImportError:
        LOGGER.warning(
            "openpyxl is not installed, so Excel workbook was not written: %s",
            xlsx_path,
        )

