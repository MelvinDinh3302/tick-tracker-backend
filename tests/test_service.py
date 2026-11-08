"""Tests for Elanco API fetching and record validation/cleaning."""

from copy import deepcopy

import pytest
import requests

import service


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_fetch_sightings_calls_correct_url_and_timeout(monkeypatch, sample_sightings):
    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return FakeResponse(sample_sightings)

    monkeypatch.setattr(service.requests, "get", fake_get)

    assert service.fetch_sightings() == sample_sightings
    assert calls == [(f"{service.BASE_URL}/tick-sightings", 15)]


def test_fetch_rejects_unexpected_json_structure(monkeypatch):
    monkeypatch.setattr(
        service.requests, "get", lambda *args, **kwargs: FakeResponse({"data": []})
    )
    with pytest.raises(ValueError, match="Expected a list"):
        service.fetch_sightings()


def test_fetch_propagates_timeout(monkeypatch):
    def timeout(*args, **kwargs):
        raise requests.Timeout("upstream timed out")

    monkeypatch.setattr(service.requests, "get", timeout)
    with pytest.raises(requests.Timeout):
        service.fetch_sightings()


def test_fetch_propagates_http_error_429(monkeypatch):
    class RateLimitedResponse(FakeResponse):
        def raise_for_status(self):
            raise requests.HTTPError("429 Too Many Requests")

    monkeypatch.setattr(
        service.requests, "get",
        lambda *args, **kwargs: RateLimitedResponse([]),
    )
    with pytest.raises(requests.HTTPError, match="429"):
        service.fetch_sightings()


def test_clean_valid_real_records(sample_sightings):
    cleaned, summary = service.clean_sightings(sample_sightings)
    assert cleaned == sample_sightings
    assert summary == {"received": 5, "valid": 5, "invalid": 0, "duplicates": 0}


def test_clean_strips_whitespace_and_removes_duplicate_ids(sample_sightings):
    first = deepcopy(sample_sightings[0])
    first["id"] = f"  {first['id']}  "
    first["location"] = "  Manchester  "

    cleaned, summary = service.clean_sightings([first, sample_sightings[0]])

    assert len(cleaned) == 1
    assert cleaned[0]["id"] == sample_sightings[0]["id"]
    assert cleaned[0]["location"] == "Manchester"
    assert summary == {"received": 2, "valid": 1, "invalid": 0, "duplicates": 1}


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("id", "   "),
        ("location", None),
        ("species", ""),
        ("latinName", 123),
        ("date", "not-a-date"),
        ("date", "2024-02-30T12:00:00"),
    ],
)
def test_clean_rejects_bad_fields(sample_sightings, field, bad_value):
    invalid = deepcopy(sample_sightings[0])
    invalid[field] = bad_value

    cleaned, summary = service.clean_sightings([invalid])

    assert cleaned == []
    assert summary["invalid"] == 1


def test_clean_rejects_missing_field(sample_sightings):
    invalid = deepcopy(sample_sightings[0])
    del invalid["latinName"]

    cleaned, summary = service.clean_sightings([invalid])
    assert cleaned == []
    assert summary["invalid"] == 1


def test_clean_rejects_non_dictionary_record():
    cleaned, summary = service.clean_sightings(["invalid entry", None])
    assert cleaned == []
    assert summary["invalid"] == 2


def test_clean_reports_mixed_valid_invalid_and_duplicates(sample_sightings):
    malformed = deepcopy(sample_sightings[1])
    malformed["date"] = "2024-99-99"

    cleaned, summary = service.clean_sightings(
        [sample_sightings[0], sample_sightings[0], malformed, sample_sightings[2]]
    )
    assert len(cleaned) == 2
    assert summary == {"received": 4, "valid": 2, "invalid": 1, "duplicates": 1}
