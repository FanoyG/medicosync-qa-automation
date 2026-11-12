<p align="center">
  <img src="img/icon.png" alt="Medicosync Logo" width="100"><br>
  <b><span style="font-size: 28px;">MedicoSync QA Automation</span></b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
    
  <img src="https://img.shields.io/badge/PyTest-0A9EDC?style=flat&logo=pytest&logoColor=white" alt="PyTest">
    
  <img src="https://img.shields.io/badge/Playwright-2EAD33?style=flat&logo=playwright&logoColor=white" alt="Playwright">
    
  <img src="https://img.shields.io/badge/Git-F05032?style=flat&logo=git&logoColor=white" alt="Git">
    
  <a href="https://github.com/FanoyG/medicosync-qa-automation/actions/workflows/ci.yml">
    <img src="https://github.com/FanoyG/medicosync-qa-automation/actions/workflows/ci.yml/badge.svg" alt="CI Status">
  </a>
</p>
Automated tests for the login and sign-up part of **MedicoSync**, a medical practice app for doctors.

- **Live app:** <https://medicosync-frontend.netlify.app/>
- **Full app source code:** <https://github.com/FanoyG/medicosync/>

This repo holds a smaller, cleaner version of MedicoSync's login and sign-up part (a FastAPI backend plus a simple web page) and all the tests for it. The tests run against this copy, with their own throwaway database, so the live app and its data are never touched.

## What is tested

| Level | What | Tools |
|---|---|---|
| Unit | request schemas, user model | pytest |
| Integration | login and sign-up logic with a real database and Redis | pytest, Testcontainers |
| API | register, login, lockout after failed attempts, health check | httpx |
| UI | login page, dashboard, logout | Playwright |

**170+ test cases** in total. Each feature has happy, sad and edge cases.

## How it works

**API tests**
- Tests read like plain English: `auth_service.register(...)`.
- Design: Test -> Service -> RequestBuilder -> async client. The service knows the endpoints, and the builder builds and sends the request.
- No network: the client hands requests straight to the FastAPI app, so tests are fast.
- Postgres and Redis start in Docker for each test run. The app is pointed at them with FastAPI `dependency_overrides`.
- Every test creates its own data (for example a random email), so tests do not depend on each other.

**UI tests**
- Page Object Model: `BasePage`, `LoginPage`, `DashboardPage`. Pages hold locators and actions. Tests hold the assertions.
- Hybrid login: the test logs in through the API, puts the token into the browser's local storage, and opens the dashboard directly. No typing into the login form, so tests are faster and more stable.
- Runs headless in CI. Screenshots and traces are saved when a test fails.

## CI pipeline (GitHub Actions)

Runs on every pull request and on pushes to `main`.

1. **Smoke tests:** a small set of must-pass tests (`pytest -m smoke`).
2. **Full suite:** unit, integration and API tests. Runs after smoke passes.
3. **UI tests:** starts Postgres, Redis and the app, then runs Playwright in headless Chromium. Runs after smoke passes.

Secrets are stored in GitHub Secrets. The workflow file only contains fake placeholder values.

![Green pipeline](docs/ci-green.png)

## What the tests found

- The password error message did not mention the 12 to 18 length or the allowed symbols, so a valid-looking password was rejected with a confusing message. Fixed with one clear message per rule.
- A hardcoded fallback for the JWT secret key was removed. The key must now come from the environment.
- Unit tests that shared one fixed email broke each other when run together. Fixed with unique data per test.

## Run it

Needs Python 3.14 and Docker.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file with these settings (see `.github/workflows/ci.yml` for example values): `DB_CONNECTION`, `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `JWT_SECRET_KEY` (at least 32 characters), `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`.

```bash
pytest -m smoke               # quick check
pytest --ignore=tests/ui      # unit, integration and API tests
```

UI tests (needs the Postgres and Redis from your `.env`):

```bash
python -m playwright install chromium
uvicorn main:app --port 8000      # terminal 1
pytest tests/ui --headed          # terminal 2
```

## Project layout

```
app/              app code (routes, services, schemas, models)
main.py           FastAPI app, also serves the web pages
tests/
  clients/        RequestBuilder and services for API tests
  pages/          page objects for UI tests
  api/            API tests
  integration/    integration tests
  unit/           unit tests (schemas, models)
  ui/             Playwright tests
.github/workflows/ci.yml
```

## Next

- More browsers and devices, parallel runs
- Clean the test database after each test. Today every test creates its own data with `uuid4` (for example a random email), so tests never collide. The catch: the rows stay in Postgres until the run ends, so the database keeps growing, and a test that counts or lists users could see rows from other tests. Redis is already cleared after each test. The plan is to do the same for Postgres, by rolling back or cleaning the tables after each test.