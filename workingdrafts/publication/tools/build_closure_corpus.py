"""Build the byte-pinned closure fixture corpus.

The corpus is shared evidence for the publication closure contract: documents,
captured Registry JSON, closure descriptors, manifests, packages and expected
outcomes. Descriptors and expectations are written out by hand here, not
derived by the reference checker, so the checker is tested against independent
data.

Run ``python -m workingdrafts.publication.tools.build_closure_corpus`` to
rewrite the corpus, or add ``--check`` to compare it with the files on disk.
"""

import hashlib
import json
from pathlib import Path
import sys

from workingdrafts.publication.tools.closure_checker import (
    COMPOSITE_CLOSURE, DIALECT, SCHEMA_CLOSURE, SCHEMA_FORMAT, TD_CONTEXT, TM, UAV,
    WOT_CLOSURE, ExampleOpcUaMaterialization,
)
from workingdrafts.publication.tools.publication_examples import VersionDocuments

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "fixtures" / "closure-corpus"
MANIFEST = "corpus-manifest.json"

PUBLISHER = {"binding": "http", "endpoint": "https://publisher.example.test"}
ORIGIN = "https://author.example.test/registry"
SCOPE = "urn:example:closure-corpus"
SITE = "https://example.test/"
OPCUA = ExampleOpcUaMaterialization.extension
UNKNOWN = "urn:example:unknown-extension"
SINGULAR = {
    "thingdescriptiongroups": "thingdescriptiongroup",
    "thingdescriptions": "thingdescription",
    "thingmodelgroups": "thingmodelgroup",
    "thingmodels": "thingmodel",
    "schemagroups": "schemagroup",
    "schemas": "schema",
    "contextgroups": "contextgroup",
    "contexts": "context",
    "nodesetgroups": "nodesetgroup",
    "nodesets": "nodeset",
}
WOT_KINDS = ("thingdescriptions", "thingmodels")


def dump(value):
    return (json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def xid(group_type, group, kind, resource, version):
    return f"/{group_type}/{group}/{kind}/{resource}/versions/{version}"


def td_xid(resource, version):
    return xid("thingdescriptiongroups", "plant", "thingdescriptions", resource, version)


def tm_xid(resource, version):
    return xid("thingmodelgroups", "acme", "thingmodels", resource, version)


def schema_xid(resource, version):
    return xid("schemagroups", "acme", "schemas", resource, version)


CONTEXT = xid("contextgroups", "acme", "contexts", "pump", "1.0.0")
NODESET = xid("nodesetgroups", "acme", "nodesets", "pump", "1.0.0")
ADDRESS = schema_xid("address", "1.0.0")
COMMON = schema_xid("common", "2.1.0")
COMMON_NEXT = schema_xid("common", "2.2.0")
SEMVER = {
    "td": td_xid("pump-7", "1.0.0"),
    "template": td_xid("pump-template", "2.1.0"),
    "pump": tm_xid("pump", "1.4.0"),
    "base": tm_xid("base", "1.2.0"),
}
INCREMENTAL = {
    "td": td_xid("pump-7", "3"),
    "template": td_xid("pump-template", "2"),
    "pump": tm_xid("pump", "4"),
    "base": tm_xid("base", "2"),
}
PUMP_PREVIOUS = tm_xid("pump", "1.3.0")
BASE_GENERATED = tm_xid("base", "0.0.0-1")

TD_BASE = SITE + "things/pump-7.td.json"
TEMPLATE_BASE = SITE + "things/pump-template.td.json"
PUMP_BASE = SITE + "models/pump.tm.json"
BASE_BASE = SITE + "models/base.tm.json"
ADDRESS_BASE = SITE + "schemas/address.json"
COMMON_BASE = SITE + "schemas/common.json"
CONTEXT_BASE = SITE + "contexts/pump.jsonld"
NODESET_BASE = SITE + "nodesets/pump.xml"

SECURITY = {"securityDefinitions": {"nosec_sc": {"scheme": "nosec"}}, "security": ["nosec_sc"]}
LINE = {
    "td": "urn:example:pump-7:line-a",
    "template": "urn:example:pump-template:line-a",
    "pump": "urn:example:pump:line-a",
    "base": "urn:example:pump:base:line-a",
}


class Doc:
    def __init__(self, view, path, base, content, attributes):
        self.view = view
        self.path = path
        self.base = base
        self.raw = content if isinstance(content, bytes) else dump(content)
        self.attributes = attributes

    @property
    def parts(self):
        return self.view.strip("/").split("/")


def wot(view, path, base, content, wotid, origin="authored", line=None):
    attributes = {"versionorigin": origin, "format": "JSON-LD/1.1", "wotid": wotid}
    if line is not None:
        attributes["compatibilityline"] = line
    return Doc(view, path, base, content, attributes)


def schema_doc(view, path, base, content):
    return Doc(view, path, base, content, {
        "format": SCHEMA_FORMAT, "contenttype": "application/schema+json",
    })


# Documents ------------------------------------------------------------------


def pump_7(floor="2.0.0"):
    return {
        "@context": [TD_CONTEXT],
        "@type": "Thing",
        "id": "urn:example:pump-7",
        "title": "Pump 7",
        "version": {"instance": "1.0.0", "model": "1.4.0"},
        "links": [
            {"rel": "type", "href": "urn:example:pump", "type": "application/tm+json",
             "tm:minVersion": "1.2.0"},
            {"rel": "td:extends", "href": "./pump-template.td.json",
             "type": "application/td+json", "td:minVersion": floor},
        ],
        **SECURITY,
        "properties": {
            "speed": {"type": "number", "forms": [{"href": "https://pump-7.example.test/speed"}]},
        },
    }


def pump_7_incremental():
    return {
        "@context": [TD_CONTEXT, {"uav": UAV}],
        "@type": "Thing",
        "id": "urn:example:pump-7",
        "title": "Pump 7",
        "version": {"instance": "3"},
        "uav:compatibilityLine": LINE["td"],
        "links": [
            {"rel": "type", "href": "urn:example:pump", "type": "application/tm+json",
             "uav:compatibilityLine": LINE["pump"], "uav:minVersion": "4"},
            {"rel": "td:extends", "href": "./pump-template.td.json",
             "type": "application/td+json", "uav:compatibilityLine": LINE["template"]},
        ],
        **SECURITY,
        "properties": {
            "speed": {"type": "number", "forms": [{"href": "https://pump-7.example.test/speed"}]},
        },
    }


def template(instance, incremental=False):
    value = {
        "@context": [TD_CONTEXT, {"uav": UAV}] if incremental else [TD_CONTEXT],
        "@type": "Thing",
        "id": "urn:example:pump-template",
        "title": "Pump template",
        "version": {"instance": instance},
    }
    if incremental:
        value["uav:compatibilityLine"] = LINE["template"]
    value.update(SECURITY)
    value["properties"] = {
        "running": {"type": "boolean",
                    "forms": [{"href": "https://pump-7.example.test/running"}]},
    }
    return value


def pump_model(incremental=False):
    extends = {"rel": "tm:extends", "href": "./base.tm.json", "type": "application/tm+json"}
    status = {"tm:ref": "./base.tm.json#/properties/status"}
    value = {
        "@context": [TD_CONTEXT, "../contexts/pump.jsonld"],
        "@type": "tm:ThingModel",
        "id": "urn:example:pump",
        "title": "Pump",
        "version": {"model": "4" if incremental else "1.4.0"},
    }
    if incremental:
        value["uav:compatibilityLine"] = LINE["pump"]
        extends.update({"uav:compatibilityLine": LINE["base"], "uav:minVersion": "2"})
        status["uav:compatibilityLine"] = LINE["base"]
    else:
        extends["tm:minVersion"] = "1.0.0"
    value["exopc:nodeset"] = "../nodesets/pump.xml"
    value["links"] = [
        extends,
        {"rel": "describedby", "href": "../schemas/address.json",
         "type": "application/schema+json"},
    ]
    value["properties"] = {
        "location": {"model:ref": "../schemas/address.json#/$defs/postal"},
        "status": status,
        "mode": {
            "type": "object",
            "description": "The default is a literal value, not a reference.",
            "default": {"tm:ref": "./not-captured.tm.json"},
        },
    }
    return value


def pump_model_previous():
    return {
        "@context": [TD_CONTEXT],
        "@type": "tm:ThingModel",
        "id": "urn:example:pump",
        "title": "Pump",
        "version": {"model": "1.3.0"},
        "properties": {"status": {"type": "string"}},
    }


def base_model(model):
    return {
        "@context": [TD_CONTEXT],
        "@type": "tm:ThingModel",
        "id": "urn:example:pump:base",
        "title": "Pump base",
        "version": {"model": model},
        "properties": {"status": {"type": "string", "enum": ["running", "stopped"]}},
    }


def address(dynamic=False, title="Postal address"):
    value = {
        "$schema": DIALECT,
        "$id": ADDRESS_BASE,
        "title": title,
        "$defs": {
            "postal": {
                "type": "object",
                "properties": {
                    "street": {"$ref": "common.json#/$defs/text"},
                    "country": {"$ref": "common.json#country"},
                    "unit": {"$ref": "units/v2#/$defs/length"},
                    "next": {"$ref": "#/$defs/postal"},
                    "weird": {"$ref": "common.json#/$defs/a~1b~0c%25d"},
                    "note": {
                        "type": "string",
                        "examples": [{"$ref": "literal-examples.json"}],
                        "default": {"$ref": "literal-default.json"},
                        "x-note": {"$ref": "literal-unknown-keyword.json"},
                    },
                },
            },
            "code": {
                "enum": [{"$ref": "literal-enum.json"}],
                "const": {"$ref": "literal-const.json"},
            },
        },
    }
    if dynamic:
        value["$defs"]["tree"] = {"$dynamicRef": "#node"}
    return value


def common():
    return {
        "$schema": DIALECT,
        "$id": COMMON_BASE,
        "title": "Common definitions",
        "$defs": {
            "text": {"type": "string"},
            "country": {"$anchor": "country", "type": "string", "pattern": "^[A-Z]{2}$"},
            "a/b~c%d": {"$ref": "address.json#/$defs/postal"},
            "units": {
                "$id": "units/v2",
                "$defs": {
                    "length": {"$ref": "#meter"},
                    "meter": {"$anchor": "meter", "type": "number"},
                },
            },
        },
    }


def common_next():
    return {
        "$schema": DIALECT,
        "$id": COMMON_BASE,
        "title": "Common definitions, published under another base",
        "$defs": {"text": {"type": "string", "maxLength": 80}},
    }


NODESET_XML = (
    b'<?xml version="1.0" encoding="utf-8"?>\n'
    b'<UANodeSet xmlns="http://opcfoundation.org/UA/2011/03/UANodeSet.xsd">\n'
    b"  <NamespaceUris>\n"
    b"    <Uri>urn:example:pump</Uri>\n"
    b"  </NamespaceUris>\n"
    b"</UANodeSet>\n"
)


def shared_documents():
    return {
        "address": schema_doc(ADDRESS, "documents/schemas/address.json", ADDRESS_BASE,
                              address()),
        "common": schema_doc(COMMON, "documents/schemas/common.json", COMMON_BASE, common()),
        "context": Doc(CONTEXT, "documents/contexts/pump.jsonld", CONTEXT_BASE, {
            "@context": {
                "model": TM,
                "exopc": "urn:example:opcua-materialization#",
                "uav": UAV,
            },
        }, {"contenttype": "application/ld+json"}),
        "nodeset": Doc(NODESET, "documents/nodesets/pump.xml", NODESET_BASE, NODESET_XML,
                       {"contenttype": "application/xml"}),
    }


def semver_documents():
    documents = {
        "td": wot(SEMVER["td"], "documents/things/pump-7.json", TD_BASE, pump_7(),
                  "urn:example:pump-7"),
        "template": wot(SEMVER["template"], "documents/things/pump-template.json",
                        TEMPLATE_BASE, template("2.1.0"), "urn:example:pump-template"),
        "pump": wot(SEMVER["pump"], "documents/models/pump.json", PUMP_BASE, pump_model(),
                    "urn:example:pump"),
        "base": wot(SEMVER["base"], "documents/models/base.json", BASE_BASE,
                    base_model("1.2.0"), "urn:example:pump:base"),
    }
    documents.update(shared_documents())
    return documents


def incremental_documents():
    documents = {
        "td": wot(INCREMENTAL["td"], "documents/incremental/pump-7.json", TD_BASE,
                  pump_7_incremental(), "urn:example:pump-7", line=LINE["td"]),
        "template": wot(INCREMENTAL["template"], "documents/incremental/pump-template.json",
                        TEMPLATE_BASE, template("2", incremental=True),
                        "urn:example:pump-template", line=LINE["template"]),
        "pump": wot(INCREMENTAL["pump"], "documents/incremental/pump.json", PUMP_BASE,
                    pump_model(incremental=True), "urn:example:pump", line=LINE["pump"]),
        # Authored SemVer text in an Incremental registry: generated revision 2.
        "base": wot(INCREMENTAL["base"], "documents/incremental/base.json", BASE_BASE,
                    base_model("1.2.0"), "urn:example:pump:base", origin="generated",
                    line=LINE["base"]),
    }
    documents.update(shared_documents())
    return documents


# Descriptors ------------------------------------------------------------------


def binding(source, pointer, operator, href, target):
    return {"source": source, "pointer": pointer, "operator": operator, "href": href,
            "target": target}


def edge(source, pointer, label, href, base, target, target_pointer):
    return {"source": source, "pointer": pointer, "label": label, "href": href,
            "base": base, "target": target, "targetPointer": target_pointer}


def wot_closure(ids, entries=None, bindings=None):
    if bindings is None:
        bindings = [
            binding(ids["td"], "/links/0", "type", "urn:example:pump", ids["pump"]),
            binding(ids["td"], "/links/1", "td:extends", "./pump-template.td.json",
                    ids["template"]),
            binding(ids["pump"], "/links/0", "tm:extends", "./base.tm.json", ids["base"]),
            binding(ids["pump"], "/properties/status", "tm:ref",
                    "./base.tm.json#/properties/status", ids["base"]),
        ]
    return {"format": "wot-publication-closure/1", "entries": entries or [ids["td"]],
            "bindings": bindings}


def address_edges():
    postal = "/$defs/postal/properties/"
    return [
        edge(ADDRESS, postal + "street", "$ref", "common.json#/$defs/text", ADDRESS_BASE,
             COMMON, "/$defs/text"),
        edge(ADDRESS, postal + "country", "$ref", "common.json#country", ADDRESS_BASE,
             COMMON, "/$defs/country"),
        edge(ADDRESS, postal + "unit", "$ref", "units/v2#/$defs/length", ADDRESS_BASE,
             COMMON, "/$defs/units/$defs/length"),
        edge(ADDRESS, postal + "weird", "$ref", "common.json#/$defs/a~1b~0c%25d",
             ADDRESS_BASE, COMMON, "/$defs/a~1b~0c%d"),
        edge(COMMON, "/$defs/a~1b~0c%d", "$ref", "address.json#/$defs/postal", COMMON_BASE,
             ADDRESS, "/$defs/postal"),
    ]


def schema_closure(entries, edges):
    return {"format": "xregistry-schema-closure/1-experimental", "entries": entries,
            "edges": edges}


def model_edges(ids):
    return [edge(ids["pump"], "/properties/location", "tm:ref",
                 "../schemas/address.json#/$defs/postal", PUMP_BASE, ADDRESS,
                 "/$defs/postal")]


def describedby_edge(ids):
    return edge(ids["pump"], "/links/1", "describedby", "../schemas/address.json", PUMP_BASE,
                ADDRESS, "")


def materialization(ids, bindings=True):
    items = [{"source": ids["pump"], "pointer": "", "label": "nodeset",
              "href": "../nodesets/pump.xml", "target": NODESET}] if bindings else []
    return {"format": "example-opcua-materialization/0", "entries": [ids["td"]],
            "bindings": items}


def composite(ids, materialize=True, contexts=True, describedby=None):
    members = [
        {"role": "wot", "extension": WOT_CLOSURE},
        {"role": "schema", "extension": SCHEMA_CLOSURE},
    ]
    if materialize:
        members.append({"role": "opcua-materialization", "extension": OPCUA})
    value = {"format": "xregistry-composite-closure/1-experimental",
             "entries": [ids["td"]], "members": members}
    if describedby is not None:
        value["describedby"] = describedby
    if contexts:
        value["contexts"] = [{"uri": CONTEXT_BASE, "target": CONTEXT}]
    value["immutableContexts"] = [TD_CONTEXT]
    return value


# Scenarios ------------------------------------------------------------------


class Scenario:
    """Inputs of one corpus case before its manifest and package are written."""

    def __init__(self, documents, profile="semver"):
        self.documents = documents
        self.profile = profile
        self.versionmode = None
        self.registry_name = profile
        self.completeness = "offline-complete"
        self.extensions = {}
        self.required = []
        self.omit = set()
        self.paths = {}
        self.manifest_name = None

    def extension(self, uri, name, value):
        self.extensions[uri] = (name, value)
        self.required.append(uri)


def composite_scenario(documents, ids, profile, name, materialize=True):
    scenario = Scenario(documents, profile)
    composite_name = name if materialize else name + "-without-materialization"
    scenario.extension(COMPOSITE_CLOSURE, f"composite/{composite_name}",
                       composite(ids, materialize=materialize))
    scenario.extension(WOT_CLOSURE, f"wot/{name}", wot_closure(ids))
    scenario.extension(SCHEMA_CLOSURE, f"schema/{name}",
                       schema_closure([ids["td"]], model_edges(ids) + address_edges()))
    if materialize:
        scenario.extension(OPCUA, f"opcua/{name}", materialization(ids))
    return scenario


def semver(materialize=True):
    return composite_scenario(semver_documents(), SEMVER, "semver", "semver", materialize)


def registry_json(scenario):
    groups = {}
    model = {"groups": groups}
    registry = {"specversion": "1.0", "registryid": "closure-corpus"}
    if scenario.profile == "incremental":
        model["attributes"] = {"wotversionprofile": {
            "name": "wotversionprofile", "type": "string", "enum": ["incremental"],
            "strict": True, "readonly": True,
        }}
        registry["wotversionprofile"] = "incremental"
    registry["model"] = model
    wot_mode = scenario.versionmode or (
        "manual" if scenario.profile == "incremental" else "semver"
    )
    for document in scenario.documents.values():
        group_type, group, kind, resource, _, version = document.parts
        group_model = groups.setdefault(group_type, {
            "singular": SINGULAR[group_type], "resources": {},
        })
        group_model["resources"].setdefault(kind, {
            "singular": SINGULAR[kind], "hasdocument": True,
            "versionmode": wot_mode if kind in WOT_KINDS else "manual",
        })
        group_value = registry.setdefault(group_type, {}).setdefault(
            group, {SINGULAR[group_type] + "id": group},
        )
        resource_value = group_value.setdefault(kind, {}).setdefault(resource, {
            SINGULAR[kind] + "id": resource, "meta": {}, "versions": {},
        })
        resource_value["meta"]["defaultversionid"] = version
        resource_value["versions"][version] = {"versionid": version, **document.attributes}
    return registry


def descriptor(version, raw):
    return {"reference": {"registry": PUBLISHER, "version": version},
            "digest": "sha256:" + sha256(raw), "size": len(raw)}


def object_xid(name):
    return f"/publications/fixtures/objects/{name.replace('/', '-')}/versions/content"


def assemble(name, scenario, files):
    """Add one case's files to ``files``; returns the case's package path."""
    registry_path = f"registries/{scenario.registry_name}.json"
    registry_raw = dump(registry_json(scenario))
    objects = [(object_xid("registry/" + scenario.registry_name), registry_path, registry_raw)]
    documents = []
    for document in scenario.documents.values():
        if document.view in scenario.omit:
            continue
        documents.append({
            "viewVersion": document.view,
            "originRegistry": ORIGIN,
            "originVersion": document.view,
            "base": document.base,
            "content": descriptor(document.view, document.raw),
        })
        objects.append((document.view, document.path, document.raw))
    extensions = {}
    for uri, (object_name, value) in scenario.extensions.items():
        raw = dump(value)
        reference = object_xid(object_name)
        extensions[uri] = descriptor(reference, raw)
        objects.append((reference, f"descriptors/{object_name}.json", raw))
    manifest = {
        "format": "xregistry-publication/1",
        "scope": SCOPE,
        "capture": "assembled",
        "completeness": scenario.completeness,
        "registry": descriptor(objects[0][0], registry_raw),
        "documents": documents,
        "extensions": extensions,
        "requiredExtensions": scenario.required,
    }
    manifest_raw = dump(manifest)
    digest = sha256(manifest_raw)
    pin = descriptor(f"/publications/fixtures/snapshots/{digest}/versions/manifest",
                     manifest_raw)
    manifest_path = f"manifests/{scenario.manifest_name or name}.json"
    objects.insert(0, (pin["reference"]["version"], manifest_path, manifest_raw))
    package = {
        "format": "xregistry-publication-package/1",
        "context": {
            "format": "xregistry-open/1",
            "scope": SCOPE,
            "snapshot": pin,
            "registry": manifest["registry"],
            "completeness": scenario.completeness,
        },
        "objects": [],
    }
    for reference, path, raw in objects:
        path = scenario.paths.get(reference, path)
        package["objects"].append({"reference": {"registry": PUBLISHER, "version": reference},
                                   "path": path})
        if reference in scenario.paths:
            continue
        if files.get(path, raw) != raw:
            raise ValueError(f"two different files share the path {path}")
        files[path] = raw
    package_path = f"packages/{name}.json"
    files[package_path] = dump(package)
    return package_path


def open_memory(scenario, name="memory"):
    """Assemble one scenario in memory; returns its snapshot pin and a reader."""
    files = {}
    package = json.loads(files[assemble(name, scenario, files)])
    documents = VersionDocuments()
    for entry in package["objects"]:
        if entry["path"] in files:
            documents.put(entry["reference"], files[entry["path"]])
    return package["context"]["snapshot"], documents.read


def complete(reached):
    return {"package": "offline-complete", "domain": {"result": "complete"},
            "runtime": "not-established", "reached": sorted(reached)}


def incomplete(code, package="offline-complete"):
    return {"package": package, "domain": {"result": "incomplete", "code": code},
            "runtime": "not-established"}


ALL_SEMVER = [SEMVER["td"], SEMVER["template"], SEMVER["pump"], SEMVER["base"],
              ADDRESS, COMMON, CONTEXT]


def cases():
    """Return (name, description, scenario, expectation) for every corpus case."""
    result = []

    def case(name, description, scenario, expect):
        result.append((name, description, scenario, expect))

    case("complete", "Composite closure with WoT, schema and materialization members.",
         semver(), complete(ALL_SEMVER + [NODESET]))

    scenario = semver(materialize=False)
    case("without-materialization",
         "The composite does not select materialization; the captured NodeSet is not reached.",
         scenario, complete(ALL_SEMVER))

    scenario = semver()
    documents = scenario.documents
    documents["pump"] = wot(SEMVER["pump"], "documents/reformatted/pump.json", PUMP_BASE,
                            json.dumps(pump_model(), indent=4).encode("ascii") + b"\n",
                            "urn:example:pump")
    documents["address"] = schema_doc(
        ADDRESS, "documents/reformatted/address.json", ADDRESS_BASE,
        json.dumps(address(), separators=(",", ":")).encode("ascii"),
    )
    case("reformatted",
         "Whitespace-only changes produce other digests and the same closure.",
         scenario, complete(ALL_SEMVER + [NODESET]))

    scenario = semver()
    scenario.extensions[COMPOSITE_CLOSURE] = (
        "composite/describedby", composite(SEMVER, describedby="mandatory"),
    )
    scenario.extensions[SCHEMA_CLOSURE] = ("schema/describedby", schema_closure(
        [SEMVER["td"]], model_edges(SEMVER) + [describedby_edge(SEMVER)] + address_edges(),
    ))
    case("describedby-mandatory",
         "The composite makes describedby to a JSON Schema a required schema occurrence.",
         scenario, complete(ALL_SEMVER + [NODESET]))

    scenario = composite_scenario(incremental_documents(), INCREMENTAL, "incremental",
                                  "incremental")
    case("incremental",
         "Incremental profile with lines, revision floors and a generated revision.",
         scenario, complete([INCREMENTAL["td"], INCREMENTAL["template"],
                             INCREMENTAL["pump"], INCREMENTAL["base"], ADDRESS, COMMON,
                             CONTEXT, NODESET]))

    scenario = semver()
    scenario.documents = {"previous": wot(
        PUMP_PREVIOUS, "documents/models/pump-1-3-0.json", PUMP_BASE, pump_model_previous(),
        "urn:example:pump",
    ), **scenario.documents}
    scenario.registry_name = "semver-two-versions"
    case("two-versions",
         "The snapshot holds two Thing Model Versions; the binding selects 1.4.0.",
         scenario, complete(ALL_SEMVER + [NODESET]))

    bound = Scenario(scenario.documents)
    bound.registry_name = "semver-two-versions"
    bound.extension(COMPOSITE_CLOSURE, "composite/semver", composite(SEMVER))
    bound.extension(WOT_CLOSURE, "wot/bound-previous", wot_closure(SEMVER, bindings=[
        binding(SEMVER["td"], "/links/0", "type", "urn:example:pump", PUMP_PREVIOUS),
        binding(SEMVER["td"], "/links/1", "td:extends", "./pump-template.td.json",
                SEMVER["template"]),
    ]))
    bound.extension(SCHEMA_CLOSURE, "schema/empty", schema_closure([SEMVER["td"]], []))
    bound.extension(OPCUA, "opcua/empty", materialization(SEMVER, bindings=False))
    case("bound-below-model",
         "The binding selects 1.3.0, below the TD's version.model floor of 1.4.0.",
         bound, incomplete("unsatisfied"))

    scenario = Scenario({
        key: value for key, value in semver_documents().items()
        if key in ("address", "common")
    })
    scenario.registry_name = "schema-only"
    scenario.extension(SCHEMA_CLOSURE, "schema/schema-only",
                       schema_closure([ADDRESS], address_edges()))
    case("schema-only", "A standalone schema closure from one JSON Schema entry.",
         scenario, complete([ADDRESS, COMMON]))

    scenario = semver()
    scenario.documents["address"] = schema_doc(
        ADDRESS, "documents/schemas/address-dynamic.json", ADDRESS_BASE, address(dynamic=True),
    )
    case("dynamic-reference", "A reached schema uses $dynamicRef.", scenario,
         incomplete("unsupported-dynamic-reference"))

    scenario = semver()
    scenario.documents["common-next"] = schema_doc(
        COMMON_NEXT, "documents/schemas/common-2-2-0.json", SITE + "schemas/common-2.2.0.json",
        common_next(),
    )
    scenario.registry_name = "semver-ambiguous"
    case("ambiguous-identity",
         "Two captured schemas declare the same $id under different bases.",
         scenario, incomplete("ambiguous-identity"))

    scenario = semver()
    scenario.manifest_name = "complete"
    scenario.paths[NODESET] = "documents/nodesets/absent.xml"
    case("missing-bytes", "The package maps a captured document to a missing file.",
         scenario, {"error": "unavailable"})

    scenario = semver()
    scenario.manifest_name = "complete"
    scenario.paths[ADDRESS] = "documents/schemas/address-tampered.json"
    case("integrity", "The package maps a captured document to other bytes.", scenario,
         {"error": "integrity_error"})

    scenario = semver()
    scenario.completeness = "linked"
    scenario.omit.add(COMMON)
    case("linked-missing-target", "A linked snapshot omits a reached schema.", scenario,
         incomplete("missing-target", package="linked"))

    scenario = semver()
    scenario.extension(UNKNOWN, "unknown/base", {"format": "example-unknown/0"})
    case("unknown-required-extension", "The manifest requires an unknown extension.",
         scenario, {"error": "unsupported_operation"})

    scenario = semver()
    scenario.extensions[WOT_CLOSURE] = ("wot/conflicting", wot_closure(
        SEMVER, bindings=wot_closure(SEMVER)["bindings"] + [binding(
            SEMVER["pump"], "/properties/location", "tm:ref",
            "../schemas/address.json#/$defs/postal", ADDRESS,
        )],
    ))
    case("conflicting-ownership",
         "The WoT member also binds a tm:ref to a JSON Schema, which the schema member owns.",
         scenario, incomplete("conflicting-ownership"))

    scenario = semver()
    bindings = wot_closure(SEMVER)["bindings"]
    bindings[2] = dict(bindings[2], operator="tm:submodel")
    scenario.extensions[WOT_CLOSURE] = ("wot/contradictory", wot_closure(
        SEMVER, bindings=bindings,
    ))
    case("contradictory-binding", "A WoT binding names another operator for a link.",
         scenario, incomplete("contradictory-binding"))

    scenario = semver()
    scenario.extensions[SCHEMA_CLOSURE] = ("schema/missing-cycle", schema_closure(
        [SEMVER["td"]], model_edges(SEMVER) + address_edges()[:-1],
    ))
    case("missing-binding", "The schema member omits the edge that closes a cycle.",
         scenario, incomplete("missing-binding"))

    scenario = semver()
    scenario.extensions[SCHEMA_CLOSURE] = ("schema/literal", schema_closure(
        [SEMVER["td"]], model_edges(SEMVER) + address_edges() + [edge(
            ADDRESS, "/$defs/postal/properties/note/examples/0", "$ref",
            "literal-examples.json", ADDRESS_BASE, COMMON, "",
        )],
    ))
    case("literal-bound", "The schema member binds a $ref inside an examples value.",
         scenario, incomplete("unexpected-binding"))

    scenario = semver()
    scenario.extensions[COMPOSITE_CLOSURE] = ("composite/no-contexts",
                                              composite(SEMVER, contexts=False))
    case("live-context", "A JSON-LD context is neither captured nor declared immutable.",
         scenario, incomplete("live-context-required"))

    scenario = composite_scenario(incremental_documents(), INCREMENTAL, "semver",
                                  "incremental")
    scenario.registry_name = "integer-ids"
    case("integer-ids-without-profile",
         "Integer Version IDs in a Registry without wotversionprofile stay SemVer.",
         scenario, incomplete("profile-mismatch"))

    scenario = semver()
    scenario.documents["td"] = wot(
        SEMVER["td"], "documents/things/pump-7-major-cap.json", TD_BASE,
        pump_7(floor="1.0.0"), "urn:example:pump-7",
    )
    case("td-major-cap", "A td:minVersion of 1.0.0 excludes the bound template 2.1.0.",
         scenario, incomplete("unsatisfied"))

    ids = dict(SEMVER, base=BASE_GENERATED)
    documents = semver_documents()
    documents["base"] = wot(BASE_GENERATED, "documents/models/base-generated.json", BASE_BASE,
                            base_model("7"), "urn:example:pump:base", origin="generated")
    scenario = Scenario(documents)
    scenario.registry_name = "semver-generated"
    scenario.extension(COMPOSITE_CLOSURE, "composite/semver", composite(SEMVER))
    scenario.extension(WOT_CLOSURE, "wot/generated", wot_closure(ids))
    scenario.extension(SCHEMA_CLOSURE, "schema/semver",
                       schema_closure([SEMVER["td"]], model_edges(SEMVER) + address_edges()))
    scenario.extension(OPCUA, "opcua/semver", materialization(SEMVER))
    case("generated-floor", "A generated 0.0.0-1 Version does not satisfy a floor.",
         scenario, incomplete("unsatisfied"))
    return result


def build():
    """Return the corpus as a mapping from relative path to bytes."""
    files = {}
    index = {}
    for name, description, scenario, expect in cases():
        package = assemble(name, scenario, files)
        index[name] = {"description": description, "package": package, "expect": expect}
    tampered = dump(address(title="Postal address, altered after capture"))
    files["documents/schemas/address-tampered.json"] = tampered
    files["cases.json"] = dump({
        "format": "xregistry-closure-corpus-cases/1-experimental",
        "handlers": [OPCUA],
        "cases": index,
    })
    listing = [{"path": path, "size": len(raw), "sha256": sha256(raw)}
               for path, raw in sorted(files.items())]
    lines = "".join(f"{item['sha256']}  {item['path']}\n" for item in listing)
    files[MANIFEST] = dump({
        "format": "xregistry-closure-corpus/1-experimental",
        "corpusDigest": "sha256:" + sha256(lines.encode("ascii")),
        "files": listing,
    })
    return files


def on_disk(corpus=CORPUS):
    return {
        path.relative_to(corpus).as_posix(): path.read_bytes()
        for path in sorted(corpus.rglob("*")) if path.is_file()
    }


def write(files, corpus=CORPUS):
    for stale in set(on_disk(corpus)) - set(files) if corpus.exists() else ():
        (corpus / stale).unlink()
    for path, raw in files.items():
        target = corpus / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    files = build()
    if argv == ["--check"]:
        if on_disk() != files:
            print("closure corpus differs from build_closure_corpus.py output")
            return 1
        print(f"closure corpus matches: {len(files)} files")
        return 0
    if argv:
        print("usage: build_closure_corpus.py [--check]")
        return 2
    write(files)
    print(f"wrote {len(files)} files to {CORPUS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
