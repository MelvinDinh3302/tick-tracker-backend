# Tick Tracker Backend

A Flask-based REST API for retrieving, cleaning, storing, searching, and reporting UK tick-sighting data from the [Elanco external API](https://dev-task.elancoapps.com/). Includes an optional machine-learning endpoint for exploring unusual monthly reporting counts.

**Elanco Software Engineering Technical Assessment - Backend**  
**Author:** Vu Trong Thang Dinh (Melvin Dinh)

## Features

- Fetch sightings from Elanco's read-only external API.
- Validate required fields and timestamps. Discard incomplete or malformed records.
- Remove duplicate sightings by ID and persist valid records in SQLite.
- Filter sightings by city and inclusive date range.
- Report sightings per city and monthly sighting counts.
- **Optional ML insights:** Use Isolation Forest to flag months with unusually high or low sighting counts.
- Handle upstream HTTP errors, timeouts, and unexpected response structures.
- Test data handling, database operations, and Flask endpoints using pytest.

## Video walkthrough

**[Watch the project walkthrough](https://youtu.be/E3YM4ea1Okg)**

The walkthrough demonstrates the application setup, backend architecture, data cleaning and storage, search and reporting endpoints, optional anomaly detection, and automated tests.

## Technology stack

- **Python** - Backend implementation
- **Flask** - HTTP and JSON endpoints
- **Requests** - External API client
- **SQLite (`sqlite3`)** - Local relational data storage
- **scikit-learn** - Isolation Forest anomaly detection
- **pytest** - Automated testing

## Architecture

```text
Elanco external API
         |
         v
service.py (fetch, validate, clean, deduplicate)
         |
         v
database.py (SQLite persistence, filtering, aggregates)
         |                              |
         |                              v
         |                       insights.py
         |                   (Isolation Forest on
         |                    monthly aggregates)
         |                              |
         +--------------+---------------+
                        |
                        v
                 app.py (Flask API)
                        |
                        v
                  JSON responses
```

- `service.py` retrieves remote records and cleans the supplied fields.
- `database.py` creates the database, inserts records, and executes parameterized SQL queries.
- `insights.py` uses monthly counts returned by `database.py` to fit an Isolation Forest and identify outlier months.
- `app.py` initializes data and exposes the HTTP API, including the optional insights endpoint.
- `tests/` contains service, database, and API tests with isolated temporary SQLite databases.

On startup, the application creates the SQLite database if necessary. **If the database is empty**, it fetches sightings from Elanco and stores the cleaned results. If the database already contains records, the cached data is reused. This avoids contacting the external service on every user request.

## Getting started

### Requirements

- Python 3 (with support for the versions pinned in `requirements.txt`)
- Internet access for the initial import from Elanco's API

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

Install dependencies, including scikit-learn:

```bash
python -m pip install -r requirements.txt
```

### Run the server

```bash
python app.py
```

The local API will be available at **http://127.0.0.1:5000**.

**Important:** Use `python app.py` rather than `flask --app app run`, since the current application's data initialization is invoked in the script entry point. The server runs with Flask's development debugger and is intended for local demonstration, not production deployment.

## API endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Application welcome message |
| GET | `/health` | Basic Flask service health response |
| GET | `/api/sightings` | Return stored sightings, newest first |
| GET | `/api/stats/locations` | Count sightings grouped by city |
| GET | `/api/stats/trends` | Count sightings grouped by month |
| GET | `/api/insights/anomalies` | Flag unusual monthly sighting counts using Isolation Forest |

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

### ML insights: monthly anomaly detection

```text
GET /api/insights/anomalies
```

This optional endpoint fits an **Isolation Forest** to the monthly sighting counts already aggregated from the local SQLite database. It identifies months whose *counts* are unusually high or low relative to the overall distribution.

Example response structure (illustrative values):

```json
{
  "method": "Isolation Forest",
  "total_months": 156,
  "anomalies": [
    {
      "month": "2017-06",
      "count": 16,
      "anomaly_score": -0.1718
    }
  ]
}
```

**Implementation details:**

- **Input features:** One numeric feature per observed month - the number of sightings that month.
- **Model:** `IsolationForest(contamination=0.05, random_state=42)` from scikit-learn.
- **Training:** The model is fitted on the aggregated monthly counts when the endpoint is called. No separate training script or saved model file is required.
- **Output:** Only months labelled anomalous by the model are returned. A **negative** `anomaly_score` denotes an outlier under the model's threshold. More negative values are considered more unusual. The score is **not** a probability.
- **Insufficient data:** When fewer than 12 distinct months are available, the endpoint returns an empty anomaly list and an explanatory message instead of fitting the model.

This is an **exploratory reporting feature**, not an outbreak predictor or public-health risk assessment. The model does not account for seasonality, reporting effort, weather, or geographical differences. A month flagged as unusual may reflect reporting variation rather than biological changes in tick populations.

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

The current test suite covers service, database, and existing HTTP API behavior. **Automated tests specifically for the new anomaly-detection endpoint have not yet been added.**

## Design decisions and limitations

- **SQLite:** A lightweight database is sufficient for a local MVP and requires no separate database server.
- **Cached imports:** Existing records are reused across restarts. The current application does not periodically refresh data from the upstream API.
- **City-level reporting:** Elanco supplies a city-style `location` field, not a formal geographic region identifier. Reports therefore aggregate by city rather than attempting unsupported region mapping.
- **Monthly trends:** The implemented trend endpoint groups sightings by month. Weekly grouping is a possible extension.
- **Date assumptions:** Search and reporting SQL assume consistently formatted timestamps beginning with `YYYY-MM-DD`, as in the supplied dataset.
- **Anomaly-detection scope:** Isolation Forest uses only monthly counts and an assumed contamination rate of 5%. Its output highlights unusual observations for further review, not confirmed errors, outbreaks, or causal effects. It also does not adjust for missing calendar months or seasonality.
- **Scale:** The sightings endpoint currently returns all matching records. Pagination and incremental synchronization would improve support for much larger datasets.
- **Health checks:** `/health` reports application availability. It does not independently verify upstream API or database readiness.
- **Future extensions:** Data refresh controls, pagination, regional mapping, weekly trends, and more contextualized analysis if richer surveillance data becomes available.
