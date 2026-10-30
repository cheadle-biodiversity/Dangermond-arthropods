from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from src.utils import load_jsonl, resolve_path, save_json, slugify, utc_now_iso, write_jsonl


LOGGER = logging.getLogger(__name__)


RAW_COLUMNS = [
    "gbifID",
    "gbifKey",
    "occurrenceID",
    "institutionCode",
    "collectionCode",
    "catalogNumber",
    "scientificName",
    "verbatimScientificName",
    "acceptedScientificName",
    "family",
    "genus",
    "species",
    "taxonRank",
    "basisOfRecord",
    "occurrenceStatus",
    "identifiedBy",
    "recordedBy",
    "eventDate",
    "year",
    "locality",
    "county",
    "stateProvince",
    "countryCode",
    "decimalLatitude",
    "decimalLongitude",
    "coordinateUncertaintyInMeters",
    "datasetName",
    "datasetKey",
    "publisher",
    "publishingOrgKey",
    "references",
    "license",
    "gbifIssueFlags",
    "lastInterpreted",
    "queryFamily",
    "queryTaxonKey",
]


def request_json(
    session: requests.Session,
    url: str,
    params: dict[str, Any],
    timeout: int,
    max_retries: int,
    retry_sleep_seconds: float,
) -> dict[str, Any]:
    """GET JSON from GBIF with a small retry loop."""
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            LOGGER.warning(
                "GBIF request failed on attempt %s/%s: %s",
                attempt,
                max_retries,
                exc,
            )
            if attempt < max_retries:
                time.sleep(retry_sleep_seconds)

    raise RuntimeError(f"GBIF request failed after {max_retries} attempts: {last_error}")


def resolve_taxon_key(
    family: str,
    session: requests.Session,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Resolve a family name to a GBIF backbone taxon key."""
    gbif_config = config["gbif"]
    url = f"{gbif_config['api_base_url'].rstrip('/')}/species/match"
    result = request_json(
        session=session,
        url=url,
        params={"name": family, "rank": "FAMILY"},
        timeout=gbif_config["request_timeout_seconds"],
        max_retries=gbif_config["max_retries"],
        retry_sleep_seconds=gbif_config["retry_sleep_seconds"],
    )

    usage_key = result.get("usageKey") or result.get("acceptedUsageKey")
    if not usage_key:
        raise ValueError(f"GBIF did not return a usage key for family: {family}")

    if result.get("matchType") == "NONE":
        raise ValueError(f"GBIF could not match family name: {family}")

    return {
        "family": family,
        "usageKey": usage_key,
        "scientificName": result.get("scientificName"),
        "canonicalName": result.get("canonicalName"),
        "rank": result.get("rank"),
        "status": result.get("status"),
        "confidence": result.get("confidence"),
        "matchType": result.get("matchType"),
    }


def query_family_occurrences(
    family: str,
    taxon_key: int,
    session: requests.Session,
    config: dict[str, Any],
    refresh: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Query California GBIF occurrences for one family, using a JSONL cache."""
    gbif_config = config["gbif"]
    raw_dir = resolve_path(config, config["paths"]["raw_dir"])
    cache_path = raw_dir / f"gbif_{slugify(family)}_raw.jsonl"

    if cache_path.exists() and not refresh:
        records = load_jsonl(cache_path)
        return records, {
            "family": family,
            "taxonKey": taxon_key,
            "records": len(records),
            "pages": None,
            "cacheUsed": True,
            "cachePath": str(cache_path),
        }

    url = f"{gbif_config['api_base_url'].rstrip('/')}/occurrence/search"
    limit = min(int(gbif_config.get("page_limit", 300)), 300)
    offset = 0
    records: list[dict[str, Any]] = []
    pages = 0
    count: int | None = None

    while True:
        params = {
            "taxonKey": taxon_key,
            "country": gbif_config["country"],
            "stateProvince": gbif_config["state_province"],
            "limit": limit,
            "offset": offset,
        }
        page = request_json(
            session=session,
            url=url,
            params=params,
            timeout=gbif_config["request_timeout_seconds"],
            max_retries=gbif_config["max_retries"],
            retry_sleep_seconds=gbif_config["retry_sleep_seconds"],
        )
        page_records = page.get("results", [])
        records.extend(page_records)
        pages += 1
        count = page.get("count", count)

        LOGGER.info(
            "%s: downloaded page %s (%s records; %s total so far)",
            family,
            pages,
            len(page_records),
            len(records),
        )

        if page.get("endOfRecords") or not page_records:
            break

        offset += limit
        if count is not None and offset >= count:
            break
        time.sleep(float(gbif_config.get("page_sleep_seconds", 0)))

    write_jsonl(records, cache_path)
    return records, {
        "family": family,
        "taxonKey": taxon_key,
        "records": len(records),
        "pages": pages,
        "cacheUsed": False,
        "cachePath": str(cache_path),
        "gbifCount": count,
    }


def flatten_occurrence(
    record: dict[str, Any],
    query_family: str,
    query_taxon_key: int,
) -> dict[str, Any]:
    """Flatten the GBIF JSON object to the workflow's raw CSV columns."""
    issues = record.get("issues")
    if isinstance(issues, list):
        issue_flags = ";".join(str(issue) for issue in issues)
    else:
        issue_flags = issues

    return {
        "gbifID": record.get("gbifID") or record.get("key"),
        "gbifKey": record.get("key"),
        "occurrenceID": record.get("occurrenceID"),
        "institutionCode": record.get("institutionCode"),
        "collectionCode": record.get("collectionCode"),
        "catalogNumber": record.get("catalogNumber"),
        "scientificName": record.get("scientificName"),
        "verbatimScientificName": record.get("verbatimScientificName"),
        "acceptedScientificName": record.get("acceptedScientificName"),
        "family": record.get("family"),
        "genus": record.get("genus"),
        "species": record.get("species"),
        "taxonRank": record.get("taxonRank"),
        "basisOfRecord": record.get("basisOfRecord"),
        "occurrenceStatus": record.get("occurrenceStatus"),
        "identifiedBy": record.get("identifiedBy"),
        "recordedBy": record.get("recordedBy"),
        "eventDate": record.get("eventDate"),
        "year": record.get("year"),
        "locality": record.get("locality"),
        "county": record.get("county"),
        "stateProvince": record.get("stateProvince"),
        "countryCode": record.get("countryCode"),
        "decimalLatitude": record.get("decimalLatitude"),
        "decimalLongitude": record.get("decimalLongitude"),
        "coordinateUncertaintyInMeters": record.get("coordinateUncertaintyInMeters"),
        "datasetName": record.get("datasetName"),
        "datasetKey": record.get("datasetKey"),
        "publisher": record.get("publisher"),
        "publishingOrgKey": record.get("publishingOrgKey"),
        "references": record.get("references"),
        "license": record.get("license"),
        "gbifIssueFlags": issue_flags,
        "lastInterpreted": record.get("lastInterpreted"),
        "queryFamily": query_family,
        "queryTaxonKey": query_taxon_key,
    }


def query_gbif(
    config: dict[str, Any],
    families: list[str],
    refresh: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Resolve configured families, query GBIF, and save raw outputs."""
    metadata: dict[str, Any] = {
        "createdAt": utc_now_iso(),
        "apiBaseUrl": config["gbif"]["api_base_url"],
        "country": config["gbif"]["country"],
        "stateProvince": config["gbif"]["state_province"],
        "families": {},
        "queryParameters": {
            "country": config["gbif"]["country"],
            "stateProvince": config["gbif"]["state_province"],
            "limit": min(int(config["gbif"].get("page_limit", 300)), 300),
        },
    }

    rows: list[dict[str, Any]] = []
    with requests.Session() as session:
        session.headers.update({"User-Agent": "central-coast-apoidea-gbif-workflow/0.1"})
        for family in families:
            LOGGER.info("Resolving GBIF taxon key for %s", family)
            resolution = resolve_taxon_key(family, session, config)
            taxon_key = int(resolution["usageKey"])
            LOGGER.info("%s resolved to GBIF taxon key %s", family, taxon_key)

            records, family_metadata = query_family_occurrences(
                family=family,
                taxon_key=taxon_key,
                session=session,
                config=config,
                refresh=refresh,
            )
            metadata["families"][family] = {
                "resolution": resolution,
                "query": family_metadata,
            }
            rows.extend(
                flatten_occurrence(record, family, taxon_key) for record in records
            )

    raw_df = pd.DataFrame(rows, columns=RAW_COLUMNS)
    raw_csv = resolve_path(config, config["paths"]["raw_occurrences_csv"])
    raw_csv.parent.mkdir(parents=True, exist_ok=True)
    raw_df.to_csv(raw_csv, index=False)
    LOGGER.info("Wrote raw occurrence CSV: %s", raw_csv)

    metadata["recordCount"] = int(len(raw_df))
    metadata_path = resolve_path(config, config["paths"]["query_metadata_json"])
    save_json(metadata, metadata_path)
    LOGGER.info("Wrote query metadata: %s", metadata_path)
    return raw_df, metadata


def load_raw_occurrences(config: dict[str, Any]) -> pd.DataFrame:
    """Load the cached combined raw CSV."""
    raw_csv = resolve_path(config, config["paths"]["raw_occurrences_csv"])
    if not raw_csv.exists():
        raise FileNotFoundError(
            f"Raw occurrence file not found: {raw_csv}. "
            "Run without --skip-query first, or place a GBIF CSV there."
        )
    return pd.read_csv(raw_csv, dtype=str)

