#!/usr/bin/env python3
"""E0 contract audit and AST validator. No graph generation, causal claim, or oracle."""
import argparse
import hashlib
import itertools
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def load_contracts():
    return (json.loads((HERE / "catalog.json").read_text(encoding="utf-8")),
            json.loads((HERE / "protocol.json").read_text(encoding="utf-8")))


def git_blob_sha(content):
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


def validate_contracts(catalog, protocol, check_sources=True):
    issues = []
    classes = catalog["classes"]
    class_ids = [c["id"] for c in classes]
    if len(class_ids) != len(set(class_ids)):
        issues.append("DUPLICATE_CLASS")
    for cl in classes:
        if len(cl["roles"]) != len(set(cl["roles"])):
            issues.append("DUPLICATE_ROLE:" + cl["id"])
        names = [p["name"] for p in cl["ports"]]
        if len(names) != len(set(names)):
            issues.append("DUPLICATE_PORT:" + cl["id"])
        for p in cl["ports"]:
            if p["direction"] not in ("in", "out"):
                issues.append("PORT_DIRECTION:" + cl["id"])
            if not p["type"].startswith(("FLOW<", "SIGNAL<", "STATE<")):
                issues.append("PORT_TYPE:" + cl["id"])
        for name, value in cl["parameters"].items():
            if value["min"] > value["max"] or not value["required"]:
                issues.append("BAD_PARAMETER_BOUND:" + name)
    for source in catalog["source_packages"].values():
        p = ROOT / source["path"]
        if check_sources and (not p.is_file() or git_blob_sha(p.read_bytes()) != source["sha"]):
            issues.append("SOURCE_INTEGRITY_FAILED:" + source["path"])
    profiles = protocol["observation_profiles"]
    if set(profiles) != {"P", "Q"}:
        issues.append("OBSERVATION_PROFILES")
    if set(profiles["Q"]["visible"]) - set(profiles["P"]["visible"]):
        issues.append("PROFILE_Q_NOT_SUBSET")
    if set(profiles["P"]["visible"]) != {"dispatchRate", "deliveryRate", "inTransit", "reportedDeliveryRate"}:
        issues.append("P_MISSING_OBSERVABLE")
    if profiles["Q"]["visible"] != ["reportedDeliveryRate"]:
        issues.append("Q_SHOULD_ONLY_SHOW_REPORT")
    if any(set(p["visible"]) & set(p["hidden"]) for p in profiles.values()):
        issues.append("VISIBLE_IS_HIDDEN")
    if "trueGraph" in profiles["P"]["visible"] or "trueGraph" in profiles["Q"]["visible"]:
        issues.append("GOLD_VISIBLE")
    if [x["id"] for x in protocol["interventions"]] != ["pulse", "step", "ramp", "high_pulse"]:
        issues.append("PROBE_MENU_CHANGED")
    budget = protocol["budgets"]
    if budget["world_responses_total"] != (budget["initial"] + budget["chosen_discriminant"] + budget["reserved"]):
        issues.append("ORACLE_BUDGET_NOT_BALANCED")
    if budget["world_responses_total"] != 3 or budget["reserved"] != 1:
        issues.append("ORACLE_BUDGET_CHANGED")
    if not protocol["commitments"]["constructor_no_gold_access"]:
        issues.append("NO_GOLD_ISOLATION")
    if protocol["numerical"]["error_bound"] <= 0:
        issues.append("INVALID_ERROR_BOUND")
    if protocol["numerical"]["error_bound_status"] != "OPERATIONAL_THRESHOLD_NOT_CERTIFIED":
        issues.append("UNVERIFIED_SOLVER_BOUND_CLAIMED")
    desc = protocol["neutral_description"].lower()
    for expression in ("boundedqueue", "firstorder", "filtro", "retardo", "dos colas", "transitonly", "reportonly", "modelo verdadero"):
        if expression in desc:
            issues.append("FUNCTIONAL_TEXT_LEAK:" + expression)
    return sorted(set(issues))


def port_type(instance, port, classes):
    cl = classes[instance["class_id"]]
    matches = [p for p in cl["ports"] if p["name"] == port]
    if len(matches) != 1:
        raise ValueError("UNKNOWN_PORT")
    p = matches[0]
    rtype = p["type"]
    for short, concrete in cl.get("role_bindings", {}).get(instance["role"], {}).items():
        rtype = rtype.replace("<" + short + ">", "<" + concrete + ">")
    return rtype, p["direction"]


def validate_graph(graph, catalog):
    """Representation check. Intentionally does NOT construct an AST."""
    issues = []
    allowed = {"instances", "links"}
    if set(graph) != allowed:
        return ["GRAPH_SCHEMA"]
    instances = graph["instances"]
    links = graph["links"]
    if not isinstance(instances, list) or not isinstance(links, list):
        return ["GRAPH_SCHEMA"]
    ids = [i.get("id") for i in instances]
    if any(not isinstance(i, str) or not NAME.fullmatch(i) for i in ids):
        issues.append("BAD_ID")
    if len(ids) != len(set(ids)):
        issues.append("DUPLICATE_ID")
    if issues:
        return issues
    entries = {c["id"]: c for c in catalog["classes"]}
    imap = {i["id"]: i for i in instances}
    roles = Counter(i.get("role") for i in instances)
    for role in ("source", "preparation", "dispatch", "receipt"):
        if roles[role] != 1:
            issues.append("MISSING_OR_DUPLICATE_REQUIRED_ROLE:" + role)
    for role, max_count in (("transit", catalog["resource_limits"]["max_transit_instances"]),
                            ("report", catalog["resource_limits"]["max_report_filter_instances"])):
        if roles[role] > max_count:
            issues.append("ROLE_LIMIT:" + role)
    for ins in instances:
        cl = entries.get(ins.get("class_id"))
        if cl is None:
            issues.append("UNKNOWN_CLASS")
            continue
        if ins.get("role") not in cl["roles"]:
            issues.append("ROLE_NOT_ALLOWED")
        if set(ins) != {"id", "class_id", "role", "parameters"}:
            issues.append("INSTANCE_SCHEMA")
        values = ins.get("parameters", {})
        if set(values) != set(cl["parameters"]):
            issues.append("PARAMETER_MISMATCH")
            continue
        for name, limits in cl["parameters"].items():
            number = values[name]
            if not isinstance(number, (int, float)) or not limits["min"] <= number <= limits["max"]:
                issues.append("PARAMETER_OUT_OF_BOUNDS")
    material_incoming = Counter()
    material_outgoing = Counter()
    taps = []
    normalized_edges = set()
    for link in links:
        if set(link) != {"from", "to", "adapter"}:
            issues.append("LINK_SCHEMA")
            continue
        try:
            src_id, src_port = link["from"].split(".")
            dst_id, dst_port = link["to"].split(".")
            if src_id not in imap or dst_id not in imap:
                raise ValueError("UNKNOWN_INSTANCE")
            src_type, src_direction = port_type(imap[src_id], src_port, entries)
            dst_type, dst_direction = port_type(imap[dst_id], dst_port, entries)
        except (ValueError, KeyError, AttributeError):
            issues.append("BAD_LINK_ENDPOINT")
            continue
        if src_direction != "out" or dst_direction != "in":
            issues.append("WRONG_DIRECTION")
        adapter = link["adapter"]
        if src_type != dst_type:
            # An observational tap cannot create a material flow or transform arbitrary types.
            declared = [a for a in catalog["adapters"] if a["id"] == adapter]
            if len(declared) != 1 or src_type != declared[0]["from"] or dst_type != declared[0]["to"]:
                issues.append("TYPE_MISMATCH")
        elif adapter is not None:
            issues.append("SPURIOUS_ADAPTER")
        key = (link["from"], link["to"], adapter)
        if key in normalized_edges:
            issues.append("DUPLICATE_LINK")
        normalized_edges.add(key)
        if src_type.startswith("FLOW<") and dst_type.startswith("FLOW<") and adapter is None:
            material_outgoing[src_id] += 1
            material_incoming[dst_id] += 1
        if adapter is not None:
            taps.append((src_id, dst_id))
    for ins in instances:
        role = ins.get("role")
        node = ins["id"]
        if role != "source" and role != "report" and material_incoming[node] != 1:
            issues.append("MATERIAL_IN_DEGREE:" + node)
        if role not in ("receipt", "report") and material_outgoing[node] != 1:
            issues.append("MATERIAL_OUT_DEGREE:" + node)
        if role in ("receipt", "report") and material_outgoing[node]:
            issues.append("MATERIAL_AFTER_TERMINAL")
    if roles["report"] == 1 and len(taps) != 1:
        issues.append("REPORT_TAP_COUNT")
    if roles["report"] == 0 and taps:
        issues.append("UNNECESSARY_TAP")
    # Verify that the rate signal comes from the same physical flow received at the terminal.
    if taps:
        receipt_id = next((i["id"] for i in instances if i.get("role") == "receipt"), None)
        terminal_sources = {l["from"].split(".")[0] for l in links
                            if l.get("to", "") == str(receipt_id) + ".arrival" and l.get("adapter") is None}
        if taps[0][0] not in terminal_sources or imap[taps[0][1]]["role"] != "report":
            issues.append("REPORT_NOT_TAPPED_AT_RECEIPT")
    return sorted(set(issues))


def canonical(graph):
    """Canonical typed edge signature ignoring instance names. Small E0 universe only."""
    inst = graph["instances"]
    groups = defaultdict(list)
    for x in inst:
        groups[(x["class_id"], x["role"])].append(x["id"])
    keys = sorted(groups)
    options = [list(itertools.permutations(sorted(groups[k]))) for k in keys]
    serializations = []
    for combination in itertools.product(*options):
        names = {}
        for key, group in zip(keys, combination):
            for j, original in enumerate(group):
                names[original] = str(keys.index(key)) + ":" + str(j)
        edges = sorted((names[a["from"].split(".")[0]], a["from"].split(".")[1],
                        names[a["to"].split(".")[0]], a["to"].split(".")[1], a["adapter"] or "")
                       for a in graph["links"])
        nodes = sorted((x["class_id"], x["role"]) for x in inst)
        serializations.append(json.dumps({"nodes":nodes,"edges":edges},sort_keys=True))
    return hashlib.sha256(min(serializations).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    c, p = load_contracts()
    result = {"status":"PASS" if not validate_contracts(c,p) else "FAIL",
              "issues":validate_contracts(c,p),
              "verdict":"ENGINEERING_ONLY",
              "causal_identification":"NOT_RUN"}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result["issues"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
