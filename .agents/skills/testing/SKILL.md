---
name: testing
description: Guidelines and standards for writing tests across the React/Vite frontend, FastAPI backend, and end-to-end (E2E) tests using Playwright.
---

# Testing Standards

This skill provides comprehensive guidelines for how to write tests in this project. Our stack consists of a React/Vite frontend, a FastAPI (Python) backend, and end-to-end (E2E) testing with Playwright. As an AI Agent, you should adhere strictly to these patterns.

## Backend Testing (FastAPI + Pytest)

### Structure & Location
- Place all backend tests inside the `backend/tests/` directory.
- Differentiate between unit tests (`backend/tests/unit/`) and integration tests (`backend/tests/integration/`).

### Integration Tests
- **Framework**: `pytest`, `pytest_asyncio`, and `httpx.AsyncClient`.
- **Database Isolation**: We use an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`) for integration tests to ensure isolation and speed.
- **Dependency Override**: Use FastAPI's `app.dependency_overrides` to swap out the production `get_db` generator with the testing session generator.
- **Fixtures**: 
  - Define an `autouse=True` async fixture (e.g., `setup_database`) that calls `Base.metadata.create_all` before the test and `drop_all` after the test.
  - Define an async `client` fixture using `AsyncClient(transport=ASGITransport(app=app), base_url="http://test")`.
- **Naming & Async**: Use `@pytest.mark.asyncio` on async test functions. Name them `test_<behavior>`.

### Unit Tests
- Fast, isolated tests focusing on a single module (e.g., `test_jwt.py` testing `create_token`).
- Do not require database setup or network layers. Mock external dependencies if necessary.

## Frontend Testing (React + Vitest)

### Structure & Location
- Place tests inside the `frontend/src/test/` directory. (e.g., previously they were side-by-side with components, but now we isolate them directly under `test/`).
- Mirror the source code structure (e.g., tests for `src/components/ui/Badge.tsx` go in `src/test/components/ui/Badge.test.tsx`).

### Tools & Patterns
- **Framework & Runner**: `vitest` for the test runner and assertions (`describe`, `it`, `expect`).
- **DOM Testing**: `@testing-library/react` for rendering components (`render`, `screen`).
- **Assertions**: We use `jest-dom` matchers like `.toBeInTheDocument()` and `.toHaveClass()`.
- **Variables & Variants**: When testing UI components with variants (e.g., success, warning, danger), write separate `it` blocks verifying that each variant applies the correct CSS classes.
- **Custom Classes**: Always verify that custom `className` properties passed as props are properly merged with default component classes.

## End-to-End Testing (Playwright)

### Structure & Location
- All E2E test files and configurations are located in the top-level `e2e/` directory.
- The actual test specifications are stored in `e2e/tests/`.
- Test files should follow the `*.spec.ts` naming convention (e.g., `login.spec.ts`).

### Tools & Frameworks
- **Runner & Framework**: `@playwright/test`.
- **Target Context**: Tests run against real, rendered UI elements and a live instance of the backend. You act as a real user navigating the browser.
- **Base URL**: The Playwright config automatically sets the `baseURL` to the frontend instance (`process.env.FRONTEND_URL` or `http://localhost:5173`).

### Writing Playwright Tests

1. **Setup & Teardown**:
   - Use `test.beforeEach` to set up browser context listeners, such as logging console messages or page errors:
     ```typescript
     test.beforeEach(({ page }) => {
         page.on('console', msg => console.log('BROWSER:', msg.text()));
         page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
     });
     ```
2. **Navigation & locators**:
   - Always navigate using relative paths: `await page.goto('/login');`.
   - Interact with elements using `page.locator(...)`, `page.getByRole(...)`, or specific CSS selectors (e.g., `input[type="email"]`, `.bg-red-50.text-red-500`).
3. **Graceful Assertions & Tolerances**:
   - In development/E2E environments, database state can vary (e.g., a test user might already exist). Use `try...catch` blocks to gracefully handle potential testing edge cases.
   - For example, when testing a successful signup flow, attempt to wait for URL redirection and verify the `localStorage` token. If it fails, alternatively check that a specific error message appeared to handle cases gracefully without failing the entire suite if the seed data is misconfigured.
4. **Local Storage**: 
   - After authentication tasks, validating successful payload delivery usually means checking the browser's local storage:
     ```typescript
     const token = await page.evaluate(() => localStorage.getItem('token'));
     expect(token).toBeTruthy();
     ```

## Executing Tests

Docker Compose is utilized to orchestrate the execution of tests across the stack:
- **`docker-compose.test.yml`**: Use this configuration to run your backend unit tests, backend integration tests, and frontend unit tests.
- **`docker-compose.e2e.yml`**: Use this configuration to execute the complete end-to-end (E2E) test suite. The `e2e` container will automatically wait for the frontend to be available before executing the `npx playwright test` command.

## General Agent AI Execution Rules

- **Progressive Disclosure**: Only read relevant files as needed. Do not guess class names or test names. Do not read every single spec to understand the app unless strictly necessary.
- **Conciseness**: Produce minimal boilerplate. Keep test files focused on the behavior being validated.
- **Idempotency**: Ensure tests can be run multiple times independently with zero shared state side-effects.
- **Single Purpose Validation**: Each test (`test(...)`) should validate a single user persona flow or behavior.
- **Robust Locators**: Avoid overly specific or brittle DOM paths. Prefer querying by role, placeholder, type, or visible text.
