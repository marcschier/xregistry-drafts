"""Closure profile evidence: the shared corpus plus in-memory mutations."""

from copy import deepcopy
import hashlib
import json
import socket

import jsonschema
import pytest

from workingdrafts.publication.tools import build_closure_corpus as corpus
from workingdrafts.publication.tools.closure_checker import (
    CORPUS, DESCRIPTOR_SCHEMAS, SCHEMA_ARRAYS, ClosureError, ExampleOpcUaMaterialization,
    check_closure, decode_fragment, main, parse_pointer, resolve_uri, run_case,
    supported_extensions,
)
from workingdrafts.publication.tools.publication_examples import (
    Channels, PublicationError, VersionDocuments, load_package,
)

# Changing any corpus byte changes this value; consumers pin the same digest.
CORPUS_DIGEST = "sha256:adcd8fb8cc531d253049e25ec87f096fcda886496d7dca6a392a645b50af0506"
HANDLERS = (ExampleOpcUaMaterialization(),)
CASES = json.loads((CORPUS / "cases.json").read_text(encoding="utf-8"))["cases"]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("closure checking opened a network connection")

    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def domain(scenario, handlers=HANDLERS):
    pin, read = corpus.open_memory(scenario)
    report = check_closure(pin, read, handlers)
    assert report["runtime"] == "not-established"
    return report["domain"]


def replace(documents, key, value, **attributes):
    document = documents[key]
    documents[key] = corpus.Doc(document.view, document.path, document.base, value,
                                {**document.attributes, **attributes})


# Corpus ------------------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(CASES))
def test_corpus_case(name):
    assert run_case(CORPUS, CASES[name]) == CASES[name]["expect"]


def test_corpus_manifest_pins_every_file():
    manifest = json.loads((CORPUS / corpus.MANIFEST).read_bytes())
    files = corpus.on_disk()
    del files[corpus.MANIFEST]
    assert [item["path"] for item in manifest["files"]] == sorted(files)
    for item in manifest["files"]:
        raw = files[item["path"]]
        assert (item["size"], item["sha256"]) == (len(raw), sha256(raw))
        assert b"\r" not in raw
    lines = "".join(f"{item['sha256']}  {item['path']}\n" for item in manifest["files"])
    assert "sha256:" + sha256(lines.encode("ascii")) == manifest["corpusDigest"]
    assert manifest["corpusDigest"] == CORPUS_DIGEST


def test_builder_reproduces_the_corpus():
    assert corpus.build() == corpus.on_disk()


def test_checker_command_runs_every_case(capsys):
    assert main([str(CORPUS)]) == 0
    assert f"{len(CASES)} of {len(CASES)} closure cases passed" in capsys.readouterr().out


def test_descriptor_schemas_are_valid_and_cover_the_corpus():
    for schema in DESCRIPTOR_SCHEMAS.values():
        jsonschema.Draft202012Validator.check_schema(schema)
    for path, raw in corpus.on_disk().items():
        kind = path.split("/")[1] if path.startswith("descriptors/") else None
        uri = {"composite": corpus.COMPOSITE_CLOSURE, "schema": corpus.SCHEMA_CLOSURE,
               "wot": corpus.WOT_CLOSURE}.get(kind)
        if uri is not None:
            jsonschema.validate(json.loads(raw), DESCRIPTOR_SCHEMAS[uri])


def test_reached_versions_align_with_captured_digests():
    package, documents = load_package(CORPUS, name="packages/incremental.json")
    report = check_closure(package["context"]["snapshot"], documents.read, HANDLERS)
    manifest = json.loads(documents.read(package["context"]["snapshot"]["reference"]))
    captured = {item["viewVersion"]: item for item in manifest["documents"]}
    for item in report["reached"]:
        association = captured[item["version"]]
        raw = documents.read(association["content"]["reference"])
        assert item["digest"] == association["content"]["digest"] == "sha256:" + sha256(raw)
        assert item["versionid"] == item["version"].rsplit("/", 1)[1]
        assert item["base"] == association["base"]
    base = next(item for item in report["reached"]
                if item["version"] == corpus.INCREMENTAL["base"])
    assert base["versionOrigin"] == "generated"
    assert base["versionProfile"] == "incremental"
    assert base["compatibilityLine"] == corpus.LINE["base"]


def test_whitespace_changes_digests_but_not_the_closure():
    reports = {}
    values = {}
    for name in ("complete", "reformatted"):
        package, documents = load_package(CORPUS, name=f"packages/{name}.json")
        reports[name] = check_closure(package["context"]["snapshot"], documents.read, HANDLERS)
        values[name] = {item["version"]: json.loads(documents.read(
            {"registry": corpus.PUBLISHER, "version": item["version"]}))
            for item in reports[name]["reached"] if item["kind"] != "nodesets"}
    first, second = ({item["version"]: item["digest"] for item in reports[name]["reached"]}
                     for name in ("complete", "reformatted"))
    assert first.keys() == second.keys()
    assert {key for key in first if first[key] != second[key]} == {
        corpus.SEMVER["pump"], corpus.ADDRESS,
    }
    assert values["complete"] == values["reformatted"]


def test_channel_move_and_rollback_keep_the_pinned_closure():
    documents = VersionDocuments()
    packages = {}
    for name in ("complete", "two-versions"):
        package, loaded = load_package(CORPUS, name=f"packages/{name}.json")
        documents.objects.update(loaded.objects)
        packages[name] = package["context"]["snapshot"]
    with pytest.raises(PublicationError) as caught:
        Channels().create("stable", corpus.SCOPE, packages["complete"], documents.read)
    assert caught.value.code == "unsupported_operation"
    channels = Channels(supported_extensions(HANDLERS))
    channels.create("stable", corpus.SCOPE, packages["complete"], documents.read)
    pinned = deepcopy(channels.records["stable"]["head"])
    before = check_closure(pinned, documents.read, HANDLERS)
    channels.move("stable", 1, packages["two-versions"], documents.read)
    assert channels.records["stable"]["head"] == packages["two-versions"]
    assert check_closure(pinned, documents.read, HANDLERS) == before
    assert before["domain"] == {"result": "complete"}
    assert before["runtime"] == "not-established"
    channels.move("stable", 2, packages["complete"], documents.read)
    rolled_back = check_closure(channels.records["stable"]["head"], documents.read, HANDLERS)
    assert rolled_back == before
    assert rolled_back["runtime"] == "not-established"
    address =  {"registry": corpus.PUBLISHER, "version": corpus.ADDRESS}
    documents.put(address, documents.read(address).replace(b"Postal", b"postal"))
    with pytest.raises(PublicationError) as caught:
        check_closure(pinned, documents.read, HANDLERS)
    assert caught.value.code == "integrity_error"


def test_unsupported_member_prevents_completeness():
    pin, read = corpus.open_memory(corpus.semver())
    with pytest.raises(PublicationError) as caught:
        check_closure(pin, read)
    assert caught.value.code == "unsupported_operation"


# URI, fragment and pointer rules -------------------------------------------------


@pytest.mark.parametrize("reference, expected", [
    ("g;x?y#s", "http://a/b/c/g;x?y#s"),
    ("../g", "http://a/b/g"),
    ("../../../g", "http://a/g"),
    ("?y", "http://a/b/c/d;p?y"),
    ("#s", "http://a/b/c/d;p?q#s"),
    ("//g", "http://g"),
    ("./g/.", "http://a/b/c/g/"),
])
def test_rfc3986_resolution(reference, expected):
    assert resolve_uri("http://a/b/c/d;p?q", reference) == expected


def test_urn_bases_resolve_fragments_and_absolute_references():
    assert resolve_uri("urn:example:pump", "#/properties/a") == "urn:example:pump#/properties/a"
    assert resolve_uri("urn:example:pump", "urn:example:base") == "urn:example:base"


def test_pointer_and_fragment_decoding():
    assert parse_pointer("/a~1b/c~0d/") == ["a/b", "c~d", ""]
    assert decode_fragment("/$defs/a~1b~0c%25d") == "/$defs/a~1b~0c%d"
    for bad in ("/a~2", "a", "/~"):
        with pytest.raises(ClosureError) as caught:
            parse_pointer(bad)
        assert caught.value.code == "invalid-fragment"
    for bad in ("%zz", "%C3%28", "%2"):
        with pytest.raises(ClosureError) as caught:
            decode_fragment(bad)
        assert caught.value.code == "invalid-fragment"


# Static schema semantics ----------------------------------------------------------


def schema_only(address=None, common=None, edges=()):
    documents = {key: value for key, value in corpus.semver_documents().items()
                 if key in ("address", "common")}
    if address is not None:
        replace(documents, "address", address)
    if common is not None:
        replace(documents, "common", common)
    scenario = corpus.Scenario(documents)
    scenario.extension(corpus.SCHEMA_CLOSURE, "schema/memory", corpus.schema_closure(
        [corpus.ADDRESS], corpus.address_edges() + list(edges),
    ))
    return scenario


def postal(value, name, reference):
    value["$defs"]["postal"]["properties"][name] = {"$ref": reference}
    return value


def defs(value, name, schema):
    value["$defs"][name] = schema
    return value


def units(value, **members):
    value["$defs"]["units"].update(members)
    return value


@pytest.mark.parametrize("address, common, code", [
    (defs(corpus.address(), "tree", {"$recursiveRef": "#"}), None,
     "unsupported-dynamic-reference"),
    (None, defs(corpus.common(), "node", {"$dynamicAnchor": "node"}),
     "unsupported-dynamic-reference"),
    (None, dict(corpus.common(), **{"$schema": "http://json-schema.org/draft-07/schema#"}),
     "unsupported-dialect"),
    (None, units(corpus.common(), **{"$id": "units/v2#part"}), "invalid-identifier"),
    (None, defs(corpus.common(), "bad", {"$anchor": "1bad"}), "invalid-identifier"),
    (None, defs(corpus.common(), "duplicate", {"$anchor": "country"}), "conflicting-anchor"),
    (postal(corpus.address(), "street", "common.json#/$defs/absent"), None,
     "invalid-fragment"),
    (postal(corpus.address(), "country", "common.json#absent"), None, "invalid-fragment"),
    (postal(corpus.address(), "street", "common.json#/$defs/text/type"), None,
     "invalid-fragment"),
    (postal(corpus.address(), "street", "common.json#/$defs/~2"), None, "invalid-fragment"),
    (postal(corpus.address(), "weird", "common.json#/$defs/a~1b~0c%zzd"), None,
     "invalid-fragment"),
    (postal(corpus.address(), "street", "common.json#/$defs/%C3%28"), None,
     "invalid-fragment"),
    (postal(corpus.address(), "street", "missing.json"), None, "missing-target"),
    (defs(corpus.address(), "list", {"allOf": []}), None, "invalid-schema"),
    (defs(corpus.address(), "list", {"prefixItems": {"type": "string"}}), None,
     "invalid-schema"),
    (defs(corpus.address(), "pair", {"prefixItems": [True, {"$ref": "missing.json"}]}),
     None, "missing-target"),
    (defs(corpus.address(), "list", {"properties": []}), None, "invalid-schema"),
])
def test_static_schema_rejections(address, common, code):
    result = domain(schema_only(address, common))
    assert (result["result"], result["code"]) == ("incomplete", code)


@pytest.mark.parametrize("keyword", SCHEMA_ARRAYS)
def test_empty_schema_arrays_follow_the_2020_12_meta_schema(keyword):
    with pytest.raises(jsonschema.SchemaError):
        jsonschema.Draft202012Validator.check_schema({keyword: []})
    jsonschema.Draft202012Validator.check_schema({keyword: [True]})
    result = domain(schema_only(defs(corpus.address(), "list", {keyword: []})))
    assert (result["result"], result["code"]) == ("incomplete", "invalid-schema")


def test_version_format_selects_the_dialect():
    scenario = schema_only()
    replace(scenario.documents, "common", corpus.common(), format="JsonSchema/draft-07")
    assert domain(scenario)["code"] == "unsupported-dialect"


def test_schema_semantics_accepted():
    nested = "https://example.test/schemas/nested/inline.json"
    address = corpus.address()
    address["$defs"]["inline"] = {"$id": "nested/inline.json",
                                  "$ref": "../common.json#/$defs/text"}
    address["$defs"]["blocked"] = {"$ref": "common.json#/$defs/never"}
    common = units(corpus.common(), **{"$id": "units/v2#"})
    common["$defs"]["text"]["$anchor"] = "meter"
    common["$defs"]["never"] = False
    edges = [
        corpus.edge(corpus.ADDRESS, "/$defs/inline", "$ref", "../common.json#/$defs/text",
                    nested, corpus.COMMON, "/$defs/text"),
        corpus.edge(corpus.ADDRESS, "/$defs/blocked", "$ref", "common.json#/$defs/never",
                    corpus.ADDRESS_BASE, corpus.COMMON, "/$defs/never"),
    ]
    assert domain(schema_only(address, common, edges)) == {"result": "complete"}


def test_literal_values_are_not_scanned():
    address = corpus.address()
    address["$defs"]["postal"]["const"] = {"$ref": "missing.json"}
    address["examples"] = [{"$ref": "missing.json", "$dynamicRef": "#x"}]
    address["$defs"]["code"]["default"] = {"$recursiveRef": "#"}
    assert domain(schema_only(address)) == {"result": "complete"}


def test_edge_base_and_target_pointer_are_compared():
    edges = corpus.address_edges()
    edges[0] = dict(edges[0], targetPointer="/$defs/country")
    scenario = schema_only()
    scenario.extensions[corpus.SCHEMA_CLOSURE] = ("schema/memory", corpus.schema_closure(
        [corpus.ADDRESS], edges,
    ))
    assert domain(scenario)["code"] == "contradictory-binding"


# Composite closure -----------------------------------------------------------------


def with_pump(change):
    scenario = corpus.semver()
    value = corpus.pump_model()
    change(value)
    replace(scenario.documents, "pump", value)
    return scenario


def test_entry_names_are_not_references():
    def change(value):
        value["properties"]["tm:ref"] = {"type": "string"}
        value["properties"]["links"] = {"type": "array"}
    assert domain(with_pump(change)) == {"result": "complete"}


@pytest.mark.parametrize("change, code", [
    (lambda value: value["properties"]["mode"].update({"@context": {"x": "urn:x#"}}),
     "unsupported-context"),
    (lambda value: value["@context"].append({"@vocab": "urn:x#"}), "unsupported-context"),
    (lambda value: value.update({"uav:compatibilityLine": "urn:example:line"}),
     "invalid-line"),
    (lambda value: value["links"][0].update({"uav:compatibilityLine": "urn:example:line"}),
     "invalid-line"),
    (lambda value: value["links"][0].update({"uav:minVersion": "1.0.0"}), "invalid-floor"),
    (lambda value: value["links"][0].update({"tm:minVersion": "2.0.0"}), "unsatisfied"),
    (lambda value: value["links"][0].update({"tm:ref": "./base.tm.json"}),
     "ambiguous-occurrence"),
])
def test_wot_document_rejections(change, code):
    assert domain(with_pump(change))["code"] == code


def test_uav_floor_maps_onto_semver():
    def change(value):
        value["links"][0]["uav:minVersion"] = value["links"][0].pop("tm:minVersion")
    assert domain(with_pump(change)) == {"result": "complete"}


def bindings_without(index):
    bindings = corpus.wot_closure(corpus.SEMVER)["bindings"]
    del bindings[index]
    return bindings


@pytest.mark.parametrize("change, code", [
    (lambda s: s.extensions.update({corpus.WOT_CLOSURE: ("wot/memory", corpus.wot_closure(
        corpus.SEMVER, entries=[corpus.SEMVER["pump"]]))}), "entry-mismatch"),
    (lambda s: s.extensions.update({corpus.WOT_CLOSURE: ("wot/memory", corpus.wot_closure(
        corpus.SEMVER, bindings=corpus.wot_closure(corpus.SEMVER)["bindings"] + [dict(
            corpus.wot_closure(corpus.SEMVER)["bindings"][2], operator="tm:submodel")]))}),
     "duplicate-binding"),
    (lambda s: s.extensions.update({corpus.WOT_CLOSURE: ("wot/memory", corpus.wot_closure(
        corpus.SEMVER, bindings=bindings_without(3)))}), "missing-binding"),
    (lambda s: s.required.remove(corpus.OPCUA), "invalid-composite"),
    (lambda s: s.extensions.update({corpus.COMPOSITE_CLOSURE: ("composite/memory", dict(
        corpus.composite(corpus.SEMVER),
        contexts=[{"uri": "https://example.test/contexts/other.jsonld",
                   "target": corpus.CONTEXT}]))}), "invalid-composite"),
    (lambda s: s.extensions.update({corpus.SCHEMA_CLOSURE: ("schema/memory",
        corpus.schema_closure([corpus.SEMVER["td"]], corpus.model_edges(corpus.SEMVER)
                              + [corpus.describedby_edge(corpus.SEMVER)]
                              + corpus.address_edges()))}), "unexpected-binding"),
    (lambda s: s.extensions.update({corpus.COMPOSITE_CLOSURE: ("composite/memory",
        corpus.composite(corpus.SEMVER, describedby="mandatory"))}), "missing-binding"),
    (lambda s: s.extensions.update({corpus.OPCUA: ("opcua/memory", corpus.materialization(
        corpus.SEMVER, bindings=False))}), "missing-binding"),
    (lambda s: s.extensions.update({corpus.COMPOSITE_CLOSURE: ("composite/memory", dict(
        corpus.composite(corpus.SEMVER), members=[{"role": "wot",
                                                    "extension": corpus.WOT_CLOSURE}]))}),
     "invalid-descriptor"),
])
def test_composite_rejections(change, code):
    scenario = corpus.semver()
    change(scenario)
    assert domain(scenario)["code"] == code


def test_unselected_materialization_is_not_an_occurrence():
    scenario = corpus.semver(materialize=False)
    assert domain(scenario) == {"result": "complete"}
    scenario = corpus.semver(materialize=False)
    scenario.extension(corpus.OPCUA, "opcua/memory", corpus.materialization(corpus.SEMVER))
    assert domain(scenario) == {"result": "complete"}


# Incremental profile ---------------------------------------------------------------


def incremental(key, change, **attributes):
    scenario = corpus.composite_scenario(corpus.incremental_documents(), corpus.INCREMENTAL,
                                         "incremental", "incremental")
    value = json.loads(scenario.documents[key].raw)
    change(value)
    replace(scenario.documents, key, value, **attributes)
    return scenario


@pytest.mark.parametrize("key, change, code", [
    ("pump", lambda value: value.update({"uav:compatibilityLine": "urn:example:pump:line-b"}),
     "inconsistent-publication"),
    ("td", lambda value: value["links"][0].pop("uav:compatibilityLine"),
     "compatibility-required"),
    ("td", lambda value: value["links"][0].update({"uav:minVersion": "5"}), "unsatisfied"),
    ("td", lambda value: value["links"][0].update(
        {"uav:compatibilityLine": corpus.LINE["base"]}), "unsatisfied"),
    ("td", lambda value: value["links"][0].update({"tm:minVersion": "1.0.0"}),
     "invalid-floor"),
])
def test_incremental_rejections(key, change, code):
    assert domain(incremental(key, change))["code"] == code


def test_incremental_line_change_is_reported_from_metadata():
    scenario = incremental("pump", lambda value: None, compatibilityline="urn:example:other")
    assert domain(scenario)["code"] == "inconsistent-publication"
