# EchoLink — Testing Guide
*How to run and write unit and integration tests for the EchoLink API*

This project includes a testing suite built with **pytest** and **FastAPI's TestClient** to ensure the recommendation engine and API endpoints function correctly and handle edge cases gracefully.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Test Suite Architecture](#test-suite-architecture)
3. [Running the Tests](#running-the-tests)
4. [Writing New Tests](#writing-new-tests)
5. [Latest Test Results](#latest-test-results)

---

## Prerequisites

Ensure you have python dependencies installed:
```bash
pip install pytest requests httpx psycopg2-binary
```

---

## Test Suite Architecture

The test suite is structured as follows:

```
echolink_api/
└── tests/
    ├── __init__.py
    ├── conftest.py          # Shared fixtures (FastAPI TestClient, DB configs)
    ├── test_unit.py         # Unit tests (with mocked database calls)
    └── test_integration.py  # Integration tests (connecting to the real database)
```

### 1. Unit Tests (`test_unit.py`)
These tests do **not** connect to the database. Instead, they mock the `database.query` and `database.query_one` functions in `echolink_api/main.py`. This ensures:
* Tests run in less than **0.1 seconds**.
* They do not depend on the state of the database or database server availability.
* They verify response schemas, error handling (400, 404), route resolution, and internal calculations (e.g. speedup factor).

### 2. Integration Tests (`test_integration.py`)
These tests make real queries to the local PostgreSQL database server running on `localhost:5432`. They verify:
* Database connection parameters work.
* Actual SQL queries execution against the database schemas.
* Autocomplete results exist for common queries.
* Recommendation functions (sorting, Jaccard calculations, same-artist exclusions) return valid outputs from the database.

---

## Running the Tests

To run the tests, execute `pytest` from the **project root directory** (`/Users/shreyaroshan/Desktop/EchoLink`):

### Run All Tests
```bash
pytest echolink_api/tests/ -v
```

### Run Unit Tests Only
```bash
pytest echolink_api/tests/test_unit.py -v
```

### Run Integration Tests Only
```bash
pytest echolink_api/tests/test_integration.py -v
```

---

## Test Cases Covered

### Unit Tests
* **`test_health_check_unit`**: Mocks a database count and checks that `/` returns `{"status": "ok"}`.
* **`test_stats_unit`**: Mocks stats payload and checks `/stats` response keys.
* **`test_search_unit`**: Mocks search query results and verifies paging/limits.
* **`test_recommend_unit_success`**: Checks track suggestions with mocked rules.
* **`test_recommend_unit_same_artist`**: Verifies that the same-artist exclusion filter works correctly in the API layer.
* **`test_recommend_unit_not_found`**: Verifies `404` error when a track is not in the database.
* **`test_recommend_unit_invalid_sort`**: Verifies `400` error when sorting by a metric that does not exist.
* **`test_benchmark_unit`**: Verifies speedup factor mathematical limits and guards against empty ruleset tables.

### Integration Tests
* **`test_db_connection`**: Confirms connection to the PostgreSQL database.
* **`test_search_integration`**: Runs a real query for "Daft" or "Coldplay" and ensures results come back.
* **`test_recommend_integration`**: Fetches recommendations for "Coldplay - Yellow" from the real database and checks they are sorted by Jaccard score.
* **`test_benchmark_integration`**: Runs queries against the benchmark tables to verify live data consistency.

---

## Latest Test Results

Below is the execution log of the full test suite run on the local development environment:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.1, pytest-9.0.2, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: /Users/shreyaroshan/Desktop/EchoLink
collected 15 items

echolink_api/tests/test_integration.py::test_db_connection PASSED        [  6%]
echolink_api/tests/test_integration.py::test_health_check_integration PASSED [ 13%]
echolink_api/tests/test_integration.py::test_stats_integration PASSED    [ 20%]
echolink_api/tests/test_integration.py::test_search_integration PASSED   [ 26%]
echolink_api/tests/test_recommend_integration PASSED [ 33%]
echolink_api/tests/test_benchmark_integration PASSED [ 40%]
echolink_api/tests/test_unit.py::test_health_check_unit PASSED           [ 46%]
echolink_api/tests/test_unit.py::test_stats_unit PASSED                  [ 53%]
echolink_api/tests/test_unit.py::test_search_unit PASSED                 [ 60%]
echolink_api/tests/test_recommend_unit_success PASSED      [ 66%]
echolink_api/tests/test_recommend_unit_include_same_artist PASSED [ 73%]
echolink_api/tests/test_unit.py::test_recommend_unit_not_found PASSED    [ 80%]
echolink_api/tests/test_unit.py::test_recommend_unit_invalid_sort PASSED [ 86%]
echolink_api/tests/test_unit.py::test_benchmark_unit PASSED              [ 93%]
echolink_api/tests/test_unit.py::test_benchmark_unit_empty_db PASSED     [100%]

======================== 15 passed in 0.30s =========================
```
