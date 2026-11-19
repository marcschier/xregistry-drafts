#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate and execute representative examples of spec section 5.5.

The cases cover the Incremental version profile: assignment, compatibility
lines, live selection, raw exact replay and snapshot-bound composition. A
SemVer target delegates to check_vectors so the uav:minVersion alternative
uses the existing SemVer resolver.
"""

import json
import re
import sys
from pathlib import Path

try:
    from . import check_vectors
except ImportError:  # executed as a script
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import check_vectors

HERE = Path(__file__).resolve().parent
ORIGIN = check_vectors.ORIGIN
OutcomeError = check_vectors.OutcomeError
REVISION = re.compile(r"[1-9][0-9]*", re.ASCII)
ABSOLUTE_IRI = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:[^\s#<>\"{}|\\^`]+")
LINE = "uav:compatibilityLine"
FLOOR = "uav:minVersion"
LEGACY = ("tm:minVersion", "td:minVersion")
TD_KINDS = check_vectors.TD_REFERENCE_KINDS


def revision_key(text):
    """Order canonical decimal strings as integers without conversion."""
    return (len(text), text)


def check_line(value):
    if not isinstance(value, str) or not ABSOLUTE_IRI.fullmatch(value):
        raise OutcomeError("invalid-line")
    return value


def incremental_requirement(requirements):
    """Validate a reference requirement for an Incremental target (5.5.4)."""
    if any(term in requirements for term in LEGACY):
        raise OutcomeError("invalid-floor")
    if LINE not in requirements:
        raise OutcomeError("compatibility-required")
    line = check_line(requirements[LINE])
    floor = requirements.get(FLOOR)
    if floor is not None and not REVISION.fullmatch(floor):
        raise OutcomeError("invalid-version")
    return line, floor


def satisfies(version, line, floor):
    if version.get("compatibilityline") != line:
        return False
    return floor is None or revision_key(version["versionid"]) >= revision_key(floor)


def resource_for(case, target):
    matches = [r for r in case["registry"] if r["wotid"] == target]
    if not matches:
        raise OutcomeError("not-found")
    if len(matches) != 1:
        raise ValueError("vectors must scope each wotid to one Resource")
    resource = matches[0]
    if case["profile"] == "incremental":
        for version in resource["versions"]:
            if not REVISION.fullmatch(version["versionid"]):
                raise ValueError("stored Incremental Versions use canonical revisions")
    return resource


def result(resource, version, profile):
    output = {
        "wotid": resource["wotid"],
        "versionid": version["versionid"],
        "contentdigest": version["contentdigest"],
        "versionprofile": profile,
        "origin": ORIGIN,
    }
    if "compatibilityline" in version:
        output["compatibilityline"] = version["compatibilityline"]
    return output


def semver_live(case):
    """Map uav:minVersion onto the SemVer resolver of Sections 5.4.1-5.4.2."""
    reference = case["reference"]
    requirements = reference.get("requirements", {})
    if LINE in requirements:
        raise OutcomeError("invalid-line")
    legacy = [term for term in LEGACY if term in requirements]
    if FLOOR in requirements and legacy:
        raise OutcomeError("invalid-floor")
    projected = {"kind": reference["kind"], "target": reference["target"]}
    if FLOOR in requirements:
        projected["minVersion"] = requirements[FLOOR]
        projected["floorTerm"] = (
            "td:minVersion" if reference["kind"] in TD_KINDS else "tm:minVersion"
        )
    elif legacy:
        projected["minVersion"] = requirements[legacy[0]]
        projected["floorTerm"] = legacy[0]
    semver_case = {"registry": case["registry"], "reference": projected}
    selected = check_vectors.resolve(semver_case)
    selected.pop("origin")
    resource = resource_for(case, reference["target"])
    version = next(v for v in resource["versions"] if v["versionid"] == selected["versionid"])
    return result(resource, version, "semver")


def live(case):
    if case["profile"] == "unknown":
        raise OutcomeError("unknown-profile")
    if case["profile"] == "semver":
        return semver_live(case)
    reference = case["reference"]
    resource = resource_for(case, reference["target"])
    line, floor = incremental_requirement(reference.get("requirements", {}))
    versions = resource["versions"]
    if resource["defaultversionsticky"]:
        selected = next(
            (v for v in versions if v["versionid"] == resource["defaultversionid"]), None
        )
        if selected is None:
            raise OutcomeError("not-found")
        if not satisfies(selected, line, floor):
            raise OutcomeError("unsatisfied")
        return result(resource, selected, "incremental")
    eligible = [v for v in versions if satisfies(v, line, floor)]
    if not eligible:
        raise OutcomeError("unsatisfied")
    selected = max(eligible, key=lambda v: revision_key(v["versionid"]))
    return result(resource, selected, "incremental")


def replay(case):
    """Raw exact replay: identity and bytes only, no requirement check."""
    if case["profile"] != "incremental":
        raise ValueError("replay vectors cover the Incremental profile")
    resource = resource_for(case, case["reference"]["target"])
    pin = case["pin"]
    if "digest" in pin:
        matches = [v for v in resource["versions"] if v["contentdigest"] == pin["digest"]]
        if not matches:
            raise OutcomeError("pin-mismatch")
        selected = max(matches, key=lambda v: revision_key(v["versionid"]))
    else:
        selected = next(
            (v for v in resource["versions"] if v["versionid"] == pin["versionid"]), None
        )
        if selected is None:
            raise OutcomeError("not-found")
    return result(resource, selected, "incremental")


def compose(case):
    """Snapshot-bound composition: exact binding first, then requirements."""
    if case["profile"] != "incremental":
        raise ValueError("composition vectors cover the Incremental profile")
    reference = case["reference"]
    binding = case.get("binding")
    if binding is None:
        raise OutcomeError("closure-incomplete")
    matches = [r for r in case["registry"] if r["wotid"] == reference["target"]]
    if len(matches) != 1:
        raise OutcomeError("closure-incomplete")
    resource = resource_for(case, reference["target"])
    selected = next(
        (v for v in resource["versions"] if v["versionid"] == binding["versionid"]), None
    )
    if selected is None or selected["contentdigest"] != binding["contentdigest"]:
        raise OutcomeError("closure-incomplete")
    line, floor = incremental_requirement(reference.get("requirements", {}))
    if not satisfies(selected, line, floor):
        raise OutcomeError("unsatisfied")
    return result(resource, selected, "incremental")


def local(case):
    """A document-local reference checks the containing exact Version."""
    if case["profile"] != "incremental":
        raise ValueError("local vectors cover the Incremental profile")
    reference = case["reference"]
    if reference["kind"] not in ("ref", "td-ref"):
        raise ValueError("a local reference is a tm:ref or td:ref")
    resource = resource_for(case, reference["target"])
    selected = next(
        (v for v in resource["versions"] if v["versionid"] == case["document"]["versionid"]),
        None,
    )
    if selected is None:
        raise ValueError("the containing revision must be a stored Version")
    line, floor = incremental_requirement(reference.get("requirements", {}))
    if not satisfies(selected, line, floor):
        raise OutcomeError("unsatisfied")
    return result(resource, selected, "incremental")


def publish(case):
    """Assign an Incremental revision, its line and its ancestor (5.5.2-5.5.3)."""
    operation = case["publish"]
    root_line = operation.get("rootLine")
    metadata_line = operation.get("metadataLine")
    if case["profile"] == "semver":
        if root_line is not None:
            raise OutcomeError("invalid-line")
        raise ValueError("SemVer publication is covered by vectors.json")
    resource = resource_for(case, operation["target"])
    for value in (root_line, metadata_line):
        if value is not None:
            check_line(value)
    if root_line is not None and metadata_line is not None and root_line != metadata_line:
        raise OutcomeError("inconsistent-publication")
    line = root_line if root_line is not None else metadata_line
    supplied = operation.get("versionid")
    if supplied is not None and (not REVISION.fullmatch(supplied) or len(supplied) > 128):
        raise OutcomeError("invalid-version")
    mark = resource["highwatermark"]
    authored = operation.get("version")
    if authored is not None and REVISION.fullmatch(authored):
        if len(authored) > 128:
            raise OutcomeError("invalid-version")
        if revision_key(authored) <= revision_key(mark):
            raise OutcomeError("version-mismatch")
        assigned, origin = authored, "authored"
    else:
        assigned, origin = str(int(mark) + 1), "generated"
    if supplied is not None and supplied != assigned:
        raise OutcomeError("version-mismatch")
    existing = [v["versionid"] for v in resource["versions"]]
    ancestor = max(existing, key=revision_key) if existing else assigned
    supplied_ancestor = operation.get("ancestorid")
    if supplied_ancestor is not None and supplied_ancestor != ancestor:
        raise OutcomeError("version-mismatch")
    assigned_record = {
        "versionid": assigned,
        "versionorigin": origin,
        "ancestorid": ancestor,
        "highwatermark": assigned,
    }
    if line is not None:
        assigned_record["compatibilityline"] = line
    return {"assigned": assigned_record}


def update(case):
    """A Version's line is fixed at creation, including absence."""
    operation = case["update"]
    resource = resource_for(case, operation["target"])
    version = next(v for v in resource["versions"] if v["versionid"] == operation["versionid"])
    requested = operation.get("compatibilityline")
    if requested is not None:
        check_line(requested)
    if requested != version.get("compatibilityline"):
        raise OutcomeError("inconsistent-publication")
    return {"updated": {"versionid": version["versionid"]}}


OPERATIONS = {
    "live": live,
    "replay": replay,
    "compose": compose,
    "local": local,
    "publish": publish,
    "update": update,
}


def load_vectors():
    cases = json.loads(
        (HERE / "incremental.json").read_text(encoding="utf-8"),
        object_pairs_hook=check_vectors._unique_object,
    )
    if not isinstance(cases, dict) or not cases:
        raise ValueError("expected a nonempty vector collection")
    return cases


def check_case(name, case):
    try:
        actual = OPERATIONS[case["operation"]](case)
        if "origin" in actual:
            if actual.pop("origin") != ORIGIN:
                raise AssertionError("resolver omitted registry origin")
            actual = {"result": actual}
    except OutcomeError as error:
        actual = {"error": str(error)}
    if actual != case["expect"]:
        raise AssertionError(f"{name}: expected {case['expect']}, got {actual}")


def main():
    cases = load_vectors()
    schema = json.loads((HERE / "incremental.schema.json").read_text(encoding="utf-8"))
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("SKIP JSON Schema validation (jsonschema is unavailable)")
    else:
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(cases)
        print("PASS JSON Schema definition (validation enabled)")
    for name, case in sorted(cases.items()):
        check_case(name, case)
        print(f"PASS {name}")
    print(f"PASS {len(cases)} vectors")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError) as error:
        print(f"FAIL {error}")
        sys.exit(1)
