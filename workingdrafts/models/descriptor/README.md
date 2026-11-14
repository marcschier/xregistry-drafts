# Descriptor Registry Service - Version 1.0-rc4

<!-- words: describedby entityid entitytype messageref schemaref planurl -->
<!-- words: contexturl opc ua prebuilt TDs USD -->

See the [Descriptor Registry specification](spec.md), its
[design rationale](design/design.md) and [model](model.json). This working
draft describes assets, devices, actors and shared processing context
through one metadata-only Resource shape. The companion
[CloudEvents proposal](https://github.com/cloudevents/spec/pull/1406) owns
`describedby` and the WoT/OPC UA event bindings.

The [sample](samples/descriptor.json) is a Core create/update input, not a
complete response. It contains an Asset Descriptor with a TD and USD asset,
an Actor Descriptor with empty `references`, and a Context Descriptor with
two TDs, explicit schema selection and typed OPC UA metadata. The Context
does not inherit metadata from the Asset. Group IDs and entity types are
illustrative catalog choices. Example URLs are not deployed services.

The generated [JSON Schema](schemas/document-schema.json),
[JSON Structure](schemas/document-schema.struct.json),
[Avro](schemas/document-schema.avsc) and [OpenAPI](schemas/openapi.json)
describe selected Registry metadata. They do not replace the domain rules:
absolute identity URI syntax, Reference names and classes, selector
existence/class, `entitytype` requiring `entityid`, specialization
requirements and publication stability need additional validation.
`planurl` is allowed only for resolved TD/TM provenance and is not fetched
as part of a bundle. The base model permits profile extensions; an OPC UA
deployment can declare the types in the [model fragment][profile fragment].

The Descriptor Avro generation command uses the opt-in
`--avro-nullable-optionals` in [tools/Makefile](../../../tools/Makefile).
It represents absent OPTIONAL fields through nullable field types and
defaults, including nested References. The generator's default output and
the published Schema, Message, Endpoint and CloudEvents Avro artifacts are
unchanged. Avro null values are serialization details, not a change to
Core JSON response or write semantics.

Ordinary GET returns metadata. The OPTIONAL
[Descriptor bundle](spec.md#74-descriptor-bundle) needs additional
resolver/serving behavior; generic Core does not assemble it. A configured
static endpoint can serve a prebuilt bundle subject to the same completeness,
authorization, freshness and Version-selection rules. It is not a snapshot.

## Scope and Deferred Work

The [comparison with other drafts][draft boundaries] separates Descriptors
from federation contexts, publication snapshots and runtime readiness.
The [document alternative][document alternative] remains recorded as a
trade-off, not the selected model.

This revision replaces the earlier Context collections, Role-keyed
References and `contexturl` design; it provides no compatibility aliases.
The CE proposal owns migration of event attributes. Digest schemes,
transitive packaging, a universal entity vocabulary and new lifecycle
or execution APIs are outside this draft.

[profile fragment]: spec.md#52-wot-and-opc-ua
[draft boundaries]: design/design.md#6-relationship-to-federation-publication-and-wot
[document alternative]: design/design.md#71-descriptor-document-alternative
