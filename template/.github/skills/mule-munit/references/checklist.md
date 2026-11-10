# MUnit checklist and gotchas

## Mocks
- Mock by exact `doc:name`. Two requests with the same `doc:name` in one file → fix the production selector first.
- `with-attribute` on connector operations matches by equality only: matcher functions fail; enum/child-element parameters cannot be matched; numeric parameter written as expression may not match the plain value. Probe in a scratch copy.
- `then-call` stub flow without its own error handler is covered by the app default handler: an assertion error inside the stub is swallowed and returned as the mocked result. Grep the log for `ERROR … <stub-flow>` first.
- Mock attributes such as `statusCode` when the flow reads them.
- `munit:attributes`: use `value=` form; CDATA body form can leave fields null.

## Assertions
- Assert structure, not only non-null; `vars.httpStatus` when the listener reads it.
- Payload media type `application/x-www-form-urlencoded`: `assert-that`/`assert-equals` throw coercion errors; transform to JSON first.
- Connector parameter ranges (page sizes, enums) are not validated under mocks: read the connector docs or bytecode (`javap -c -p`) before choosing a value.

## Retry
- `until-successful maxRetries="2"` → 3 total calls. Property-driven: use the configured value.

## Runtime
- MUnit starts with lazy init: a flow referenced only by an APIkit mapping is not created; `flow-ref` entry avoids this.
- Two MUnit runs at once collide on the HTTP listener port; run projects serially.
- IDE (Anypoint Studio/Code Builder) may rewrite open XML files while agents edit: close/refresh before multi-file refactors.
- Laptop sleep makes Maven look slow; wrap long runs (`caffeinate -ims` on macOS) before diagnosing dependencies.
- Unresolved config placeholders, missing spec artifacts, missing Maven credentials are blockers, not test failures to patch around.
