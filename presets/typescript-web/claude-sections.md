# TypeScript Web Preset — CLAUDE.md Sections

## CONVENTIONS
- TypeScript strict mode throughout
- Functional components (React) or composables (Vue) — follow the project's framework
- API responses typed with shared interfaces between client and server
- Environment variables for configuration — never hardcode secrets or URLs
- Consistent error handling: try/catch at API boundaries, error boundaries in UI

## CODE_STANDARDS
- **Every module gets tests immediately**: When creating a new service, hook, or utility, write tests in the same session. Minimum: one happy-path test + one edge case.
- **Name every number**: Define constants instead of magic numbers in business logic.
- **Add logging with the feature**: API calls = info, state changes = debug, errors = error with context.
- **Run `npm test` after every code change**: Verify continuously.

## ERROR_HANDLING
- **API handlers**: Return appropriate HTTP status codes with error messages. Never leak stack traces to clients.
- **UI components**: Use error boundaries. Show user-friendly messages, log technical details.
- **Utilities**: Return `Result` types or throw typed errors — no silent failures.
- **Never swallow errors**: Always log or surface them.

## TESTING
- **What to test**: Business logic, API handlers, utility functions, complex UI interactions.
- **What not to test**: Third-party library internals, simple pass-through components, CSS.
- **Test style**: Co-located test files (`*.test.ts`) or `__tests__/` directories.
- **New modules must have tests**: At minimum, test the happy path and one error case.

## DEPENDENCY_PHILOSOPHY
- **Evaluate before adding**: Check bundle size impact, maintenance status, and whether the functionality is achievable in <100 lines.
- **Prefer well-maintained packages**: Check npm download counts, last publish date, open issues.
- **Pin versions**: Use exact versions or lock files to prevent surprise breaks.

## LOGGING
- `error`: Unhandled exceptions, failed API calls, data corruption. `warn`: Deprecated usage, retry attempts. `info`: API requests, auth events, deployments. `debug`: State changes, cache hits/misses.
- Every new API endpoint and service must include appropriate logging.
