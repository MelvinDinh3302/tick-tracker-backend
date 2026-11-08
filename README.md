# Tick Tracker Backend

A Flask-based REST API for retrieving, cleaning, storing, searching, and reporting UK tick-sighting data from the [Elanco external API](https://dev-task.elancoapps.com/data).

**Elanco Software Engineering Technical Assessment — Backend**  
**Author:** Thang (Melvin) Dinh

## Features

- Fetch sightings from Elanco's read-only external API.
- Validate required fields and timestamps; discard incomplete or malformed records.
- Remove duplicate sightings by ID and persist valid records in SQLite.
- Filter sightings by city and inclusive date range.
- Report sightings per city and monthly sighting counts.
- Handle upstream HTTP errors, timeouts, and unexpected response structures.
- Test data handling, database operations, and Flask endpoints using pytest.

## Video walkthrough

**[Watch the project walkthrough](VIDEO_URL)**

The walkthrough demonstrates the application setup, backend architecture, search and reporting endpoints, error handling, and automated tests.

## Technology stack

- **Python** — Backend implementation
- **Flask** — HTTP and JSON endpoints
- **Requests** — External API client
- **SQLite (`sqlite3`)** — Local relational data storage
- **pytest** — Automated testing

## Architecture

```text
Elanco external API
         |
         v
service.py  (fetch, validate, clean, deduplicate)
         |
         v
database.py (SQLite persistence, filtering, aggregates)
         |
         v
app.py      (Flask REST endpoints)
         |
         v
JSON responses
```

- `service.py` retrieves remote records and cleans the supplied fields.
- `database.py` creates the database, inserts records, and executes parameterized SQL queries.
- `app.py` initializes data and exposes the HTTP API.
- `tests/` contains service, database, and API tests with isolated temporary SQLite databases.

On startup, the application creates the SQLite database if necessary. **If the database is empty**, it fetches sightings from Elanco and stores the cleaned results. If the database already contains records, the cached data is reused. This avoids contacting the external service on every user request.

## Getting started

### Requirements

- Python 3
- Internet access for the initial data import

### Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/MelvinDinh3302/tick-tracker-backend.git
cd tick-tracker-backend
```

Create and activate a virtual environment.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

### Run the server

```bash
python app.py
```

The local API will be available at **http://127.0.0.1:5000**.

**Important:** Use `python app.py` rather than `flask --app app run`, since the current application's data initialization is invoked in the script entry point.

The development server runs with Flask debug mode enabled. It is intended for local assessment and demonstration, not production deployment.

## API endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Application welcome message |
| GET | `/health` | Basic Flask service health response |
| GET | `/api/sightings` | Return stored sightings, newest first |
| GET | `/api/stats/locations` | Count sightings grouped by city |
| GET | `/api/stats/trends` | Count sightings grouped by month |

### Search and filtering

`GET /api/sightings` accepts optional query parameters:

| Parameter | Example | Behaviour |
| --- | --- | --- |
| `location` | `London` | Exact city match, case-insensitive |
| `start` | `2022-01-01` | Include records on or after this date |
| `end` | `2022-12-31` | Include records on or before this date |

Examples:

```text
GET /api/sightings
GET /api/sightings?location=London
GET /api/sightings?start=2022-01-01&end=2022-12-31
GET /api/sightings?location=London&start=2022-01-01&end=2022-12-31
```

The results are returned as JSON arrays. Malformed dates and reversed date ranges return HTTP **400** with a JSON error message.

### Location report

```text
GET /api/stats/locations
```

Returns an object with `group_by: "city"` and a `data` array containing each location and its count, ordered by count descending.

### Monthly trend report

```text
GET /api/stats/trends
```

Returns an object with `interval: "monthly"` and a `data` array containing `YYYY-MM` month labels and counts, ordered chronologically.

## Data quality and reliability

- **Missing or empty data:** Records must contain nonempty string values for `id`, `date`, `location`, `species`, and `latinName`.
- **Invalid dates:** Dates must be parseable as ISO-format timestamps.
- **Duplicates:** Repeated IDs are removed during cleaning; the SQLite primary key and `INSERT OR IGNORE` prevent duplicate inserts across imports.
- **External API failures:** Fetch operations use a 15-second timeout and raise HTTP errors. During startup, request or data-format failures are logged without crashing Flask.
- **SQL safety:** Filtering uses parameterized SQL rather than interpolating user input into queries.

## Testing

The automated tests use Flask's test client, mocked external API responses, and temporary SQLite databases, so they do not modify the application's actual `sightings.db` file or require the live API.

Run all tests from the project root:

```bash
python -m pytest -v
```

Or run a particular suite:

```bash
python -m pytest tests/test_service.py -v
python -m pytest tests/test_database.py -v
python -m pytest tests/test_api.py -v
```

## Design decisions and limitations

- **SQLite:** A lightweight database is sufficient for a local MVP and requires no separate database server.
- **Cached imports:** Existing records are reused across restarts. The current application does not periodically refresh data from the upstream API.
- **City-level reporting:** Elanco supplies a city-style `location` field, not a formal geographic region identifier. Reports therefore aggregate by city rather than attempting unsupported region mapping.
- **Monthly trends:** The implemented trend endpoint groups sightings by month; weekly grouping is a possible extension.
- **Date assumptions:** Search and reporting SQL assume consistently formatted timestamps beginning with `YYYY-MM-DD`, as in the supplied dataset.
- **Scale:** The sightings endpoint currently returns all matching records. Pagination and incremental synchronization would improve support for much larger datasets.
- **Health checks:** `/health` reports application availability; it does not independently verify upstream API or database readiness.
- **Future extensions:** Data refresh controls, pagination, regional mapping, additional trend intervals, and optional analytical/ML insights.
