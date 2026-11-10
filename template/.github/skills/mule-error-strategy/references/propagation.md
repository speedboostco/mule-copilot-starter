# Error propagation mechanics (Mule 4, layered APIs)

Verify each point against the project's own handler and DWL; variants differ per project.

## Relay chain
1. **System layer**: the error DWL builds `{code, message, errorDescription}`-style bodies from the backend's status/message plus an app code identifying the backend; backend text often only when an "expose target error" flag is set. HTTP status = mapped status of the Mule error type, not necessarily the backend's.
2. **Process layer**: the outbound call raises `HTTP:*` carrying `error.errorMessage.payload` (downstream body) and `error.errorMessage.attributes.statusCode`. The handler DWL relays a downstream body that already has the standard fields; errors without a body get an internal-error body.
3. **Experience layer**: same relay; may strip internal fields and add a consumer error code. Common status policy: override to 500 unless the error is APIKIT, `vars.httpStatus` is set, or the status is in an allow-list (e.g. 400/403/409). So a downstream 401/404/503 often reaches the client as 500.
4. Main listener: `vars.httpStatus default 200` on success, `default 500` on error.

## Facts that bite
- `raise-error` (any type) creates an error with no `errorMessage`, so `vars.httpStatus` wins over downstream attributes. A bare `on-error-propagate` that only sets `vars.httpStatus` cannot change a real `HTTP:*` status when the DWL reads `errorMessage.attributes.statusCode` first.
- `until-successful` replaces the original error type with `MULE:RETRY_EXHAUSTED` (→ 500): a retry scope in a process layer loses 401 vs 503. Retry belongs to the system layer.
- A system layer that retries can outlive its caller's response timeout; flag it, do not add a caller-side retry.
- MUnit cannot attach a body or status to a mocked `http:request` error (`munit-tools:error` carries only the type; `raise-error` rejects the `HTTP` namespace). Prove relay by reading the DWL; prove a status-dependent DWL branch with a test-scoped real HTTP stub listener under `src/test` only.
- A handler DWL that assumes a JSON downstream body can itself throw `MULE:EXPRESSION` on an empty or `text/plain` error body (gateway pages). Check `payload is Object` guards when touching it.
- Custom namespaces map to no status and need their own handler branch — the cost of inventing one.
