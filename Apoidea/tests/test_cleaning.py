from __future__ import annotations

import unittest

import pandas as pd

from src.clean_occurrences import clean_occurrences, normalize_county


CONFIG = {
    "families": ["Bembicidae", "Sphecidae"],
    "bee_families": ["Apidae"],
    "counties": ["Santa Barbara", "Ventura"],
    "county_aliases": {
        "santa barbara": "Santa Barbara",
        "santa barbara county": "Santa Barbara",
        "ventura": "Ventura",
        "ventura county": "Ventura",
    },
    "quality": {"coordinate_uncertainty_threshold_m": 10000},
}


class CleaningTests(unittest.TestCase):
    def test_county_aliases(self) -> None:
        self.assertEqual(
            normalize_county("Santa Barbara County", CONFIG["county_aliases"]),
            "Santa Barbara",
        )

    def test_cleaning_splits_excluded_records(self) -> None:
        raw = pd.DataFrame(
            [
                {
                    "gbifID": "1",
                    "occurrenceID": "occ-1",
                    "institutionCode": "UCSB",
                    "collectionCode": "ENT",
                    "catalogNumber": "A1",
                    "scientificName": "Bembix americana",
                    "verbatimScientificName": "Bembix americana",
                    "acceptedScientificName": "Bembix americana",
                    "family": "Bembicidae",
                    "queryFamily": "Bembicidae",
                    "genus": "Bembix",
                    "species": "Bembix americana",
                    "taxonRank": "SPECIES",
                    "basisOfRecord": "PRESERVED_SPECIMEN",
                    "occurrenceStatus": "PRESENT",
                    "eventDate": "1920-06-01",
                    "year": "1920",
                    "county": "Santa Barbara County",
                    "stateProvince": "California",
                    "countryCode": "US",
                    "decimalLatitude": "34.5",
                    "decimalLongitude": "-120.3",
                    "coordinateUncertaintyInMeters": "100",
                    "datasetName": "Example",
                },
                {
                    "gbifID": "1",
                    "family": "Bembicidae",
                    "queryFamily": "Bembicidae",
                    "county": "Santa Barbara County",
                    "stateProvince": "California",
                    "countryCode": "US",
                    "occurrenceStatus": "PRESENT",
                },
                {
                    "gbifID": "2",
                    "family": "Apidae",
                    "queryFamily": "Apidae",
                    "county": "Santa Barbara County",
                    "stateProvince": "California",
                    "countryCode": "US",
                    "occurrenceStatus": "PRESENT",
                },
                {
                    "gbifID": "3",
                    "family": "Bembicidae",
                    "queryFamily": "Bembicidae",
                    "county": "Los Angeles County",
                    "stateProvince": "California",
                    "countryCode": "US",
                    "occurrenceStatus": "PRESENT",
                },
            ]
        )

        cleaned, excluded, stats = clean_occurrences(raw, CONFIG)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(len(excluded), 3)
        self.assertEqual(stats["duplicateGbifIDs"], 1)
        self.assertEqual(cleaned.iloc[0]["countyClean"], "Santa Barbara")
        self.assertEqual(cleaned.iloc[0]["workingScientificName"], "Bembix americana")


if __name__ == "__main__":
    unittest.main()

