"""Offline reference checker for the experimental closure profiles.

The checker derives schema closure and composite closure occurrences from
captured bytes and compares them with the closure descriptors of a pinned
publication. It reads bytes only through the caller's reader and opens no
network connection. It is an example, not a production Consumer.
"""

import json
from pathlib import Path
import re
import sys

import jsonschema

from workingdrafts.models.wot.tests.resolution import check_incremental, check_vectors
from workingdrafts.publication.tools.publication_examples import (
    PublicationError, _json, _xid_key, check_snapshot, checked_bytes, load_package,
    open_context,
)

ROOT = Path(__file__).resolve().parents[1]
WOT_ROOT = ROOT.parent / "models" / "wot"
CORPUS = ROOT / "fixtures" / "closure-corpus"

SCHEMA_CLOSURE = (
    "https://xregistry.io/workingdrafts/publication/profiles/schema-closure/1-experimental"
)
COMPOSITE_CLOSURE = (
    "https://xregistry.io/workingdrafts/publication/profiles/composite-closure/1-experimental"
)
WOT_CLOSURE = "http://opcfoundation.org/UA/WoT-Binding/publication-closure/1"
DIALECT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_FORMAT = "JsonSchema/draft/2020-12"

TD = "https://www.w3.org/2019/wot/td#"
TM = "https://www.w3.org/2019/wot/tm#"
UAV = "http://opcfoundation.org/UA/WoT-Binding/"
TD_CONTEXT = "https://www.w3.org/2022/wot/td/v1.1"
# Deliberate subset: only the prefixes the checker interprets.
BUILTIN_CONTEXTS = {TD_CONTEXT: {"td": TD, "tm": TM}}

THING_MODELS = "thingmodels"
THING_DESCRIPTIONS = "thingdescriptions"
SCHEMAS = "schemas"
WOT_KINDS = (THING_MODELS, THING_DESCRIPTIONS)

SCHEMA_MAPS = ("$defs", "properties", "patternProperties", "dependentSchemas")
SCHEMA_SINGLE = (
    "additionalProperties", "items", "contains", "propertyNames", "not", "if",
    "then", "else", "unevaluatedItems", "unevaluatedProperties", "contentSchema",
)
SCHEMA_ARRAYS = ("prefixItems", "allOf", "anyOf", "oneOf")
DYNAMIC = ("$dynamicRef", "$dynamicAnchor", "$recursiveRef", "$recursiveAnchor")
ANCHOR = re.compile(r"[A-Za-z_][-A-Za-z0-9._]*", re.ASCII)
INDEX = re.compile(r"0|[1-9][0-9]*", re.ASCII)
BAD_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")
BAD_TILDE = re.compile(r"~(?![01])")

LITERAL_MEMBERS = ("const", "default", "enum", "examples")
ENTRY_MAPS = (
    "properties", "actions", "events", "uriVariables", "schemaDefinitions",
    "securityDefinitions",
)
REFERENCE_MEMBERS = {TM + "ref": "tm:ref", TD + "ref": "td:ref"}
REFERENCE_TARGETS = {"tm:ref": (THING_MODELS, SCHEMAS), "td:ref": (THING_DESCRIPTIONS,)}
LINK_RELATIONS = {
    THING_MODELS: {"tm:extends": THING_MODELS, "tm:submodel": THING_MODELS},
    THING_DESCRIPTIONS: {
        "td:extends": THING_DESCRIPTIONS, "td:subthing": THING_DESCRIPTIONS,
        "type": THING_MODELS,
    },
}
VECTOR_KINDS = {
    "tm:extends": "extends", "tm:submodel": "submodel", "tm:ref": "ref",
    "td:extends": "td-extends", "td:subthing": "td-subthing", "td:ref": "td-ref",
    "type": "type",
}
REQUIREMENT_TERMS = {
    TM + "minVersion": "tm:minVersion",
    TD + "minVersion": "td:minVersion",
    UAV + "minVersion": "uav:minVersion",
    UAV + "compatibilityLine": "uav:compatibilityLine",
}
SCHEMA_MEDIA_TYPE = "application/schema+json"


class ClosureError(Exception):
    """A domain closure finding; package and integrity errors stay PublicationError."""

    def __init__(self, code, detail=""):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _load_schema(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


DESCRIPTOR_SCHEMAS = {
    SCHEMA_CLOSURE: _load_schema(ROOT / "schemas" / "schema-closure.json"),
    COMPOSITE_CLOSURE: _load_schema(ROOT / "schemas" / "composite-closure.json"),
    WOT_CLOSURE: _load_schema(WOT_ROOT / "schemas" / "publication-closure.schema.json"),
}


def validate_descriptor(schema, value, name):
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(value), key=str)
    if errors:
        raise ClosureError("invalid-descriptor", f"{name}: {errors[0].message}")


# RFC 3986 Section 5.2, applied exactly: no case or percent normalization.
_URI = re.compile(r"(?:([^:/?#]+):)?(?://([^/?#]*))?([^?#]*)(?:\?([^#]*))?(?:#(.*))?", re.S)


def _components(uri):
    return _URI.fullmatch(uri).groups()


def _remove_dot_segments(path):
    output = []
    while path:
        if path.startswith("../"):
            path = path[3:]
        elif path.startswith("./"):
            path = path[2:]
        elif path.startswith("/./"):
            path = "/" + path[3:]
        elif path == "/.":
            path = "/"
        elif path.startswith("/../") or path == "/..":
            path = "/" + path[4:]
            output[-1:] = []
        elif path in (".", ".."):
            path = ""
        else:
            end = path.find("/", 1 if path.startswith("/") else 0)
            end = len(path) if end < 0 else end
            output.append(path[:end])
            path = path[end:]
    return "".join(output)


def resolve_uri(base, reference):
    """Resolve a URI-reference against an absolute base URI (RFC 3986 5.2.2)."""
    scheme, authority, path, query, fragment = _components(reference)
    if scheme is None:
        base_scheme, base_authority, base_path, base_query, _ = _components(base)
        if base_scheme is None:
            raise ClosureError("invalid-base", base)
        scheme = base_scheme
        if authority is None:
            authority = base_authority
            if path == "":
                path = base_path
                query = base_query if query is None else query
            elif not path.startswith("/"):
                if base_authority is not None and base_path == "":
                    path = "/" + path
                else:
                    path = base_path[:base_path.rfind("/") + 1] + path
    path = _remove_dot_segments(path)
    result = scheme + ":"
    if authority is not None:
        result += "//" + authority
    result += path
    if query is not None:
        result += "?" + query
    if fragment is not None:
        result += "#" + fragment
    return result


def split_fragment(uri):
    """Return the URI without its fragment, and the fragment or None."""
    if "#" not in uri:
        return uri, None
    head, fragment = uri.split("#", 1)
    return head, fragment


def format_pointer(path):
    return "".join(
        "/" + str(token).replace("~", "~0").replace("/", "~1") for token in path
    )


def parse_pointer(text):
    """Parse an RFC 6901 JSON Pointer; a bad escape is an invalid fragment."""
    if text == "":
        return []
    if not text.startswith("/"):
        raise ClosureError("invalid-fragment", text)
    tokens = []
    for token in text[1:].split("/"):
        if BAD_TILDE.search(token):
            raise ClosureError("invalid-fragment", text)
        tokens.append(token.replace("~1", "/").replace("~0", "~"))
    return tokens


def decode_fragment(fragment):
    """Percent-decode a URI fragment as UTF-8."""
    if BAD_ESCAPE.search(fragment):
        raise ClosureError("invalid-fragment", fragment)
    raw = bytearray()
    index = 0
    while index < len(fragment):
        if fragment[index] == "%":
            raw.append(int(fragment[index + 1:index + 3], 16))
            index += 3
        else:
            raw.extend(fragment[index].encode("utf-8"))
            index += 1
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ClosureError("invalid-fragment", fragment) from error


def _evaluate(value, start, tokens, detail):
    node = value
    for token in start:
        node = node[token]
    path = list(start)
    for token in tokens:
        if isinstance(node, dict) and token in node:
            node = node[token]
            path.append(token)
        elif isinstance(node, list) and INDEX.fullmatch(token) and int(token) < len(node):
            node = node[int(token)]
            path.append(int(token))
        else:
            raise ClosureError("invalid-fragment", detail)
    return tuple(path)


def expand_term(name, terms):
    """Expand a member name: an exact term first, then a known prefix."""
    if name in terms:
        return terms[name]
    if ":" in name:
        prefix, suffix = name.split(":", 1)
        if prefix in terms and not suffix.startswith("//"):
            return terms[prefix] + suffix
    return name


class Document:
    """One captured Version document and its captured Registry metadata."""

    def __init__(self, association, raw, registry):
        self.xid = association["viewVersion"]
        self.key = _xid_key(self.xid)
        self.group_type, self.group_id, self.kind, self.resource_id = self.key[:4]
        self.version_id = self.key[5]
        self.base = split_fragment(association["base"])[0]
        self.raw = raw
        self.digest = association["content"]["digest"]
        resource = registry[self.group_type][self.group_id][self.kind][self.resource_id]
        self.version = resource["versions"][self.version_id]
        self._value = None

    @property
    def resource_key(self):
        return self.key[:4]

    def value(self):
        if self._value is None:
            try:
                self._value = (_json(self.raw),)
            except (PublicationError, UnicodeDecodeError, ValueError) as error:
                raise ClosureError("invalid-document", self.xid) from error
        return self._value[0]


class SchemaIndex:
    """Static identities, anchors, positions and references of one schema document."""

    def __init__(self):
        self.resources = {}
        self.anchors = {}
        self.positions = set()
        self.references = []
        self.error = None


def _walk_schema(index, node, path, base, resource):
    index.positions.add(path)
    if isinstance(node, bool):
        return
    pointer = format_pointer(path)
    if not isinstance(node, dict):
        raise ClosureError("invalid-schema", pointer)
    for keyword in DYNAMIC:
        if keyword in node:
            raise ClosureError("unsupported-dynamic-reference", pointer + "/" + keyword)
    if "$schema" in node and node["$schema"] != DIALECT:
        raise ClosureError("unsupported-dialect", pointer)
    if "$id" in node:
        identifier = node["$id"]
        if not isinstance(identifier, str):
            raise ClosureError("invalid-identifier", pointer)
        uri, fragment = split_fragment(resolve_uri(base, identifier))
        if fragment:
            raise ClosureError("invalid-identifier", pointer)
        base, resource = uri, path
        index.resources.setdefault(uri, set()).add(resource)
    if "$anchor" in node:
        name = node["$anchor"]
        if not isinstance(name, str) or not ANCHOR.fullmatch(name):
            raise ClosureError("invalid-identifier", pointer)
        anchors = index.anchors.setdefault(resource, {})
        if name in anchors:
            raise ClosureError("conflicting-anchor", pointer)
        anchors[name] = path
    if "$ref" in node:
        if not isinstance(node["$ref"], str):
            raise ClosureError("invalid-schema", pointer)
        index.references.append((path, node["$ref"], base))
    for keyword in SCHEMA_MAPS:
        if keyword in node:
            if not isinstance(node[keyword], dict):
                raise ClosureError("invalid-schema", pointer + "/" + keyword)
            for name, child in node[keyword].items():
                _walk_schema(index, child, path + (keyword, name), base, resource)
    for keyword in SCHEMA_SINGLE:
        if keyword in node:
            _walk_schema(index, node[keyword], path + (keyword,), base, resource)
    for keyword in SCHEMA_ARRAYS:
        if keyword in node:
            if not isinstance(node[keyword], list) or not node[keyword]:
                raise ClosureError("invalid-schema", pointer + "/" + keyword)
            for position, child in enumerate(node[keyword]):
                _walk_schema(index, child, path + (keyword, position), base, resource)


def analyze_schema(document):
    """Index one captured schema document; an error is kept until it is reached."""
    index = SchemaIndex()
    index.resources.setdefault(document.base, set()).add(())
    try:
        if document.version.get("format") != SCHEMA_FORMAT:
            raise ClosureError("unsupported-dialect", document.xid)
        _walk_schema(index, document.value(), (), document.base, ())
    except ClosureError as error:
        index.error = error
    return index


class Occurrence:
    def __init__(self, source, pointer, label, role, href, target, holder=None):
        self.source = source
        self.pointer = pointer
        self.label = label
        self.role = role
        self.href = href
        self.target = target
        self.holder = holder

    @property
    def key(self):
        return self.source.key, self.pointer, self.label


class Record:
    def __init__(self, role, source, pointer, label, href, target, extra):
        self.role = role
        self.key = (source, pointer, label)
        self.href = href
        self.target = target
        self.extra = extra


class ExampleOpcUaMaterialization:
    """Example member handler for the fixture corpus only.

    The OPC UA WoT Binding defines the real materialization extension. This
    stand-in shows how a composite Consumer plugs in a member it supports.
    """

    role = "opcua-materialization"
    extension = "urn:example:opcua-materialization"
    member = "urn:example:opcua-materialization#nodeset"
    label = "nodeset"
    target_kinds = ("nodesets",)
    schema = {
        "type": "object",
        "required": ["format", "entries", "bindings"],
        "properties": {
            "format": {"const": "example-opcua-materialization/0"},
            "entries": {"type": "array", "minItems": 1, "uniqueItems": True,
                        "items": {"type": "string"}},
            "bindings": {"type": "array", "items": {
                "type": "object",
                "required": ["source", "pointer", "label", "href", "target"],
                "properties": {
                    "source": {"type": "string"},
                    "pointer": {"type": "string", "pattern": "^(?:/(?:[^~/]|~[01])*)*$"},
                    "label": {"const": "nodeset"},
                    "href": {"type": "string"},
                    "target": {"type": "string"},
                },
                "additionalProperties": False,
            }},
        },
        "additionalProperties": False,
    }

    def recognize(self, iri):
        return self.label if iri == self.member else None

    def records(self, descriptor):
        validate_descriptor(self.schema, descriptor, self.extension)
        return descriptor["entries"], [
            (item["source"], item["pointer"], item["label"], item["href"],
             item["target"], {})
            for item in descriptor["bindings"]
        ]


def _wot_records(descriptor):
    validate_descriptor(DESCRIPTOR_SCHEMAS[WOT_CLOSURE], descriptor, WOT_CLOSURE)
    return descriptor["entries"], [
        (item["source"], item["pointer"], item["operator"], item["href"],
         item["target"], {})
        for item in descriptor["bindings"]
    ]


def _schema_records(descriptor):
    validate_descriptor(DESCRIPTOR_SCHEMAS[SCHEMA_CLOSURE], descriptor, SCHEMA_CLOSURE)
    return descriptor["entries"], [
        (item["source"], item["pointer"], item["label"], item["href"], item["target"],
         {"base": item["base"], "targetPointer": item["targetPointer"]})
        for item in descriptor["edges"]
    ]


def _decoded(xid):
    try:
        return _xid_key(xid)
    except PublicationError as error:
        raise ClosureError("invalid-descriptor", xid) from error


def _requirements(holder, terms):
    result = {}
    for name, value in holder.items():
        term = REQUIREMENT_TERMS.get(expand_term(name, terms))
        if term is not None:
            result[term] = value
    return result


class _Checker:
    def __init__(self, manifest, read_document, handlers):
        self.manifest = manifest
        self.read = read_document
        self.handlers = {handler.extension: handler for handler in handlers}
        self.active_handlers = []
        self.registry = _json(checked_bytes(manifest["registry"], read_document))
        self.documents = {}
        for association in manifest["documents"]:
            raw = checked_bytes(association["content"], read_document)
            document = Document(association, raw, self.registry)
            self.documents[document.key] = document
        self.schema_indexes = {}
        self.identities = None
        self.terms = {}
        self.describedby = "advisory"
        self.contexts = {}
        self.immutable = set()
        self.records = {}
        self.records_by_path = {}
        self.used = set()
        self.occurrences = {}
        self.reached = {}
        self.context_documents = set()
        self.profile = None

    # Captured identities ------------------------------------------------

    def schema_index(self, document):
        if document.key not in self.schema_indexes:
            self.schema_indexes[document.key] = analyze_schema(document)
        return self.schema_indexes[document.key]

    def schema_identities(self):
        if self.identities is None:
            self.identities = {}
            for document in self.documents.values():
                if document.kind == SCHEMAS:
                    for uri, paths in self.schema_index(document).resources.items():
                        for path in paths:
                            self.identities.setdefault(uri, set()).add((document.key, path))
        return self.identities

    def candidates(self, uri):
        """Captured documents identified by a fragment-free URI."""
        identities = self.schema_identities()
        matches = set()
        for document in self.documents.values():
            if document.base == uri:
                matches.add(document.key)
            elif document.kind in WOT_KINDS and document.version.get("wotid") == uri:
                matches.add(document.key)
            elif document.kind == SCHEMAS and (document.key, ()) in identities.get(uri, ()):
                matches.add(document.key)
        if not matches:
            raise ClosureError("missing-target", uri)
        documents = [self.documents[key] for key in matches]
        if len(matches) > 1 and not (
            all(document.kind in WOT_KINDS for document in documents)
            and len({document.resource_key for document in documents}) == 1
        ):
            raise ClosureError("ambiguous-identity", uri)
        return documents

    def apply_fragment(self, document, resource, fragment, detail):
        index = self.schema_index(document)
        if index.error is not None:
            raise index.error
        if not fragment:
            path = resource
        else:
            decoded = decode_fragment(fragment)
            if decoded.startswith("/"):
                path = _evaluate(document.value(), resource, parse_pointer(decoded), detail)
            elif ANCHOR.fullmatch(decoded) and decoded in index.anchors.get(resource, {}):
                path = index.anchors[resource][decoded]
            else:
                raise ClosureError("invalid-fragment", detail)
        if path not in index.positions:
            raise ClosureError("invalid-fragment", detail)
        return path

    def resolve_schema_reference(self, document, index, href, base):
        uri, fragment = split_fragment(resolve_uri(base, href))
        local = index.resources.get(uri)
        if local:
            if len(local) > 1:
                raise ClosureError("ambiguous-identity", uri)
            target, resource = document, next(iter(local))
        else:
            matches = {
                match for match in self.schema_identities().get(uri, ())
                if match[0] != document.key
            }
            if not matches:
                raise ClosureError("missing-target", uri)
            if len(matches) > 1:
                raise ClosureError("ambiguous-identity", uri)
            key, resource = matches.pop()
            target = self.documents[key]
        return target, self.apply_fragment(target, resource, fragment, href)

    # Contexts and profiles ----------------------------------------------

    def context_terms(self, document):
        if document.key not in self.terms:
            terms = {}
            self._apply_context(document.value().get("@context"), document.base, terms, set())
            self.terms[document.key] = terms
        return self.terms[document.key]

    def _apply_context(self, context, base, terms, active):
        if context is None:
            terms.clear()
        elif isinstance(context, list):
            for item in context:
                self._apply_context(item, base, terms, active)
        elif isinstance(context, str):
            uri = resolve_uri(base, context)
            if uri in self.contexts:
                document = self.contexts[uri]
                self.context_documents.add(document.key)
                if uri not in active:
                    value = document.value()
                    if not isinstance(value, dict) or "@context" not in value:
                        raise ClosureError("invalid-document", document.xid)
                    self._apply_context(
                        value["@context"], document.base, terms, active | {uri},
                    )
            elif uri not in self.immutable:
                raise ClosureError("live-context-required", uri)
            elif uri in BUILTIN_CONTEXTS:
                terms.update(BUILTIN_CONTEXTS[uri])
            else:
                raise ClosureError("unsupported-context", uri)
        elif isinstance(context, dict):
            for name, definition in context.items():
                if name in ("@vocab", "@import", "@context"):
                    raise ClosureError("unsupported-context", name)
                if name.startswith("@"):
                    continue
                if definition is None:
                    terms.pop(name, None)
                elif isinstance(definition, str):
                    terms[name] = expand_term(definition, terms)
                elif isinstance(definition, dict):
                    if "@context" in definition:
                        raise ClosureError("unsupported-context", name)
                    if isinstance(definition.get("@id"), str):
                        terms[name] = expand_term(definition["@id"], terms)
                else:
                    raise ClosureError("unsupported-context", name)
        else:
            raise ClosureError("unsupported-context", repr(context))

    def check_profiles(self):
        attribute = self.registry.get("wotversionprofile")
        if attribute not in (None, "incremental"):
            raise ClosureError("profile-mismatch", "wotversionprofile")
        self.profile = attribute or "semver"
        mode = "manual" if self.profile == "incremental" else "semver"
        pattern = check_incremental.REVISION if attribute else check_vectors.SEMVER
        groups = self.registry["model"]["groups"]
        for document in sorted(self.documents.values(), key=lambda item: item.xid):
            if document.kind not in WOT_KINDS:
                continue
            model = groups[document.group_type]["resources"][document.kind]
            if model.get("versionmode") != mode or not pattern.fullmatch(document.version_id):
                raise ClosureError("profile-mismatch", document.xid)

    # Bindings -------------------------------------------------------------

    def index_records(self, members):
        for role, items, member_key in members:
            seen = set()
            for source, pointer, label, href, target, extra in items:
                record = Record(role, _decoded(source), pointer, label, href,
                                _decoded(target), extra)
                local = member_key(record.key)
                if local in seen:
                    raise ClosureError("duplicate-binding", f"{source} {pointer}")
                seen.add(local)
                if record.key in self.records:
                    raise ClosureError("conflicting-ownership", f"{source} {pointer}")
                self.records[record.key] = record
                self.records_by_path.setdefault(record.key[:2], []).append(record)

    def bind(self, source, pointer, label, role, href, candidates, extra):
        """Select the bound target among the captured candidates of one occurrence."""
        key = (source.key, pointer, label)
        detail = f"{source.xid} {pointer} {label}"
        record = self.records.get(key)
        if record is None:
            located = self.records_by_path.get(key[:2], [])
            if any(item.role == role for item in located):
                raise ClosureError("contradictory-binding", detail)
            if located:
                raise ClosureError("conflicting-ownership", detail)
            raise ClosureError("missing-binding", detail)
        if record.role != role:
            raise ClosureError("conflicting-ownership", detail)
        keys = {document.key for document in candidates}
        if record.href != href or record.target not in keys:
            raise ClosureError("contradictory-binding", detail)
        target = self.documents[record.target]
        if record.extra != extra(target):
            raise ClosureError("contradictory-binding", detail)
        self.used.add(key)
        return target

    # Occurrence derivation ------------------------------------------------

    def add(self, occurrence, queue):
        if occurrence.key in self.occurrences:
            raise ClosureError("ambiguous-occurrence", occurrence.pointer)
        self.occurrences[occurrence.key] = occurrence
        queue.append(occurrence.target)

    def walk_schema(self, document, queue):
        index = self.schema_index(document)
        if index.error is not None:
            raise index.error
        for path, href, base in index.references:
            target, target_path = self.resolve_schema_reference(document, index, href, base)
            if target.key == document.key:
                continue
            pointer = format_pointer(path)
            extra = {"base": base, "targetPointer": format_pointer(target_path)}
            bound = self.bind(document, pointer, "$ref", "schema", href, [target],
                              lambda _target: extra)
            self.add(Occurrence(document, pointer, "$ref", "schema", href, bound), queue)

    def walk_wot(self, document, queue):
        value = document.value()
        if not isinstance(value, dict):
            raise ClosureError("invalid-document", document.xid)
        terms = self.context_terms(document)
        lines = [value[name] for name in value
                 if expand_term(name, terms) == UAV + "compatibilityLine"]
        if lines and self.profile != "incremental":
            raise ClosureError("invalid-line", document.xid)
        if lines and lines[0] != document.version.get("compatibilityline"):
            raise ClosureError("inconsistent-publication", document.xid)
        found = []
        links = value.get("links", [])
        if isinstance(links, list):
            for position, link in enumerate(links):
                if isinstance(link, dict) and isinstance(link.get("rel"), str):
                    found.append((("links", position), None, link["rel"], link, None))
        _scan_members(value, (), terms, self.active_handlers, found)
        by_path = {}
        for item in found:
            by_path.setdefault(item[0], []).append(item)
        for path in sorted(by_path, key=format_pointer):
            items = by_path[path]
            if sum(1 for item in items if item[1] is None) > 1:
                raise ClosureError("ambiguous-occurrence", format_pointer(path))
            for _, handler, label, holder, member in items:
                self.classify(document, path, handler, label, holder, member, queue)

    def classify(self, document, path, handler, label, holder, member, queue):
        pointer = format_pointer(path)
        if handler is not None:
            expected, role, href = handler.target_kinds, handler.role, holder[member]
        elif member is not None:
            expected, role, href = REFERENCE_TARGETS[label], "wot", holder[member]
        elif label == "describedby":
            if holder.get("type") != SCHEMA_MEDIA_TYPE or self.describedby != "mandatory":
                return
            expected, role, href = (SCHEMAS,), "schema", holder.get("href")
        elif label in LINK_RELATIONS[document.kind]:
            expected = (LINK_RELATIONS[document.kind][label],)
            role, href = "wot", holder.get("href")
        else:
            return
        if not isinstance(href, str):
            raise ClosureError("invalid-reference", pointer)
        if href.startswith("#"):
            return
        uri, fragment = split_fragment(resolve_uri(document.base, href))
        if uri in (document.base, document.version.get("wotid")):
            return
        candidates = self.candidates(uri)
        if any(candidate.kind not in expected for candidate in candidates):
            raise ClosureError("invalid-reference", pointer)
        if candidates[0].kind == SCHEMAS:
            role = "schema"
            target_path = self.apply_fragment(candidates[0], (), fragment, href)
            extra = {"base": document.base, "targetPointer": format_pointer(target_path)}
        else:
            extra = {}
        bound = self.bind(document, pointer, label, role, href, candidates,
                          lambda _target: extra)
        self.add(Occurrence(document, pointer, label, role, href, bound, holder), queue)

    def walk(self, entries):
        queue = [self.documents[key] for key in sorted(entries)]
        while queue:
            document = queue.pop(0)
            if document.key in self.reached:
                continue
            self.reached[document.key] = document
            if document.kind == SCHEMAS:
                self.walk_schema(document, queue)
            elif document.kind in WOT_KINDS:
                self.walk_wot(document, queue)
        for key in sorted(self.records):
            if key not in self.used:
                raise ClosureError("unexpected-binding", f"{key[1]} {key[2]}")

    # Requirements -----------------------------------------------------------

    def check_requirements(self):
        for key in sorted(self.occurrences):
            occurrence = self.occurrences[key]
            if occurrence.role == "wot":
                try:
                    self.check_requirement(occurrence)
                except check_vectors.OutcomeError as error:
                    raise ClosureError(
                        str(error), f"{occurrence.source.xid} {occurrence.pointer}",
                    ) from error

    def check_requirement(self, occurrence):
        """Snapshot-bound composition: the bound Version first, then requirements."""
        source, target = occurrence.source, occurrence.target
        terms = self.context_terms(source)
        requirements = _requirements(occurrence.holder, terms)
        kind = VECTOR_KINDS[occurrence.label]
        version = {"versionid": target.version_id, "contentdigest": target.digest}
        if "compatibilityline" in target.version:
            version["compatibilityline"] = target.version["compatibilityline"]
        registry = [{
            "wotid": occurrence.pointer, "defaultversionid": target.version_id,
            "defaultversionsticky": True, "versions": [version],
        }]
        if self.profile == "incremental":
            check_incremental.compose({
                "profile": "incremental",
                "reference": {"kind": kind, "target": occurrence.pointer,
                              "requirements": requirements},
                "binding": {"versionid": target.version_id, "contentdigest": target.digest},
                "registry": registry,
            })
            return
        if "uav:compatibilityLine" in requirements:
            raise check_vectors.OutcomeError("invalid-line")
        legacy = [term for term in ("tm:minVersion", "td:minVersion") if term in requirements]
        if "uav:minVersion" in requirements and legacy:
            raise check_vectors.OutcomeError("invalid-floor")
        expected = (
            "td:minVersion" if kind in check_vectors.TD_REFERENCE_KINDS else "tm:minVersion"
        )
        reference = {"kind": kind, "target": occurrence.pointer}
        if "uav:minVersion" in requirements:
            reference.update(minVersion=requirements["uav:minVersion"], floorTerm=expected)
        elif legacy:
            reference.update(minVersion=requirements[legacy[0]], floorTerm=legacy[0])
        case = {"registry": registry, "reference": reference}
        version_member = source.value().get("version")
        model = version_member.get("model") if isinstance(version_member, dict) else None
        if kind == "type" and model is not None:
            links = []
            for item in self.occurrences.values():
                if item.source is source and item.label == "type":
                    floors = _requirements(item.holder, terms)
                    link = {"target": item.pointer}
                    floor = floors.get("uav:minVersion", floors.get("tm:minVersion"))
                    if floor is not None:
                        link["minVersion"] = floor
                    links.append(link)
            case["document"] = {"typeLinks": links, "version.model": model}
        check_vectors.resolve(case)

    # Modes and results --------------------------------------------------------

    def descriptor(self, extension):
        if extension not in self.manifest.get("extensions", {}):
            raise ClosureError("invalid-composite", extension)
        raw = checked_bytes(self.manifest["extensions"][extension], self.read)
        try:
            return _json(raw)
        except (PublicationError, UnicodeDecodeError, ValueError) as error:
            raise ClosureError("invalid-descriptor", extension) from error

    def check_entries(self, entries, kinds):
        keys = []
        for entry in entries:
            key = _decoded(entry)
            document = self.documents.get(key)
            if document is None or document.kind not in kinds:
                raise ClosureError("invalid-entry", entry)
            keys.append(key)
        return keys

    def run_schema(self):
        entries, items = _schema_records(self.descriptor(SCHEMA_CLOSURE))
        keys = self.check_entries(entries, (SCHEMAS,))
        self.index_records([("schema", items, _full_key)])
        self.walk(keys)

    def run_composite(self, required):
        composite = self.descriptor(COMPOSITE_CLOSURE)
        validate_descriptor(DESCRIPTOR_SCHEMAS[COMPOSITE_CLOSURE], composite,
                            COMPOSITE_CLOSURE)
        self.describedby = composite.get("describedby", "advisory")
        entries = {_decoded(entry) for entry in composite["entries"]}
        members = []
        for member in composite["members"]:
            extension, role = member["extension"], member["role"]
            if extension not in required:
                raise ClosureError("invalid-composite", extension)
            descriptor = self.descriptor(extension)
            if role == "wot":
                member_entries, items = _wot_records(descriptor)
                member_key = _wot_key
            elif role == "schema":
                member_entries, items = _schema_records(descriptor)
                member_key = _full_key
            else:
                handler = self.handlers.get(extension)
                if handler is None or handler.role != role:
                    raise ClosureError("invalid-composite", extension)
                member_entries, items = handler.records(descriptor)
                member_key = _full_key
                self.active_handlers.append(handler)
            if {_decoded(entry) for entry in member_entries} != entries:
                raise ClosureError("entry-mismatch", extension)
            members.append((role, items, member_key))
        for item in composite.get("contexts", []):
            if item["uri"] in self.contexts:
                raise ClosureError("invalid-composite", item["uri"])
            document = self.documents.get(_decoded(item["target"]))
            if document is None:
                raise ClosureError("missing-target", item["target"])
            if document.base != item["uri"]:
                raise ClosureError("invalid-composite", item["uri"])
            self.contexts[item["uri"]] = document
        self.immutable = set(composite.get("immutableContexts", []))
        keys = self.check_entries(composite["entries"], WOT_KINDS + (SCHEMAS,))
        self.check_profiles()
        self.index_records(members)
        self.walk(keys)
        self.check_requirements()

    def reached_report(self):
        result = []
        keys = set(self.reached) | self.context_documents
        for document in sorted((self.documents[key] for key in keys), key=lambda d: d.xid):
            item = {
                "version": document.xid,
                "kind": document.kind,
                "versionid": document.version_id,
                "digest": document.digest,
                "base": document.base,
            }
            if document.kind in WOT_KINDS:
                item["wotid"] = document.version.get("wotid")
                item["versionOrigin"] = document.version.get("versionorigin")
                item["versionProfile"] = self.profile
                if "compatibilityline" in document.version:
                    item["compatibilityLine"] = document.version["compatibilityline"]
            result.append(item)
        return result

    def run(self):
        required = self.manifest.get("requiredExtensions", [])
        report = {
            "package": self.manifest["completeness"],
            "domain": {"result": "not-requested"},
            "runtime": "not-established",
            "reached": [],
        }
        if COMPOSITE_CLOSURE not in required and SCHEMA_CLOSURE not in required:
            return report
        try:
            if COMPOSITE_CLOSURE in required:
                self.run_composite(required)
            else:
                self.run_schema()
        except ClosureError as error:
            report["domain"] = {"result": "incomplete", "code": error.code,
                                "detail": error.detail}
        else:
            report["domain"] = {"result": "complete"}
        report["reached"] = self.reached_report()
        return report


def _wot_key(key):
    return key[:2]


def _full_key(key):
    return key


def _scan_members(node, path, terms, handlers, found, entries=False):
    """Collect reference members; literal values and entry names are not scanned."""
    if isinstance(node, list):
        for position, item in enumerate(node):
            _scan_members(item, path + (position,), terms, handlers, found)
        return
    if not isinstance(node, dict):
        return
    if entries:
        for name, child in node.items():
            _scan_members(child, path + (name,), terms, handlers, found)
        return
    for name, child in node.items():
        if name == "@context":
            if path:
                raise ClosureError("unsupported-context", format_pointer(path))
            continue
        iri = expand_term(name, terms)
        if iri in REFERENCE_MEMBERS:
            found.append((path, None, REFERENCE_MEMBERS[iri], node, name))
        for handler in handlers:
            label = handler.recognize(iri)
            if label is not None:
                found.append((path, handler, label, node, name))
        if name in LITERAL_MEMBERS:
            continue
        _scan_members(child, path + (name,), terms, handlers, found,
                      entries=name in ENTRY_MAPS)


def supported_extensions(handlers=()):
    """Extension URIs this checker can evaluate, plus those of the given handlers."""
    supported = {SCHEMA_CLOSURE, COMPOSITE_CLOSURE, WOT_CLOSURE}
    supported.update(handler.extension for handler in handlers)
    return tuple(sorted(supported))


def check_closure(pin, read_document, handlers=()):
    """Check a pinned snapshot; returns separate package, domain and runtime results."""
    manifest = check_snapshot(pin, read_document, supported_extensions(handlers))
    return _Checker(manifest, read_document, handlers).run()


def check_package(directory, name="publication-package.json", handlers=()):
    """Open a package context, then check the closure of its pinned snapshot."""
    package, documents = load_package(directory, name=name)
    manifest = open_context(
        package["context"], documents.read, supported_extensions(handlers),
    )
    return _Checker(manifest, documents.read, handlers).run()


def run_case(corpus, case, handlers=(ExampleOpcUaMaterialization(),)):
    """Run one corpus case; a PublicationError becomes an error outcome."""
    try:
        report = check_package(corpus, case["package"], handlers)
    except PublicationError as error:
        return {"error": error.code}
    outcome = {"package": report["package"], "domain": dict(report["domain"])}
    outcome["domain"].pop("detail", None)
    outcome["runtime"] = report["runtime"]
    if outcome["domain"]["result"] == "complete":
        outcome["reached"] = [item["version"] for item in report["reached"]]
    return outcome


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    corpus = Path(argv[0]) if argv else CORPUS
    cases = json.loads((corpus / "cases.json").read_text(encoding="utf-8"))
    failures = 0
    for name, case in cases["cases"].items():
        outcome = run_case(corpus, case)
        if outcome != case["expect"]:
            failures += 1
            print(f"FAIL {name}: {json.dumps(outcome, sort_keys=True)}")
    print(f"{len(cases['cases']) - failures} of {len(cases['cases'])} closure cases passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
