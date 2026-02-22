# E2E Selenium Auth Tests

This folder contains Python Selenium tests that hit the frontend auth harness page:
- Frontend page: `/e2e/auth`
- Test file: `tests/test_auth_selenium.py`

## Environment
Use `.env.example` as the template.

Required variables:
- `FRONTEND_BASE_URL` - frontend endpoint to test
- `SELENIUM_REMOTE_URL` - Selenium remote WebDriver endpoint

## Run with Docker Compose
From repository root:

```bash
docker compose -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from e2e-tests
```

This starts:
1. `db`
2. `backend` (waits for healthy db)
3. `frontend` (waits for healthy backend)
4. `selenium`
5. `e2e-tests` (waits and then runs pytest)
