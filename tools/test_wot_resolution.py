import copy
import hashlib
import json
from pathlib import Path

import jsonschema
import pytest
from jsonschema import Draft202012Validator, FormatChecker
from jsonpointer import resolve_pointer


ROOT = Path(__file__).parent.parent
WOT = ROOT / "workingdrafts" / "models" / "wot"
SCHEMAS = WOT / "schemas"
FIXTURES = WOT / "samples" / "resolution"
PROFILE = (
    "https://xregistry.io/workingdrafts/models/wot/"
    "profiles/reference-resolution/0.2"
)


def _read_json(path):
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _file_digest(path):
    return "sha-256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_descriptor_key(artifact):
    keys = (
        "digest",
        "mediaType",
        "documentUrl",
        "interpretationBase",
        "contextBindings",
    )
    descriptor = {key: artifact[key] for key in keys if key in artifact}
    if "registry" in artifact:
        descriptor["scopedRegistryIdentity"] = artifact["registry"]
    return json.dumps(
        descriptor, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _validate(instance, schema_path):
    schema = _read_json(schema_path)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(
        schema, format_checker=FormatChecker()
    ).validate(instance)


def _assert_local_schema_refs(schema):
    if isinstance(schema, dict):
        ref = schema.get("$ref")
        assert ref is None or ref.startswith("#/")
        for value in schema.values():
            _assert_local_schema_refs(value)
    elif isinstance(schema, list):
        for value in schema:
            _assert_local_schema_refs(value)


def _assert_resolution_evidence(policy, policy_bytes, record, retained_bytes):
    core = record["core"]
    artifacts = {item["artifactId"]: item for item in core["artifacts"]}
    root = artifacts[core["rootArtifact"]]
    assert root["digest"] == _file_digest_bytes(retained_bytes[core["rootArtifact"]])
    assert policy["rootDigest"] == root["digest"]
    assert core["policyDigest"] == _file_digest_bytes(policy_bytes)

    root_document = json.loads(retained_bytes[core["rootArtifact"]])
    occurrence_edges = {}
    for edge in core["edges"]:
        source_id = edge["from"]
        assert source_id in artifacts
        target_id = edge["to"]
        assert target_id in artifacts
        key = (source_id, edge["sourcePointer"], edge["role"])
        assert key not in occurrence_edges, f"conflicting occurrence mapping: {key}"
        occurrence_edges[key] = edge

    for edge in core["edges"]:
        source_document = json.loads(retained_bytes[edge["from"]])
        assert edge["authoredReference"] == resolve_pointer(
            source_document, edge["sourcePointer"]
        )

    for artifact_id, artifact in artifacts.items():
        assert artifact_id in retained_bytes, "missing retained artifact bytes"
        assert artifact["digest"] == _file_digest_bytes(retained_bytes[artifact_id])

    for rule in policy["rules"]:
        key = (core["rootArtifact"], rule["sourcePointer"], rule["role"])
        assert key in occurrence_edges, f"dangling policy occurrence: {key}"
        edge = occurrence_edges[key]
        assert edge["authoredReference"] == resolve_pointer(
            root_document, rule["sourcePointer"]
        )
        target = artifacts[edge["to"]]
        assert target["kind"] == rule["expectedKind"]
        assert target["identity"] == rule["expectedIdentity"]
        assert target["registry"]["origin"] == rule["resolver"]["registry"]
        assert target["registry"]["groupCollection"] == rule["resolver"][
            "groupCollection"
        ]
        assert target["registry"]["groupId"] == rule["resolver"]["groupId"]
        assert target["registry"]["resourceCollection"] == rule["resolver"][
            "resourceCollection"
        ]
        assert target["registry"]["resourceId"] == rule["resolver"]["resourceId"]
        assert edge["selection"] == rule["selection"]
        assert rule.get("expectedDigest") in (None, target["digest"])
        if rule["selection"]["mode"] == "exact":
            assert target["registry"]["versionId"] == rule["selection"][
                "versionId"
            ]

    for transformation in core["transformations"]:
        referenced = set(transformation["inputs"])
        referenced.add(transformation["output"])
        referenced.update(
            mapping["sourceArtifact"] for mapping in transformation["mappings"]
        )
        assert referenced <= artifacts.keys(), "missing retained transformation input"


def _assert_registry_attachments(version, policy_bytes, record_bytes, root_bytes):
    policy_attachment = version["resolutionpolicy"]
    record_attachment = version["resolutionrecords"][0]
    assert policy_attachment["digest"] == _file_digest_bytes(policy_bytes)
    assert record_attachment["digest"] == _file_digest_bytes(record_bytes)
    assert record_attachment["rootdigest"] == _file_digest_bytes(root_bytes)


def _evidence_fixture():
    policy_path = FIXTURES / "policy.json"
    record_path = FIXTURES / "record.json"
    return (
        _read_json(policy_path),
        policy_path.read_bytes(),
        _read_json(record_path),
        {
            "a0": (FIXTURES / "processing-config.json").read_bytes(),
            "a1": (FIXTURES / "controller-resolved.tm.json").read_bytes(),
            "a2": (FIXTURES / "controller.tm.json").read_bytes(),
            "a3": (FIXTURES / "sensors-v7.tm.json").read_bytes(),
        },
    )


def _file_digest_bytes(data):
    return "sha-256:" + hashlib.sha256(data).hexdigest()


def test_wot_model_uses_draft_03_and_defines_optional_version_metadata():
    model = _read_json(WOT / "model.json")
    resources = [
        model["groups"]["thingdescriptiongroups"]["resources"][
            "thingdescriptions"
        ],
        model["groups"]["thingmodelgroups"]["resources"]["thingmodels"],
    ]

    assert model["groups"]["thingdescriptiongroups"]["modelversion"] == "0.3"
    assert model["groups"]["thingmodelgroups"]["modelversion"] == "0.3"
    for resource in resources:
        assert resource["modelversion"] == "0.3"
        assert resource["modelcompatiblewith"] == (
            "https://xregistry.io/xreg/domains/wot/specs/model.json"
        )
        attributes = resource["attributes"]
        assert {
            "documentdigest",
            "documentbase",
            "resolutionpolicy",
            "resolutionrecords",
        } <= attributes.keys()
        assert attributes["documentdigest"]["readonly"] is True
        assert "matchversions" not in attributes["documentdigest"]
        assert "immutable" not in attributes["documentdigest"]
        assert attributes["documentbase"]["type"] == "uri"
        assert attributes["resolutionrecords"]["type"] == "array"


def test_wot_policy_fixture_binds_root_kind_identity_and_scoped_default():
    policy = _read_json(FIXTURES / "policy.json")
    _validate(policy, SCHEMAS / "resolution-policy.schema.json")

    assert policy["rootDigest"] == _file_digest(
        FIXTURES / "controller.tm.json"
    )
    rule = policy["rules"][0]
    assert rule["sourcePointer"] == "/properties/temperature/tm:ref"
    assert rule["expectedKind"] == "TM"
    assert rule["expectedIdentity"] == "urn:example:sensors:model"
    assert rule["resolver"]["registry"] == "https://registry.example"
    assert rule["resolver"]["groupId"] == "vendor"
    assert rule["resolver"]["resourceId"] == "sensors"
    assert rule["selection"] == {"mode": "registry-default"}


def test_wot_policy_schema_accepts_exact_version_selection():
    policy = _read_json(FIXTURES / "policy.json")
    policy["rules"][0]["selection"] = {
        "mode": "exact",
        "versionId": "7",
    }

    _validate(policy, SCHEMAS / "resolution-policy.schema.json")


def test_wot_resolution_schemas_compile_with_local_references_only():
    for schema_path in SCHEMAS.glob("*.schema.json"):
        schema = _read_json(schema_path)
        Draft202012Validator.check_schema(schema)
        _assert_local_schema_refs(schema)


def test_wot_semantic_contract_accepts_captured_resolution_evidence():
    policy, policy_bytes, record, retained_bytes = _evidence_fixture()

    _assert_resolution_evidence(policy, policy_bytes, record, retained_bytes)


def test_wot_policy_schema_rejects_exact_selection_without_version_id():
    policy = _read_json(FIXTURES / "policy.json")
    policy["rules"][0]["selection"] = {"mode": "exact"}

    with pytest.raises(jsonschema.ValidationError):
        _validate(policy, SCHEMAS / "resolution-policy.schema.json")


def test_wot_policy_schema_rejects_version_ids_outside_core_id_grammar():
    policy = _read_json(FIXTURES / "policy.json")
    policy["rules"][0]["selection"] = {
        "mode": "exact",
        "versionId": "bad/version",
    }

    with pytest.raises(jsonschema.ValidationError):
        _validate(policy, SCHEMAS / "resolution-policy.schema.json")


def test_wot_semantics_reject_conflicting_occurrence_mappings():
    policy, policy_bytes, record, retained_bytes = _evidence_fixture()
    conflicting_edge = copy.deepcopy(record["core"]["edges"][0])
    conflicting_edge["to"] = "a2"
    record["core"]["edges"].append(conflicting_edge)

    with pytest.raises(AssertionError, match="conflicting occurrence mapping"):
        _assert_resolution_evidence(policy, policy_bytes, record, retained_bytes)


def test_wot_semantics_reject_dangling_policy_occurrence_mapping():
    policy, policy_bytes, record, retained_bytes = _evidence_fixture()
    record["core"]["edges"].clear()

    with pytest.raises(AssertionError, match="dangling policy occurrence"):
        _assert_resolution_evidence(policy, policy_bytes, record, retained_bytes)


def test_wot_semantics_distinguish_nested_same_pointer_by_container_and_base():
    policy, policy_bytes, record, retained_bytes = _evidence_fixture()
    first_doc = json.dumps(
        {"properties": {"temperature": {"tm:ref": "urn:example:inner:model"}}}
    ).encode()
    second_doc = first_doc
    first = copy.deepcopy(record["core"]["artifacts"][2])
    first.update(
        artifactId="a4",
        digest=_file_digest_bytes(first_doc),
        documentUrl="https://registry-a.example/parent.tm.json",
        interpretationBase="https://registry-a.example/parent.tm.json",
    )
    second = copy.deepcopy(first)
    second.update(
        artifactId="a5",
        documentUrl="https://registry-b.example/parent.tm.json",
        interpretationBase="https://registry-b.example/parent.tm.json",
    )
    record["core"]["artifacts"].extend((first, second))
    retained_bytes.update({"a4": first_doc, "a5": second_doc})
    for source in ("a4", "a5"):
        record["core"]["edges"].append(
            {
                "from": source,
                "sourcePointer": "/properties/temperature/tm:ref",
                "authoredReference": "urn:example:inner:model",
                "role": "tm:ref",
                "selection": {"mode": "registry-default"},
                "to": "a3",
            }
        )

    _assert_resolution_evidence(policy, policy_bytes, record, retained_bytes)
    occurrence_keys = {
        (edge["from"], edge["sourcePointer"], edge["role"])
        for edge in record["core"]["edges"]
    }
    assert (
        "a4",
        "/properties/temperature/tm:ref",
        "tm:ref",
    ) in occurrence_keys
    assert (
        "a5",
        "/properties/temperature/tm:ref",
        "tm:ref",
    ) in occurrence_keys
    assert first["interpretationBase"] != second["interpretationBase"]


def test_wot_semantics_reject_changed_bytes_at_unchanged_version():
    policy, policy_bytes, record, retained_bytes = _evidence_fixture()
    retained_bytes["a3"] += b" "

    with pytest.raises(AssertionError):
        _assert_resolution_evidence(policy, policy_bytes, record, retained_bytes)


def test_wot_semantics_reject_wrong_scoped_identity():
    policy, policy_bytes, record, retained_bytes = _evidence_fixture()
    policy["rules"][0]["resolver"]["groupId"] = "another-vendor"
    policy_bytes = json.dumps(policy, indent=2).encode() + b"\n"
    record["core"]["policyDigest"] = _file_digest_bytes(policy_bytes)

    with pytest.raises(AssertionError):
        _assert_resolution_evidence(policy, policy_bytes, record, retained_bytes)


def test_wot_semantics_reject_policy_or_record_attachment_substitution():
    policy, policy_bytes, record, retained_bytes = _evidence_fixture()
    substituted_policy_bytes = policy_bytes + b" "

    with pytest.raises(AssertionError):
        _assert_resolution_evidence(
            policy, substituted_policy_bytes, record, retained_bytes
        )

    sample = _read_json(WOT / "samples" / "resolution-evidence.xreg.json")
    version = sample["thingmodelgroups"]["vendor"]["thingmodels"][
        "controller"
    ]["versions"]["release-A"]
    record_bytes = (FIXTURES / "record.json").read_bytes()
    root_bytes = (FIXTURES / "controller.tm.json").read_bytes()
    _assert_registry_attachments(version, policy_bytes, record_bytes, root_bytes)

    substituted_record_bytes = record_bytes + b" "
    with pytest.raises(AssertionError):
        _assert_registry_attachments(
            version, policy_bytes, substituted_record_bytes, root_bytes
        )


def test_wot_semantics_reject_missing_retained_input():
    policy, policy_bytes, record, retained_bytes = _evidence_fixture()
    del retained_bytes["a3"]

    with pytest.raises(AssertionError, match="missing retained artifact bytes"):
        _assert_resolution_evidence(policy, policy_bytes, record, retained_bytes)


def test_wot_record_fixture_replays_captured_version_after_default_drift():
    record = _read_json(FIXTURES / "record.json")
    _validate(record, SCHEMAS / "resolution-record.schema.json")
    core = record["core"]
    artifacts = {item["artifactId"]: item for item in core["artifacts"]}
    edge = core["edges"][0]
    artifact_ids = set(artifacts)
    canonical_ids = [
        item["artifactId"]
        for item in sorted(core["artifacts"], key=_artifact_descriptor_key)
    ]

    assert core["rootArtifact"] == "a2"
    assert canonical_ids == ["a0", "a1", "a2", "a3"]
    assert edge["from"] == "a2"
    assert edge["to"] == "a3"
    assert {edge["from"], edge["to"]} <= artifact_ids
    assert edge["selection"] == {"mode": "registry-default"}
    assert artifacts["a3"]["registry"]["versionId"] == "7"
    observation = record["observations"]["defaults"][0]
    assert observation["observedDefaultVersionId"] == "7"
    assert observation["laterObservedDefaultVersionId"] == "8"
    assert artifacts["a3"]["documentUrl"].endswith("/versions/7")
    assert artifacts["a3"]["interpretationBase"] == artifacts["a3"][
        "documentUrl"
    ]
    assert artifacts["a3"]["digest"] == _file_digest(
        FIXTURES / "sensors-v7.tm.json"
    )
    assert artifacts["a3"]["digest"] != _file_digest(
        FIXTURES / "sensors-v8.tm.json"
    )
    assert artifacts["a1"]["digest"] == _file_digest(
        FIXTURES / "controller-resolved.tm.json"
    )
    assert artifacts["a0"]["digest"] == _file_digest(
        FIXTURES / "processing-config.json"
    )
    assert artifacts["a0"]["byteLength"] == str(
        (FIXTURES / "processing-config.json").stat().st_size
    )
    assert core["transformations"][0]["configurationDigest"] == artifacts[
        "a0"
    ]["digest"]
    assert core["transformations"][0]["mappings"][0] == {
        "outputPointer": "/properties/temperature",
        "sourceArtifact": "a3",
        "sourcePointer": "/properties/temperature",
    }
    assert set(core["transformations"][0]["inputs"]) <= artifact_ids
    assert core["transformations"][0]["output"] in artifact_ids
    authored_root = _read_json(FIXTURES / "controller.tm.json")
    resolved_result = _read_json(FIXTURES / "controller-resolved.tm.json")
    assert "tm:ref" in authored_root["properties"]["temperature"]
    assert "tm:ref" not in resolved_result["properties"]["temperature"]
    assert resolved_result["properties"]["temperature"] == _read_json(
        FIXTURES / "sensors-v7.tm.json"
    )["properties"]["temperature"]


def test_wot_record_schema_rejects_file_artifact_without_exact_byte_length():
    record = _read_json(FIXTURES / "record.json")
    broken = copy.deepcopy(record)
    del broken["core"]["artifacts"][0]["byteLength"]

    with pytest.raises(jsonschema.ValidationError):
        _validate(broken, SCHEMAS / "resolution-record.schema.json")


def test_wot_file_digest_fixture_covers_original_octets_not_normalized_json():
    source = FIXTURES / "controller.tm.json"
    document = json.loads(source.read_bytes())
    normalized = json.dumps(
        document, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")

    assert _file_digest(source) == (
        "sha-256:e180bfb9851d0d3910858fa22d2e04e05b614b2c17827d367ef8b007cf3a5ce9"
    )
    assert hashlib.sha256(source.read_bytes()).digest() != hashlib.sha256(
        normalized
    ).digest()


def test_wot_registry_sample_shows_sticky_default_and_nonnumeric_ids():
    sample = _read_json(WOT / "samples" / "resolution-evidence.xreg.json")
    resources = sample["thingmodelgroups"]["vendor"]["thingmodels"]

    controller = resources["controller"]
    assert controller["meta"]["defaultversionid"] == "release-B"
    assert controller["meta"]["defaultversionsticky"] is True
    assert set(controller["versions"]) == {"release-A", "release-B"}
    assert controller["versions"]["release-A"]["resolutionrecords"][0][
        "rootdigest"
    ] == _file_digest(FIXTURES / "controller.tm.json")

    sensors = resources["sensors"]
    assert sensors["meta"]["defaultversionid"] == "8"
    assert sensors["meta"]["defaultversionsticky"] is True
    assert "publisher" in sensors["versions"]["7"]
    assert sensors["versions"]["7"]["maturity"] == "Vendor"


def test_wot_attachment_digests_match_separately_stored_policy_and_record():
    sample = _read_json(WOT / "samples" / "resolution-evidence.xreg.json")
    version = sample["thingmodelgroups"]["vendor"]["thingmodels"][
        "controller"
    ]["versions"]["release-A"]
    policy = _read_json(FIXTURES / "policy.json")
    record = _read_json(FIXTURES / "record.json")
    policy_file_digest = _file_digest(FIXTURES / "policy.json")
    record_file_digest = _file_digest(FIXTURES / "record.json")
    root_digest = _file_digest(FIXTURES / "controller.tm.json")

    assert version["resolutionpolicy"]["digest"] == policy_file_digest
    assert version["resolutionrecords"][0]["digest"] == record_file_digest
    assert version["resolutionrecords"][0]["rootdigest"] == root_digest
    assert record["core"]["policyDigest"] == policy_file_digest
    assert policy["rootDigest"] == root_digest


# Amendment A descriptors and evidence packages are kept separate from the
# earlier reference-resolution policy/record fixtures above.
PROCESSING_SAMPLES = WOT / "samples" / "processing"
PROFILE_SCHEMA = SCHEMAS / "processing-profile.schema.json"
PROFILE_DEFINITION_SCHEMA = SCHEMAS / "processing-profile-definition.schema.json"
CONFIGURATION_SCHEMA = SCHEMAS / "processing-configuration.schema.json"
PROFILE_DESCRIPTOR = PROCESSING_SAMPLES / "processing-profile.json"
CONFIGURATION_DESCRIPTOR = PROCESSING_SAMPLES / "configuration-shared.json"
PROCESSING_PROFILE_DEFINITION = (
    PROCESSING_SAMPLES / "processing-profile-definition.json"
)


def _assert_profile_attachment(configuration, profile):
    assert configuration["profile"] == {
        "id": profile["id"],
        "version": profile["version"],
        "digest": _file_digest(PROFILE_DESCRIPTOR),
    }


def _assert_no_duplicate_configuration_rule_matches(configuration):
    """Reject repeated rules that could make one selection ambiguous."""
    matches = [
        (
            rule["role"],
            rule["expectedKind"],
            rule["expectedIdentity"],
            json.dumps(rule["selection"], sort_keys=True),
        )
        for rule in configuration["rules"]
    ]
    assert len(matches) == len(set(matches)), "duplicate configuration rule match"


def test_wot_processing_group_model_placement():
    model = _read_json(WOT / "model.json")
    groups = model["groups"]
    processing = groups["wotprocessinggroups"]
    resources = processing["resources"]

    assert {"processingprofiles", "processingconfigurations"} <= resources.keys()
    assert "wotprocessinggroups" not in groups["thingmodelgroups"]["resources"][
        "thingmodels"
    ]["attributes"]

    thingmodels = groups["thingmodelgroups"]["resources"]["thingmodels"]
    assert {"resolutionpolicy", "resolutionrecords"} <= thingmodels[
        "attributes"
    ].keys()
    assert thingmodels["attributes"]["resolutionpolicy"]["type"] == "object"
    assert thingmodels["attributes"]["resolutionrecords"]["type"] == "array"

    profile_attributes = resources["processingprofiles"]["attributes"]
    configuration_attributes = resources["processingconfigurations"]["attributes"]
    assert profile_attributes["stableprofileuri"]["type"] == "uri"
    assert profile_attributes["stableprofileuri"]["required"] is True
    assert configuration_attributes["configurationuri"]["type"] == "uri"
    assert configuration_attributes["configurationuri"]["required"] is True


def test_wot_profile_descriptor_schema():
    profile = _read_json(PROFILE_DESCRIPTOR)
    schema = _read_json(PROFILE_SCHEMA)
    Draft202012Validator.check_schema(schema)
    _validate(profile, PROFILE_SCHEMA)

    expected = {
        "formatVersion",
        "id",
        "version",
        "definition",
        "operations",
        "roles",
        "representationProfiles",
    }
    assert set(profile) == expected
    assert set(profile["definition"]) == {"id", "version", "digest"}
    assert set(schema["required"]) >= expected
    assert set(schema["properties"]) == expected
    assert set(schema["properties"]["definition"]["required"]) >= {
        "id",
        "version",
        "digest",
    }

    invalid_cases = []
    missing_descriptor_member = copy.deepcopy(profile)
    del missing_descriptor_member["operations"]
    invalid_cases.append(missing_descriptor_member)
    missing_definition_member = copy.deepcopy(profile)
    del missing_definition_member["definition"]["digest"]
    invalid_cases.append(missing_definition_member)
    malformed_digest = copy.deepcopy(profile)
    malformed_digest["definition"]["digest"] = "sha-256:not-a-full-digest"
    invalid_cases.append(malformed_digest)
    wrong_definition_type = copy.deepcopy(profile)
    wrong_definition_type["definition"]["version"] = 7
    invalid_cases.append(wrong_definition_type)
    for invalid in invalid_cases:
        with pytest.raises(jsonschema.ValidationError):
            _validate(invalid, PROFILE_SCHEMA)
    if schema.get("additionalProperties") is False:
        unexpected_member = copy.deepcopy(profile)
        unexpected_member["unreviewedExtension"] = True
        with pytest.raises(jsonschema.ValidationError):
            _validate(unexpected_member, PROFILE_SCHEMA)


def test_wot_processing_profile_definition_uses_owner_local_schema():
    definition = _read_json(PROCESSING_PROFILE_DEFINITION)
    schema = _read_json(PROFILE_DEFINITION_SCHEMA)
    Draft202012Validator.check_schema(schema)
    _assert_local_schema_refs(schema)
    _validate(definition, PROFILE_DEFINITION_SCHEMA)

    assert definition["operations"] == ["resolve-definition"]
    assert definition["roles"] == ["tm:ref"]
    assert definition["context"] == {
        "@version": 1.1,
        "tm": "https://www.w3.org/2022/wot/tm#",
    }
    assert definition["processing"]["remoteContexts"] == "unsupported"
    assert definition["processing"]["externalSchemas"] == "unsupported"

    changed_context = copy.deepcopy(definition)
    changed_context["context"]["tm"] = "https://attacker.invalid/tm#"
    with pytest.raises(jsonschema.ValidationError):
        _validate(changed_context, PROFILE_DEFINITION_SCHEMA)
    changed_schema_dependency = copy.deepcopy(definition)
    changed_schema_dependency["processing"]["externalSchemas"] = (
        "https://example.invalid/schema.json"
    )
    with pytest.raises(jsonschema.ValidationError):
        _validate(changed_schema_dependency, PROFILE_DEFINITION_SCHEMA)


def test_wot_configuration_descriptor_schema():
    configuration = _read_json(CONFIGURATION_DESCRIPTOR)
    schema = _read_json(CONFIGURATION_SCHEMA)
    Draft202012Validator.check_schema(schema)
    _validate(configuration, CONFIGURATION_SCHEMA)

    expected = {
        "formatVersion",
        "id",
        "version",
        "profile",
        "rules",
        "limits",
    }
    assert set(configuration) == expected
    assert set(configuration["profile"]) == {"id", "version", "digest"}
    assert set(configuration["limits"]) == {
        "maxDepth",
        "maxBytes",
        "maxMilliseconds",
    }
    assert all(
        isinstance(value, int) and value > 0
        for value in configuration["limits"].values()
    )
    assert set(schema["required"]) >= expected
    assert set(schema["properties"]) == expected
    assert set(schema["properties"]["profile"]["required"]) >= {
        "id",
        "version",
        "digest",
    }

    invalid_cases = []
    missing_required_member = copy.deepcopy(configuration)
    del missing_required_member["limits"]
    invalid_cases.append(missing_required_member)
    missing_attachment_digest = copy.deepcopy(configuration)
    del missing_attachment_digest["profile"]["digest"]
    invalid_cases.append(missing_attachment_digest)
    malformed_attachment_digest = copy.deepcopy(configuration)
    malformed_attachment_digest["profile"]["digest"] = "bad-digest"
    invalid_cases.append(malformed_attachment_digest)
    wrong_attachment_type = copy.deepcopy(configuration)
    wrong_attachment_type["profile"]["version"] = ["not", "a", "version"]
    invalid_cases.append(wrong_attachment_type)
    for invalid in invalid_cases:
        with pytest.raises(jsonschema.ValidationError):
            _validate(invalid, CONFIGURATION_SCHEMA)
    if schema.get("additionalProperties") is False:
        unexpected_member = copy.deepcopy(configuration)
        unexpected_member["fallbackConfiguration"] = "implicit"
        with pytest.raises(jsonschema.ValidationError):
            _validate(unexpected_member, CONFIGURATION_SCHEMA)

    for limit_name in ("maxDepth", "maxBytes", "maxMilliseconds"):
        zero_limit = copy.deepcopy(configuration)
        zero_limit["limits"][limit_name] = 0
        with pytest.raises(jsonschema.ValidationError):
            _validate(zero_limit, CONFIGURATION_SCHEMA)
        unbounded_limit = copy.deepcopy(configuration)
        unbounded_limit["limits"][limit_name] = 9007199254740992
        with pytest.raises(jsonschema.ValidationError):
            _validate(unbounded_limit, CONFIGURATION_SCHEMA)

    legacy_names = copy.deepcopy(configuration)
    legacy_names["limits"] = {
        "depth": 12,
        "retainedBytes": 4194304,
        "elapsedMilliseconds": 10000,
    }
    with pytest.raises(jsonschema.ValidationError):
        _validate(legacy_names, CONFIGURATION_SCHEMA)


def test_wot_owner_local_and_shared_configurations_are_root_free():
    own = _read_json(PROCESSING_SAMPLES / "configuration-own.json")
    shared = _read_json(PROCESSING_SAMPLES / "configuration-shared.json")
    own_imported = _read_json(
        PROCESSING_SAMPLES / "configuration-own-imported.json"
    )
    registry_selected = _read_json(
        PROCESSING_SAMPLES / "configuration-registry.json"
    )
    configurations = (own, own_imported, shared, registry_selected)
    for configuration in configurations:
        _validate(configuration, CONFIGURATION_SCHEMA)
        assert set(configuration["limits"]) == {
            "maxDepth",
            "maxBytes",
            "maxMilliseconds",
        }
        assert not {
            "root",
            "rootDocument",
            "request",
            "operation",
            "pointer",
        } & set(configuration)
        assert configuration["profile"] == {
            "id": _read_json(PROFILE_DESCRIPTOR)["id"],
            "version": _read_json(PROFILE_DESCRIPTOR)["version"],
            "digest": _file_digest(PROFILE_DESCRIPTOR),
        }

    assert own["rules"] == []
    assert all(len(configuration["rules"]) == 1 for configuration in configurations[1:])
    assert own["id"] != shared["id"]


def test_wot_descriptor_identity_and_attachment_bindings():
    model = _read_json(WOT / "model.json")
    profile = _read_json(PROFILE_DESCRIPTOR)
    configuration = _read_json(CONFIGURATION_DESCRIPTOR)
    processing_resources = _read_json(
        PROCESSING_SAMPLES / "processing-resources.xreg.json"
    )["wotprocessinggroups"]["portable-reference-processing"]
    processing = model["groups"]["wotprocessinggroups"]["resources"]

    assert profile["id"].startswith(("https://", "urn:"))
    assert configuration["id"] == configuration["id"].strip()
    assert configuration["id"].startswith(("https://", "urn:"))
    assert processing["processingprofiles"]["attributes"][
        "stableprofileuri"
    ]["name"] == "stableprofileuri"
    assert processing["processingconfigurations"]["attributes"][
        "configurationuri"
    ]["name"] == "configurationuri"
    assert (
        processing_resources["processingprofiles"]["tm-property-reference"][
            "stableprofileuri"
        ]
        == profile["id"]
    )
    assert (
        processing_resources["processingconfigurations"]["vendor-default"][
            "configurationuri"
        ]
        == configuration["id"]
    )
    _assert_profile_attachment(configuration, profile)

    for field, replacement in (
        ("id", profile["id"] + "/substituted"),
        ("version", profile["version"] + "-substituted"),
    ):
        substituted = copy.deepcopy(profile)
        substituted[field] = replacement
        with pytest.raises(AssertionError):
            _assert_profile_attachment(configuration, substituted)

    substituted_digest = copy.deepcopy(profile)
    substituted_digest["id"] += "/substituted"
    with pytest.raises(AssertionError):
        _assert_profile_attachment(configuration, substituted_digest)

    substituted_attachment_digest = copy.deepcopy(configuration)
    substituted_attachment_digest["profile"]["digest"] = (
        "sha-256:" + "0" * 64
        if configuration["profile"]["digest"] != "sha-256:" + "0" * 64
        else "sha-256:" + "1" * 64
    )
    with pytest.raises(AssertionError):
        _assert_profile_attachment(substituted_attachment_digest, profile)

    substituted_configuration = copy.deepcopy(configuration)
    substituted_configuration["profile"]["id"] += "/substituted"
    with pytest.raises(AssertionError):
        _assert_profile_attachment(substituted_configuration, profile)


def test_wot_versions_are_opaque_exact_labels():
    profile = _read_json(PROFILE_DESCRIPTOR)
    configuration = _read_json(CONFIGURATION_DESCRIPTOR)
    opaque_version = "release/candidate+vendor-label"

    for descriptor, schema_path in (
        (profile, PROFILE_SCHEMA),
        (configuration, CONFIGURATION_SCHEMA),
    ):
        changed = copy.deepcopy(descriptor)
        changed["version"] = opaque_version
        _validate(changed, schema_path)
        assert changed["version"] == opaque_version

    _assert_profile_attachment(configuration, profile)
    mismatched = copy.deepcopy(configuration)
    mismatched["profile"]["version"] = profile["version"] + "-range"
    with pytest.raises(AssertionError):
        _assert_profile_attachment(mismatched, profile)


def test_wot_configuration_selection_is_exactly_one():
    configuration = _read_json(CONFIGURATION_DESCRIPTOR)
    _validate(configuration, CONFIGURATION_SCHEMA)

    assert configuration["rules"]
    _assert_no_duplicate_configuration_rule_matches(configuration)

    exact_selection = copy.deepcopy(configuration)
    exact_selection["rules"][0]["selection"] = {
        "mode": "exact",
        "versionId": "release-A",
    }
    _validate(exact_selection, CONFIGURATION_SCHEMA)
    assert exact_selection["rules"][0]["selection"] == {
        "mode": "exact",
        "versionId": "release-A",
    }

    unsupported_selection = copy.deepcopy(configuration)
    unsupported_selection["rules"][0]["selection"] = {
        "mode": "compatible-range",
        "versionRange": ">=7",
    }
    with pytest.raises(jsonschema.ValidationError):
        _validate(unsupported_selection, CONFIGURATION_SCHEMA)
    duplicate = copy.deepcopy(configuration)
    duplicate["rules"].append(copy.deepcopy(duplicate["rules"][0]))
    with pytest.raises(AssertionError, match="duplicate configuration rule match"):
        _assert_no_duplicate_configuration_rule_matches(duplicate)

    # A descriptor is a single reusable configuration. Selection remains
    # explicit; composition and implicit fallback are not descriptor behavior.
    assert not {
        "fallback",
        "fallbackConfiguration",
        "overlay",
        "extends",
        "merge",
        "extension",
    } & set(configuration)
    assert configuration["id"] and configuration["version"]
    configuration_schema = _read_json(CONFIGURATION_SCHEMA)
    if configuration_schema.get("additionalProperties") is False:
        for forbidden in (
            "fallback",
            "fallbackConfiguration",
            "overlay",
            "extends",
            "merge",
            "extension",
        ):
            with pytest.raises(jsonschema.ValidationError):
                _validate(
                    {**configuration, forbidden: "not part of this contract"},
                    CONFIGURATION_SCHEMA,
                )


def test_wot_rule_authority_and_expected_target_contract():
    configuration = _read_json(CONFIGURATION_DESCRIPTOR)
    schema = _read_json(CONFIGURATION_SCHEMA)
    Draft202012Validator.check_schema(schema)
    _validate(configuration, CONFIGURATION_SCHEMA)

    rule = configuration["rules"][0]
    assert {"role", "expectedKind", "expectedIdentity", "authority", "selection"} <= (
        rule.keys()
    )
    assert {"adapter", "origin", "scope"} <= rule["authority"].keys()
    assert rule["selection"]["mode"] in {"exact", "registry-default"}
    if rule["selection"]["mode"] == "exact":
        assert isinstance(rule["selection"].get("versionId"), str)
    assert "expectedDigest" not in rule or rule["expectedDigest"].startswith(
        "sha-256:"
    )

    invalid_cases = []
    for member in ("role", "expectedKind", "expectedIdentity", "authority", "selection"):
        invalid = copy.deepcopy(configuration)
        del invalid["rules"][0][member]
        invalid_cases.append(invalid)
    for member, replacement in (
        ("scope", "unrestricted"),
        ("origin", "not a URI"),
    ):
        invalid = copy.deepcopy(configuration)
        invalid["rules"][0]["authority"][member] = replacement
        invalid_cases.append(invalid)
    invalid_kind = copy.deepcopy(configuration)
    invalid_kind["rules"][0]["expectedKind"] = "unknown-kind"
    invalid_cases.append(invalid_kind)
    invalid_identity = copy.deepcopy(configuration)
    invalid_identity["rules"][0]["expectedIdentity"] = "not a URI"
    invalid_cases.append(invalid_identity)
    invalid_selection = copy.deepcopy(configuration)
    invalid_selection["rules"][0]["selection"] = {"mode": "latest-compatible"}
    invalid_cases.append(invalid_selection)

    for invalid in invalid_cases:
        with pytest.raises(jsonschema.ValidationError):
            _validate(invalid, CONFIGURATION_SCHEMA)

    optional_digest = copy.deepcopy(configuration)
    optional_digest["rules"][0].pop("expectedDigest", None)
    _validate(optional_digest, CONFIGURATION_SCHEMA)

    with_expected_digest = copy.deepcopy(configuration)
    with_expected_digest["rules"][0]["expectedDigest"] = (
        "sha-256:" + "a" * 64
    )
    _validate(with_expected_digest, CONFIGURATION_SCHEMA)
    malformed_expected_digest = copy.deepcopy(with_expected_digest)
    malformed_expected_digest["rules"][0]["expectedDigest"] = "sha-256:bad"
    with pytest.raises(jsonschema.ValidationError):
        _validate(malformed_expected_digest, CONFIGURATION_SCHEMA)

    open_scope = copy.deepcopy(configuration)
    open_scope["rules"][0]["authority"]["scope"]["unreviewedTenant"] = "other"
    with pytest.raises(jsonschema.ValidationError):
        _validate(open_scope, CONFIGURATION_SCHEMA)


# Portable-contract-v2 evidence inputs are authored in the processing sample
# directory; they remain read-only test inputs.
EVIDENCE_SCHEMA = SCHEMAS / "processing-evidence.schema.json"
LOCAL_INVOCATION_EVIDENCE = PROCESSING_SAMPLES / "local-evidence.json"
RETAINED_INVOCATION_EVIDENCE = PROCESSING_SAMPLES / "imported-evidence.json"
OWN_IMPORTED_INVOCATION_EVIDENCE = (
    PROCESSING_SAMPLES / "own-imported-evidence.json"
)
REGISTRY_CONFIGURATION_INVOCATION_EVIDENCE = (
    PROCESSING_SAMPLES / "registry-configuration-evidence.json"
)
EVIDENCE_CASES = (
    (
        "local",
        LOCAL_INVOCATION_EVIDENCE,
        PROCESSING_SAMPLES / "local-replay-pins.json",
        PROCESSING_SAMPLES / "configuration-own.json",
        "own",
        "local-definition",
        False,
        False,
    ),
    (
        "own-imported",
        OWN_IMPORTED_INVOCATION_EVIDENCE,
        PROCESSING_SAMPLES / "own-imported-replay-pins.json",
        PROCESSING_SAMPLES / "configuration-own-imported.json",
        "own",
        "retained-resolution",
        False,
        True,
    ),
    (
        "shared-imported",
        RETAINED_INVOCATION_EVIDENCE,
        PROCESSING_SAMPLES / "imported-replay-pins.json",
        PROCESSING_SAMPLES / "configuration-shared.json",
        "shared",
        "retained-resolution",
        True,
        True,
    ),
    (
        "registry-configuration",
        REGISTRY_CONFIGURATION_INVOCATION_EVIDENCE,
        PROCESSING_SAMPLES / "registry-configuration-replay-pins.json",
        PROCESSING_SAMPLES / "configuration-registry.json",
        "own",
        "retained-resolution",
        True,
        True,
    ),
)
RETAINED_RESOLUTION_CASES = tuple(
    case for case in EVIDENCE_CASES if case[5] == "retained-resolution"
)


def _jcs_sha256(value):
    """Hash the JCS-compatible JSON values used by these invocation fixtures."""
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return _file_digest_bytes(canonical)


def _json_leaf_paths(value, prefix=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _json_leaf_paths(child, prefix + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _json_leaf_paths(child, prefix + (index,))
    else:
        yield prefix


def _invocation_digest_input(invocation):
    required = {"profile", "configuration", "root", "request"}
    assert required <= invocation.keys()
    assert set(invocation) <= required | {"effectivePolicyDigest"}
    return {
        key: invocation[key]
        for key in ("profile", "configuration", "root", "request")
    }


def _assert_invocation_digest(evidence):
    invocation = evidence["invocation"]
    assert evidence["invocationDigest"] == _jcs_sha256(
        _invocation_digest_input(invocation)
    )


def _assert_replay_digest_pins(
    evidence, expected_invocation_digest, expected_evidence_digest
):
    """Check independent caller inputs against the captured replay evidence."""
    assert expected_invocation_digest == evidence["invocationDigest"]
    assert expected_invocation_digest == _jcs_sha256(
        _invocation_digest_input(evidence["invocation"])
    )
    assert expected_evidence_digest == _jcs_sha256(evidence)


def _json_member_names(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _json_member_names(child)
    elif isinstance(value, list):
        for child in value:
            yield from _json_member_names(child)


def _assert_binding_matches_descriptor(
    package, binding, descriptor, descriptor_path
):
    descriptor_bytes = descriptor_path.read_bytes()
    assert binding["id"] == descriptor["id"]
    assert binding["version"] == descriptor["version"]
    assert binding["digest"] == _file_digest_bytes(descriptor_bytes)

    retained = [
        artifact
        for artifact in package["retainedArtifacts"]
        if artifact["digest"] == binding["digest"]
    ]
    assert len(retained) == 1
    assert binding["documentUrl"] == retained[0]["documentUrl"]
    assert binding["interpretationBase"] == retained[0]["interpretationBase"]
    if "registry" in retained[0]:
        assert binding["registry"] == retained[0]["registry"]


def _assert_invocation_descriptor_bindings(
    package, configuration_path=CONFIGURATION_DESCRIPTOR
):
    evidence = package["evidence"]
    invocation = evidence["invocation"]
    profile = _read_json(PROFILE_DESCRIPTOR)
    configuration = _read_json(configuration_path)

    assert invocation["configuration"]["source"] in {"own", "shared"}
    _assert_profile_attachment(configuration, profile)
    _assert_binding_matches_descriptor(
        package, invocation["profile"], profile, PROFILE_DESCRIPTOR
    )
    _assert_binding_matches_descriptor(
        package,
        invocation["configuration"],
        configuration,
        configuration_path,
    )


def _assert_invocation_root_and_request(package, package_path):
    invocation = package["evidence"]["invocation"]
    root = invocation["root"]
    assert root["digestScope"] == "decoded-file-octets"
    assert root["identity"]
    assert root["digest"].startswith("sha-256:")
    assert root["documentUrl"]
    assert root["interpretationBase"]
    matching_roots = [
        artifact
        for artifact in package["retainedArtifacts"]
        if artifact["digest"] == root["digest"]
    ]
    assert len(matching_roots) == 1
    retained_root = matching_roots[0]
    assert root["identity"] == retained_root["identity"]
    assert root["digestScope"] == retained_root["digestScope"]
    assert root["documentUrl"] == retained_root["documentUrl"]
    assert root["interpretationBase"] == retained_root["interpretationBase"]
    if "registry" in retained_root:
        assert root["registry"] == retained_root["registry"]

    request = invocation["request"]
    assert request["operation"] == "resolve-definition"
    assert request["pointer"] == "" or request["pointer"].startswith("/")
    root_document = _read_json(_artifact_file(package_path, retained_root))
    resolve_pointer(root_document, request["pointer"])


@pytest.mark.parametrize("case", EVIDENCE_CASES, ids=lambda case: case[0])
def test_wot_invocation_binds_exact_profile_and_configuration(case):
    _, package_path, _, configuration_path, *_ = case
    package = _read_json(package_path)
    _validate(package, EVIDENCE_SCHEMA)
    evidence = package["evidence"]

    _assert_invocation_descriptor_bindings(package, configuration_path)
    _assert_invocation_digest(evidence)

    invocation = evidence["invocation"]
    for binding_name in ("profile", "configuration"):
        for member in ("id", "version", "digest"):
            changed = copy.deepcopy(package)
            changed["evidence"]["invocation"][binding_name][member] += "-substituted"
            with pytest.raises(AssertionError):
                _assert_invocation_descriptor_bindings(
                    changed, configuration_path
                )

    for binding_name in ("profile", "configuration"):
        for member in ("id", "version", "digest"):
            changed = copy.deepcopy(package)
            del changed["evidence"]["invocation"][binding_name][member]
            with pytest.raises(jsonschema.ValidationError):
                _validate(changed, EVIDENCE_SCHEMA)

    # The descriptor attachment is part of the same exact selection.
    changed_configuration = copy.deepcopy(_read_json(configuration_path))
    changed_configuration["profile"]["version"] += "-substituted"
    with pytest.raises(AssertionError):
        _assert_profile_attachment(changed_configuration, _read_json(PROFILE_DESCRIPTOR))


@pytest.mark.parametrize("case", EVIDENCE_CASES, ids=lambda case: case[0])
def test_wot_invocation_binds_document_and_root_scope(case):
    _, package_path, _, configuration_path, *_ = case
    package = _read_json(package_path)
    _validate(package, EVIDENCE_SCHEMA)
    evidence = package["evidence"]
    _assert_invocation_descriptor_bindings(package, configuration_path)
    _assert_invocation_root_and_request(package, package_path)
    _assert_invocation_digest(evidence)

    original = evidence["invocation"]
    mutations = (
        ("profile", "documentUrl"),
        ("profile", "interpretationBase"),
        ("configuration", "documentUrl"),
        ("configuration", "interpretationBase"),
        ("configuration", "source"),
        ("root", "identity"),
        ("root", "digestScope"),
        ("root", "digest"),
        ("root", "documentUrl"),
        ("root", "interpretationBase"),
        ("request", "operation"),
        ("request", "pointer"),
    )
    for binding_name, member in mutations:
        changed = copy.deepcopy(evidence)
        current = changed["invocation"][binding_name][member]
        changed_value = (
            current + "-substituted"
            if isinstance(current, str)
            else "substituted"
        )
        changed["invocation"][binding_name][member] = changed_value
        with pytest.raises(AssertionError):
            _assert_invocation_digest(changed)

    for binding_name, member in mutations:
        changed = copy.deepcopy(package)
        del changed["evidence"]["invocation"][binding_name][member]
        with pytest.raises(jsonschema.ValidationError):
            _validate(changed, EVIDENCE_SCHEMA)

    assert original["request"]["operation"] == "resolve-definition"
    assert original["root"]["digestScope"] == "decoded-file-octets"


def test_wot_invocation_digest_uses_exact_jcs_input():
    package = _read_json(RETAINED_INVOCATION_EVIDENCE)
    _validate(package, EVIDENCE_SCHEMA)
    evidence = package["evidence"]
    invocation = evidence["invocation"]
    digest_input = _invocation_digest_input(invocation)

    assert set(digest_input) == {"profile", "configuration", "root", "request"}
    _assert_invocation_digest(evidence)

    reordered = dict(reversed(list(invocation.items())))
    for name in ("profile", "configuration", "root", "request"):
        reordered[name] = dict(reversed(list(reordered[name].items())))
    assert _jcs_sha256(_invocation_digest_input(reordered)) == evidence[
        "invocationDigest"
    ]
    reformatted = json.loads(json.dumps(invocation, indent=4))
    assert _jcs_sha256(_invocation_digest_input(reformatted)) == evidence[
        "invocationDigest"
    ]

    full_invocation_digest = _jcs_sha256(invocation)
    assert full_invocation_digest != evidence["invocationDigest"]
    for omitted in ("profile", "configuration", "root", "request"):
        incomplete = dict(digest_input)
        del incomplete[omitted]
        with pytest.raises(AssertionError):
            _invocation_digest_input(incomplete)
        assert _jcs_sha256(incomplete) != evidence["invocationDigest"]

    extended = dict(digest_input)
    extended["unrelated"] = {"not": "an invocation input"}
    assert _jcs_sha256(extended) != evidence["invocationDigest"]
    with pytest.raises(AssertionError):
        _invocation_digest_input({**invocation, "unrelated": True})

    for changed_path in _json_leaf_paths(digest_input):
        changed = copy.deepcopy(digest_input)
        target = changed
        for part in changed_path[:-1]:
            target = target[part]
        original_value = target[changed_path[-1]]
        target[changed_path[-1]] = (
            original_value + "-changed"
            if isinstance(original_value, str)
            else not original_value
        )
        assert _jcs_sha256(changed) != evidence["invocationDigest"]


def test_wot_replay_requires_independent_caller_supplied_digest_pins():
    for (
        _case_name,
        package_path,
        pins_path,
        configuration_path,
        _expected_source,
        _expected_kind,
        _configuration_has_registry,
        _root_has_registry,
    ) in EVIDENCE_CASES:
        package = _read_json(package_path)
        _validate(package, EVIDENCE_SCHEMA)
        evidence = package["evidence"]
        caller_pins = _read_json(pins_path)
        assert set(caller_pins) == {
            "expectedInvocationDigest",
            "expectedEvidenceDigest",
        }
        expected_invocation_digest = caller_pins[
            "expectedInvocationDigest"
        ]
        expected_evidence_digest = caller_pins["expectedEvidenceDigest"]

        _assert_replay_digest_pins(
            evidence,
            expected_invocation_digest,
            expected_evidence_digest,
        )
        serialized_documents = (
            _read_json(PROFILE_DESCRIPTOR),
            _read_json(configuration_path),
            evidence,
        )
        for document in serialized_documents:
            member_names = set(_json_member_names(document))
            assert "expectedInvocationDigest" not in member_names
            assert "expectedEvidenceDigest" not in member_names

        wrong_invocation_pin = "sha-256:" + "0" * 64
        with pytest.raises(AssertionError):
            _assert_replay_digest_pins(
                evidence, wrong_invocation_pin, expected_evidence_digest
            )
        wrong_evidence_pin = "sha-256:" + "0" * 64
        with pytest.raises(AssertionError):
            _assert_replay_digest_pins(
                evidence, expected_invocation_digest, wrong_evidence_pin
            )

        changed_result = copy.deepcopy(evidence)
        changed_result["output"]["value"] = {"substitutedResult": True}
        changed_result["output"]["digest"] = _jcs_sha256(
            changed_result["output"]["value"]
        )
        _assert_evidence_output_digest(changed_result)
        with pytest.raises(AssertionError):
            _assert_replay_digest_pins(
                changed_result,
                expected_invocation_digest,
                expected_evidence_digest,
            )
        _assert_replay_digest_pins(
            changed_result,
            expected_invocation_digest,
            _jcs_sha256(changed_result),
        )

        changed_source = copy.deepcopy(evidence)
        source = changed_source["invocation"]["configuration"]["source"]
        changed_source["invocation"]["configuration"]["source"] = (
            "shared" if source == "own" else "own"
        )
        with pytest.raises(AssertionError):
            _assert_replay_digest_pins(
                changed_source,
                expected_invocation_digest,
                _jcs_sha256(changed_source),
            )

        changed_evidence = copy.deepcopy(evidence)
        if changed_evidence["kind"] == "local-definition":
            changed_evidence["localReferences"][0]["targetPointer"] = ""
        else:
            changed_policy_binding = changed_evidence["invocation"][
                "effectivePolicyDigest"
            ]
            changed_evidence["invocation"]["effectivePolicyDigest"] = (
                changed_policy_binding[:-1]
                + ("0" if changed_policy_binding[-1] != "0" else "1")
            )
        with pytest.raises(AssertionError):
            _assert_replay_digest_pins(
                changed_evidence,
                expected_invocation_digest,
                expected_evidence_digest,
            )
        _assert_replay_digest_pins(
            changed_evidence,
            expected_invocation_digest,
            _jcs_sha256(changed_evidence),
        )

@pytest.mark.parametrize("case", EVIDENCE_CASES, ids=lambda case: case[0])
def test_wot_retained_invocation_digest_adds_effective_policy_digest_only_for_retained_branch(
    case,
):
    _, package_path, _, _, _, expected_kind, *_ = case
    package = _read_json(package_path)
    _validate(package, EVIDENCE_SCHEMA)
    evidence = package["evidence"]
    invocation = evidence["invocation"]

    assert evidence["kind"] == expected_kind
    _assert_invocation_digest(evidence)
    if expected_kind == "retained-resolution":
        assert invocation["effectivePolicyDigest"].startswith("sha-256:")
        assert _jcs_sha256(invocation) != evidence["invocationDigest"]
        missing_effective_digest = copy.deepcopy(package)
        del missing_effective_digest["evidence"]["invocation"][
            "effectivePolicyDigest"
        ]
        with pytest.raises(jsonschema.ValidationError):
            _validate(missing_effective_digest, EVIDENCE_SCHEMA)
    else:
        assert "effectivePolicyDigest" not in invocation
        local_with_policy_digest = copy.deepcopy(package)
        local_with_policy_digest["evidence"]["invocation"][
            "effectivePolicyDigest"
        ] = "sha-256:" + "0" * 64
        with pytest.raises(jsonschema.ValidationError):
            _validate(local_with_policy_digest, EVIDENCE_SCHEMA)


@pytest.mark.parametrize("case", EVIDENCE_CASES, ids=lambda case: case[0])
def test_wot_profile_and_configuration_bytes_are_integrity_bound(case):
    _, package_path, _, configuration_path, *_ = case
    package = _read_json(package_path)
    _validate(package, EVIDENCE_SCHEMA)
    invocation = package["evidence"]["invocation"]
    descriptors = (
        ("profile", PROFILE_DESCRIPTOR),
        ("configuration", configuration_path),
    )

    for binding_name, descriptor_path in descriptors:
        binding = invocation[binding_name]
        descriptor = _read_json(descriptor_path)
        original_bytes = descriptor_path.read_bytes()
        original_version = descriptor["version"]
        assert binding["version"] == original_version
        assert binding["digest"] == _file_digest_bytes(original_bytes)

        changed_bytes = original_bytes + b" "
        assert json.loads(changed_bytes)["version"] == original_version
        assert descriptor["version"] == original_version
        with pytest.raises(AssertionError):
            assert binding["digest"] == _file_digest_bytes(changed_bytes)

        changed_claim = copy.deepcopy(binding)
        changed_claim["digest"] = _file_digest_bytes(changed_bytes)
        with pytest.raises(AssertionError):
            assert changed_claim["digest"] == _file_digest_bytes(original_bytes)


def test_wot_configuration_source_own_or_shared_is_explicit():
    for (
        _case_name,
        package_path,
        _pins_path,
        descriptor_path,
        expected_source,
        expected_kind,
        configuration_has_registry,
        root_has_registry,
    ) in EVIDENCE_CASES:
        package = _read_json(package_path)
        _validate(package, EVIDENCE_SCHEMA)
        invocation = package["evidence"]["invocation"]
        assert "configuration" in invocation
        assert "configurations" not in invocation
        configuration = invocation["configuration"]
        assert package["evidence"]["kind"] == expected_kind
        assert "source" not in invocation["profile"]
        assert configuration["source"] == expected_source
        _assert_binding_matches_descriptor(
            package,
            configuration,
            _read_json(descriptor_path),
            descriptor_path,
        )
        expected_registry_members = {
            "origin",
            "groupCollection",
            "groupId",
            "resourceCollection",
            "resourceId",
            "versionId",
        }
        for binding_name, has_registry in (
            ("profile", root_has_registry),
            ("configuration", configuration_has_registry),
            ("root", root_has_registry),
        ):
            if has_registry:
                assert set(invocation[binding_name]["registry"]) == (
                    expected_registry_members
                )
            else:
                assert "registry" not in invocation[binding_name]

        for invalid_source in (None, "merged", ["own", "shared"]):
            invalid = copy.deepcopy(package)
            invalid["evidence"]["invocation"]["configuration"][
                "source"
            ] = invalid_source
            with pytest.raises(jsonschema.ValidationError):
                _validate(invalid, EVIDENCE_SCHEMA)

        missing_source = copy.deepcopy(package)
        del missing_source["evidence"]["invocation"]["configuration"]["source"]
        with pytest.raises(jsonschema.ValidationError):
            _validate(missing_source, EVIDENCE_SCHEMA)

        forbidden_profile_source = copy.deepcopy(package)
        forbidden_profile_source["evidence"]["invocation"]["profile"][
            "source"
        ] = "shared"
        with pytest.raises(jsonschema.ValidationError):
            _validate(forbidden_profile_source, EVIDENCE_SCHEMA)

        multiple_configurations = copy.deepcopy(package)
        multiple_configurations["evidence"]["invocation"]["configurations"] = [
            configuration,
            configuration,
        ]
        with pytest.raises(jsonschema.ValidationError):
            _validate(multiple_configurations, EVIDENCE_SCHEMA)


# Phase 3 Amendment A evidence contracts. Evidence package names follow the
# samples/processing/README.md; retained inputs are read relative to each package.
PROCESSING_PROFILE_DESCRIPTOR = PROFILE_DESCRIPTOR
PROCESSING_CONFIGURATION_SCHEMA = CONFIGURATION_SCHEMA
PROCESSING_CONFIGURATION = PROCESSING_SAMPLES / "configuration-shared.json"
IMPORTED_RECORD = PROCESSING_SAMPLES / "imported-record.json"


def _artifact_file(package_path, artifact):
    return package_path.parent / artifact["archivePath"]


def _artifact_descriptor(artifact):
    return {
        key: artifact[key]
        for key in (
            "digestScope",
            "digest",
            "documentUrl",
            "interpretationBase",
        )
    }


def _retained_artifacts_by_digest(package):
    return {
        artifact["digest"]: artifact
        for artifact in package["retainedArtifacts"]
    }


def _assert_evidence_output_digest(evidence):
    output = evidence["output"]
    assert output["digestScope"] == "json-jcs"
    assert output["digest"] == _jcs_sha256(output["value"])


def _assert_local_reference_closure(package, package_path):
    evidence = package["evidence"]
    artifacts_by_digest = _retained_artifacts_by_digest(package)
    expected = []

    for artifact in package["retainedArtifacts"]:
        document_path = _artifact_file(package_path, artifact)
        if not document_path.is_file():
            continue
        try:
            document = _read_json(document_path)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        for source_pointer, reference in _tm_reference_values(document):
            if isinstance(reference, str) and reference.startswith("#/"):
                expected.append(
                    (
                        _artifact_descriptor(artifact),
                        source_pointer,
                        reference[1:],
                    )
                )

    actual = [
        (
            reference["from"],
            reference["sourcePointer"],
            reference["targetPointer"],
        )
        for reference in evidence["localReferences"]
    ]
    assert len(actual) == len(set(
        (
            json.dumps(item[0], sort_keys=True),
            item[1],
            item[2],
        )
        for item in actual
    )), "conflicting local occurrence mappings"
    normalized_actual = sorted(
        (json.dumps(item[0], sort_keys=True), item[1], item[2])
        for item in actual
    )
    normalized_expected = sorted(
        (json.dumps(item[0], sort_keys=True), item[1], item[2])
        for item in expected
    )
    assert normalized_actual == normalized_expected

    for descriptor, source_pointer, target_pointer in actual:
        retained = artifacts_by_digest[descriptor["digest"]]
        source_document = _read_json(_artifact_file(package_path, retained))
        authored = resolve_pointer(source_document, source_pointer)
        assert authored == "#" + target_pointer
        resolve_pointer(source_document, target_pointer)


def _assert_retained_bindings_match_artifacts(package, package_path):
    evidence = package["evidence"]
    policy_artifact, policy_bytes = _assert_existing_document_is_pinned(
        package,
        package_path,
        "policy",
        SCHEMAS / "resolution-policy.schema.json",
    )
    lock_artifact, record_bytes = _assert_existing_document_is_pinned(
        package,
        package_path,
        "lock",
        SCHEMAS / "resolution-record.schema.json",
    )
    policy = json.loads(policy_bytes)
    record = json.loads(record_bytes)
    assert record["core"]["policyDigest"] == policy_artifact["digest"]
    assert (
        evidence["invocation"]["effectivePolicyDigest"]
        == policy_artifact["digest"]
    )
    root_artifact_id = record["core"]["rootArtifact"]
    root = next(
        item for item in record["core"]["artifacts"]
        if item["artifactId"] == root_artifact_id
    )
    assert root["digest"] == evidence["invocation"]["root"]["digest"]
    retained_bytes = {}
    for record_artifact in record["core"]["artifacts"]:
        matching = [
            artifact
            for artifact in package["retainedArtifacts"]
            if artifact["digest"] == record_artifact["digest"]
        ]
        assert len(matching) == 1
        retained_bytes[record_artifact["artifactId"]] = _artifact_file(
            package_path, matching[0]
        ).read_bytes()
    _assert_resolution_evidence(
        policy, policy_bytes, record, retained_bytes
    )
    assert _file_digest(_artifact_file(package_path, lock_artifact)) == (
        lock_artifact["digest"]
    )
    assert evidence["policy"] == policy
    assert evidence["lock"] == record
    return policy_artifact, lock_artifact


def _assert_existing_document_is_pinned(
    package, package_path, evidence_member, schema_path
):
    document = package["evidence"][evidence_member]
    _validate(document, schema_path)
    matches = []
    for artifact in package["retainedArtifacts"]:
        data = _artifact_file(package_path, artifact).read_bytes()
        if (
            artifact["digest"] == _file_digest_bytes(data)
            and json.loads(data) == document
        ):
            matches.append((artifact, data))
    assert len(matches) == 1, (
        f"missing or substituted retained {evidence_member} bytes"
    )
    return matches[0]


def _tm_reference_values(value, prefix=""):
    if isinstance(value, dict):
        for key, child in value.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            pointer = prefix + "/" + escaped
            if key == "tm:ref":
                yield pointer, child
            yield from _tm_reference_values(child, pointer)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            pointer = prefix + "/" + str(index)
            yield from _tm_reference_values(child, pointer)


def _assert_supported_interpretation_inputs(root_document, definition):
    assert root_document.get("@context") == definition["context"]
    assert definition["processing"]["remoteContexts"] == "unsupported"
    assert definition["processing"]["externalSchemas"] == "unsupported"
    assert not any(
        key in root_document
        for key in ("$schema", "schema", "schemas", "remoteContext")
    )


def _assert_profile_definition_retained(package, package_path):
    definition_digest = _file_digest(PROCESSING_PROFILE_DEFINITION)
    retained = [
        artifact
        for artifact in package["retainedArtifacts"]
        if artifact["digest"] == definition_digest
    ]
    assert len(retained) == 1, "missing retained profile definition"
    assert _file_digest(_artifact_file(package_path, retained[0])) == (
        definition_digest
    )


def _assert_consumer_supported_profile(
    descriptor, installed_profile_id, reviewed_definition_version,
    reviewed_definition_digest,
):
    assert descriptor["id"] == installed_profile_id
    assert descriptor["definition"]["version"] == reviewed_definition_version
    assert descriptor["definition"]["digest"] == reviewed_definition_digest


def _assert_configuration_rule_matches_record(configuration, record):
    rule = configuration["rules"][0]
    edge = record["core"]["edges"][0]
    target = next(
        artifact
        for artifact in record["core"]["artifacts"]
        if artifact["artifactId"] == edge["to"]
    )
    registry = target["registry"]
    authority = rule["authority"]
    scope = authority["scope"]

    assert rule["role"] == edge["role"]
    assert rule["expectedKind"] == target["kind"]
    assert rule["expectedIdentity"] == target["identity"]
    assert authority["adapter"] == (
        "https://xregistry.io/workingdrafts/models/wot/adapters/xregistry/1"
    )
    assert authority["origin"] == registry["origin"]
    assert scope["groupCollection"] == registry["groupCollection"]
    assert scope["groupId"] == registry["groupId"]
    assert scope["resourceCollection"] == registry["resourceCollection"]
    assert rule["selection"] == edge["selection"]
    if "resourceId" in scope:
        assert scope["resourceId"] == registry["resourceId"]
    if rule["selection"]["mode"] == "exact":
        assert rule["selection"]["versionId"] == registry["versionId"]
    if "expectedDigest" in rule:
        assert rule["expectedDigest"] == target["digest"]


def test_wot_local_definition_branch_contract():
    package = _read_json(LOCAL_INVOCATION_EVIDENCE)
    _validate(package, EVIDENCE_SCHEMA)
    evidence = package["evidence"]

    assert evidence["kind"] == "local-definition"
    assert {
        "invocation",
        "invocationDigest",
        "localReferences",
        "output",
    } <= evidence.keys()
    assert not {"policy", "lock"} & evidence.keys()
    assert "effectivePolicyDigest" not in evidence["invocation"]
    _assert_invocation_digest(evidence)
    _assert_evidence_output_digest(evidence)
    assert evidence["output"]["value"] == _read_json(
        PROCESSING_SAMPLES / "local-output.json"
    )

    for invalid in ("output",):
        for member in ("digestScope", "digest", "value"):
            changed = copy.deepcopy(package)
            del changed["evidence"][invalid][member]
            with pytest.raises(jsonschema.ValidationError):
                _validate(changed, EVIDENCE_SCHEMA)

    wrong_scope = copy.deepcopy(package)
    wrong_scope["evidence"]["output"]["digestScope"] = (
        "decoded-file-octets"
    )
    with pytest.raises(jsonschema.ValidationError):
        _validate(wrong_scope, EVIDENCE_SCHEMA)

    wrong_digest = copy.deepcopy(package)
    wrong_digest["evidence"]["output"]["digest"] = "sha-256:" + "0" * 64
    with pytest.raises(AssertionError):
        _assert_evidence_output_digest(wrong_digest["evidence"])

    changed_value = copy.deepcopy(package)
    changed_value["evidence"]["output"]["value"] = {
        "substituted": "not the reviewed definition"
    }
    with pytest.raises(AssertionError):
        _assert_evidence_output_digest(changed_value["evidence"])

    for forbidden in ("policy", "lock"):
        changed = copy.deepcopy(package)
        changed["evidence"][forbidden] = {}
        with pytest.raises(jsonschema.ValidationError):
            _validate(changed, EVIDENCE_SCHEMA)

    changed_policy_digest = copy.deepcopy(package)
    changed_policy_digest["evidence"]["invocation"][
        "effectivePolicyDigest"
    ] = evidence["invocationDigest"]
    with pytest.raises(jsonschema.ValidationError):
        _validate(changed_policy_digest, EVIDENCE_SCHEMA)

    coerced = copy.deepcopy(package)
    coerced["evidence"]["kind"] = "retained-resolution"
    with pytest.raises(jsonschema.ValidationError):
        _validate(coerced, EVIDENCE_SCHEMA)


def test_wot_retained_resolution_branch_contract():
    for case in RETAINED_RESOLUTION_CASES:
        _assert_retained_resolution_branch_contract(case[1])


def _assert_retained_resolution_branch_contract(package_path):
    package = _read_json(package_path)
    _validate(package, EVIDENCE_SCHEMA)
    evidence = package["evidence"]

    assert evidence["kind"] == "retained-resolution"
    assert evidence["policy"]["profile"] == PROFILE
    assert evidence["lock"]["core"]["profile"] == PROFILE
    assert evidence["invocation"]["effectivePolicyDigest"].startswith(
        "sha-256:"
    )
    _assert_invocation_digest(evidence)
    _assert_evidence_output_digest(evidence)
    assert evidence["output"]["value"] == _read_json(
        PROCESSING_SAMPLES / "imported-output.json"
    )
    _assert_retained_bindings_match_artifacts(package, package_path)

    for member in ("policy", "lock", "output", "invocationDigest"):
        changed = copy.deepcopy(package)
        del changed["evidence"][member]
        with pytest.raises(jsonschema.ValidationError):
            _validate(changed, EVIDENCE_SCHEMA)

    changed_policy = copy.deepcopy(package)
    changed_policy["evidence"]["policy"]["rootDigest"] = (
        "sha-256:" + "0" * 64
    )
    with pytest.raises(AssertionError):
        _assert_retained_bindings_match_artifacts(
            changed_policy, package_path
        )

    changed_profile = copy.deepcopy(package)
    changed_profile["evidence"]["policy"]["profile"] = "urn:substitute"
    with pytest.raises(
        (AssertionError, jsonschema.ValidationError)
    ):
        _assert_retained_bindings_match_artifacts(
            changed_profile, package_path
        )

    missing_policy_input = copy.deepcopy(package)
    policy_artifact, _ = _assert_existing_document_is_pinned(
        package,
        package_path,
        "policy",
        SCHEMAS / "resolution-policy.schema.json",
    )
    missing_policy_input["retainedArtifacts"] = [
        artifact
        for artifact in missing_policy_input["retainedArtifacts"]
        if artifact["digest"] != policy_artifact["digest"]
    ]
    with pytest.raises(
        AssertionError,
        match="missing or substituted retained policy bytes",
    ):
        _assert_retained_bindings_match_artifacts(
            missing_policy_input, package_path
        )

    changed_lock = copy.deepcopy(package)
    changed_lock["evidence"]["lock"]["core"]["policyDigest"] = (
        "sha-256:" + "0" * 64
    )
    with pytest.raises(AssertionError):
        _assert_retained_bindings_match_artifacts(
            changed_lock, package_path
        )


def test_wot_local_references_map_original_document_pointers():
    packages = []
    for case_name, package_path, *_ in EVIDENCE_CASES:
        package = _read_json(package_path)
        _validate(package, EVIDENCE_SCHEMA)
        packages.append((case_name, package, package_path))

    local = next(package for name, package, _ in packages if name == "local")
    local_path = LOCAL_INVOCATION_EVIDENCE
    local_references = local["evidence"]["localReferences"]
    assert local_references
    assert all(
        set(reference) == {"from", "sourcePointer", "targetPointer"}
        for reference in local_references
    )
    assert all(
        set(reference["from"])
        == {"digestScope", "digest", "documentUrl", "interpretationBase"}
        for reference in local_references
    )
    _assert_local_reference_closure(local, local_path)
    for case_name, package, package_path in packages:
        assert "localReferences" in package["evidence"]
        if case_name != "local":
            assert package["evidence"]["localReferences"] == []
        assert all(
            set(reference["from"])
            == {
                "digestScope",
                "digest",
                "documentUrl",
                "interpretationBase",
            }
            for reference in package["evidence"]["localReferences"]
        )
        _assert_local_reference_closure(package, package_path)

    missing = copy.deepcopy(local)
    missing["evidence"]["localReferences"].pop()
    with pytest.raises(AssertionError):
        _assert_local_reference_closure(missing, local_path)

    conflicting = copy.deepcopy(local)
    conflicting["evidence"]["localReferences"].append(
        copy.deepcopy(conflicting["evidence"]["localReferences"][0])
    )
    with pytest.raises(AssertionError, match="conflicting local occurrence"):
        _assert_local_reference_closure(conflicting, local_path)

    different_target = copy.deepcopy(local)
    conflicting_reference = copy.deepcopy(
        different_target["evidence"]["localReferences"][0]
    )
    conflicting_reference["targetPointer"] = ""
    different_target["evidence"]["localReferences"].append(
        conflicting_reference
    )
    with pytest.raises(AssertionError):
        _assert_local_reference_closure(different_target, local_path)

    incorrect_pointer = copy.deepcopy(local)
    incorrect_pointer["evidence"]["localReferences"][0][
        "targetPointer"
    ] += "/not-present"
    from jsonpointer import JsonPointerException

    with pytest.raises((AssertionError, JsonPointerException)):
        _assert_local_reference_closure(incorrect_pointer, local_path)

    incorrect_source = copy.deepcopy(local)
    incorrect_source["evidence"]["localReferences"][0][
        "sourcePointer"
    ] += "/not-present"
    with pytest.raises(AssertionError):
        _assert_local_reference_closure(incorrect_source, local_path)

    provider_edge = copy.deepcopy(local)
    provider_edge["evidence"]["localReferences"][0]["provider"] = {
        "origin": "https://registry.example"
    }
    with pytest.raises(jsonschema.ValidationError):
        _validate(provider_edge, EVIDENCE_SCHEMA)

    for forbidden_member, value in (
        ("artifactId", "a1"),
        ("kind", "TM"),
        ("identity", "urn:example:local"),
    ):
        artifact_identity = copy.deepcopy(local)
        artifact_identity["evidence"]["localReferences"][0]["from"][
            forbidden_member
        ] = value
        with pytest.raises(jsonschema.ValidationError):
            _validate(artifact_identity, EVIDENCE_SCHEMA)


def test_wot_external_closure_can_be_empty_with_required_context_retained():
    package = _read_json(LOCAL_INVOCATION_EVIDENCE)
    _validate(package, EVIDENCE_SCHEMA)
    assert package["evidence"]["kind"] == "local-definition"
    assert not {"policy", "lock"} & package["evidence"].keys()
    assert package["retainedArtifacts"]

    definition = _read_json(PROCESSING_PROFILE_DEFINITION)
    profile_descriptor = _read_json(PROCESSING_PROFILE_DESCRIPTOR)
    definition_digest = _file_digest(PROCESSING_PROFILE_DEFINITION)
    assert profile_descriptor["definition"]["digest"] == definition_digest
    _assert_profile_definition_retained(package, LOCAL_INVOCATION_EVIDENCE)
    root_artifact = next(
        artifact
        for artifact in package["retainedArtifacts"]
        if artifact["digest"] == package["evidence"]["invocation"]["root"][
            "digest"
        ]
    )
    root_document = _read_json(_artifact_file(LOCAL_INVOCATION_EVIDENCE, root_artifact))
    _assert_supported_interpretation_inputs(root_document, definition)
    authored_references = [
        reference
        for _, reference in _tm_reference_values(root_document)
    ]
    assert authored_references
    assert all(
        isinstance(reference, str) and reference.startswith("#/")
        for reference in authored_references
    )

    missing_definition = copy.deepcopy(package)
    missing_definition["retainedArtifacts"] = [
        artifact
        for artifact in missing_definition["retainedArtifacts"]
        if artifact["digest"] != definition_digest
    ]
    with pytest.raises(AssertionError, match="missing retained profile definition"):
        _assert_profile_definition_retained(
            missing_definition, LOCAL_INVOCATION_EVIDENCE
        )

    missing_context = copy.deepcopy(root_document)
    del missing_context["@context"]
    with pytest.raises(AssertionError):
        _assert_supported_interpretation_inputs(missing_context, definition)


def test_wot_unknown_or_overridden_context_and_schema_dependencies_reject():
    definition = _read_json(PROCESSING_PROFILE_DEFINITION)
    root_document = _read_json(PROCESSING_SAMPLES / "local-root.tm.json")
    _assert_supported_interpretation_inputs(root_document, definition)

    invalid_documents = []
    remote_context = copy.deepcopy(root_document)
    remote_context["@context"] = "https://example.invalid/context.jsonld"
    invalid_documents.append(remote_context)
    overridden_context = copy.deepcopy(root_document)
    overridden_context["@context"]["tm"] = "https://attacker.invalid/tm#"
    invalid_documents.append(overridden_context)
    unknown_schema = copy.deepcopy(root_document)
    unknown_schema["$schema"] = "https://example.invalid/model.schema.json"
    invalid_documents.append(unknown_schema)
    overridden_schema = copy.deepcopy(root_document)
    overridden_schema["schemas"] = {
        "https://xregistry.io/supported.schema.json": (
            "https://attacker.invalid/override.json"
        )
    }
    invalid_documents.append(overridden_schema)
    for invalid in invalid_documents:
        with pytest.raises(AssertionError):
            _assert_supported_interpretation_inputs(invalid, definition)


def test_wot_retained_artifacts_are_separate_from_evidence():
    for _case_name, package_path, *_ in EVIDENCE_CASES:
        package = _read_json(package_path)
        _validate(package, EVIDENCE_SCHEMA)
        evidence = package["evidence"]
        assert "retainedArtifacts" not in evidence
        artifacts = package["retainedArtifacts"]
        assert len({item["artifactId"] for item in artifacts}) == len(artifacts)

        for artifact in artifacts:
            data = _artifact_file(package_path, artifact).read_bytes()
            assert artifact["digest"] == _file_digest_bytes(data)

        changed_artifact = copy.deepcopy(package)
        changed_artifact["retainedArtifacts"][0]["digest"] = (
            "sha-256:" + "0" * 64
        )
        with pytest.raises(AssertionError):
            assert changed_artifact["retainedArtifacts"][0]["digest"] == (
                _file_digest_bytes(
                    _artifact_file(
                        package_path, package["retainedArtifacts"][0]
                    ).read_bytes()
                )
            )

        evidence_substitution = copy.deepcopy(package)
        evidence_substitution["evidence"]["retainedArtifacts"] = artifacts
        with pytest.raises(jsonschema.ValidationError):
            _validate(evidence_substitution, EVIDENCE_SCHEMA)


def test_wot_evidence_archive_member_names_are_safe_relative_paths():
    rejected_paths = (
        "/absolute/member.json",
        "C:/drive/member.json",
        "C:\\drive\\member.json",
        "nested\\member.json",
        "../parent/member.json",
        "nested/../parent/member.json",
    )
    for _case_name, package_path, *_ in EVIDENCE_CASES:
        package = _read_json(package_path)
        _validate(package, EVIDENCE_SCHEMA)

        for artifact in package["retainedArtifacts"]:
            archive_path = artifact["archivePath"]
            relative_path = Path(archive_path)
            assert archive_path
            assert not relative_path.is_absolute()
            assert not relative_path.drive
            assert ".." not in relative_path.parts
            assert "\\" not in archive_path
            assert artifact["digest"] == _file_digest_bytes(
                _artifact_file(package_path, artifact).read_bytes()
            )

        safe_entry = copy.deepcopy(package)
        safe_entry["retainedArtifacts"][0]["archivePath"] = (
            "archive/safe-entry.json"
        )
        _validate(safe_entry, EVIDENCE_SCHEMA)

        for invalid_path in rejected_paths:
            unsafe_entry = copy.deepcopy(package)
            unsafe_entry["retainedArtifacts"][0]["archivePath"] = (
                invalid_path
            )
            with pytest.raises(jsonschema.ValidationError):
                _validate(unsafe_entry, EVIDENCE_SCHEMA)


def test_wot_consumer_requires_installed_reviewed_profile_support():
    descriptor = _read_json(PROCESSING_PROFILE_DESCRIPTOR)
    definition_bytes = PROCESSING_PROFILE_DEFINITION.read_bytes()
    definition = _read_json(PROCESSING_PROFILE_DEFINITION)
    reviewed_version = definition["version"]
    reviewed_digest = _file_digest_bytes(definition_bytes)
    supported_identity = descriptor["id"]

    assert descriptor["definition"]["id"] == definition["id"]
    assert descriptor["definition"]["version"] == reviewed_version
    assert descriptor["definition"]["digest"] == reviewed_digest
    _assert_consumer_supported_profile(
        descriptor, supported_identity, reviewed_version, reviewed_digest
    )

    for field, replacement in (
        ("id", "https://example.invalid/unsupported-profile"),
        ("version", reviewed_version + "-unreviewed"),
        ("digest", "sha-256:" + "0" * 64),
    ):
        unsupported = copy.deepcopy(descriptor)
        if field == "id":
            unsupported["id"] = replacement
        else:
            unsupported["definition"][field] = replacement
        with pytest.raises(AssertionError):
            _assert_consumer_supported_profile(
                unsupported,
                supported_identity,
                reviewed_version,
                reviewed_digest,
            )

    # A syntactically valid descriptor claim is not support without the
    # consumer's independently installed identity and reviewed definition.
    with pytest.raises(AssertionError):
        _assert_consumer_supported_profile(
            descriptor, "https://example.invalid/not-installed",
            reviewed_version, reviewed_digest,
        )


def test_wot_closed_local_definition_and_imported_branch_behavior():
    local = _read_json(LOCAL_INVOCATION_EVIDENCE)
    retained = _read_json(RETAINED_INVOCATION_EVIDENCE)
    _validate(local, EVIDENCE_SCHEMA)
    _validate(retained, EVIDENCE_SCHEMA)

    branch_mutations = []
    for field in ("policy", "lock"):
        changed = copy.deepcopy(local)
        changed["evidence"][field] = {}
        branch_mutations.append(changed)
    changed = copy.deepcopy(local)
    changed["evidence"]["invocation"]["effectivePolicyDigest"] = (
        retained["evidence"]["invocation"]["effectivePolicyDigest"]
    )
    branch_mutations.append(changed)
    changed = copy.deepcopy(retained)
    del changed["evidence"]["policy"]
    branch_mutations.append(changed)
    changed = copy.deepcopy(retained)
    del changed["evidence"]["lock"]
    branch_mutations.append(changed)
    changed = copy.deepcopy(retained)
    del changed["evidence"]["invocation"]["effectivePolicyDigest"]
    branch_mutations.append(changed)
    changed = copy.deepcopy(local)
    changed["evidence"]["kind"] = "retained-resolution"
    branch_mutations.append(changed)
    changed = copy.deepcopy(retained)
    changed["evidence"]["kind"] = "local-definition"
    branch_mutations.append(changed)

    for invalid in branch_mutations:
        with pytest.raises(jsonschema.ValidationError):
            _validate(invalid, EVIDENCE_SCHEMA)

    record = _read_json(IMPORTED_RECORD)
    for case in RETAINED_RESOLUTION_CASES:
        configuration = _read_json(case[3])
        _validate(configuration, PROCESSING_CONFIGURATION_SCHEMA)
        _assert_configuration_rule_matches_record(configuration, record)
    configuration = _read_json(PROCESSING_CONFIGURATION)

    for section, member, replacement, schema_rejects in (
        ("authority", "origin", "https://other-registry.example", False),
        (
            "authority",
            "scope",
            {
                "groupCollection": "thingmodelgroups",
                "groupId": "other-vendor",
                "resourceCollection": "thingmodels",
                "resourceId": "sensors",
            },
            False,
        ),
        ("rule", "expectedKind", "TD", True),
        ("rule", "expectedIdentity", "urn:example:other:model", False),
        (
            "authority",
            "adapter",
            "https://example.invalid/unsupported-adapter",
            True,
        ),
    ):
        changed = copy.deepcopy(configuration)
        if section == "authority":
            changed["rules"][0]["authority"][member] = replacement
        else:
            changed["rules"][0][member] = replacement
        with pytest.raises(AssertionError):
            _assert_configuration_rule_matches_record(changed, record)
        if schema_rejects:
            with pytest.raises(jsonschema.ValidationError):
                _validate(changed, PROCESSING_CONFIGURATION_SCHEMA)
        else:
            _validate(changed, PROCESSING_CONFIGURATION_SCHEMA)

    for forbidden in ("fallback", "fallbackConfiguration", "overlay", "extends"):
        changed = copy.deepcopy(configuration)
        changed[forbidden] = "implicit composition"
        with pytest.raises(jsonschema.ValidationError):
            _validate(changed, PROCESSING_CONFIGURATION_SCHEMA)
