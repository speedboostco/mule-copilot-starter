# CR-Style Architecture Documentation Format

Use this format when the user asks for architecture documentation, CR documentation, technical design documentation, or shareable integration design Markdown. The style is based on the workspace examples `/Users/vadimssergejevs/Downloads/CR copy.md` and `/Users/vadimssergejevs/Downloads/CR.md`.

## Document Shape

Start with a compact metadata table:

```markdown
| Name | Value |
| --- | --- |
| Version | 1.0.0 |
| Related Document | <link or -> |
| Related ticket | <ticket or -> |
| Reviewed | <name/date or -> |
| Approved | <name/date or -> |
| Intended use | <short purpose> |
```

For change requests, use the alternate change table when requester/date/scope are known:

```markdown
**Change description**

| Requested by | <names> |
| --- | --- |
| Subject | <subject> |
| Date | <date> |
| Tasks, scope affected | <ticket/list> |
```

Then use these sections in this order when applicable:

1. `### **Description**` or `### **Description of changes**`
2. `### **Sequence diagram**`
3. `### **Key Components**`
4. `### **Preconditions**`
5. `### **Steps**`
6. `### **Error Handling**`
7. `### **Data Mapping**`
8. `### **Acceptance Criteria**`

Use `***` or `* * *` separators between major sections when the document is long.

## Sequence Diagram

Prefer Mermaid:

```markdown
### **Sequence diagram**

::: mermaid
sequenceDiagram
    participant Source
    participant Platform
    participant Target

    Source->>Platform: 1. POST:/example
    Platform-->>Source: 2. 202 Accepted
    Platform->>Target: 3. POST:/target
    Target-->>Platform: Response
:::
```

Use numbered messages matching the step numbers. Include `alt`, `opt`, and `Note over` blocks for branching, optional processing, callbacks, retry, rollback, or async behavior.

## Key Components

Use bullet definitions. **The integration platform is always one component, never split into EAPI/PAPI/SAPI-labeled sub-bullets or sub-participants in the sequence diagram** — internal Mule layer routing (whether an operation is direct EAPI→SAPI or orchestrated through PAPI) is an implementation decision, not something the design document narrates. It belongs in the internal user-story backlog/implementation plan, not in the stakeholder-facing document. This applies even when the operation genuinely requires multi-hop internal orchestration (e.g., paginated aggregation) — the document still shows one `C as the platform` participant doing the work, matching every other scenario doc in this workspace:

```markdown
### **Key Components**

* **<Platform name from profile.md>**: Integration middleware responsible for handling data from source to target system.
* **<Source system>**: <role in the integration>.
* **<Target system>**: <role in the integration>.
```

## Preconditions

Capture only prerequisites that must be true before build/test/deploy:

```markdown
### **Preconditions**

* Authentication is configured on <system> side, credentials are provided to the integration team.
* Endpoint URLs and environment-specific values are confirmed for sandbox, qa, preprod, and production.
* Required source payload examples or mappings are provided.
```

## Steps

Each step uses this pattern:

```markdown
**1. Source → Platform** (short purpose)

**API Request Schema**:
| Parameter Name | Value |
| --- | --- |
| **Base URL** | {Platform application URL} |
| **Endpoint** | /api/example |
| **Type** | Private |
| **Method** | POST |
| **Authorization** | Bearer {Access Token} |

**Headers**:
| Parameter Name | Value |
| --- | --- |
| Content-Type | application/json |

**Request Body**:
| Parameter | Required | Data type | Description | Mapping |
| --- | --- | --- | --- | --- |
| _field_ | yes | string | Business meaning | [step1].payload._field_ |

**Request Body Example**:

    {
      "field": "value"
    }

**Response body**:
| Parameter | Required | Data type | Description | Mapping |
| --- | --- | --- | --- | --- |
| _message_ | yes | string | - | "Accepted for further processing" |
```

Step rules:
- Use `Source → Target` titles and a short parenthesized purpose.
- Use `API Request Schema`, `Headers`, `URI parameters`, `Request Body`, `Response body`, and examples only when relevant.
- Put vault/secure values as `vault`, `vaulted`, `{Access Token}`, or `![encrypted]`; never include real secrets.
- Use step references like `[step1].payload._id_` in Mapping columns.
- Use indented code blocks for simple examples if matching the CR examples; fenced blocks are acceptable for larger JSON.

## Error Handling

Describe errors the way the platform produces them. Target-system errors propagate SAPI -> PAPI -> EAPI -> client: the SAPI names the failing system's app code and the upper layers relay its status and `errorDescription` (`"<status>: <description> (<appCode>)"`) unchanged; internal failures use fallback code `000`. Propagation is always acceptable (user decision 2026-10-13): do not specify case-specific statuses, texts, or numeric `errorCode` values; the developer pipeline will not build custom handling for them. Keep the default below.

Use this default structure unless the requirement overrides it:

```markdown
### **Error Handling**

* **Any type of errors returned from target systems:**

**HTTP Status code**: 500 Internal Server Error

**Body**:
| Parameter | Required | Data type | Description |
| --- | --- | --- | --- |
| _message_ | yes | string | "Something went wrong, please try again or contact support" |
| _errorDescription_ | yes | string | Cause of the error |

**Message body example**:

    {
      "message": "Something went wrong, please try again or contact support",
      "errorDescription": "401: authentication failed (E020)"
    }
```

If async processing returns 202 before downstream work, document where failures are logged or delivered by callback instead of implying the original HTTP response changes.

## Data Mapping

Use a compact mapping table for high-level transformations and detailed field mapping tables inside steps:

```markdown
### **Data Mapping**
| Source system format | Target system format | Comment |
| --- | --- | --- |
| JSON | XML | the platform transforms request body before sending to target |
```

For field-level mapping, include `Parameter`, `Required`, `Data type`, `Description`, and `Mapping`.

## Acceptance Criteria

Use observable bullets:

```markdown
### **Acceptance Criteria**
* the platform accepts the documented request and returns the expected HTTP status/body.
* the platform maps all documented fields according to the mapping tables.
* If any required downstream step fails, the documented error behavior is followed.
* the platform performs three attempts only at the SAPI backend call when network connectivity retry is required.
* Error responses follow the documented structure and codes.
```

## CR Amendment / Clarification Format

Use this variant instead of the full initial-CR shape above when the request is a **change/clarification to an already-delivered CR/AsBuilt document**, not a first-time design (real workspace example: `ccp-mendix-eapi/CR-1 ASD-INT-003 - AsBuilt Data`).

```markdown
| Name | Value |
| --- | --- |
| **Related ticket** | #<ticket> |
| **Tasks, scope affected** | #<ticket(s)> |
| **Requested by** | <name> |
| **Subject** | Clarifications on <original CR/doc ID> |
| **Date** | <date> |

## **Changes Overview**

<1-3 sentence prose summary of what behavior changes and why, referencing the affected step numbers from the original document.>

## **Updated Requirements**

### 1. <Short title for the changed behavior, with affected step numbers>

| No | Aspect | Original document <name> | Updated by this CR |
| --- | --- | --- | --- |
| 1 | **Step <n>:** <what this step does> | <prior documented behavior, or "No documented handling"> | <new behavior> |

### 2. <Next changed aspect, e.g. a transformation/mapping change>

Updated mapping row (<request/response body name>):

| Field | Required | Data type | Source | Transformation |
| --- | --- | --- | --- | --- |
| `field` | Yes/No | type | <source path> | <transformation rule> |

This replaces the previous row, which specified `field` as <prior value/TBC/mock>.

**Example:**

Given <input>, `field` is <derivation>.

### 3. Updated Sequence Diagram (<sub-flow name>, Steps <range>)

Only the <sub-flow name> sub-flow changes. The other sections of the sequence diagram remain unchanged.

:::mermaid
sequenceDiagram
    participant <A>
    participant Platform
    participant <B>

    autonumber <n>

    Note over Platform, <B>: <Sub-flow name> (updated)

    <diagram continuing from the original document's step numbering, using autonumber to preserve continuity>
:::

## **Additional Acceptance Criteria**

1. <Observable, testable criterion for the first change>
1. <Observable, testable criterion for the second change>
1. <Criterion covering partial/edge-case behavior explicitly, if the change affects loop/match logic>
```

Rules specific to this variant:
- Always name the original document being amended (`Original document ASD-INT-003 - AsBuilt Data` style) in both the metadata Subject line and the before/after table header — never present a clarification as if it were the first version of the design.
- The before/after comparison table is mandatory for behavior changes; do not describe a behavior change in prose only.
- `autonumber <n>` in the Mermaid block must continue the step count from where the original document's diagram left off, not restart at 1 — confirm the original document's last step number before writing this.
- Acceptance criteria use a flat `1.` numbered list (Markdown auto-renumbers), one criterion per observable behavior, including explicit coverage of partial-match/edge-case behavior when the change touches loop or matching logic.

## Quality Rules

- Keep the documentation readable for stakeholders, not only developers.
- Use real endpoint paths, methods, systems, and project names when known.
- Mark unknown values as `TBD` and add stakeholder questions in the architecture package.
- Keep architecture documentation separate from internal implementation stories.
- Do not include implementation-only file paths unless the user explicitly wants developer notes in the document.
- **Never write negative-space statements** — sentences describing what a system does *not* do, does *not* touch, or is *not* changing, when that thing isn't otherwise relevant to the document. If information doesn't need to be in the document, omit it entirely; don't include it framed as a negation ("this does not modify X", "the platform does not do Y", "not independently deployable from Z"). State only what the scenario in front of you actually does.
- **The integration platform is one component.** Do not label sequence diagram participants or Key Components bullets by internal Mule layer (`the platform EAPI`, `the platform PAPI`, `the platform SAPI`) — a single `C as the platform` covers it regardless of how many internal hops the real implementation needs. See Key Components above.
- **Do not name a new endpoint after an existing one's suffix/pattern unless the reason for that pattern actually applies.** A `-search` suffix means the endpoint accepts filter/query parameters; don't apply it to a plain, unfiltered list endpoint just because a sibling endpoint elsewhere uses that suffix. State the endpoint path plainly based on what the resource actually is (`/api/groups` for "list all groups", not `/api/groups-search` for a resource with no search capability).
