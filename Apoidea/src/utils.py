from __future__ import annotations

import json
import logging
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def project_root() -> Path:
    """Return the repository root for this small workflow."""
    return Path(__file__).resolve().parents[1]


def load_config(config_path: str | Path) -> dict[str, Any]:
    """Load the YAML config file with a helpful dependency error."""
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required to read config.yaml. Install dependencies with "
            "`python3 -m pip install -r requirements.txt`."
        ) from exc

    path = Path(config_path)
    if not path.is_absolute():
        path = project_root() / path

    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    if not isinstance(config, dict):
        raise ValueError(f"Config file did not parse as a mapping: {path}")

    config["_config_path"] = str(path)
    config["_project_root"] = str(project_root())
    return config


def resolve_path(config: dict[str, Any], path_value: str | Path) -> Path:
    """Resolve a path from config relative to the project root."""
    path = Path(path_value)
    if path.is_absolute():
        return path
    return Path(config["_project_root"]) / path


def ensure_directories(config: dict[str, Any]) -> None:
    """Create configured data and output directories if needed."""
    for key in ["raw_dir", "interim_dir", "processed_dir", "output_dir"]:
        resolve_path(config, config["paths"][key]).mkdir(parents=True, exist_ok=True)


def configure_logging(config: dict[str, Any]) -> None:
    """Configure console and file logging for the pipeline."""
    ensure_directories(config)
    log_file = resolve_path(config, config["paths"]["log_file"])

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, mode="a", encoding="utf-8"),
        ],
        force=True,
    )


def utc_now_iso() -> str:
    """Return a UTC timestamp for metadata files."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    """Make a filesystem-friendly lowercase label."""
    value = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    return value.strip("_").lower()


def save_json(data: dict[str, Any], path: Path) -> None:
    """Write JSON with stable indentation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read one JSON object per line."""
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(rows: Iterable[dict[str, Any]], path: Path) -> None:
    """Write one JSON object per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def unique_join(values: Iterable[Any], separator: str = "; ") -> str:
    """Join unique non-empty values in stable sorted order."""
    cleaned = {
        str(value).strip()
        for value in values
        if value is not None and str(value).strip() and str(value).strip() != "<NA>"
    }
    return separator.join(sorted(cleaned))


def first_non_empty(values: Iterable[Any]) -> Any:
    """Return the first non-empty value, or None."""
    for value in values:
        if value is not None and str(value).strip() and str(value).strip() != "<NA>":
            return value
    return None


def safe_int(value: Any) -> int | None:
    """Convert a value to int when possible."""
    if value is None:
        return None
    try:
        if math.isnan(value):
            return None
    except TypeError:
        pass
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def extract_year(value: Any) -> int | None:
    """Extract a four-digit year from an event date-like value."""
    if value is None:
        return None
    match = re.search(r"\b(17|18|19|20)\d{2}\b", str(value))
    if not match:
        return None
    return int(match.group(0))


def haversine_km(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """Calculate great-circle distance between two WGS84 points."""
    radius_km = 6371.0088
    lat1 = math.radians(latitude_1)
    lat2 = math.radians(latitude_2)
    delta_lat = math.radians(latitude_2 - latitude_1)
    delta_lon = math.radians(longitude_2 - longitude_1)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

