# Anypoint Platform REST APIs — Discovery Reference

Read-only discovery endpoints only. Verify current path/version against official docs before use — these APIs change across releases and this file is a starting map, not a guarantee.

## Official Sources

- Access Management / Platform APIs overview: https://docs.mulesoft.com/access-management/
- Exchange API: https://docs.mulesoft.com/exchange/to-exchange-api
- API Manager API: https://docs.mulesoft.com/api-manager/2.x/api-manager-api-v2
- Runtime Manager API (CloudHub 2 / hybrid vary by deployment target): https://docs.mulesoft.com/runtime-manager/
- Anypoint CLI 4 (alternative to raw REST calls when a connected app is already configured): https://docs.mulesoft.com/anypoint-cli/latest/

## Control Plane Base URL

- US: `https://anypoint.mulesoft.com`
- EU: `https://eu1.anypoint.mulesoft.com`

This workspace's Maven/Exchange dependency resolution already targets EU (`https://maven.eu1.anypoint.mulesoft.com`), so default to the EU control plane and let the user override with `ANYPOINT_BASE_URL`.

## Identity and Scope

```
GET {base}/accounts/api/me
```
Returns the authenticated user, organization ID, and business group memberships. Always call first to confirm the token is valid and to resolve `orgId`.

```
GET {base}/accounts/api/organizations/{orgId}/environments
```
Returns environment name-to-ID mapping (`sandbox`, `qa`, `preprod`, `production`, or workspace-specific names). Required before any API Manager call.

## Exchange (asset discovery)

```
GET {base}/exchange/api/v2/assets?search={term}
```
Organization-scoped search. Confirm current query-param name (`search` vs `q`) and whether org scoping needs an `X-ANYPNT-ORG-ID` header or a path segment in the current API version before relying on results.

```
GET {base}/exchange/api/v2/assets/{groupId}/{assetId}
GET {base}/exchange/api/v2/assets/{groupId}/{assetId}/{version}
```
Asset and version detail: classifier list (`oas`, `raml`, `wsdl`, `fat-jar`), file download links, dependency `groupId:assetId:version` triples matching this workspace's Maven `classifier=oas,type=zip` pattern.

## API Manager (deployed instance discovery)

```
GET {base}/apimanager/api/v1/organizations/{orgId}/environments/{envId}/apis
```
Lists managed API instances in an environment: API name, asset version, instance ID, endpoint URI, deployment type.

```
GET {base}/apimanager/api/v1/organizations/{orgId}/environments/{envId}/apis/{apiId}
GET {base}/apimanager/api/v1/organizations/{orgId}/environments/{envId}/apis/{apiId}/policies
```
Instance detail and applied policies. Use to confirm whether a candidate EAPI/PAPI/SAPI is already deployed in the target environment and what policies (rate limiting, client-id enforcement, etc.) already apply — relevant to reuse-vs-extend decisions and to error-handling/security assumptions in architecture docs.

## Runtime Manager (deployment target discovery)

Endpoint shape depends on deployment target (CloudHub 1, CloudHub 2, RTF, standalone/hybrid) and changes more often than Exchange/API Manager. Do not hardcode a Runtime Manager endpoint here — confirm the project's actual deployment target from `ccp-devops-pipelines/deploy-config.json` first, then look up the matching current Runtime Manager API for that target in official docs before calling it.

## Headers

- `Authorization: Bearer $ANYPOINT_TOKEN` on every call.
- `Content-Type: application/json` where the endpoint expects it (not needed for GET-only discovery).
- Never log or print the `Authorization` header value.
