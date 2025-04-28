# D-C-MS Application Tests

This directory contains automated tests for the main Doctor-Client Management System (D-C-MS) FastAPI application located in the parent directory (`../main.py`).

## Requirements

*   Python 3.x
*   `pytest` and `pytest-asyncio`: Install using `pip install pytest pytest-asyncio`
*   Project dependencies: Ensure you have installed the dependencies from the main project's `requirements.txt` (e.g., `pip install -r ../requirements.txt`).

## Running the Tests

1.  Navigate to the **root project directory** (the parent of this `tests` directory) in your terminal.
2.  Activate your Python virtual environment (e.g., `.\env\Scripts\activate` on Windows or `source env/bin/activate` on Linux/macOS).
3.  Run the tests using the following command:

    ```bash
    pytest -v tests/test_main.py
    ```

    *   The `-v` flag provides verbose output, showing the status of each individual test function.

## Test Structure

*   All tests are currently located within `test_main.py`.
*   The tests utilize the `pytest` framework and FastAPI's `TestClient` for integration testing of the web application and API endpoints.
*   Coverage includes:
    *   API Key authentication dependency (`get_api_key`).
    *   Standard web routes (HTML responses) for CRUD operations on Programs, Clients, and Enrollments.
    *   API endpoints under the `/api/` path.
    *   Client search functionality.
    *   Edge cases like attempting to delete programs/clients with dependencies.

## Mocking

*   A `MockDatabase` class within `test_main.py` simulates the behavior of the actual `Database` class used by the main application. It provides an in-memory replacement for database interactions.
*   The `unittest.mock.patch` decorator, managed via a `pytest` fixture (`mock_db_main`), automatically replaces the application's `db` instance with this `MockDatabase` for the duration of each test function. This ensures tests run in isolation without affecting a real database.

## Important Notes

*   **Redirect Handling:** When testing POST, PUT, or DELETE endpoints that are expected to return a redirect (HTTP status code `303 See Other`), the `TestClient` calls include `follow_redirects=False`. This is crucial to verify that the endpoint correctly returns the redirect response itself, rather than the `TestClient` automatically following the redirect and returning the `200 OK` from the subsequent GET request.
*   **TemplateResponse Argument Order:** The main application (`main.py`) uses `TemplateResponse` to render HTML. Ensure that the `request` object is passed as the **first** argument to `TemplateResponse`, as required by current versions of Starlette/FastAPI (e.g., `TemplateResponse(request, "template.html", context)`). Incorrect argument order can lead to unexpected behavior or errors, especially during testing.

## Test Results

All 19 tests passed successfully as of the last run.

![Successful Test Run](https://github.com/CamreshJames/D-C-MS/blob/main/tests/passed%20test.png)