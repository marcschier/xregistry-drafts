# SPDX-License-Identifier: Apache-2.0
"""Incremental version profile vectors and the model.json overlay."""

from copy import deepcopy
import json
from pathlib import Path

import jsonschema
from jsonschema.validators import validator_for
import pytest

from workingdrafts.models.wot.tests.resolution import check_incremental


WOT = Path(__file__).resolve().parents[1]
REPO = WOT.parents[2]
CASES = check_incremental.load_vectors()
BASE_URL = "https://xregistry.io/xreg/domains/wot/specs/"
RESOURCES = (
    ("thingmodelgroups", "thingmodels"),
    ("thingdescriptiongroups", "thingdescriptions"),
)


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


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
    """Apply the declarations listed in spec section 5.5.1 to model.json."""
    model = deepcopy(base)
    model["attributes"] = {
        "wotversionprofile": {
            "name": "wotversionprofile",
            "type": "string",
            "required": True,
            "enum": ["incremental"],
            "strict": True,
            "readonly": True,
            "default": "incremental",
        }
    }
    compatibility = {
        "name": "compatibility",
        "type": "string",
        "required": True,
        "enum": ["none"],
        "strict": True,
        "default": "none",
    }
    for group_name, resource_name in RESOURCES:
        group = model["groups"][group_name]
        group["modelcompatiblewith"] = BASE_URL + "model-incremental.json"
        resource = group["resources"][resource_name]
        resource["modelcompatiblewith"] = BASE_URL + "model-incremental.json"
        resource["versionmode"] = "manual"
        resource["singleversionroot"] = False
        resource["metaattributes"] = {"compatibility": dict(compatibility)}
        attributes = {}
        for key, value in resource["attributes"].items():
            if key == "format":
                attributes["compatibilityline"] = {
                    "name": "compatibilityline",
                    "type": "uriabsolute",
                }
            attributes[key] = value
        resource["attributes"] = attributes
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


def test_canonical_revision_order_does_not_convert_integers():
    small = "9" * 200
    large = "1" + "0" * 200
    assert check_incremental.revision_key(large) > check_incremental.revision_key(small)


def test_overlay_differs_from_base_model_only_in_declared_profile():
    base = _load(WOT / "model.json")
    overlay = _load(WOT / "model-incremental.json")
    assert _strip_descriptions(overlay) == _strip_descriptions(_expected_overlay(base))
    assert list(
        overlay["groups"]["thingmodelgroups"]["resources"]["thingmodels"]["attributes"]
    ) == list(
        _expected_overlay(base)["groups"]["thingmodelgroups"]["resources"][
            "thingmodels"
        ]["attributes"]
    )
    assert overlay["description"]
    assert overlay["attributes"]["wotversionprofile"]["description"]
    for group_name, resource_name in RESOURCES:
        resource = overlay["groups"][group_name]["resources"][resource_name]
        assert resource["attributes"]["compatibilityline"]["description"]


def test_base_model_declares_no_incremental_profile():
    base = _load(WOT / "model.json")
    assert "wotversionprofile" not in base.get("attributes", {})
    for group_name, resource_name in RESOURCES:
        resource = base["groups"][group_name]["resources"][resource_name]
        assert resource["versionmode"] == "semver"
        assert "compatibilityline" not in resource["attributes"]


@pytest.mark.parametrize("name", ["model.json", "model-incremental.json"])
def test_model_matches_core_model_schema(name):
    schema = _load(REPO / "core" / "model.schema.json")
    validator = validator_for(schema, default=jsonschema.Draft202012Validator)
    validator.check_schema(schema)
    errors = list(validator(schema).iter_errors(_load(WOT / name)))
    assert not errors, [error.message for error in errors]
