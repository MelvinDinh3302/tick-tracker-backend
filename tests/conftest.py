"""Shared test data and isolated SQLite fixtures for the Tick Tracker backend."""

import pytest

import database


@pytest.fixture
def sample_sightings():
    """Five genuine records selected from Elanco's supplied dataset."""
    return [
        {
            "id": "02WNholuSg6ndCk4c1dA",
            "date": "2022-08-01T06:40:31",
            "location": "Manchester",
            "species": "Marsh tick",
            "latinName": "Ixodes apronophorus",
        },
        {
            "id": "Jw6921YckWOYdE7UfGcL",
            "date": "2022-08-19T01:26:28",
            "location": "London",
            "species": "Fox/badger tick",
            "latinName": "Ixodes canisuga",
        },
        {
            "id": "02rFwLCaAwZSVxdTDicK",
            "date": "2014-09-12T23:33:03",
            "location": "London",
            "species": "Southern rodent tick",
            "latinName": "Ixodes acuminatus",
        },
        {
            "id": "MJs0uyrOMj0kcOftlmrO",
            "date": "2014-09-12T22:20:02",
            "location": "London",
            "species": "Fox/badger tick",
            "latinName": "Ixodes canisuga",
        },
        {
            "id": "05349NmKTyfUhYKZNNH0",
            "date": "2015-03-17T09:10:25",
            "location": "Glasgow",
            "species": "Passerine tick",
            "latinName": "Dermacentor frontalis",
        },
    ]


@pytest.fixture
def empty_db(tmp_path, monkeypatch):
    """Create an isolated, empty SQLite database for each test."""
    path = tmp_path / "test-sightings.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    database.init_db()
    return path


@pytest.fixture
def seeded_db(empty_db, sample_sightings):
    """Insert known sample records for predictable query expectations."""
    assert database.save_sightings(sample_sightings) == len(sample_sightings)
    return empty_db


@pytest.fixture
def client(seeded_db):
    """Use Flask's test client; no actual web server is started."""
    from app import app

    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client
