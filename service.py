
import requests
from datetime import datetime

BASE_URL = "https://dev-task.elancoapps.com/data"


def fetch_sightings():
    response = requests.get(
        f"{BASE_URL}/tick-sightings",
        timeout=15
    )

    response.raise_for_status()

    sightings = response.json()

    if not isinstance(sightings, list):
        raise ValueError("Expected a list of sightings")

    return sightings


def clean_sightings(sightings):
    cleaned = []
    seen_ids = set()

    invalid_count = 0
    duplicate_count = 0

    required_fields = (
        "id", "date", "location", "species", "latinName"
    )

    for sighting in sightings:
        # Check for missing fields
        if not isinstance(sighting, dict) or any(
            not isinstance(sighting.get(field), str)
            or not sighting[field].strip()
            for field in required_fields
        ):
            invalid_count += 1
            continue

        # Validate date
        try:
            datetime.fromisoformat(
                sighting["date"].strip().replace("Z", "+00:00")
            )
        except ValueError:
            invalid_count += 1
            continue

        # Check for duplicate IDs
        sighting_id = sighting["id"].strip()

        if sighting_id in seen_ids:
            duplicate_count += 1
            continue

        seen_ids.add(sighting_id)

        # Remove unnecessary whitespace
        cleaned.append({
            field: sighting[field].strip()
            for field in required_fields
        })

    summary = {
        "received": len(sightings),
        "valid": len(cleaned),
        "invalid": invalid_count,
        "duplicates": duplicate_count
    }

    return cleaned, summary



if __name__ == "__main__":
    try:
        sightings = fetch_sightings()

        cleaned, summary = clean_sightings(sightings)

        print("Cleaning summary:", summary)

        if cleaned:
            print("First cleaned sighting:", cleaned[0])

    except (requests.RequestException, ValueError) as error:
        print(f"Error: {error}")