---
applyTo: "**/src/test/**"
description: "MUnit defaults. Test Necessity Gate and test shape; full workflow in the mule-munit skill."
---
# MUnit — defaults

Style of suites, test names and fixtures: `house-style-munit.instructions.md` and the neighbouring suites.

- Run the Test Necessity Gate (`mule-munit` skill) before writing any test. A test must catch a plausible defect in project-owned code that this change touched and no existing test catches.
- No tests for: test-only changes, pass-through/1:1 mapping, config/pom/OAS-only edits, constraints APIkit/OAS already enforce, equivalent inputs, coverage percentage.
- Shape: only the main suite touches APIkit (health check + router invoked with router mocked). Every other test enters by `flow-ref` to the endpoint flow, inputs via `munit:set-event`, outbound `http:request` mocked by `doc:name`. Never test through the real listener/router.
- Fixtures under the project's existing scaffolder layout (request / mock / response).
- System-layer retry change: verify the total call count (initial + retries).
- Downstream error: one test per new/changed outbound call asserting the global handler's observable result (`vars.httpStatus`, END logger not reached, call count). MUnit error mocks carry no body/status: do not build stub flows or handlers to fake a relayed body.
- `mule.key` for tests: the value from `profile.md` (Mule secure properties need exactly 16 chars).
- Never delete, disable or loosen an existing test; never edit a passing test's expectations to fit new code.
- Payload with media type `application/x-www-form-urlencoded`: transform to JSON before `assert-that`/`assert-equals`.
- `with-attribute` matching on connector operations is equality-only; probe before relying on it.
