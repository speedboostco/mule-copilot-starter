# Scenario Catalog

## Sources

- MuleSoft MUnit test structure: https://docs.mulesoft.com/munit/latest/munit-test-concept
- MuleSoft MUnit matchers: https://docs.mulesoft.com/munit/latest/munit-matchers
- MuleSoft MUnit mock processors: https://docs.mulesoft.com/munit/latest/mock-event-processor
- MuleSoft MUnit coverage: https://docs.mulesoft.com/munit/latest/munit-coverage-report
- OWASP Web Security Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/

This catalog is a menu of candidate cases, not a checklist. Every case must first pass the Test Necessity Gate in the `mule-munit-builder` skill; cases the OAS/APIkit contract enforces, cases an existing test already covers, and cases that hit no project-owned logic are skipped.

## Mule API Input Cases

Cases only the APIkit router can reject (required, extra or wrong-type fields, malformed JSON, wrong content type, unsupported method, path-parameter patterns) are `SKIP:framework`; none is tested through the router.

- Missing required body, query, path, or header fields.
- Null, blank string, whitespace-only, empty object, empty array, and array with null item.
- Wrong type: string for number, number for string, object for scalar, array for object.
- Unknown enum, wrong case enum, deprecated value, and value with leading/trailing spaces.
- Boundary values: min, max, just below min, just above max, zero, negative, very large number, long string.
- Date/time values: invalid date, timezone offset, UTC `Z`, leap day, daylight-saving boundary, date-only vs datetime.
- Identifier values: unknown ID, duplicate ID, mixed valid and invalid IDs, case sensitivity, special characters.
- Extra fields and nested extra fields: confirm ignored, rejected, or passed through according to contract.
- Malformed JSON/XML, invalid encoding, wrong content type, missing accept header, unsupported method.

## DataWeave And Mapping Cases

- Optional source field absent vs present as `null`.
- Empty arrays and single-item arrays.
- Mixed array item validity.
- Default values when config or payload fields are missing.
- Numeric precision, string trimming, boolean coercion, enum normalization, and date formatting.
- Backend response missing expected fields or containing unknown additional fields.
- Error response mapping when `error.description`, status, or backend body is absent.

## Downstream And Runtime Cases

- Backend timeout, refused connection, DNS/host failure, TLS/auth failure.
- Backend 400, 401, 403, 404, 409, 422, 429, 500, 502, 503, and 504.
- Empty successful response, malformed successful response, and successful response with business error payload.
- Retry exhaustion, non-retryable errors, and call count assertions.
- Async dispatch failure after accepted input.
- Duplicate request, out-of-order event, repeated callback, and idempotency conflict.
- Config missing key, blank env value, and unresolved secure placeholder.

## Test Selection Rules

- Keep one happy path per new endpoint or flow.
- Add no 400 test per endpoint or route; router rejections are covered once by `main-test-suite.xml`. Add a validation test per rule this project owns (explicit `validation:` checks, DWL rules), entered by `flow-ref`, never for constraints the OAS/APIkit contract enforces.
- Cover one representative of each group of inputs that behave the same (missing/null/blank, each enum value) and only when project-owned logic distinguishes them.
- Add boundary tests for numeric, length, date, pagination, or collection-size rules only when the rule is implemented in this project's DWL or flow code.
- Add one downstream error test per new or changed outbound call.
- Add retry call-count tests only where retry behavior is owned by the layer.
- Add a regression test for the exact bug shape when fixing a defect, unless the reproducing test already is that test.
- Search `src/test/munit/` first and add nothing an existing test already covers.
- Write no scenarios for changes confined to `src/test/**`.
- Avoid snapshots that assert large full payloads unless contract shape is the behavior under test.

## General-Language Patterns

- Use table-driven tests for many input variants.
- Use property-based tests when invariants matter more than fixed examples.
- Use fuzz tests for parsers, decoders, validators, and request deserializers when the language/framework supports them.
- Use integration tests for framework wiring, serialization, auth, database, queue, or external API boundaries.
- Keep mocks narrow: assert important calls and outputs, not incidental implementation steps.
