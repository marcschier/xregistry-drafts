# xRegistry Publications: Static JSON Schema Closure

<!-- words: anchors applicator dialect jsonld metaschema metaschemas -->
<!-- words: nodeset nodesets offline percent publication publications -->
<!-- words: recursiveanchor recursiveref dynamicanchor dynamicref -->
<!-- words: subschema subschemas targetpointer versionid workingdrafts -->
<!-- words: xid xids xregistry -->
<!-- words: additionalproperties allof anyof contentschema dependentschemas -->
<!-- words: href minitems oneof patternproperties prefixitems propertynames py -->
<!-- words: REQUIREDEXTENSIONS unevaluateditems unevaluatedproperties -->

## Abstract

This working draft defines an experimental publication profile for static
JSON Schema dependencies. A publication that uses it records, for each schema
reference that leaves its document, the exact target Version and the schema
position the reference selects. A Consumer derives the same references from
the captured bytes and compares them with that record. It can then show
without network access that every schema the entries depend on is captured.

## Overview

A [publication](../spec.md) fixes the bytes of its captured documents, and
Federation completeness covers declared xRegistry content. A `$ref` inside a
captured schema is content, not a declaration. A snapshot can capture
`address.json` and omit the `common.json` it references, and the snapshot
does not record which Version of `common.json` the publisher checked. A
reader that resolves the reference against a live Registry gets an answer
that depends on when it asks.

This profile adds a closure descriptor that lists each cross-document schema
reference with its exact target Version and target position. The Consumer
walks the captured schema documents, finds every reference itself, resolves
it with the identities in the snapshot, and compares the result with the
descriptor. The descriptor states the publisher's binding; it is not the
source of the reference list.

The profile is static. It covers the core identifier, anchor and reference
keywords of JSON Schema 2020-12 and its applicator keywords. It rejects the
dynamic reference keywords, whose target depends on the evaluation path.

## Scope and Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHOULD", "SHOULD NOT",
"MAY", and "OPTIONAL" are interpreted as described in
[RFC2119](https://www.rfc-editor.org/rfc/rfc2119).

The [publication specification](../spec.md) defines manifests, byte
descriptors, document associations and extensions. The
[Schema Registry](../../../schema/spec.md#431-json-schema) defines the
`JsonSchema/draft/2020-12` format, and
[JSON Schema 2020-12 Core][JSON Schema Core] defines the keywords. RFC 3986
defines URI resolution and RFC 6901 defines JSON Pointer. The publication's
[identity contract](../spec.md#cross-repository-identity-contract) defines
Version identity, source base and digest domain for every closure profile.

| Term | Meaning |
| --- | --- |
| Schema document | Captured Version document whose captured Version `format` is `JsonSchema/draft/2020-12`. |
| Schema resource | The root of a schema document, or a schema position that has `$id`. |
| Schema position | JSON value that this profile evaluates as a schema, as listed in [Schema Positions](#schema-positions). |
| Captured identity | Absolute URI without fragment that identifies a schema resource, derived from captured bytes and the document association. |
| Effective base | URI against which a position's `$id` and `$ref` resolve. |
| Occurrence | One reference at one position of one source Version whose target lies in another captured document. |
| Occurrence key | `(source, pointer, label)` of an occurrence. |
| Edge | Descriptor record that binds one occurrence to its target. |

The identifiers below are experimental. The owning project assigns final
identifiers when the profile is accepted. A Consumer MUST reject a descriptor
with another `format` value as `invalid-descriptor`.

| Item | Value |
| --- | --- |
| Extension URI | `https://xregistry.io/workingdrafts/publication/profiles/schema-closure/1-experimental` |
| Descriptor `format` | `xregistry-schema-closure/1-experimental` |
| Descriptor schema | [schema-closure.json](../schemas/schema-closure.json) |

This profile does not validate instances, does not check schemas against the
2020-12 metaschema, and does not cover other schema formats such as JSON
Schema draft-07, XML Schema, Avro or Protobuf.

## Descriptor and Placement

A publication that declares static schema closure MUST store the closure
descriptor as a Version document, MUST add the extension URI to the
manifest's `extensions` map with a byte descriptor of that document, and MUST
list the URI in `requiredExtensions`. The
[manifest rules](../spec.md#manifest-format) then apply: a Consumer that does
not support the extension rejects the manifest when it opens it.

| Field | Meaning |
| --- | --- |
| `format` | `xregistry-schema-closure/1-experimental`. |
| `entries` | Exact Version XIDs from which closure is evaluated. At least one; no duplicates. |
| `edges` | One record for each occurrence. |

Each edge has these fields, all REQUIRED:

| Field | Meaning |
| --- | --- |
| `source` | Version XID of the document that holds the occurrence. |
| `pointer` | RFC 6901 JSON Pointer into the source document's captured JSON, identifying the object that holds the reference member. |
| `label` | `$ref` for a schema reference. `tm:ref` and `describedby` are used only under the [composite closure](composite-closure.md). |
| `href` | The authored reference string. |
| `base` | Effective base, an absolute URI without fragment. |
| `target` | Version XID of the document that holds the selected schema position. |
| `targetPointer` | RFC 6901 JSON Pointer from the target document's root to the selected schema position. |

When the profile is used without a composite closure, every entry MUST be a
schema document and every edge MUST use the label `$ref`. A Consumer MUST
reject another entry as `invalid-entry` and another label as
`unexpected-binding`.

## Dialect

A schema document's captured Version `format` MUST be
`JsonSchema/draft/2020-12`. A `$schema` member at any schema position MUST be
`https://json-schema.org/draft/2020-12/schema`. A Consumer MUST reject any
other `format` or `$schema` value as `unsupported-dialect`. Custom
metaschemas and `$vocabulary` declarations are outside this profile.

A `$dynamicRef` or `$recursiveRef` target depends on the dynamic scope at
evaluation time, so the captured bytes alone do not determine it. In
2020-12, a `$dynamicAnchor` also defines a plain-name fragment, which this
profile does not index. A Consumer MUST reject a schema document that has a
`$dynamicRef`, `$dynamicAnchor`, `$recursiveRef` or `$recursiveAnchor` member
at a schema position as `unsupported-dynamic-reference`.

## Schema Positions

The document root is a schema position. The members of a schema position
listed below are schema positions too:

| Keyword | Schema positions |
| --- | --- |
| `$defs`, `properties`, `patternProperties`, `dependentSchemas` | Each member value of the object. |
| `additionalProperties`, `items`, `contains`, `propertyNames`, `not`, `if`, `then`, `else`, `unevaluatedItems`, `unevaluatedProperties`, `contentSchema` | The value. |
| `prefixItems`, `allOf`, `anyOf`, `oneOf` | Each item of the array. |

A schema position is an object or a boolean. A boolean has no members.
Keywords beside `$ref` are schema keywords like any other, and their
positions are walked.

No other member is a schema position. The values of `examples`, `default`,
`enum` and `const` are literal JSON, and unknown keywords, including the
draft-07 `definitions`, are outside this vocabulary. A Consumer MUST NOT treat
a `$ref`, `$id` or `$anchor` inside such a value as a reference or identity.

A Consumer MUST reject as `invalid-schema` a schema position that is neither
an object nor a boolean, an object-valued keyword above whose value is not an
object, an array-valued keyword above whose value is not an array or is an
empty array, and a `$ref` whose value is not a string.

The empty-array rule is the dialect's own rule, not a restriction this profile
adds. [JSON Schema Core][JSON Schema Core] sections 10.2.1.1 to 10.2.1.3 and
10.3.1.1 require `allOf`, `anyOf`, `oneOf` and `prefixItems` to be non-empty
arrays, and the 2020-12 applicator metaschema enforces this with
`minItems: 1`. A schema with `prefixItems: []` is therefore not a valid 2020-12
schema.

## Identities

Each schema document has one or more captured identities:

1. The document association's `base`, without its fragment, identifies the
   document's root resource.
2. A `$id` at a schema position is resolved against the effective base at
   that position. The result identifies a schema resource rooted there and
   becomes the effective base of that position, of its `$ref` and of its
   descendants. A root `$id` gives the root resource a second identity.

A Consumer MUST reject a `$id` that is not a string, or whose resolved value
has a non-empty fragment, as `invalid-identifier`.

An `$anchor` names its position within the nearest enclosing schema resource.
Its value MUST match `[A-Za-z_][-A-Za-z0-9._]*`; a Consumer MUST reject
another value as `invalid-identifier`. A Consumer MUST reject two anchors
with the same name in one schema resource as `conflicting-anchor`. Anchors in
different resources do not conflict.

Identities come only from captured bytes and the captured document
associations. A Consumer MUST NOT use a retrieval location, a live Registry
or a network request to identify a schema. URIs compare as exact strings
after resolution; this profile applies no case or percent-encoding
normalization.

## Resolving a Reference

For each `$ref` at a schema position, a Consumer MUST apply these steps in
order:

1. Resolve the `$ref` value against the effective base of its position, as
   RFC 3986 Section 5.2 specifies, and split the result into an absolute URI
   and a fragment.
2. Select the schema resource that the URI identifies. Look first among the
   resources of the same document. If none matches, look among the captured
   identities of every other schema document in the snapshot. If no resource
   matches, reject the reference as `missing-target`. If more than one
   matches, reject it as `ambiguous-identity`.
3. Percent-decode the fragment as UTF-8. Reject a malformed escape or invalid
   UTF-8 as `invalid-fragment`.
4. Select a position within the selected resource:
   - An empty fragment selects the resource root.
   - A fragment that starts with `/` is an RFC 6901 JSON Pointer evaluated
     from the resource root. It can descend into embedded resources. A `~`
     that is not followed by `0` or `1`, an array index that is not a
     canonical decimal integer within range, or a missing member is rejected
     as `invalid-fragment`.
   - Any other fragment is an anchor name looked up in the selected resource
     only. An unknown name is rejected as `invalid-fragment`.
5. Reject the reference as `invalid-fragment` if the selected value is not a
   schema position, for example a value under `examples` or `definitions`.

The fragment applies to the resource that step 2 selected, never to the
document root or to another resource. For example, the reference
`units/v2#/$defs/length` in `address.json` resolves to the resource
`https://example.test/schemas/units/v2`, which is embedded at `/$defs/units`
in `common.json`. Its pointer selects `/$defs/units/$defs/length` in that
document.

## Occurrences and Edges

A reference whose selected position lies in the same document is internal: it
is not an occurrence and has no edge. A reference whose selected position
lies in another captured document is an occurrence. Its key is the source
Version XID, the RFC 6901 pointer from the source root to the object that
holds the `$ref`, and the label `$ref`. Pointers use the authored member
names with RFC 6901 escaping and no percent-encoding, so the member `a/b~c%d`
of `$defs` has the pointer `/$defs/a~1b~0c%d`.

Each occurrence MUST have exactly one edge, and that edge MUST record:

- `href` equal to the authored `$ref` string, without resolution or decoding.
- `base` equal to the effective base used in step 1.
- `target` equal to the Version XID of the document that holds the selected
  position.
- `targetPointer` equal to the pointer from that document's root to the
  selected position.

`source` and `target` compare as Version identities under the publication's
[reference comparison](../spec.md#reference-comparison) rules. Pointers,
`href` and `base` compare as exact, case-sensitive strings.

A Consumer MUST reject:

- An occurrence without an edge as `missing-binding`.
- An edge at the occurrence's source and pointer whose label, `href`, `base`,
  `target` or `targetPointer` differs from the derived values as
  `contradictory-binding`.
- Two edges with the same occurrence key as `duplicate-binding`.
- An edge that no reached occurrence uses, including one for a literal value
  or an unreached document, as `unexpected-binding`.

## Traversal

A Consumer starts with the entries and processes documents breadth-first.
For each document, it derives the occurrences, checks their edges and queues
each occurrence's target document. It keeps a set of visited Versions and
processes each Version once. Cycles are allowed: `address.json` can reference
`common.json`, which references `address.json` again.

The Consumer derives occurrences from the whole target document, not only
from the referenced subschema. A subschema can reach other parts of its
document through internal references, and walking the whole document covers
them without tracking which parts are reachable.

A Consumer MUST NOT read a schema, metaschema or other document that the
manifest does not describe. Replaying an exact manifest repeats the same
derivation over the same bytes and gives the same result.

## Rejections

Each condition below makes the domain result incomplete. The reported code
names the first condition found; a Consumer MAY stop there.

| Condition | Code |
| --- | --- |
| The descriptor does not match its schema | `invalid-descriptor` |
| A captured document is not JSON | `invalid-document` |
| A document association `base` is not an absolute URI | `invalid-base` |
| An entry is not a captured schema document | `invalid-entry` |
| A dialect or `format` other than JSON Schema 2020-12 | `unsupported-dialect` |
| A dynamic reference or dynamic anchor keyword | `unsupported-dynamic-reference` |
| A malformed schema position, keyword value or `$ref` | `invalid-schema` |
| A malformed `$id` or `$anchor` | `invalid-identifier` |
| Two anchors with one name in one resource | `conflicting-anchor` |
| A reference URI with no captured identity | `missing-target` |
| A reference URI with more than one captured identity | `ambiguous-identity` |
| A fragment that does not select a schema position | `invalid-fragment` |
| An occurrence without an edge | `missing-binding` |
| An edge that disagrees with its occurrence | `contradictory-binding` |
| Two edges with one occurrence key | `duplicate-binding` |
| An edge that no reached occurrence uses | `unexpected-binding` |

## Results

A Consumer reports three separate results:

| Result | Values | Determined by |
| --- | --- | --- |
| Package | Federation `linked` or `offline-complete` | The manifest's `completeness`, checked when the snapshot is opened. |
| Domain | `complete`, `incomplete` with a code, or `not-requested` | This profile, when the manifest requires its extension. |
| Runtime | `not-established` | A validator, code generator or runtime that loads the schemas, outside this profile. |

Missing bytes, a digest mismatch and an unsupported extension listed in
`requiredExtensions` prevent opening the snapshot, as the publication
specification defines. They produce no domain result. A linked package can
report a complete domain result only if every reached document is captured.

A complete domain result shows that every static schema dependency of the
entries is captured and bound to an exact schema position. It does not show
that the schemas are valid, that a validator accepts recursive schemas, or
that a code generator can translate them. This profile imposes no restricted
assertion language. A tool that accepts only a subset of JSON Schema reports
its own result.

## Example

The [closure corpus](../fixtures/README.md) contains two captured schema
documents. `address.json`, with the base
`https://example.test/schemas/address.json`, has four references into
`common.json`. `common.json` embeds the resource `units/v2`, which has the
anchor `meter`, and its `$defs` member `a/b~c%d` references `address.json`
again. The edge for the escaped reference is:

```json
{
  "source": "/schemagroups/acme/schemas/address/versions/1.0.0",
  "pointer": "/$defs/postal/properties/weird",
  "label": "$ref",
  "href": "common.json#/$defs/a~1b~0c%25d",
  "base": "https://example.test/schemas/address.json",
  "target": "/schemagroups/acme/schemas/common/versions/2.1.0",
  "targetPointer": "/$defs/a~1b~0c%d"
}
```

The `href` keeps the authored `%25`. The fragment decodes to
`/$defs/a~1b~0c%d`, and the pointer selects the member `a/b~c%d`. The
reference `#/$defs/postal` inside `address.json` is internal and has no edge.
The `$ref` members under `examples`, `default`, `enum`, `const` and the
unknown keyword `x-note` are literal values and have no edges either.

## Evidence

The [closure corpus](../fixtures/README.md) is byte-pinned and lists the
expected result of each case. The
[reference checker](../tools/closure_checker.py) derives edges from the
captured bytes and checks every case:

```text
python -B -m workingdrafts.publication.tools.closure_checker
```

The checker is an example, not a production Consumer. It opens no network
connection and reads bytes only through the package.

[JSON Schema Core]: https://json-schema.org/draft/2020-12/json-schema-core
