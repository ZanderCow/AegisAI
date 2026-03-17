---
name: end-to-end
description: Guidelines and standards for writing end-to-end (E2E) tests using Playwright and Docker Compose.
---

# End-to-End Testing Standards

This skill provides comprehensive guidelines for how to write and execute end-to-end (E2E) tests in this project. 

Our application runs fullstack E2E tests using **Playwright**, executed within an orchestrated Docker environment. As an AI Agent, you should adhere strictly to these patterns when adding or modifying E2E tests.

## Structure & Location

- All E2E test files and configurations are located in the top-level `e2e/` directory.
- The actual test specifications are stored in `e2e/tests/`.
- Test files should follow the `*.spec.ts` naming convention (e.g., `login.spec.ts`).

## Tools & Frameworks

- **Runner & Framework**: `@playwright/test`.
- **Target Context**: Tests run against real, rendered UI elements and a live instance of the backend. You act as a real user navigating the browser.
- **Base URL**: The Playwright config automatically sets the `baseURL` to the frontend instance (`process.env.FRONTEND_URL` or `http://localhost:5173`).

## Writing Playwright Tests

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

## Executing E2E Tests

E2E tests require a fully orchestrated environment (Database, Backend API, Frontend Server, and Playwright container).

- We use the dedicated file: **`infra/docker-compose.e2e.yml`** to run the complete end-to-end test suite.
- The `e2e` container will automatically wait for the frontend to be available before executing the `npx playwright test` command.

## General Agent AI Execution Rules

- **Progressive Disclosure**: Only read relevant files as needed. Do not read every single spec to understand the app unless strictly necessary.
- **Single Purpose Validation**: Each test (`test(...)`) should validate a single user persona flow or behavior.
- **Robust Locators**: Avoid overly specific or brittle DOM paths. Prefer querying by role, placeholder, type, or visible text.
