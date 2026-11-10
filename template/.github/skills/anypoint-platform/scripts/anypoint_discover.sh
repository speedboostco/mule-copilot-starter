#!/usr/bin/env bash
set -euo pipefail

: "${ANYPOINT_BASE_URL:=https://anypoint.mulesoft.com}"

anypoint::_require_token() {
    if [ -z "${ANYPOINT_TOKEN:-}" ]; then
        echo "ANYPOINT_TOKEN is not set. export ANYPOINT_TOKEN=<bearer-token> and retry." >&2
        return 1
    fi
}

anypoint::_get() {
    local path="$1"
    anypoint::_require_token || return 1
    echo "GET ${ANYPOINT_BASE_URL}${path} -H 'Authorization: Bearer [REDACTED]'" >&2
    curl --silent --show-error --fail-with-body \
        --connect-timeout 10 --max-time 30 \
        --location \
        -H "Authorization: Bearer ${ANYPOINT_TOKEN}" \
        -H "Accept: application/json" \
        "${ANYPOINT_BASE_URL}${path}"
}

anypoint::_get_json() {
    if command -v jq >/dev/null 2>&1; then
        anypoint::_get "$1" | jq .
    else
        anypoint::_get "$1"
    fi
}

anypoint::whoami() {
    anypoint::_get_json "/accounts/api/me"
}

anypoint::environments() {
    local org_id="$1"
    anypoint::_get_json "/accounts/api/organizations/${org_id}/environments"
}

anypoint::exchange_search() {
    local org_id="$1"
    local term="$2"
    anypoint::_get_json "/exchange/api/v2/assets?search=$(printf '%s' "$term" | jq -sRr @uri 2>/dev/null || printf '%s' "$term")&organizationId=${org_id}"
}

anypoint::exchange_asset() {
    local group_id="$1"
    local asset_id="$2"
    local version="$3"
    anypoint::_get_json "/exchange/api/v2/assets/${group_id}/${asset_id}/${version}"
}

anypoint::apimgr_list_apis() {
    local org_id="$1"
    local env_id="$2"
    anypoint::_get_json "/apimanager/api/v1/organizations/${org_id}/environments/${env_id}/apis"
}

anypoint::apimgr_api_detail() {
    local org_id="$1"
    local env_id="$2"
    local api_id="$3"
    anypoint::_get_json "/apimanager/api/v1/organizations/${org_id}/environments/${env_id}/apis/${api_id}"
}

anypoint::apimgr_api_policies() {
    local org_id="$1"
    local env_id="$2"
    local api_id="$3"
    anypoint::_get_json "/apimanager/api/v1/organizations/${org_id}/environments/${env_id}/apis/${api_id}/policies"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    cmd="${1:-}"
    if [ -z "$cmd" ] || ! declare -F "anypoint::${cmd}" >/dev/null; then
        echo "usage: $0 {whoami|environments <orgId>|exchange_search <orgId> <term>|exchange_asset <group> <asset> <version>|apimgr_list_apis <orgId> <envId>|apimgr_api_detail <orgId> <envId> <apiId>|apimgr_api_policies <orgId> <envId> <apiId>}" >&2
        exit 2
    fi
    shift
    "anypoint::${cmd}" "$@"
fi
