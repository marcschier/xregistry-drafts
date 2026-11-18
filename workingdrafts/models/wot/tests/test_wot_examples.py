"""Representative resolution cases and proposed closure-shape examples."""

from copy import deepcopy
import json
from pathlib import Path
import re
from urllib.parse import unquote, urldefrag, urljoin, urlsplit

import jsonschema
import pytest

from workingdrafts.models.wot.tests.resolution import check_vectors

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "publication-closure.schema.json").read_text())
EXAMPLE = json.loads((ROOT / "samples" / "publication-closure.json").read_text())
VECTORS = check_vectors.load_vectors()
VECTOR_SCHEMA = json.loads((check_vectors.HERE / "schema.json").read_bytes())
PROFILE_SCHEMA = json.loads(
    (ROOT / "schemas" / "descriptor-profile.schema.json").read_bytes()
)
SUBJECT_DESCRIPTOR = json.loads(
    (ROOT / "samples" / "subject-descriptor.json").read_bytes()
)


@pytest.mark.parametrize("name", VECTORS)
def test_resolution_vector(name):
    jsonschema.validate({name: VECTORS[name]}, VECTOR_SCHEMA)
    check_vectors.check_case(name, VECTORS[name])


def test_long_semver_floor_is_not_limited_by_core_identifier_length():
    target = "urn:example:pump:v1"
    digest = "sha256:" + "0" * 64
    floor = "1.0.0-" + "a" * 123
    assert len(floor) > 128

    check_vectors.check_case(
        "long-semver-floor",
        {
            "registry": [
                {
                    "wotid": target,
                    "defaultversionsticky": False,
                    "defaultversionid": "1.0.0",
                    "versions": [
                        {
                            "versionid": "1.0.0",
                            "versionorigin": "authored",
                            "contentdigest": digest,
                        }
                    ],
                }
            ],
            "reference": {
                "kind": "ref",
                "target": target,
                "minVersion": floor,
            },
            "expect": {
                "result": {
                    "wotid": target,
                    "versionid": "1.0.0",
                    "contentdigest": digest,
                }
            },
        },
    )


def test_long_implicit_semver_floor_is_not_limited_by_core_identifier_length():
    target = "urn:example:pump-model:v1"
    digest = "sha256:" + "0" * 64
    floor = "1.0.0-" + "a" * 123
    assert len(floor) == 129

    check_vectors.check_case(
        "long-implicit-semver-floor",
        {
            "registry": [
                {
                    "wotid": target,
                    "defaultversionsticky": False,
                    "defaultversionid": "1.0.0",
                    "versions": [
                        {
                            "versionid": "1.0.0",
                            "versionorigin": "authored",
                            "contentdigest": digest,
                        }
                    ],
                }
            ],
            "reference": {
                "kind": "type",
                "target": target,
            },
            "document": {
                "version.model": floor,
                "typeLinks": [{"target": target}],
            },
            "expect": {
                "result": {
                    "wotid": target,
                    "versionid": "1.0.0",
                    "contentdigest": digest,
                }
            },
        },
    )


def test_huge_implicit_semver_floor_with_no_matching_version_is_unsatisfied():
    target = "urn:example:pump-model:v1"
    floor = "9" * 5000 + ".0.0"

    check_vectors.check_case(
        "huge-implicit-semver-floor",
        {
            "registry": [
                {
                    "wotid": target,
                    "defaultversionsticky": False,
                    "defaultversionid": "1.0.0",
                    "versions": [
                        {
                            "versionid": "1.0.0",
                            "versionorigin": "authored",
                            "contentdigest": "sha256:" + "0" * 64,
                        }
                    ],
                }
            ],
            "reference": {
                "kind": "type",
                "target": target,
            },
            "document": {
                "version.model": floor,
                "typeLinks": [{"target": target}],
            },
            "expect": {"error": "unsatisfied"},
        },
    )


def test_authored_semver_version_id_remains_core_length_limited():
    target = "urn:example:pump:v1"
    version = "1.0.0-" + "a" * 123

    check_vectors.check_case(
        "long-authored-version",
        {
            "registry": [
                {
                    "wotid": target,
                    "defaultversionsticky": False,
                    "defaultversionid": None,
                    "versions": [],
                }
            ],
            "publish": {
                "target": target,
                "version.model": version,
            },
            "expect": {"error": "invalid-version"},
        },
    )


def test_large_semver_major_compares_without_integer_conversion_limit():
    floor = check_vectors.Version("9" * 5000 + ".0.0")
    candidate = check_vectors.Version("1.0.0")

    assert candidate < floor


def test_proposed_closure_shape():
    jsonschema.Draft202012Validator.check_schema(SCHEMA)
    jsonschema.validate(EXAMPLE, SCHEMA)


def test_closure_shape_preserves_empty_external_reference_href():
    source_uri = "https://models.example.test/source.json"
    link = {
        "rel": "tm:extends",
        "href": "",
        "@context": {"@base": "https://models.example.test/target.json"},
    }
    resolved = urljoin(link["@context"]["@base"], link["href"])
    assert resolved == "https://models.example.test/target.json"
    assert resolved != source_uri

    example = deepcopy(EXAMPLE)
    binding = example["bindings"][0]
    binding["pointer"] = "/links/0"
    binding["operator"] = link["rel"]
    binding["href"] = link["href"]
    jsonschema.validate(example, SCHEMA)
    assert json.loads(json.dumps(example))["bindings"][0]["href"] == ""


@pytest.mark.parametrize("href", [None, 0, [], {}])
def test_closure_shape_still_requires_a_string_href(href):
    example = deepcopy(EXAMPLE)
    example["bindings"][0]["href"] = href
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(example, SCHEMA)


def test_closure_shape_still_requires_the_href_member():
    example = deepcopy(EXAMPLE)
    del example["bindings"][0]["href"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(example, SCHEMA)


def _classify_captured_reference(href, base, operator, identities):
    resolved = urldefrag(urljoin(base, href)).url
    matches = {
        (identity["kind"], identity["resource"], identity.get("version"))
        for identity in identities
        if identity["identity_type"] in {"wotid", "base", "document-view"}
        and identity["uri"] == resolved
    }
    if len(matches) != 1:
        raise ValueError("The captured URI identity is missing or ambiguous.")

    kind, resource, version = matches.pop()
    if operator in {"tm:ref", "describedby"} and kind == "schema":
        return "outside-profile", resource, version
    expected_kind = {
        "tm:ref": "thingmodel",
        "td:ref": "thingdescription",
        "type": "thingmodel",
        "describedby": "schema",
    }.get(operator)
    if expected_kind is None or kind != expected_kind:
        raise ValueError("The captured Resource kind does not match the operator.")
    return "dependency", resource, version


def test_closure_identity_classifies_tm_reference_from_wotid_without_binding():
    identities = [
        {
            "uri": "urn:example:pump-model:v1",
            "identity_type": "wotid",
            "kind": "thingmodel",
            "resource": "/thingmodelgroups/acme/thingmodels/pump",
        }
    ]

    result = _classify_captured_reference(
        "urn:example:pump-model:v1",
        "https://registry.example/thingmodels/source",
        "tm:ref",
        identities,
    )

    assert result == (
        "dependency",
        "/thingmodelgroups/acme/thingmodels/pump",
        None,
    )


def test_closure_identity_excludes_schema_reference_before_binding():
    href = (
        "../../schemagroups/acme/schemas/temperature/versions/1"
        "#/properties/value"
    )
    identities = [
        {
            "uri": (
                "https://registry.example/schemagroups/acme/schemas/"
                "temperature/versions/1"
            ),
            "identity_type": "document-view",
            "kind": "schema",
            "resource": "/schemagroups/acme/schemas/temperature",
            "version": "/schemagroups/acme/schemas/temperature/versions/1",
        }
    ]

    result = _classify_captured_reference(
        href,
        "https://registry.example/thingmodels/pump/v1",
        "tm:ref",
        identities,
    )

    assert result == (
        "outside-profile",
        "/schemagroups/acme/schemas/temperature",
        "/schemagroups/acme/schemas/temperature/versions/1",
    )
    assert href == (
        "../../schemagroups/acme/schemas/temperature/versions/1"
        "#/properties/value"
    )


def test_closure_identity_excludes_describedby_schema_link():
    uri = "https://registry.example/schemas/temperature/versions/1"
    identities = [
        {
            "uri": uri,
            "identity_type": "document-view",
            "kind": "schema",
            "resource": "/schemagroups/acme/schemas/temperature",
            "version": "/schemagroups/acme/schemas/temperature/versions/1",
        }
    ]

    result = _classify_captured_reference(
        uri,
        "https://registry.example/things/oven",
        "describedby",
        identities,
    )

    assert result == (
        "outside-profile",
        "/schemagroups/acme/schemas/temperature",
        "/schemagroups/acme/schemas/temperature/versions/1",
    )


def test_closure_identity_resolves_type_link_through_captured_view_url():
    uri = "https://registry.example/thingmodels/pump/versions/2"
    identities = [
        {
            "uri": uri,
            "identity_type": "document-view",
            "kind": "thingmodel",
            "resource": "/thingmodelgroups/acme/thingmodels/pump",
            "version": "/thingmodelgroups/acme/thingmodels/pump/versions/2",
        }
    ]

    result = _classify_captured_reference(
        uri + "#/properties/speed",
        "https://registry.example/things/oven",
        "type",
        identities,
    )

    assert result == (
        "dependency",
        "/thingmodelgroups/acme/thingmodels/pump",
        "/thingmodelgroups/acme/thingmodels/pump/versions/2",
    )


@pytest.mark.parametrize(
    "identities",
    [
        [],
        [
            {
                "uri": "https://registry.example/shared",
                "identity_type": "wotid",
                "kind": "thingmodel",
                "resource": "/thingmodelgroups/acme/thingmodels/pump",
            },
            {
                "uri": "https://registry.example/shared",
                "identity_type": "document-view",
                "kind": "schema",
                "resource": "/schemagroups/acme/schemas/pump",
            },
        ],
        [
            {
                "uri": "https://registry.example/shared",
                "identity_type": "document-view",
                "kind": "thingmodel",
                "resource": "/thingmodelgroups/acme/thingmodels/pump",
                "version": "/thingmodelgroups/acme/thingmodels/pump/versions/1",
            },
            {
                "uri": "https://registry.example/shared",
                "identity_type": "document-view",
                "kind": "thingmodel",
                "resource": "/thingmodelgroups/acme/thingmodels/pump",
                "version": "/thingmodelgroups/acme/thingmodels/pump/versions/2",
            },
        ],
    ],
)
def test_closure_identity_rejects_missing_or_ambiguous_mappings(identities):
    with pytest.raises(ValueError):
        _classify_captured_reference(
            "https://registry.example/shared",
            "https://registry.example/thingmodels/source",
            "tm:ref",
            identities,
        )


def test_duplicate_identity_records_for_the_same_target_are_not_ambiguous():
    identity = {
        "uri": "urn:example:pump-model:v1",
        "identity_type": "wotid",
        "kind": "thingmodel",
        "resource": "/thingmodelgroups/acme/thingmodels/pump",
    }

    result = _classify_captured_reference(
        identity["uri"],
        "https://registry.example/thingmodels/source",
        "tm:ref",
        [identity, identity.copy()],
    )

    assert result == (
        "dependency",
        "/thingmodelgroups/acme/thingmodels/pump",
        None,
    )


def test_closure_identity_does_not_match_origin_registry_provenance():
    identity = {
        "uri": "https://registry.example/shared",
        "identity_type": "originRegistry",
        "kind": "thingmodel",
        "resource": "/thingmodelgroups/acme/thingmodels/pump",
    }

    with pytest.raises(ValueError):
        _classify_captured_reference(
            identity["uri"],
            "https://registry.example/thingmodels/source",
            "tm:ref",
            [identity],
        )


@pytest.mark.parametrize(
    "operator",
    [
        "tm:extends",
        "tm:submodel",
        "tm:ref",
        "td:extends",
        "td:subthing",
        "td:ref",
        "type",
        "https://raw.githubusercontent.com/marcschier/wot-thing-description/"
        "main/proposals/wot-projections/context.experimental-v1.jsonld#projects",
    ],
)
def test_closure_shape_accepts_canonical_operator_strings(operator):
    example = deepcopy(EXAMPLE)
    example["bindings"][0]["operator"] = operator
    jsonschema.validate(example, SCHEMA)


@pytest.mark.parametrize(
    "operator",
    [
        "",
        None,
        ["type"],
        "TYPE",
        "@type",
        "td:type",
        "model:ref",
        "https://www.w3.org/2019/wot/tm#ref",
        "https://www.w3.org/2019/wot/td#type",
        "wotproj:projects",
        "https://example.org/wot/projection#projects",
    ],
)
def test_closure_shape_rejects_noncanonical_operator_strings(operator):
    example = deepcopy(EXAMPLE)
    example["bindings"][0]["operator"] = operator
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(example, SCHEMA)


@pytest.mark.parametrize("pointer", ["links/0"])
def test_invalid_json_pointer_rejected(pointer):
    example = deepcopy(EXAMPLE)
    example["bindings"][0]["pointer"] = pointer
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(example, SCHEMA)


def test_missing_exact_target_rejected():
    example = deepcopy(EXAMPLE)
    del example["bindings"][0]["target"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(example, SCHEMA)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("entries", "/thingmodelgroups/acme/thingmodels/pump"),
        ("source", "urn:example:pump:v1"),
        ("target", "https://example.test/thingmodels/base"),
    ],
)
def test_closure_requires_exact_version_xids(field, value):
    example = deepcopy(EXAMPLE)
    if field == "entries":
        example[field][0] = value
    else:
        example["bindings"][0][field] = value

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(example, SCHEMA)


@pytest.mark.parametrize(
    ("index", "expected_source", "expected_version", "expected_fragment"),
    [
        (
            0,
            "https://factory.example.com/line1",
            "1.0.0",
            "/events/overheated",
        ),
        (
            1,
            "urn:fabrikam:actor:telemetry-service",
            None,
            "",
        ),
    ],
    ids=["direct-version-affordance", "direct-default-whole-thing"],
)
def test_cloudevents_source_and_subject_match_lamp_td(
    index,
    expected_source,
    expected_version,
    expected_fragment,
):
    events = json.loads((ROOT / "samples" / "cloudevents.json").read_bytes())
    assert len(events) == 5
    event = events[index]
    assert set(event) == {
        "specversion",
        "id",
        "source",
        "type",
        "subject",
        "datacontenttype",
        "data",
    }
    assert event["specversion"] == "1.0"
    assert event["id"] == f"lamp-42-overheated-{index + 1}"
    assert event["type"] == "com.fabrikam.lamp.overheated.v1"
    assert re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+",
        event["type"],
    )
    assert re.fullmatch(r"v[1-9][0-9]*", event["type"].rsplit(".", 1)[-1])
    assert events[0]["type"] == events[1]["type"]
    assert set(event["data"]) == {"temperature"}
    assert type(event["data"]["temperature"]) is int
    assert event["datacontenttype"] == "application/json"

    assert event["source"] == expected_source
    prefix, delimiter, fragment = event["subject"].partition("#")
    assert delimiter == "#"
    subject_url = urlsplit(prefix)
    assert (subject_url.scheme, subject_url.netloc) == ("https", "example.com")
    assert subject_url.query == subject_url.fragment == ""
    resource_path = (
        "/thingdescriptiongroups/Fabrikam.FactoryFloor.01/"
        "thingdescriptions/urn.fabrikam.lamp.42"
    )
    assert subject_url.path == resource_path + (
        f"/versions/{expected_version}" if expected_version else ""
    )
    assert fragment == expected_fragment

    registry = json.loads((ROOT / "samples" / "registry.json").read_bytes())
    resources = registry["thingdescriptiongroups"]["Fabrikam.FactoryFloor.01"][
        "thingdescriptions"
    ]
    resource = resources[subject_url.path.split("/")[4]]
    td = resource["thingdescription"]
    assert td["id"] == resource["wotid"] == "urn:fabrikam:lamp:42"
    assert resource["versionid"] == td["version"]["instance"] == "1.0.0"
    if expected_version:
        assert expected_version == resource["versionid"]

    selected = td
    pointer = unquote(fragment)
    for token in pointer.split("/")[1:]:
        selected = selected[token.replace("~1", "/").replace("~0", "~")]
    if index == 0:
        assert selected is td["events"]["overheated"]
    else:
        assert selected is td
    jsonschema.validate(event["data"], td["events"]["overheated"]["data"])


@pytest.mark.parametrize("index", [2, 3, 4], ids=["subject", "describedby", "source"])
def test_descriptor_event_routes_select_sample_lamp_td(index):
    events = json.loads((ROOT / "samples" / "cloudevents.json").read_bytes())
    event = events[index]
    descriptor_url = (
        "https://example.com/descriptorgroups/subjects/descriptors/"
        "lamp-42-temperature/versions/1"
    )
    reference = SUBJECT_DESCRIPTOR["references"]["lamp42"]
    assert event["id"] == f"lamp-42-overheated-{index + 1}"
    assert event["type"] == events[0]["type"]
    if index == 2:
        assert event["subject"] == descriptor_url
        assert "describedby" not in event
        assert event["source"] == "urn:fabrikam:actor:telemetry-service"
        assert SUBJECT_DESCRIPTOR["thingref"] == "lamp42"
        pointer = SUBJECT_DESCRIPTOR["affordanceselector"]["pointer"]
    elif index == 3:
        assert event["describedby"] == descriptor_url
        assert event["source"] == "urn:fabrikam:actor:telemetry-service"
        url, delimiter, pointer = event["subject"].partition("#")
        assert delimiter == "#"
        matches = [
            item for item in SUBJECT_DESCRIPTOR["references"].values()
            if item["class"] == "https://xregistry.io/classes/thingdescription"
            and item["url"] == url
        ]
        assert matches == [reference]
    else:
        assert event["source"] == descriptor_url
        assert "describedby" not in event
        name, delimiter, pointer = event["subject"].partition("#")
        assert delimiter == "#"
        assert SUBJECT_DESCRIPTOR["references"][name] is reference
    assert pointer == "/events/overheated"
    assert reference["class"] == "https://xregistry.io/classes/thingdescription"
    registry = json.loads((ROOT / "samples" / "registry.json").read_bytes())
    path = urlsplit(reference["url"]).path.split("/")
    resource = registry[path[1]][path[2]][path[3]][path[4]]
    assert path[5:] == ["versions", resource["versionid"]]
    td = resource["thingdescription"]
    selected = td
    for token in pointer.split("/")[1:]:
        selected = selected[token.replace("~1", "/").replace("~0", "~")]
    assert selected is td["events"]["overheated"]
    jsonschema.validate(event["data"], selected["data"])


def test_subject_descriptor_sample_selects_lamp_affordance():
    jsonschema.Draft202012Validator.check_schema(PROFILE_SCHEMA)
    schema = {**PROFILE_SCHEMA, "$ref": "#/$defs/subjectDescriptor"}
    jsonschema.validate(SUBJECT_DESCRIPTOR, schema)
    selector = SUBJECT_DESCRIPTOR["affordanceselector"]
    reference = SUBJECT_DESCRIPTOR["references"][SUBJECT_DESCRIPTOR["thingref"]]
    jsonschema.validate(
        reference, {**PROFILE_SCHEMA, "$ref": "#/$defs/tdReference"}
    )
    registry = json.loads((ROOT / "samples" / "registry.json").read_bytes())
    path = urlsplit(reference["url"]).path.split("/")
    resource = registry[path[1]][path[2]][path[3]][path[4]]
    assert path[5:] == ["versions", resource["versionid"]]
    td = resource["thingdescription"]
    selected = _select_sample_subject(SUBJECT_DESCRIPTOR, td)
    assert selected is td["events"]["overheated"]
    assert selector["quantitykind"] == "https://example.com/quantities/temperature"
    assert "quantitykind" not in SUBJECT_DESCRIPTOR


def _select_sample_subject(descriptor, td):
    jsonschema.validate(
        descriptor, {**PROFILE_SCHEMA, "$ref": "#/$defs/subjectDescriptor"}
    )
    reference = descriptor["references"][descriptor["thingref"]]
    jsonschema.validate(
        reference, {**PROFILE_SCHEMA, "$ref": "#/$defs/tdReference"}
    )
    if "affordanceselector" not in descriptor:
        return td
    category, name = descriptor["affordanceselector"]["pointer"].split("/")[1:]
    name = name.replace("~1", "/").replace("~0", "~")
    return td[category][name]


def test_omitted_affordance_selector_selects_whole_thing_with_descriptor_metadata():
    descriptor = deepcopy(SUBJECT_DESCRIPTOR)
    del descriptor["affordanceselector"]
    descriptor["description"] = "The whole lamp"
    td = {"title": "Lamp"}
    assert _select_sample_subject(descriptor, td) is td
    assert descriptor["description"] == "The whole lamp"


def test_pointer_outside_affordance_selector_does_not_select_an_affordance():
    descriptor = deepcopy(SUBJECT_DESCRIPTOR)
    del descriptor["affordanceselector"]
    descriptor["pointer"] = "/events/overheated"
    td = {"events": {"overheated": {}}}
    assert _select_sample_subject(descriptor, td) is td


@pytest.mark.parametrize(
    "pointer",
    ["/events/overheated", "/properties/pressure~1bar", "/actions/a~0b",
     "/properties/a%2Fb"],
)
def test_subject_pointer_schema_accepts_string_form(pointer):
    schema = {**PROFILE_SCHEMA, "$ref": "#/$defs/affordanceSelector"}
    jsonschema.validate({"pointer": pointer}, schema)


@pytest.mark.parametrize(
    "pointer",
    [None, 0, "", "/", "#", "#/events/overheated", "events/alarm",
     "/events", "/events/", "/events/a~2b", "/events/a~",
     "/events/overheated/data", "/title", "/links/0"],
)
def test_subject_pointer_schema_rejects_non_string_or_fragment_form(pointer):
    schema = {**PROFILE_SCHEMA, "$ref": "#/$defs/affordanceSelector"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"pointer": pointer}, schema)


@pytest.mark.parametrize("member", ["thingref", "pointer"])
def test_subject_descriptor_schema_requires_selector_members(member):
    descriptor = deepcopy(SUBJECT_DESCRIPTOR)
    if member == "thingref":
        del descriptor[member]
    else:
        del descriptor["affordanceselector"][member]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            descriptor, {**PROFILE_SCHEMA, "$ref": "#/$defs/subjectDescriptor"}
        )


@pytest.mark.parametrize("member", ["thingref", "affordanceselector", "pointer"])
def test_subject_descriptor_schema_rejects_null_selector_members(member):
    descriptor = deepcopy(SUBJECT_DESCRIPTOR)
    if member in {"thingref", "affordanceselector"}:
        descriptor[member] = None
    else:
        descriptor["affordanceselector"][member] = None
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            descriptor, {**PROFILE_SCHEMA, "$ref": "#/$defs/subjectDescriptor"}
        )


def test_old_wotsubject_is_rejected_only_for_subject_admission():
    descriptor = {"references": {}, "wotsubject": {"reference": "lamp42", "pointer": ""}}
    jsonschema.validate(descriptor, PROFILE_SCHEMA)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            descriptor, {**PROFILE_SCHEMA, "$ref": "#/$defs/subjectDescriptor"}
        )
    descriptor["thingref"] = "lamp42"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            descriptor, {**PROFILE_SCHEMA, "$ref": "#/$defs/subjectDescriptor"}
        )


@pytest.mark.parametrize(
    ("pointer", "expected"),
    [("/properties/a~1b", "slash"), ("/properties/a%2Fb", "percent"),
     ("/properties/a~0b", "tilde")],
)
def test_affordance_pointer_decodes_tokens_but_not_percent(pointer, expected):
    descriptor = deepcopy(SUBJECT_DESCRIPTOR)
    descriptor["affordanceselector"]["pointer"] = pointer
    td = {"properties": {"a/b": "slash", "a%2Fb": "percent", "a~b": "tilde"}}
    assert _select_sample_subject(descriptor, td) == expected


def test_affordance_pointer_requires_existing_member():
    descriptor = deepcopy(SUBJECT_DESCRIPTOR)
    with pytest.raises(KeyError):
        _select_sample_subject(descriptor, {"events": {"other": {}}})


@pytest.mark.parametrize("kind", ["properties", "actions", "events"])
def test_affordance_selector_selects_one_member_of_each_kind(kind):
    descriptor = deepcopy(SUBJECT_DESCRIPTOR)
    descriptor["affordanceselector"]["pointer"] = f"/{kind}/target"
    target = {"title": "Selected affordance"}
    td = {kind: {"target": target, "other": {}}}
    assert _select_sample_subject(descriptor, td) is target


@pytest.mark.parametrize("thingref", ["absent", None])
def test_subject_thingref_requires_exact_existing_reference(thingref):
    descriptor = deepcopy(SUBJECT_DESCRIPTOR)
    descriptor["thingref"] = thingref
    with pytest.raises((KeyError, jsonschema.ValidationError)):
        _select_sample_subject(descriptor, {})


def test_subject_thingref_cannot_select_a_thingmodel():
    descriptor = deepcopy(SUBJECT_DESCRIPTOR)
    descriptor["references"]["lamp42"]["class"] = "https://xregistry.io/classes/thingmodel"
    with pytest.raises(jsonschema.ValidationError):
        _select_sample_subject(descriptor, {})


@pytest.mark.parametrize("kind", ["thingdescription", "thingmodel"])
def test_wot_reference_schema_requires_owned_uri_class(kind):
    definition = "tdReference" if kind == "thingdescription" else "tmReference"
    schema = {**PROFILE_SCHEMA, "$ref": f"#/$defs/{definition}"}
    reference = {
        "class": f"https://xregistry.io/classes/{kind}",
        "url": "https://example.com/wot/versions/1",
        "planurl": "https://example.com/plans/versions/1",
    }
    jsonschema.validate(reference, schema)
    reference["class"] = kind
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(reference, schema)


def test_profile_schema_keeps_empty_base_inventory_valid():
    jsonschema.validate({"references": {}}, PROFILE_SCHEMA)


@pytest.mark.parametrize("reference_class", ["thingdescription", "thingmodel"])
def test_profile_schema_allows_unselected_unknown_bare_classes(reference_class):
    descriptor = deepcopy(SUBJECT_DESCRIPTOR)
    descriptor["references"]["other"] = {"class": reference_class}
    jsonschema.validate(descriptor, PROFILE_SCHEMA)
    schema = {"$defs": PROFILE_SCHEMA["$defs"], "$ref": "#/$defs/subjectDescriptor"}
    jsonschema.validate(descriptor, schema)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/%ZZ",
        "https://example.com/<plan>",
        "https://example.com/plan\n",
        "https://example.com/plan#fragment",
        "https://example.com:bad/plan",
        "https://example.com/a%2",
        "https://[2001:db8:::1]/plan",
        "https://example.com/a b",
    ],
)
@pytest.mark.parametrize("definition", ["tdReference", "tmReference"])
@pytest.mark.parametrize("attribute", ["url", "planurl"])
def test_wot_reference_schema_rejects_malformed_absolute_urls(
    url, definition, attribute
):
    kind = "thingdescription" if definition == "tdReference" else "thingmodel"
    reference = {
        "class": f"https://xregistry.io/classes/{kind}",
        "url": "https://example.com/td",
        attribute: url,
    }
    schema = {"$defs": PROFILE_SCHEMA["$defs"], "$ref": f"#/$defs/{definition}"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(reference, schema)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/a%2Fb?version=1",
        "https://[2001:db8::1]/plan",
        "https://[::ffff:192.0.2.1]/plan",
        "https://[v1.fe80::]/plan",
        "urn:example:plan",
        "mailto:person@example.com",
    ],
)
def test_wot_reference_schema_accepts_absolute_fragment_free_urls(url):
    schema = {"$defs": PROFILE_SCHEMA["$defs"], "$ref": "#/$defs/tdReference"}
    jsonschema.validate(
        {"class": "https://xregistry.io/classes/thingdescription", "url": url},
        schema,
    )


def test_direct_subject_descriptor_reference_applies_reference_constraints():
    descriptor = deepcopy(SUBJECT_DESCRIPTOR)
    descriptor["references"]["other"] = {
        "class": "schema",
        "planurl": "https://example.com/plan",
    }
    schema = {"$defs": PROFILE_SCHEMA["$defs"], "$ref": "#/$defs/subjectDescriptor"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(descriptor, schema)


@pytest.mark.parametrize(
    "schema",
    [
        PROFILE_SCHEMA,
        {"$defs": PROFILE_SCHEMA["$defs"], "$ref": "#/$defs/subjectDescriptor"},
    ],
    ids=["profile-root", "subject-descriptor"],
)
@pytest.mark.parametrize("planurl", ["https://example.com/%ZZ", "https://example.com/#fragment"])
def test_reference_map_rejects_malformed_plan_urls(schema, planurl):
    descriptor = deepcopy(SUBJECT_DESCRIPTOR)
    descriptor["references"]["other"] = {
        "class": "https://xregistry.io/classes/thingdescription",
        "planurl": planurl,
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(descriptor, schema)


@pytest.mark.parametrize(
    ("reference_class", "planurl"),
    [
        ("schema", "https://example.com/plan"),
        ("thingdescription", "https://example.com/plan"),
        ("https://xregistry.io/classes/thingdescription", "/plan"),
        ("https://xregistry.io/classes/thingmodel", "https://example.com/plan#"),
    ],
)
def test_profile_schema_restricts_planurl_to_wot_uri_classes_and_document_urls(
    reference_class, planurl
):
    descriptor = {
        "references": {"result": {"class": reference_class, "planurl": planurl}}
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(descriptor, PROFILE_SCHEMA)


def test_subject_attribute_model_fragment_uses_core_definitions():
    core_schema = json.loads(
        (ROOT.parents[2] / "core" / "model.schema.json").read_bytes()
    )
    fragment = json.loads((ROOT / "descriptor-profile.attributes.json").read_bytes())
    jsonschema.Draft7Validator(
        {**core_schema, "$ref": "#/definitions/AttributeDefinitions"}
    ).validate(fragment)
