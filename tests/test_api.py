"""Tests for the Flask JSON endpoints and startup behavior."""

import pytest
import requests

import app as app_module
import database


def test_home_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.is_json
    assert response.json["message"] == "Elanco Tick Tracker Backend"


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "healthy"}


def test_get_all_sightings_as_json(client):
    response = client.get("/api/sightings")
    assert response.status_code == 200
    assert response.is_json
    assert len(response.json) == 5
    assert set(response.json[0]) == {"id", "date", "location", "species", "latinName"}


def test_search_by_city_case_insensitively(client):
    response = client.get("/api/sightings?location=london")
    assert response.status_code == 200
    assert len(response.json) == 3
    assert all(s["location"] == "London" for s in response.json)


def test_combined_city_and_date_search(client):
    response = client.get(
        "/api/sightings?location=London&start=2022-08-01&end=2022-08-31"
    )
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["date"] == "2022-08-19T01:26:28"


def test_search_for_unknown_city(client):
    response = client.get("/api/sightings?location=Bath")
    assert response.status_code == 200
    assert response.json == []


@pytest.mark.parametrize(
    "query",
    [
        "start=not-a-date",
        "start=2024-02-30",
        "end=2024-13-01",
        "start=2024-1-1",
    ],
)
def test_invalid_date_returns_400(client, query):
    response = client.get(f"/api/sightings?{query}")
    assert response.status_code == 400
    assert response.is_json
    assert "error" in response.json


def test_start_date_after_end_date_returns_400(client):
    response = client.get("/api/sightings?start=2024-12-01&end=2024-01-01")
    assert response.status_code == 400
    assert "error" in response.json


def test_locations_report(client):
    response = client.get("/api/stats/locations")
    assert response.status_code == 200
    assert response.json["group_by"] == "city"
    counts = {row["location"]: row["count"] for row in response.json["data"]}
    assert counts == {"London": 3, "Manchester": 1, "Glasgow": 1}


def test_monthly_trends_report(client):
    response = client.get("/api/stats/trends")
    assert response.status_code == 200
    assert response.json["interval"] == "monthly"
    assert response.json["data"] == [
        {"month": "2014-09", "count": 2},
        {"month": "2015-03", "count": 1},
        {"month": "2022-08", "count": 2},
    ]


def test_startup_reuses_existing_database(seeded_db, monkeypatch):
    def should_not_fetch():
        raise AssertionError("Startup should reuse cached sightings")

    monkeypatch.setattr(app_module, "fetch_sightings", should_not_fetch)
    app_module.initialize_data()
    assert database.count_sightings() == 5


def test_startup_handles_external_api_timeout(empty_db, monkeypatch):
    def timed_out():
        raise requests.Timeout("Elanco API unavailable")

    monkeypatch.setattr(app_module, "fetch_sightings", timed_out)
    app_module.initialize_data()  # Should not crash on an upstream timeout.
    assert database.count_sightings() == 0
