# SPDX-License-Identifier: Apache-2.0
"""Incremental version profile vectors and the model.json overlay."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import jsonschema
from jsonschema.validators import validator_for
import pytest

from workingdrafts.models.wot.tests.resolution import check_incremental


WOT = Path(__file__).resolve().parents[1]
REPO = WOT.parents[2]
CASES = check_incremental.load_vectors()
RESOURCES = (
    ("thingmodelgroups", "thingmodels"),
    ("thingdescriptiongroups", "thingdescriptions"),
)


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_model(path):
    spec = importlib.util.spec_from_file_location(
        "schema_generator", REPO / "tools" / "schema-generator.py"
    )
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    return generator.resolve_imports(str(path.parent), _load(path))


def _strip_descriptions(value):
    if isinstance(value, dict):
        return {
            key: _strip_descriptions(item)
            for key, item in value.items()
            if key != "description"
        }
    if isinstance(value, list):
        return [_strip_descriptions(item) for item in value]
    return value


def _expected_overlay(base):
    """Apply the incremental model's overrides to the resolved SemVer model."""
    model = deepcopy(base)
    model["attributes"] = {
        "wotversionprofile": {
            "type": "string",
            "required": True,
            "enum": ["incremental"],
            "strict": True,
            "readonly": True,
            "default": "incremental",
        }
    }
    for group_name, resource_name in RESOURCES:
        group = model["groups"][group_name]
        resource = group["resources"][resource_name]
        resource["versionmode"] = "manual"
        resource["singleversionroot"] = False
        if "metaattributes" in resource:
            resource["metaattributes"] = {}
        resource["attributes"]["compatibilityline"] = {
            "type": "uri",
            "immutable": True,
        }
    return model


@pytest.mark.parametrize("name", sorted(CASES))
def test_incremental_vector(name):
    check_incremental.check_case(name, CASES[name])


def test_incremental_vectors_match_schema():
    schema = _load(WOT / "tests" / "resolution" / "incremental.schema.json")
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(CASES)


def test_incremental_vectors_cover_every_operation():
    operations = {case["operation"] for case in CASES.values()}
    assert operations == set(check_incremental.OPERATIONS)


@pytest.mark.parametrize("pin_kind", ["versionid", "digest"])
def test_unambiguous_replay_does_not_require_a_known_profile(pin_kind):
    case = deepcopy(CASES["i021-replay-versionid-other-line"])
    case["profile"] = "unknown"
    selected = case["registry"][0]["versions"][1]
    pin_value = selected["versionid" if pin_kind == "versionid" else "contentdigest"]
    case["pin"] = {pin_kind: pin_value}
    result = check_incremental.replay(case)
    assert result == {
        "wotid": case["reference"]["target"],
        "versionid": selected["versionid"],
        "contentdigest": selected["contentdigest"],
        "origin": check_incremental.ORIGIN,
    }
    case["expect"] = {"result": {key: value for key, value in result.items() if key != "origin"}}
    schema = _load(WOT / "tests" / "resolution" / "incremental.schema.json")
    jsonschema.Draft202012Validator(schema).validate({"i999-unknown-replay": case})


def test_duplicate_digest_replay_requires_a_known_profile():
    case = deepcopy(CASES["i020-replay-digest-duplicate-highest"])
    case["profile"] = "unknown"
    with pytest.raises(check_incremental.OutcomeError, match="^unknown-profile$"):
        check_incremental.replay(case)


def test_canonical_revision_order_does_not_convert_integers():
    small = "9" * 200
    large = "1" + "0" * 200
    assert check_incremental.revision_key(large) > check_incremental.revision_key(small)


def test_overlay_differs_from_base_model_only_in_declared_profile():
    base = _load_model(WOT / "model.json")
    overlay = _load_model(WOT / "model-incremental.json")
    assert _strip_descriptions(overlay) == _strip_descriptions(_expected_overlay(base))


def test_base_model_declares_no_incremental_profile():
    base = _load(WOT / "model.json")
    assert base["attributes"]["wotversionprofile"]["enum"] == ["semver"]
    for group_name, resource_name in RESOURCES:
        resource = base["groups"][group_name]["resources"][resource_name]
        assert resource["versionmode"] == "semver"
        assert "compatibilityline" not in resource["attributes"]


@pytest.mark.parametrize("name", ["model.json", "model-incremental.json"])
def test_model_matches_core_model_schema(name):
    schema = _load(REPO / "core" / "model.schema.json")
    validator = validator_for(schema, default=jsonschema.Draft202012Validator)
    validator.check_schema(schema)
    errors = list(validator(schema).iter_errors(_load_model(WOT / name)))
    assert not errors, [error.message for error in errors]
