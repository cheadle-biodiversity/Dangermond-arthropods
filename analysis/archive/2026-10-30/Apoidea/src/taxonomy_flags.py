from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.utils import resolve_path


SPECIES_COMPLEX_COLUMNS = [
    "inputName",
    "acceptedName",
    "family",
    "genus",
    "complexFlag",
    "evidenceType",
    "citation",
    "notes",
    "dateReviewed",
]

ALLOWED_COMPLEX_FLAGS = {"Yes", "Suspected", "No", "Unknown"}


def ensure_species_complex_table(path: Path) -> None:
    """Create the manual species-complex table if it is missing."""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=SPECIES_COMPLEX_COLUMNS).to_csv(path, index=False)


def load_species_complexes(config: dict[str, Any]) -> pd.DataFrame:
    """Load manually curated species-complex flags."""
    path = resolve_path(config, config["paths"]["species_complexes_csv"])
    ensure_species_complex_table(path)
    table = pd.read_csv(path, dtype=str).fillna("")
    for column in SPECIES_COMPLEX_COLUMNS:
        if column not in table.columns:
            table[column] = ""
    return table[SPECIES_COMPLEX_COLUMNS]


def normalize_flag(value: Any) -> str:
    """Normalize manual flags to allowed values."""
    text = str(value or "").strip().lower()
    if text == "yes":
        return "Yes"
    if text == "suspected":
        return "Suspected"
    if text == "no":
        return "No"
    return "Unknown"


def add_taxonomy_flags(
    checklist: pd.DataFrame,
    species_complexes: pd.DataFrame,
) -> pd.DataFrame:
    """Attach species-complex flags to checklist rows."""
    result = checklist.copy()
    result["taxonomyComplexFlag"] = "Unknown"
    result["taxonomyComplexEvidence"] = ""
    result["taxonomyComplexNotes"] = ""

    if species_complexes.empty or result.empty:
        return result

    table = species_complexes.copy()
    table["complexFlag"] = table["complexFlag"].map(normalize_flag)
    table["lookupName"] = table["acceptedName"].where(
        table["acceptedName"].str.strip().ne(""), table["inputName"]
    )
    table["lookupName"] = table["lookupName"].str.strip().str.lower()
    table = table[table["lookupName"].ne("")]
    table = table.drop_duplicates("lookupName", keep="first")
    lookup = table.set_index("lookupName").to_dict(orient="index")

    for index, row in result.iterrows():
        key = str(row.get("workingScientificName", "")).strip().lower()
        record = lookup.get(key)
        if not record:
            continue

        evidence_parts = [
            record.get("evidenceType", ""),
            record.get("citation", ""),
        ]
        result.at[index, "taxonomyComplexFlag"] = normalize_flag(
            record.get("complexFlag")
        )
        result.at[index, "taxonomyComplexEvidence"] = "; ".join(
            part for part in evidence_parts if str(part).strip()
        )
        result.at[index, "taxonomyComplexNotes"] = record.get("notes", "")

    return result

