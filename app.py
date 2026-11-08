
import requests
from datetime import date
from flask import Flask, jsonify, request

from service import fetch_sightings, clean_sightings
from database import (
    init_db,
    count_sightings,
    save_sightings,
    get_sightings,
    get_sightings_by_location,
    get_monthly_trends
)

app = Flask(__name__)


def initialize_data():
    init_db()

    if count_sightings() == 0:
        try:
            sightings = fetch_sightings()
            cleaned, summary = clean_sightings(sightings)
            inserted = save_sightings(cleaned)

            app.logger.info(
                "Imported %d sightings: %s",
                inserted, summary
            )

        except (requests.RequestException, ValueError) as error:
            app.logger.warning(
                "Could not load sightings: %s", error
            )


@app.route("/")
def home():
    return jsonify({
        "message": "Elanco Tick Tracker Backend"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route("/api/sightings")
def sightings():
    location = request.args.get("location")
    start = request.args.get("start")
    end = request.args.get("end")

    # Validate date parameters
    for value in (start, end):
        if value:
            try:
                if date.fromisoformat(value).isoformat() != value:
                    raise ValueError
            except ValueError:
                return jsonify({
                    "error": "Dates must use YYYY-MM-DD format"
                }), 400

    if start and end and start > end:
        return jsonify({
            "error": "Start date must not exceed end date"
        }), 400

    results = get_sightings(location, start, end)

    return jsonify(results)

@app.route("/api/stats/locations")
def stats_by_location():
    results = get_sightings_by_location()

    return jsonify({
        "group_by": "city",
        "data": results
    })


@app.route("/api/stats/trends")
def stats_trends():
    results = get_monthly_trends()

    return jsonify({
        "interval": "monthly",
        "data": results
    })



if __name__ == "__main__":
    initialize_data()
    app.run(debug=True, use_reloader=False)
