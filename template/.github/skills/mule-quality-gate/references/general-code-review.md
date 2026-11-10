# General Code Review

## Sources

- Google code review standard: https://google.github.io/eng-practices/review/reviewer/standard.html
- Google review checklist: https://google.github.io/eng-practices/review/reviewer/looking-for.html
- GitHub pull request reviews: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/about-pull-request-reviews
- OWASP Code Review Guide: https://owasp.org/www-project-code-review-guide/
- OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/

## Review Checklist

- Requirement fit: changed behavior matches the request, ticket, PR title, or acceptance criteria.
- Design: boundaries, abstractions, ownership, and dependency direction fit the existing codebase.
- Functionality: edge cases, null or missing data, retries, idempotency, pagination, time zones, concurrency, and failure paths are handled.
- Simplicity: no speculative abstraction, broad refactor, unrelated formatting, or new dependency without a concrete payoff.
- Security: authentication, authorization, input validation, output encoding, injection, deserialization, path traversal, SSRF, secrets, logging, and dependency risks are reviewed.
- Privacy: no PII exposure in logs, telemetry, fixtures, screenshots, analytics, or error messages.
- Tests: tests fail for the right reason when behavior is broken; assertions are specific; fixtures are minimal; changed production behavior has matching tests.
- Compatibility: public APIs, data contracts, migrations, config keys, env vars, CLI flags, and deployment behavior remain backward compatible or are documented.
- Observability: errors are actionable, logs are bounded and non-sensitive, metrics or traces are added when needed for production diagnosis.
- Performance: avoid obvious N+1 calls, unbounded memory growth, blocking work on hot paths, inefficient parsing, or accidental quadratic behavior.
- Maintainability: names, file placement, comments, and docs make the change easy to modify later.
- Operations: generated files, lockfiles, schemas, migrations, IaC, and deployment manifests are consistent with code changes.

## Validation Hints

Use the repo's own scripts first: `Makefile`, package scripts, CI config, Maven/Gradle, npm/pnpm/yarn, pytest, go test, cargo test, shellcheck, or lint/typecheck commands already present.

Common focused checks:

```bash
mvn test
npm test
npm run lint
npm run typecheck
pnpm test
pytest
go test ./...
cargo test
shellcheck <script>
```

Do not invent a new toolchain during review. If validation cannot run locally, report the blocker and identify the highest-value command for CI or the user.

## Findings Format

Use:

```text
<severity> <file>:<line> - <problem>
Impact: <runtime/user/security/test consequence>
Fix: <specific correction or decision needed>
```

Severity order: blocker, high, medium, low. Use `Nit:` only for optional polish that should not block.
