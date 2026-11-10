from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

DOC_NAME = "{http://www.mulesoft.org/schema/mule/documentation}name"
GLOBAL_FILES = ("globals.xml", "global.xml")
FLOW_TAGS = ("flow", "sub-flow")
NON_OPERATION_NS = {"apikit", "mule-apikit", "ee", "munit", "munit-tools", "spring", "secure-properties"}
PUBLISH_OPERATIONS = {"amqp:publish", "jms:publish", "vm:publish", "anypoint-mq:publish", "kafka:publish"}
NON_CONFIG_TAGS = {"flow", "sub-flow", "error-handler", "configuration", "configuration-properties", "global-property", "import", "description"}
NON_CONFIG_NS = {"apikit", "mule-apikit", "secure-properties", "spring", "os", "tls", "ee", "munit", "munit-tools", "validation"}
NON_CONFIG_LOCAL = {"listener-config", "object-store", "security-manager"}
PLACEHOLDER = re.compile(r"\$\{([^}]+)\}")
CONFIG_SUFFIX = re.compile(r"(?:_SAPI)?(?:_HTTP)?(?:_Request)?(?:_configuration|_config|_Config)?$")


def prefix_of(uri: str) -> str:
    if uri.endswith("/ee/core"):
        return "ee"
    segment = uri.rstrip("/").rsplit("/", 1)[-1]
    return "" if segment == "core" else segment


def qname(element) -> str:
    tag = element.tag
    if not isinstance(tag, str):
        return ""
    if tag.startswith("{"):
        uri, local = tag[1:].split("}", 1)
        prefix = prefix_of(uri)
        return f"{prefix}:{local}" if prefix else local
    return tag


def local_of(element) -> str:
    return qname(element).rsplit(":", 1)[-1]


def namespace_of(element) -> str:
    name = qname(element)
    return name.split(":", 1)[0] if ":" in name else ""


def doc_name_of(element) -> str:
    return element.attrib.get(DOC_NAME, "")


def attributes_of(element) -> dict:
    return {key: value for key, value in element.attrib.items() if not key.startswith("{")}


def flatten(data, path="", out=None) -> dict:
    out = {} if out is None else out
    if isinstance(data, dict):
        for key, value in data.items():
            flatten(value, f"{path}.{key}" if path else str(key), out)
    elif isinstance(data, (str, int, float, bool)):
        out[path] = str(data)
    return out


def load_properties(project: Path) -> dict:
    try:
        import yaml
    except Exception:
        return {}

    class Loader(yaml.SafeLoader):
        pass

    Loader.add_multi_constructor("!", lambda loader, suffix, node: None)
    properties: dict = {}
    for name in ("config-common.yaml", "config-qa.yaml"):
        path = project / "src" / "main" / "resources" / "config" / name
        if not path.is_file():
            continue
        try:
            for document in yaml.load_all(path.read_text(errors="ignore"), Loader=Loader):
                properties.update(flatten(document or {}))
        except Exception:
            continue
    return properties


def resolve(text: str, properties: dict) -> str:
    return PLACEHOLDER.sub(lambda match: properties.get(match.group(1), match.group(0)), text or "")


def system_of(config_ref: str) -> str:
    stem = CONFIG_SUFFIX.sub("", config_ref or "")
    return re.sub(r"^[a-z0-9]+-(?=[a-z0-9-]+-(?:eapi|papi|sapi)$)", "", re.sub(r"[_\s]+", "-", stem).strip("-").lower())


def normalized_text(element) -> str:
    return re.sub(r"\s+", " ", " ".join(part.strip() for part in element.itertext() if part and part.strip()))


def signature_of(element, properties: dict) -> str:
    def render(node):
        attrs = {key: resolve(value, properties) for key, value in attributes_of(node).items() if key != "name"}
        return [qname(node), attrs, [render(child) for child in node if isinstance(child.tag, str)]]

    return json.dumps(render(element), sort_keys=True)


def connection_of(element, properties: dict) -> str:
    parts = []
    for child in element.iter():
        if local_of(child).endswith("connection"):
            attrs = attributes_of(child)
            parts.append("/".join(resolve(attrs.get(key, ""), properties) for key in ("protocol", "host", "port")))
    base = resolve(element.attrib.get("basePath", ""), properties)
    return (parts[0] if parts else "") + base if parts else ""


def operation_core(element, properties: dict):
    name = qname(element)
    config = element.attrib.get("config-ref", "")
    if name == "http:request":
        target = resolve(element.attrib.get("path") or element.attrib.get("url") or "", properties)
        return (name, config, element.attrib.get("method", "GET").upper(), target)
    if name in PUBLISH_OPERATIONS:
        return (name, config)
    attrs = tuple(sorted((key, resolve(value, properties)) for key, value in attributes_of(element).items() if key not in ("config-ref", "target", "targetValue")))
    return (name, config, attrs, normalized_text(element))


def summarize(items) -> str:
    seen: dict = {}
    for item in items:
        seen.setdefault((item["flow"], item["file"]), []).append(item["doc"])
    parts = []
    for (flow, file), docs in seen.items():
        detail = f", {len(docs)} operations" if len(docs) > 1 else (f", doc:name \"{docs[0]}\"" if docs[0] else "")
        parts.append(f"{flow} ({file}{detail})")
    return ", ".join(parts)


def describe_core(core) -> str:
    if core[0] == "http:request":
        return f"http:request {core[2]} {core[3]} via {core[1]}"
    return f"{core[0]} via {core[1]}"


def is_operation(element, parent_flow, is_first_child_of_flow: bool) -> bool:
    name = qname(element)
    if not name or ":" not in name or namespace_of(element) in NON_OPERATION_NS:
        return False
    if "config-ref" not in element.attrib:
        return False
    local = local_of(element)
    is_source = local in ("listener", "scheduler") or local.startswith("on-") or local.endswith("-listener")
    if is_first_child_of_flow and is_source and parent_flow is not None and local_of(parent_flow) == "flow":
        return False
    return True


def scan(project: Path) -> dict:
    mule_dir = project / "src" / "main" / "mule"
    properties = load_properties(project)
    files = sorted(mule_dir.glob("*.xml")) if mule_dir.is_dir() else []
    configs, flows, operations, refs, skipped = [], {}, [], {}, []
    has_globals = any(path.name in GLOBAL_FILES for path in files)
    for path in files:
        try:
            root = ET.parse(path).getroot()
        except Exception:
            skipped.append(path.name)
            continue
        for child in root:
            if not isinstance(child.tag, str):
                continue
            local = local_of(child)
            if local in FLOW_TAGS:
                flows[child.attrib.get("name", "")] = {"file": path.name, "kind": local, "element": child}
                children = [item for item in child if isinstance(item.tag, str)]
                for node in child.iter():
                    if node is child:
                        continue
                    first = bool(children) and node is children[0]
                    if is_operation(node, child, first):
                        operations.append({
                            "flow": child.attrib.get("name", ""), "file": path.name, "doc": doc_name_of(node),
                            "core": operation_core(node, properties),
                        })
                    if local_of(node) == "flow-ref" and node.attrib.get("name"):
                        refs.setdefault(node.attrib["name"], []).append((path.name, child.attrib.get("name", "")))
                continue
            name = child.attrib.get("name")
            if local in NON_CONFIG_TAGS or not name or namespace_of(child) in NON_CONFIG_NS and local != "request-config":
                continue
            if local in NON_CONFIG_LOCAL:
                continue
            configs.append({
                "name": name, "type": qname(child), "file": path.name, "doc": doc_name_of(child),
                "signature": signature_of(child, properties), "backend": connection_of(child, properties),
            })
    per_flow: dict = {}
    for item in operations:
        per_flow.setdefault(item["flow"], []).append(item)
    wrappers = []
    for flow_name, items in per_flow.items():
        info = flows.get(flow_name)
        if info is None or len(items) != 1:
            continue
        in_services = info["file"].endswith("-services.xml")
        callers = refs.get(flow_name, [])
        if in_services or callers:
            wrappers.append({
                "flow": flow_name, "file": info["file"], "core": items[0]["core"], "in_services": in_services,
                "callers": len(callers), "caller_files": sorted({file for file, _ in callers}),
            })
    findings = []
    groups: dict = {}
    for item in operations:
        groups.setdefault(item["core"], []).append(item)
    for core, members in groups.items():
        if len({member["flow"] for member in members}) < 2:
            continue
        canonical = next((m for m in members if m["file"].endswith("-services.xml") and any(w["flow"] == m["flow"] for w in wrappers)), None)
        if canonical:
            duplicates = [m for m in members if m["flow"] != canonical["flow"]]
            kind = "duplicate-operation"
            message = (
                f"{describe_core(core)} is implemented again in " + summarize(duplicates)
                + f"; call the shared sub-flow instead: <flow-ref name=\"{canonical['flow']}\"/> ({canonical['file']})"
            )
        else:
            duplicates = members
            kind = "extract-candidate"
            system = system_of(core[1]) or "backend"
            message = (
                f"{describe_core(core)} appears in " + summarize(members)
                + f"; move it into one sub-flow in {system}-services.xml (name {system}-services:<operation>) and flow-ref it"
            )
        findings.append({
            "kind": kind, "message": message, "files": sorted({m["file"] for m in duplicates}),
            "markers": sorted({m["flow"] for m in duplicates} | {m["doc"] for m in duplicates if m["doc"]}),
        })
    by_signature: dict = {}
    for config in configs:
        by_signature.setdefault((config["type"], config["signature"]), []).append(config)
    for (kind_name, _), members in by_signature.items():
        if len(members) > 1:
            names = ", ".join(f"{m['name']} ({m['file']})" for m in members)
            findings.append({
                "kind": "duplicate-config", "message": f"{kind_name} declared more than once with identical settings: {names}; keep one and point every operation at it",
                "files": sorted({m["file"] for m in members[1:]}), "markers": sorted({m["name"] for m in members[1:]}),
            })
    by_backend: dict = {}
    for config in configs:
        if config["backend"]:
            by_backend.setdefault((config["type"], config["backend"]), []).append(config)
    for (kind_name, backend), members in by_backend.items():
        if len({m["signature"] for m in members}) > 1:
            findings.append({
                "kind": "same-backend", "message": f"{kind_name} entries {', '.join(m['name'] for m in members)} point at the same backend {backend} with different settings; confirm the difference is intended",
                "files": sorted({m["file"] for m in members}), "markers": [], "info": True,
            })
    if has_globals:
        for config in configs:
            if config["file"] not in GLOBAL_FILES:
                findings.append({
                    "kind": "config-outside-globals",
                    "message": f"{config['type']} {config['name']} is declared in {config['file']}; global connector configs belong in {'globals.xml' if (mule_dir / 'globals.xml').is_file() else 'global.xml'}",
                    "files": [config["file"]], "markers": [config["name"]],
                })
    placement = []
    seen_systems = set()
    for config in configs:
        system = system_of(config["name"])
        if system and system not in seen_systems and config["type"] != "http:listener-config":
            seen_systems.add(system)
            placement.append({"system": system, "config": config["name"], "file": f"{system}-services.xml", "exists": (mule_dir / f"{system}-services.xml").is_file()})
    return {
        "project": project.name, "files": [path.name for path in files], "skipped": skipped, "resolved_properties": bool(properties), "placement": placement,
        "configs": [{k: v for k, v in c.items() if k != "signature"} for c in configs],
        "wrappers": wrappers, "operations": operations, "findings": findings,
    }


def format_text(result: dict, only: set | None = None) -> str:
    lines = [f"REUSE SCAN {result['project']} ({len(result['files'])} Mule files{'' if result['resolved_properties'] else ', properties not resolved'})"]
    lines.append("Global configs:")
    for config in result["configs"]:
        lines.append(f"  {config['type']} {config['name']} [{config['file']}]" + (f" -> {config['backend']}" if config["backend"] else ""))
    shared = [w for w in result["wrappers"] if w["in_services"]]
    local = [w for w in result["wrappers"] if not w["in_services"]]
    lines.append("Shared operation wrappers in *-services.xml (flow-ref these, do not copy the operation):")
    for wrapper in sorted(shared, key=lambda w: w["flow"]):
        lines.append(f"  {wrapper['flow']} [{wrapper['file']}] {describe_core(wrapper['core'])}, called {wrapper['callers']}x")
    lines.append("Single-operation sub-flows inside use-case files (local, reusable only by flow-ref):")
    for wrapper in sorted(local, key=lambda w: w["flow"]):
        lines.append(f"  {wrapper['flow']} [{wrapper['file']}] {describe_core(wrapper['core'])}, called {wrapper['callers']}x")
    lines.append("Placement for a new shared operation (one sub-flow per operation, <system>-services:<operation>):")
    for item in result["placement"]:
        lines.append(f"  {item['config']} -> {item['file']} ({'exists' if item['exists'] else 'create it'})")
    wrapped = {w["flow"] for w in result["wrappers"]}
    inline = [o for o in result["operations"] if o["flow"] not in wrapped]
    lines.append("Operations inside use-case flows (not wrapped):")
    for item in inline[:40]:
        lines.append(f"  {item['flow']} [{item['file']}] {describe_core(item['core'])}")
    if len(inline) > 40:
        lines.append(f"  ... {len(inline) - 40} more (use --json for the full list)")
    findings = [f for f in result["findings"] if only is None or only & set(f["files"])]
    lines.append(f"Findings ({len(findings)}{' in the selected files' if only else ''}):")
    for finding in findings:
        lines.append(f"  {'info' if finding.get('info') else 'REUSE'} {finding['kind']}: {finding['message']}")
    return "\n".join(lines)
