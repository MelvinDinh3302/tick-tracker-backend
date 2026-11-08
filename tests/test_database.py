"""Tests for SQLite initialization, insertion, filtering, and reporting."""

import database


def test_init_db_is_idempotent(empty_db):
    database.init_db()  # Calling a second time must not fail.
    assert database.count_sightings() == 0


def test_save_and_count_sightings(seeded_db):
    assert database.count_sightings() == 5


def test_insert_same_records_twice_does_not_duplicate(seeded_db, sample_sightings):
    assert database.save_sightings(sample_sightings) == 0
    assert database.count_sightings() == 5


def test_location_filter_is_case_insensitive(seeded_db):
    results = database.get_sightings(location="lOnDoN")
    assert len(results) == 3
    assert all(row["location"] == "London" for row in results)


def test_unknown_city_returns_empty_list(seeded_db):
    # Bath is absent from the provided Elanco dataset.
    assert database.get_sightings(location="Bath") == []


def test_date_range_includes_both_boundaries(seeded_db):
    results = database.get_sightings(start="2014-09-12", end="2014-09-12")
    assert len(results) == 2
    assert all(row["date"].startswith("2014-09-12") for row in results)


def test_combined_location_and_date_filters(seeded_db):
    results = database.get_sightings(
        location="london", start="2022-08-01", end="2022-08-31"
    )
    assert len(results) == 1
    assert results[0]["species"] == "Fox/badger tick"


def test_sightings_are_ordered_newest_first(seeded_db):
    dates = [row["date"] for row in database.get_sightings()]
    assert dates == sorted(dates, reverse=True)


def test_location_filter_uses_sql_parameters(seeded_db):
    # A malicious-looking value must be treated as data, not executable SQL.
    assert database.get_sightings(location="London' OR 1=1 --") == []
    assert database.count_sightings() == 5


def test_location_report_counts_correctly(seeded_db):
    counts = {
        row["location"]: row["count"]
        for row in database.get_sightings_by_location()
    }
    assert counts == {"London": 3, "Manchester": 1, "Glasgow": 1}
    assert sum(counts.values()) == database.count_sightings()


def test_monthly_report_counts_and_order(seeded_db):
    rows = database.get_monthly_trends()
    assert rows == [
        {"month": "2014-09", "count": 2},
        {"month": "2015-03", "count": 1},
        {"month": "2022-08", "count": 2},
    ]
    assert sum(row["count"] for row in rows) == database.count_sightings()
