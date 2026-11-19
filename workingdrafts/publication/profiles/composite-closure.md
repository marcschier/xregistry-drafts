# xRegistry Publications: Composite Closure

<!-- words: describedby dynamicref jsonld nodeset nodesets offline -->
<!-- words: opcua publication publications semver submodel subthing -->
<!-- words: targetpointer versionmode versionid workingdrafts xid xids -->
<!-- words: xregistry wotid wotversionprofile compatibilityline exopc -->
<!-- words: href immutablecontexts py uav uriVariables urivariables -->
<!-- words: schemadefinitions securitydefinitions REQUIREDEXTENSIONS -->
<!-- words: iri namespace tds tms -->

## Abstract

This working draft defines an experimental composite closure contract. It
joins the Web of Things (WoT) publication closure, the
[static JSON Schema closure](schema-closure.md) and, when a publication
selects it, an OPC UA materialization extension. The composite gives every
mandatory reference occurrence in the reached documents exactly one owner, so
a Consumer can check the whole dependency graph of a WoT publication from the
captured bytes alone.

## Overview

Each member closure covers one kind of reference. The WoT closure binds
`tm:extends`, `tm:ref`, `td:ref` and the other WoT operators to exact Thing
Model (TM) and Thing Description (TD) Versions. The schema closure binds
`$ref` between schema documents. An OPC UA materialization extension binds
the OPC UA artifacts that a model needs. A TM can reach a schema through
`tm:ref`, and that schema can reference further schemas. No single member
covers that chain, and two members could both bind the same occurrence.

The composite descriptor lists its members. The Consumer derives every
occurrence from the reached documents, assigns it to one member by its
occurrence kind and captured target, and checks the member's binding. An
occurrence with no binding, with a binding from the wrong member or with
bindings from two members makes the domain result incomplete.

## Scope and Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHOULD", "SHOULD NOT",
"MAY", and "OPTIONAL" are interpreted as described in
[RFC2119](https://www.rfc-editor.org/rfc/rfc2119).

The [publication specification](../spec.md) defines manifests, extensions and
the [identity contract](../spec.md#cross-repository-identity-contract) that
every member uses. The WoT model's
[publication closure](../../models/wot/spec.md#544-publication-closure)
defines the WoT member and its operators, and
[versioned reference resolution](../../models/wot/spec.md#54-versioned-reference-resolution)
defines floors, lines and caps. The [schema closure](schema-closure.md)
defines schema identities, resolution and edges.

| Term | Meaning |
| --- | --- |
| Member | One closure extension that the composite joins. |
| Role | The member's function in the composite: `wot`, `schema` or `opcua-materialization`. |
| Occurrence | One reference in one reached source Version whose target lies in another captured document. |
| Owner | The member whose descriptor binds an occurrence. |
| Occurrence key | `(source, pointer, label)`, with the member-specific spelling in [Occurrence Keys and Ownership](#occurrence-keys-and-ownership). |

The identifiers below are experimental. The owning project assigns final
identifiers when the contract is accepted.

| Item | Value |
| --- | --- |
| Extension URI | `https://xregistry.io/workingdrafts/publication/profiles/composite-closure/1-experimental` |
| Descriptor `format` | `xregistry-composite-closure/1-experimental` |
| Descriptor schema | [composite-closure.json](../schemas/composite-closure.json) |

## Descriptor and Placement

A publication that declares composite closure MUST:

- Store the composite descriptor and every member descriptor as Version
  documents.
- Add each of their extension URIs to the manifest's `extensions` map.
- List each of those extension URIs in `requiredExtensions`.

A Consumer that does not support one of them rejects the manifest when it
opens it, as the [manifest rules](../spec.md#manifest-format) require. A
Consumer that supports the composite MUST evaluate the composite and its
members together, not each member on its own.

| Field | Meaning |
| --- | --- |
| `format` | `xregistry-composite-closure/1-experimental`. |
| `entries` | Exact Version XIDs of TMs, TDs or schemas from which closure is evaluated. At least one; no duplicates. |
| `members` | The joined members, each with `role` and `extension`. |
| `describedby` | `advisory`, the default, or `mandatory`. See [Deriving Occurrences](#deriving-occurrences). |
| `contexts` | Captured JSON-LD context documents, each with its context `uri` and the Version XID `target` that captures it. |
| `immutableContexts` | Context URIs that the Consumer resolves from a declared immutable set instead of captured bytes. |

## Members

| Role | Extension | Cardinality | Owns |
| --- | --- | --- | --- |
| `wot` | `http://opcfoundation.org/UA/WoT-Binding/publication-closure/1` | Exactly one | WoT link and `tm:ref` or `td:ref` occurrences whose target is a TM or TD. |
| `schema` | The [schema closure](schema-closure.md) extension | Exactly one | `$ref` occurrences, `tm:ref` occurrences whose target is a schema, and `describedby` links when `describedby` is `mandatory`. |
| `opcua-materialization` | Defined by the OPC UA WoT Binding | At most one | The materialization member's occurrences. |

The WoT member descriptor is the `wot-publication-closure/1` descriptor
unchanged. Its own rules continue to apply, including its binding key
`(source, pointer)`. The composite adds the ownership rules below. It does not
reinterpret WoT bindings.

A Consumer MUST reject a composite descriptor that does not match its schema
as `invalid-descriptor`. The schema fixes the extension of the `wot` and
`schema` roles and the cardinality of each role. A Consumer MUST reject the
composite as `invalid-composite` if a member extension is not listed in
`requiredExtensions`, if the manifest has no descriptor for it or if the
Consumer supports the extension under another role. Every member's `entries`
MUST equal the composite's `entries` as a set of Version identities. A
Consumer MUST reject a difference as `entry-mismatch`. An entry that is not a
captured TM, TD or schema Version MUST be rejected as `invalid-entry`.

## OPC UA Materialization Member

The OPC UA WoT Binding defines the materialization extension: its URI,
descriptor format, recognized members and target kinds. This contract defines
only how the composite refers to it. A publication selects it by listing it
as a member with the role `opcua-materialization`. A materialization
extension that is listed in `requiredExtensions` but not as a member is not
part of the composite's result. The manifest rules for that extension still
apply.

For the composite, the materialization extension's definition MUST state:

- The expanded IRIs of the WoT members whose values are materialization
  references, and the label each one records.
- The captured target kinds that each label accepts.
- The binding fields that carry `source`, `pointer`, `label`, `href` and
  `target`, with the same meaning as in a schema closure edge.

A Consumer that does not support the listed extension rejects the manifest
when it opens it. A Consumer that supports it applies the extension's rules to
the occurrences it owns and the ownership rules of this contract to all of
them.

The [closure corpus](../fixtures/README.md) uses the stand-in extension
`urn:example:opcua-materialization`, which recognizes the member IRI
`urn:example:opcua-materialization#nodeset` with the label `nodeset` and
accepts captured NodeSet documents. It shows the plug-in shape only. It is
not the OPC UA WoT Binding's extension.

## Occurrence Keys and Ownership

Every occurrence has one key of the form `(source, pointer, label)`. `source`
is the source Version XID, compared under the publication's
[reference comparison](../spec.md#reference-comparison) rules. `pointer` is
an RFC 6901 JSON Pointer into the source document's captured JSON, compared
as an exact string. Each member records the key as follows:

| Role | `source` | `pointer` | `label` |
| --- | --- | --- | --- |
| `wot` | Binding `source` | Binding `pointer` | Binding `operator` |
| `schema` | Edge `source` | Edge `pointer` | Edge `label`: `$ref`, `tm:ref` or `describedby` |
| `opcua-materialization` | Binding `source` | Binding `pointer` | Binding `label` |

The `wot` member's labels are the canonical operators of the WoT closure.
`tm:ref` keeps that spelling under every member, whatever prefix the source
document uses.

Each occurrence MUST have exactly one owner, determined by the occurrence's
kind and the kind of its captured target, as the [Members](#members) table
states. Member order in the descriptor has no effect. A Consumer MUST reject:

| Condition | Code |
| --- | --- |
| Two members bind the same occurrence key | `conflicting-ownership` |
| A member other than the owner binds the occurrence's source and pointer, and the owner does not bind the key | `conflicting-ownership` |
| The owner has a binding at the occurrence's source and pointer with another label, `href`, target, `base` or `targetPointer` | `contradictory-binding` |
| No member binds the occurrence | `missing-binding` |
| A member binds a key twice, or the WoT member binds `(source, pointer)` twice | `duplicate-binding` |
| A binding that no reached occurrence uses | `unexpected-binding` |

## Deriving Occurrences

A Consumer derives occurrences from the captured bytes of every reached
document, never from the bindings:

- In a schema document, the [schema closure](schema-closure.md) rules apply.
- In a TM or TD, each `links` item whose `rel` is one of the WoT closure's
  link relations is an occurrence at the link object's pointer.
- In a TM or TD, each member whose expanded IRI is
  `https://www.w3.org/2019/wot/tm#ref` or `https://www.w3.org/2019/wot/td#ref`
  is an occurrence at the pointer of the object that holds it. So is each
  member whose expanded IRI the selected materialization extension
  recognizes.

Member names are expanded under the document's
[contexts](#contexts). The names of `properties`, `actions`, `events`,
`uriVariables`, `schemaDefinitions` and `securityDefinitions` entries are
authored names, not terms, and are not expanded. The values of `const`,
`default`, `enum` and `examples` are literal JSON. A reference member inside
one is not an occurrence. A Consumer MUST reject two WoT reference members in
one object as `ambiguous-occurrence`. A WoT reference and a materialization
reference in one object are two occurrences with different labels.

An `href` that starts with `#`, or that resolves to the source document's own
base or `wotid`, is local and is not an occurrence. Other references resolve
against the source document's base, and the URI without its fragment selects
captured candidates by document base, `wotid` or schema root identity. No
candidate is `missing-target`. Several candidates are allowed only when they
are Versions of one WoT Resource. The Consumer MUST reject a reference with
any other set of several candidates as `ambiguous-identity`. A candidate of a
kind that the operator does not accept is `invalid-reference`.

An ordinary `tm:ref` whose captured target is a schema is a mandatory schema
dependency. The schema member owns it with the label `tm:ref`, the source
document's base as `base`, and the position its fragment selects in the
schema document as `targetPointer`. The target schema document is then walked
under the schema closure rules. A `tm:ref` to a TM stays with the WoT member.

A `links` item with `rel: "describedby"` and `type: "application/schema+json"`
is advisory by default: it is not an occurrence, and a binding for it is
rejected as `unexpected-binding`. When the composite's `describedby` is
`mandatory`, each such link is a schema occurrence with the label
`describedby`, owned and checked like a `tm:ref` to a schema.

## Contexts

A Consumer MUST NOT fetch a context while opening or replaying a
publication. It MUST determine the expanded IRI of each member name from
captured bytes or a declared immutable context set:

- A context URI listed in `contexts` is read from its captured `target`
  Version. That Version's document association `base` MUST equal the URI.
  Each URI MUST appear once in `contexts`. A Consumer MUST reject a violation
  of either rule as `invalid-composite`. A `target` that is not captured is
  `missing-target`.
- A context URI listed in `immutableContexts` is resolved from the Consumer's
  own copy of that context. A Consumer without such a copy rejects it as
  `unsupported-context`.
- A Consumer MUST reject any other context URI as `live-context-required`.

A Consumer that cannot determine expanded IRIs under a context rejects it as
`unsupported-context` rather than guessing.

## Version Profiles

The captured Registry JSON selects the WoT version profile. A Registry
without `wotversionprofile` uses the SemVer base model. The value
`incremental` selects the
[Incremental Version Profile](../../models/wot/spec.md#55-incremental-version-profile).
The spelling of Version IDs is not profile discovery. A Consumer MUST reject
the composite as `profile-mismatch` if a captured TM or TD Resource's
`versionmode`, or a captured Version ID, does not match the selected profile,
or if `wotversionprofile` has another value.

## Requirement Checks

The composite checks each WoT occurrence by snapshot-bound composition, as
the WoT model's
[floors and pins](../../models/wot/spec.md#541-floors-and-pins) define. The
bound target Version comes first. The Consumer then checks the occurrence's
floor, compatibility line and TD major cap against that Version and reports a
failure with the WoT resolver's code, such as `unsatisfied`, `invalid-floor`,
`invalid-line` or `inconsistent-publication`. A generated `0.0.0-N` Version
ID does not satisfy a floor. A failed check makes the domain result
incomplete, and the Consumer does not select another Version in its place.
Live selection of a newer Version is outside this contract.

## Results

A Consumer reports package, domain and runtime results separately, as the
[schema closure](schema-closure.md#results) defines. Missing bytes, a digest
mismatch and an unsupported extension listed in `requiredExtensions` prevent
opening the snapshot. A complete domain result shows that every mandatory
dependency of the entries is captured, owned by one member and bound to an
exact Version or schema position, and that every WoT requirement holds for
the bound Version. It does not show that a runtime can load the models, that
a validator accepts the schemas, or that an OPC UA server can materialize the
NodeSets.

## Example

In the [closure corpus](../fixtures/README.md), the TD `pump-7` is the only
entry. Its reached occurrences and their owners are:

| Source | Pointer | Label | Owner | Target |
| --- | --- | --- | --- | --- |
| TD `pump-7` 1.0.0 | `/links/0` | `type` | `wot` | TM `pump` 1.4.0 |
| TD `pump-7` 1.0.0 | `/links/1` | `td:extends` | `wot` | TD `pump-template` 2.1.0 |
| TM `pump` 1.4.0 | (root) | `nodeset` | `opcua-materialization` | NodeSet `pump` 1.0.0 |
| TM `pump` 1.4.0 | `/links/0` | `tm:extends` | `wot` | TM `base` 1.2.0 |
| TM `pump` 1.4.0 | `/properties/location` | `tm:ref` | `schema` | Schema `address` 1.0.0, `/$defs/postal` |
| TM `pump` 1.4.0 | `/properties/status` | `tm:ref` | `wot` | TM `base` 1.2.0 |
| Schema `address` 1.0.0 | Four positions | `$ref` | `schema` | Schema `common` 2.1.0 |
| Schema `common` 2.1.0 | `/$defs/a~1b~0c%d` | `$ref` | `schema` | Schema `address` 1.0.0 |

The TM spells the schema reference `model:ref`. Its context maps `model` to
the TM namespace, so the member expands to `tm:ref`. The `describedby` link
at `/links/1` of the TM is advisory and has no binding. The `tm:ref` inside
the `default` value of `/properties/mode` is literal JSON and has no binding.

## Evidence

The [closure corpus](../fixtures/README.md) covers complete, incomplete and
rejected composites, including both version profiles. The
[reference checker](../tools/closure_checker.py) evaluates every case:

```text
python -B -m workingdrafts.publication.tools.closure_checker
```

The reference checker evaluates the WoT closure only as a composite member.
For a manifest that requires the WoT closure without a composite, it reports
the domain result `not-requested`. It supports a subset of JSON-LD contexts
(prefix and term definitions) and rejects the rest as `unsupported-context`.
