"""Resolve distinct interpreted names via GBIF v2 / Catalogue of Life XR.

Responses are cached locally; no occurrence rows or coordinates are uploaded.
The user has approved all named species-or-below service results.
Original match diagnostics and the initial strict-screen status are retained.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import csv
import gzip
import hashlib
import json
import time
import threading
import urllib.error
import urllib.parse

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/regional-candidate-pool/gbif-vgv5ee"
SOURCE = OUT / "species_identified_insect_records.csv.gz"
TARGET = OUT / "species_identified_insect_records_taxonomy_resolved.csv.gz"
CACHE = OUT / "taxonomy_api_cache.jsonl"
CHECKLIST = "7ddf754f-d193-4cc9-b351-99906754a03b"
ENDPOINT = "https://api.gbif.org/v2/species/match"
INPUT = ["scientificName", "taxonRank", "order", "family"]
ADDED = ["resolved_taxon_name", "resolved_taxon_key", "resolved_taxon_rank", "resolved_species_name", "resolved_species_key", "taxon_resolution_status", "taxon_resolution_match_type", "taxon_resolution_confidence", "taxon_resolution_service"]
LOCAL = threading.local()
CORRECTIONS = Path(__file__).with_name("reviewed_taxonomic_corrections.csv")
ADDED += ["taxon_resolution_automatic_status", "taxon_resolution_automatic_match_type", "taxon_resolution_automatic_confidence", "taxon_resolution_note"]
ADDED += ["taxon_resolution_matched_name", "taxon_resolution_matched_status", "taxon_resolution_accepted_name", "taxon_resolution_accepted_status", "taxon_resolution_service_candidate_name", "taxon_resolution_service_candidate_key", "taxon_resolution_service_candidate_rank", "taxon_resolution_diagnostics_json", "taxon_resolution_query_url", "taxon_resolution_retrieved_at", "taxon_resolution_checklist_key", "taxon_resolution_baseline_status"]

def query(row):
    params = dict(zip(INPUT, row))
    params.update(kingdom="Animalia", phylum="Arthropoda", **{"class": "Insecta"}, checklistKey=CHECKLIST)
    url = ENDPOINT + "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v})
    if not hasattr(LOCAL, "session"):
        LOCAL.session = requests.Session()
        LOCAL.session.headers.update({"User-Agent": "Dangermond-arthropods-taxonomy/1.0"})
    for attempt in range(5):
        try:
            response = LOCAL.session.get(url, timeout=45)
            response.raise_for_status()
            data = response.json()
            return {"input": row, "url": url, "retrieved_at": datetime.now(timezone.utc).isoformat(), "response": data}
        except requests.RequestException as error:
            if attempt == 4:
                return {"input": row, "url": url, "error": str(error)}
            delay = min(60, 2 ** (attempt + 1))
            if isinstance(error, requests.HTTPError) and error.response.status_code == 429:
                delay = max(delay, int(error.response.headers.get("Retry-After", "30")))
            time.sleep(delay)

def evaluate(item):
    data = item.get("response", {})
    diagnostic = data.get("diagnostics", {})
    usage = data.get("usage", {})
    accepted = data.get("acceptedUsage") or usage
    classification = data.get("classification", [])
    species = next((v for v in classification if v.get("rank") == "SPECIES"), {})
    if accepted.get("rank") == "SPECIES":
        species = accepted
    insect = any(v.get("rank") == "CLASS" and v.get("name") == "Insecta" for v in classification)
    match_type = diagnostic.get("matchType", "")
    confidence = diagnostic.get("confidence", 0)
    status = "resolved_synonym" if data.get("synonym") else "resolved_exact"
    if "error" in item:
        status = "service_error"
    elif not usage:
        status = "unmatched"
    elif not species or accepted.get("rank") not in {"SPECIES", "SUBSPECIES", "VARIETY", "FORM", "SUBVARIETY", "SUBFORM"}:
        status = "review_higher_taxon"
    elif not insect:
        status = "review_classification"
    elif match_type != "EXACT" or confidence < 95 or diagnostic.get("issues") or diagnostic.get("flags"):
        status = "review_match"
    elif usage.get("status") not in {"ACCEPTED", "SYNONYM"}:
        status = "review_taxonomic_status"
    baseline_status = status
    if "error" not in item and accepted.get("canonicalName") and accepted.get("rank") in {"SPECIES", "SUBSPECIES", "VARIETY", "FORM", "SUBVARIETY", "SUBFORM"}:
        if not status.startswith("resolved_"):
            status = "resolved_service_accepted"
        if not species:
            # The name can be accepted even when the service omits a species
            # ancestor. Infer the binomial text only; never invent a key.
            binomial = " ".join(accepted["canonicalName"].split()[:2])
            species = {"canonicalName": binomial}
    resolved = status.startswith("resolved_")
    values = [accepted.get("canonicalName", "") if resolved else "", accepted.get("key", "") if resolved else "", accepted.get("rank", "") if resolved else "", species.get("canonicalName", species.get("name", "")) if resolved else "", species.get("key", "") if resolved else "", status, match_type, confidence, "GBIF v2 species match / Catalogue of Life XR"]
    result = dict(zip(ADDED, values)) | {
        "candidate_taxon_name": accepted.get("canonicalName", ""),
        "candidate_taxon_key": accepted.get("key", ""),
        "matched_name": usage.get("name", ""),
        "matched_taxonomic_status": usage.get("status", ""),
        "diagnostics_json": json.dumps(diagnostic, sort_keys=True),
        "query_url": item["url"],
        "retrieved_at": item.get("retrieved_at", ""),
        "error": item.get("error", ""),
    }
    result.update({
        "taxon_resolution_matched_name": usage.get("name", ""),
        "taxon_resolution_matched_status": usage.get("status", ""),
        "taxon_resolution_accepted_name": accepted.get("name", ""),
        "taxon_resolution_accepted_status": accepted.get("status", ""),
        "taxon_resolution_service_candidate_name": accepted.get("canonicalName", ""),
        "taxon_resolution_service_candidate_key": accepted.get("key", ""),
        "taxon_resolution_service_candidate_rank": accepted.get("rank", ""),
        "taxon_resolution_diagnostics_json": json.dumps(diagnostic, sort_keys=True),
        "taxon_resolution_query_url": item["url"],
        "taxon_resolution_retrieved_at": item.get("retrieved_at", ""),
        "taxon_resolution_checklist_key": CHECKLIST,
        "taxon_resolution_baseline_status": baseline_status,
    })
    return result

def write_report(metadata):
    lines = [
        "# Taxonomic name-resolution results", "",
        f"Completed (UTC): {metadata['completed_at']}", "",
        "Service: [GBIF Species Match API v2](https://techdocs.gbif.org/en/openapi/v1/species), explicitly querying Catalogue of Life eXtended Release (COL XR), checklist `" + CHECKLIST + "`.", "",
        "Input: species-identified regional insect records from GBIF DOI [10.15468/dl.vgv5ee](https://doi.org/10.15468/dl.vgv5ee). The new table retains every occurrence and original field; original taxonomy and legacy GBIF keys are unchanged.", "",
        "| Resolution status | Distinct name/context combinations | Occurrence records |",
        "|---|---:|---:|",
    ]
    for status in sorted(metadata["name_combinations_by_status"]):
        lines.append(f"| {status} | {metadata['name_combinations_by_status'][status]:,} | {metadata['occurrence_records_by_status'].get(status, 0):,} |")
    lines += [
        "", f"Distinct resolved COL XR species keys: **{metadata['distinct_resolved_species_keys']:,}**. Reviewed names without a matching COL XR species identifier remain named but have blank resolved keys.", "",
        "`resolved_taxon_name` contains the accepted canonical scientific name without authorship. It preserves infraspecific detail where available. `resolved_species_name` and `resolved_species_key` provide the species-level roll-up; COL XR keys belong to a different identifier system from the original GBIF keys.", "",
        "Current policy: the user approved all named species-or-below service results on 27 October 2026, including variant/higher-rank species matches and provisional, ambiguous or misapplied statuses. Those service statuses and confidence values are preserved, not upgraded. A genus-only or higher match does not replace an identified species. The initial strict-screen outcome remains in taxon_resolution_baseline_status.", "",
        "User-reviewed decisions in `analysis/regional-candidate-pool/reviewed_taxonomic_corrections.csv` override automatic results and receive status `resolved_manual`. Original API status, match type and confidence are retained in the automatic audit columns. Manual decisions have no numeric service confidence; COL XR keys are supplied only when the returned canonical taxon name matches the reviewed name. Junonia grisea is retained; its historical association with J. coenia does not reassign other J. coenia records.", "",
        "Each distinct scientificName/rank/order/family combination is queried once, with Animalia/Arthropoda/Insecta context. Full API responses, request URLs and retrieval timestamps are cached locally. Query details and occurrence weights are in `taxonomy_name_resolution.csv`; provenance and the source checksum are in `taxonomy_resolution_metadata.json`.", "",
        "A flagged name indicates a taxonomic matching question, not necessarily a bad specimen identification. Name matching does not validate specimens, geographic plausibility or conservation status. BOLD eligibility remains pending. These are regional candidate occurrences and do not demonstrate occurrence on Dangermond Preserve.",
    ]
    (OUT / "taxonomy_resolution_report.md").write_text("\n".join(lines) + "\n")

def main():
    name_counts = Counter()
    for chunk in pd.read_csv(SOURCE, usecols=INPUT, dtype=str, keep_default_na=False, chunksize=100000):
        name_counts.update(chunk[INPUT].itertuples(index=False, name=None))
    cached = {}
    if CACHE.exists():
        for line in CACHE.read_text().splitlines():
            item = json.loads(line)
            if "response" in item:
                cached[tuple(item["input"])] = item
    pending = [key for key in name_counts if key not in cached]
    print(f"Distinct name/classification combinations: {len(name_counts):,}; uncached: {len(pending):,}", flush=True)
    with CACHE.open("a") as cache, ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(query, row): row for row in pending}
        for i, future in enumerate(as_completed(futures), 1):
            item = future.result()
            cache.write(json.dumps(item) + "\n")
            cache.flush()
            cached[tuple(item["input"])] = item
            if i % 500 == 0:
                print(f"Taxonomy queries completed: {i:,}/{len(pending):,}", flush=True)
    lookup = {key: evaluate(cached[key]) for key in name_counts}
    correction_rows = list(csv.DictReader(CORRECTIONS.open())) if CORRECTIONS.exists() else []
    corrections = {(row["input_scientific_name"], row["input_rank"]): row for row in correction_rows}
    manual_counts = Counter()
    for key, result in lookup.items():
        result["taxon_resolution_automatic_status"] = result["taxon_resolution_status"]
        result["taxon_resolution_automatic_match_type"] = result["taxon_resolution_match_type"]
        result["taxon_resolution_automatic_confidence"] = result["taxon_resolution_confidence"]
        result["taxon_resolution_note"] = ""
        correction = corrections.get((key[0], key[1]))
        if correction:
            name = correction["resolved_name"]
            # A genus match is never used as the identifier for a reviewed species.
            col_key = result["candidate_taxon_key"] if result["candidate_taxon_name"] == name else ""
            resolved_rank, species_name, species_key = "SPECIES", name, col_key
            if col_key:
                response = cached[key]["response"]
                accepted = response.get("acceptedUsage") or response.get("usage", {})
                resolved_rank = accepted["rank"]
                if resolved_rank != "SPECIES":
                    ancestor = next((v for v in response.get("classification", []) if v.get("rank") == "SPECIES"), {})
                    species_name = ancestor.get("canonicalName", ancestor.get("name", ""))
                    species_key = ancestor.get("key", "")
                    assert species_name and species_key, "Reviewed infraspecific name needs a species ancestor"
            result.update(resolved_taxon_name=name, resolved_species_name=species_name,
                          resolved_taxon_rank=resolved_rank, resolved_taxon_key=col_key,
                          resolved_species_key=species_key, taxon_resolution_status="resolved_manual",
                          taxon_resolution_match_type="MANUAL_REVIEW", taxon_resolution_confidence="",
                          taxon_resolution_service=correction["review_source"],
                          taxon_resolution_note=correction["review_note"] + " Review date: " + correction["review_date"])
            manual_counts[name] += name_counts[key]
    rows = [dict(zip(INPUT, key)) | value | {"occurrence_records": name_counts[key]} for key, value in lookup.items()]
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "taxonomy_name_resolution.csv", index=False)
    table.loc[~table.taxon_resolution_status.str.startswith("resolved_")].to_csv(OUT / "taxonomy_names_for_review.csv", index=False)
    counts = Counter()
    resolved_species = set()
    partial = TARGET.with_suffix(".gz.partial")
    first = True
    with gzip.open(partial, "wt", encoding="utf-8", newline="", compresslevel=3) as target:
        for chunk in pd.read_csv(SOURCE, dtype=str, keep_default_na=False, chunksize=25000):
            additions = [lookup[key] for key in chunk[INPUT].itertuples(index=False, name=None)]
            extra = pd.DataFrame(additions, index=chunk.index)[ADDED]
            counts.update(extra.taxon_resolution_status)
            resolved_species.update(extra.loc[extra.resolved_species_key.ne(""), "resolved_species_key"])
            pd.concat([chunk, extra], axis=1).to_csv(target, index=False, header=first)
            first = False
    assert sum(counts.values()) == sum(name_counts.values())
    assert sum(counts.values()) == json.loads((OUT / "species_subset_metadata.json").read_text())["counts"]["retained_records"]
    partial.replace(TARGET)
    with SOURCE.open("rb") as f:
        source_sha = hashlib.file_digest(f, "sha256").hexdigest()
    metadata = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "service": "GBIF Species Match API v2", "endpoint": ENDPOINT,
        "checklist": "Catalogue of Life eXtended Release", "checklist_key": CHECKLIST,
        "documentation": "https://techdocs.gbif.org/en/data-processing/taxonomy-interpretation",
        "source_doi": "10.15468/dl.vgv5ee", "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": source_sha, "output": str(TARGET.relative_to(ROOT)),
        "input_name_fields": INPUT, "request_context": {"kingdom": "Animalia", "phylum": "Arthropoda", "class": "Insecta"},
        "automatic_acceptance": "User approved all service-returned named species-or-finer candidates on 2026-10-27, regardless of match type, confidence, taxonomic status or missing classification. Preserve original diagnostics; no invented keys. Genus/higher matches remain unresolved. Exact user-reviewed corrections take precedence.",
        "approval_provenance": "User instruction: accept all of the corrections from the service and maintain the information provided via the matching service",
        "resolved_taxon_name_definition": "Accepted canonical name without authorship, preserving subspecies/variety rank when matched. resolved_species_name/key provide species-level roll-up. Original columns unchanged.",
        "query_combinations": len(name_counts), "name_combinations_by_status": dict(Counter(v["taxon_resolution_status"] for v in lookup.values())),
        "manual_correction_file": str(CORRECTIONS.relative_to(ROOT)),
        "manual_correction_sha256": hashlib.sha256(CORRECTIONS.read_bytes()).hexdigest() if CORRECTIONS.exists() else None,
        "manually_reviewed_occurrences_by_name": dict(manual_counts),
        "manual_key_policy": "No COL XR key invented for user-reviewed names. A key is retained only if the API candidate canonical taxon name matches the reviewed name; otherwise resolved keys stay blank.",
        "occurrence_records_by_status": dict(counts), "distinct_resolved_species_keys": len(resolved_species),
        "limitations": "Automated nomenclatural matching does not validate specimen identifications, geographic plausibility or conservation status. Input scientificName is the GBIF-interpreted name, not a re-identification of verbatim names. No rows dropped; BOLD eligibility still pending. Full responses and timestamps are cached locally because the live checklist can change.",
    }
    (OUT / "taxonomy_resolution_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    write_report(metadata)
    print(json.dumps(metadata, indent=2), flush=True)

if __name__ == "__main__":
    main()
