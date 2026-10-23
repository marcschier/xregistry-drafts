# WoT Registry Service - Version 1.0-rc4

<!-- words: WoT JSON-LD Servient affordances affordance discoverability tm td -->
<!-- words: thing thingid thingurl things thingsurl thingscount thingbase64 -->
<!-- words: thinggroup thinggroups thinggroupid thinggroupsurl thinggroupscount -->
<!-- words: ThingDescription ThingModel ThingProjection tp -->
<!-- words: invokeaction readproperty writeproperty subscribeevent securitydefinitions versionmode urn href -->
<!-- words: workbench fabrikam lamp lighting jwt tenantid deviceid -->
<!-- words: formatvalidated compatibilityvalidated formatvalidatedreason compatibilityvalidatedreason -->
<!-- words: coap describedby integrators lifecycles modbus opc tds tms ua matchversions -->
<!-- words: wotid wotids derivedfrom canonicalurl standardsbody submodel spdx openusd -->
<!-- words: toolchain byom contoso maturity publisher nosniff validateformat -->
<!-- words: shortself -->
<!-- words: dereferenceable thingdescriptiongroups thingdescriptions -->
<!-- words: thingmodelgroups thingmodels validatecompatibility -->

## Abstract

This specification defines a WoT (Web of Things) Registry extension to the
xRegistry document format and API [specification][xRegistry Core]. A WoT
Registry allows for the storage, management and discovery of W3C
[WoT Thing Description (WoT-TD)][WoT-TD-1.1],
[WoT Thing Model (WoT-TM)][WoT-TM-1.1], and provisional WoT Thing
Projection (WoT-TP) documents. All kinds share one Group and Resource
structure; a REQUIRED `kind` attribute distinguishes them.

## Table of Contents

- [WoT Registry Service - Version 1.0-rc4](#wot-registry-service---version-10-rc4)
  - [Abstract](#abstract)
  - [Table of Contents](#table-of-contents)
  - [1. Overview](#1-overview)
    - [1.1. Document Kinds](#11-document-kinds)
    - [1.2. Relationship to Other xRegistry Specs](#12-relationship-to-other-xregistry-specs)
    - [1.3. Versioning](#13-versioning)
    - [1.4. Document Store](#14-document-store)
  - [2. Notations and Terminology](#2-notations-and-terminology)
    - [2.1. Notational Conventions](#21-notational-conventions)
    - [2.2. Terminology](#22-terminology)
      - [2.2.1. Thing Description](#221-thing-description)
      - [2.2.2. Thing Model](#222-thing-model)
      - [2.2.3. WoT Identifier](#223-wot-identifier)
      - [2.2.4. Thing Projection](#224-thing-projection)
      - [2.2.5. Thing Resource](#225-thing-resource)
    - [2.3. Thing Group](#23-thing-group)
  - [3. WoT Registry Model](#3-wot-registry-model)
  - [4. WoT Registry](#4-wot-registry)
    - [4.1. Thing Groups](#41-thing-groups)
    - [4.2. Thing Resources](#42-thing-resources)
    - [4.3. Document Kind](#43-document-kind)
    - [4.4. Validation by Kind](#44-validation-by-kind)
    - [4.5. Formats](#45-formats)
      - [4.5.1. WoT Thing Description](#451-wot-thing-description)
      - [4.5.2. WoT Thing Model](#452-wot-thing-model)
      - [4.5.3. WoT Thing Projection](#453-wot-thing-projection)
    - [4.6. Provenance and Selection Metadata](#46-provenance-and-selection-metadata)
  - [5. Identity and Resolution](#5-identity-and-resolution)
    - [5.1. WoT Identifiers and Registry Ids](#51-wot-identifiers-and-registry-ids)
      - [5.1.1. Breaking Changes and Successor Identifiers](#511-breaking-changes-and-successor-identifiers)
    - [5.2. Preserving Customer Documents](#52-preserving-customer-documents)
    - [5.3. Lookup](#53-lookup)
      - [5.3.1. Kind-Filtered Discovery and Access](#531-kind-filtered-discovery-and-access)
    - [5.4. Migration from Separate Collections](#54-migration-from-separate-collections)
  - [6. Relationships and Cross-References](#6-relationships-and-cross-references)
    - [6.1. Thing Description to Thing Model](#61-thing-description-to-thing-model)
    - [6.2. Thing Description to Endpoint Registry](#62-thing-description-to-endpoint-registry)
    - [6.3. Thing Description to Schema Registry](#63-thing-description-to-schema-registry)
    - [6.4. Affordance Grouping](#64-affordance-grouping)
  - [7. Security](#7-security)

## 1. Overview

A WoT Registry provides a repository for managing Web of Things documents:
**Thing Descriptions** (TDs), which describe concrete network-facing instances
of Things; **Thing Models** (TMs), which describe reusable, abstract
templates for classes of Things; and **Thing Projections** (TPs), whose
document contract is provisional in this draft.

A WoT Registry is generally used to share Thing metadata amongst multiple
parties: device fleets, gateways, integrators, and consuming applications. The
registry is intended to make Things and their templates **discoverable** in a
manner aligned with the W3C
[WoT Discovery][WoT-Discovery] specification, while also allowing WoT documents
to be cross-referenced from xRegistry [Endpoint][xRegistry Endpoint],
[Message][xRegistry Message], and [Schema][xRegistry Schema] entries.

### 1.1. Document Kinds

A **Thing Description** (TD) is a JSON-LD 1.1 document conforming to
[WoT-TD 1.1][WoT-TD-1.1]. It identifies a deployed Thing instance, declares its
properties, actions, and events, and provides one or more `forms` that bind
those interaction affordances to network endpoints over specific protocols
(HTTP, MQTT, CoAP, OPC-UA, Modbus, etc.).

A **Thing Model** (TM) is a JSON-LD 1.1 document conforming to
[WoT-TM 1.1][WoT-TM-1.1]. It is an **abstract** description of a class of
Things, typically without `href` values in its forms. Thing Models are
intended to be reused: a concrete Thing Description MAY extend or compose one
or more Thing Models via the WoT `tm:extends` and `tm:ref` mechanisms, or via
JSON-LD `@type` declarations.

All three kinds use JSON-LD 1.1 in this draft. A **Thing Projection** (TP)
is provisionally admitted using `application/json`; this specification does
not yet define its vocabulary, lineage, or derivation rules, and makes no
claim of conformance to a W3C Thing Projection standard.

A WoT Registry MUST store all kinds using the same `thing` Resource type
inside `thinggroup` Groups. A Group MAY mix kinds. Every document Version
MUST carry a `kind` attribute in its registry metadata, with one of
`ThingDescription`, `ThingModel`, or `ThingProjection`. The attribute is not
inserted into the document. Kind-specific validation and independent
Resource lifecycles are retained without partitioning collections by kind.

### 1.2. Relationship to Other xRegistry Specs

A WoT Registry is complementary to the xRegistry [Endpoint][xRegistry Endpoint],
[Message][xRegistry Message], and [Schema][xRegistry Schema] registries:

- A Thing Description's `forms` array describes protocol bindings that MAY
  also be represented as `endpoint` Resources; see
  [Section 6.2](#62-thing-description-to-endpoint-registry).
- A Thing Description's property/action/event data schemas (declared inline
  via WoT data-schema vocabulary) MAY reference external schemas managed by
  the xRegistry Schema Registry; see
  [Section 6.3](#63-thing-description-to-schema-registry).
- A Thing Description MAY reference one or more Thing Models from which it
  is derived; see [Section 6.1](#61-thing-description-to-thing-model).

This specification does not require a registry to resolve or validate these
cross-references: an implementation MAY check that a referent exists, but a
document whose referents are absent is still stored and served. That is a
statement about what the *registry* enforces, not about whether the
references matter — a Consumer composing a TD from its Thing Models, or
binding an affordance to an endpoint, depends on them.

### 1.3. Versioning

Each Version of a `thing` Resource holds a complete TD, TM, or TP
document. This specification does not require a registry to
parse the document in order to derive registry metadata; the document is
stored as-is and the xRegistry [`versionid`][xRegistry version-ids] is
assigned by the xRegistry Core rules.

A Version's identifier — its [`versionid`][xRegistry version-ids] — is never
part of a Resource's identity. A Resource's `wotid`, `kind`, and `thingid`
are stable across revisions of the document they name; `wotid` and `kind`
are declared with [`matchversions`][xRegistry matchversions], so a registry
MUST reject a Version that supplies a different value for either. Creating
a TD from a TM produces a separate Resource, not a change of kind. See
[Section 5.1](#51-wot-identifiers-and-registry-ids).

The xRegistry Core versioning rules (monotonically increasing integer
`versionid`s, [`ancestorid`][xRegistry ancestorid] lineage, default-Version
selection) apply unchanged. A breaking change to a TD or TM that violates the
Resource's [`compatibility`][xRegistry compatibility] policy MUST result in a
new Resource, not a new Version. The same rule applies to TPs.
`compatibility` is OPTIONAL in Core and this
specification does not set it, so a deployment that wants this rule to bind
sets `compatibility` on the Resource; where it is absent, Core makes no
statement about the relationship between Versions and the registry behaves as
a plain document store.

Because all Versions of a Resource share one `kind` and `wotid`, a
same-kind successor Resource is reached by authoring a *new* WoT identifier,
and the superseded Resource
records where the successor lives; see
[Section 5.1.1](#511-breaking-changes-and-successor-identifiers).

### 1.4. Document Store

The WoT Registry is a document store: the `things` Resources rely on
the xRegistry Core default of
[`hasdocument`][xRegistry hasdocument] `true`, which is why
[model.json](model.json) does not declare it.

Such a Resource is exposed through two views:

- The **document view** serves the stored JSON-LD TD, TM, or TP document itself,
  using its stored media type — `application/td+json` for TDs and
  `application/tm+json` for TMs, per
  [WoT-TD 1.1 §12.1 and §12.2][WoT-TD-1.1], and provisionally
  `application/json` for TPs.
- The **metadata view** serves the entity's xRegistry attributes. The
  applicable protocol binding defines how the two views are selected; the
  xRegistry HTTP Binding uses the `$details` URL suffix to select the
  metadata view.

Because these Resources have a document, an entity's
[`self`][xRegistry self] URL is its **metadata-view** URL — in the HTTP
binding, the `$details`-suffixed one. The URL that serves the document is that
same URL *without* the `$details` suffix, which is also what
[`shortself`][xRegistry shortself] is an alternative for where a deployment
enables that capability.

This means an xRegistry-unaware WoT consumer MAY be handed a Version's `self`
URL with the `$details` suffix removed — or its `shortself` URL — and treat it
as a regular WoT document URL. Handing that consumer the `self` URL unchanged
would return xRegistry metadata rather than the document, so the two are not
interchangeable.

Addressing a `thing` Resource without naming a
Version serves that Resource's [default Version][xRegistry version-ids];
[Section 5.3](#53-lookup) describes both forms of retrieval.

## 2. Notations and Terminology

### 2.1. Notational Conventions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://tools.ietf.org/html/rfc2119).

For clarity, OPTIONAL attributes (specification-defined and extensions) are
OPTIONAL for clients to use, but the servers' responsibility will vary.
Server-unknown extension attributes MUST be silently stored in the backing
datastore. Specification-defined, and server-known extension, attributes MUST
generate an error if the corresponding feature is not supported or enabled.
However, as with all attributes, if accepting the attribute results in a bad
state (such as exceeding a size limit or resulting in a security issue), then
the server MAY choose to reject the request.

In the pseudo JSON format snippets `?` means the preceding attribute is
OPTIONAL, `*` means the preceding attribute MAY appear zero or more times,
and `+` means the preceding attribute MUST appear at least once. The presence
of the `#` character means the remaining portion of the line is a comment.
Whitespace characters in the JSON snippets are used for readability and are
not normative.

### 2.2. Terminology

This specification defines the following terms:

#### 2.2.1. Thing Description

A **Thing Description** is a concrete WoT-TD 1.1 JSON-LD document describing
a deployed Thing instance. It is stored as a Version of a `thing` Resource
with `kind` set to `ThingDescription`.

#### 2.2.2. Thing Model

A **Thing Model** is a concrete WoT-TM 1.1 JSON-LD document stored as a
Version of a `thing` Resource with `kind` set to `ThingModel`.

A Thing Model is distinguished from a Thing by purpose: a Thing Model
describes a **class** of Things and typically lacks concrete `href` values in
its forms, whereas a Thing Description describes a **specific** deployed Thing
instance.

#### 2.2.3. WoT Identifier

A **WoT identifier** is the URI a WoT document carries in its `id` member, as
defined by [WoT-TD 1.1][WoT-TD-1.1] — for example `urn:fabrikam:lamp:42`. It
is location-independent: it names *what* the document describes, not where it
is stored, and it is the identifier that other WoT documents and WoT tooling
use to refer to it.

A WoT identifier is held in the `wotid` attribute and is distinct from the
xRegistry `thingid`, which is the Resource's id
*within a registry*. The two MAY hold the same string where the authored
identifier happens to satisfy the xRegistry id grammar, but most do not — a
URL such as `https://fabrikam.example/things/lamp-42` is not a legal
xRegistry id — so this specification keeps them as two attributes rather than
reusing the Resource id for both.
[Section 5.1](#51-wot-identifiers-and-registry-ids) defines how the two
relate.

#### 2.2.4. Thing Projection

A **Thing Projection** is a JSON-LD 1.1 document stored as a Version of a
`thing` Resource with `kind` set to `ThingProjection`. Its admission and
media type are provisional; see [Section 4.5.3](#453-wot-thing-projection).

#### 2.2.5. Thing Resource

A **Thing Resource** (`thing`) groups Versions of one logical WoT document.
It is a registry container, not necessarily a deployed Thing. Addressing it
without a Version selects its [default Version][xRegistry version-ids].
All Versions share one `kind` and one `wotid` and adhere to the Resource's
[`compatibility`][xRegistry compatibility] policy, if specified.

### 2.3. Thing Group

A **Thing Group** is an application-defined container for Thing Resources,
for example all documents for a tenant, fleet, site, vendor, or product
family. A Group MAY contain TDs, TMs, and TPs together; this specification
does not impose a kind-based partition.

## 3. WoT Registry Model

The authoritative xRegistry extension model of the WoT Registry resides in
the [model.json](model.json) file. Its `modelversion` — `0.2` while this
remains a working draft — versions *this* model, and moves independently of
the xRegistry Core specification version that appears in a Registry's
`specversion`.

For easy reference, the JSON serialization of a WoT Registry adheres to this
form:

```yaml
{
  "specversion": "<STRING>",                       # xRegistry core attributes
  "registryid": "<STRING>",
  "self": "<URL>",
  "xid": "<XID>",
  "epoch": <UINTEGER>,
  "name": "<STRING>", ?
  "description": "<STRING>", ?
  "documentation": "<URL>", ?
  "labels": {
    "<STRING>": "<STRING>" *
  }, ?
  "createdat": "<TIMESTAMP>",
  "modifiedat": "<TIMESTAMP>",

  "model": { ... }, ?

  "thinggroups": {                                 # Thing Groups collection
    "KEY": {                                       # thinggroupid
      "thinggroupid": "<STRING>",                  # xRegistry core attributes
      "self": "<URL>",
      "xid": "<XID>",
      "epoch": <UINTEGER>,
      "name": "<STRING>", ?
      "description": "<STRING>", ?
      "documentation": "<URL>", ?
      "labels": { "<STRING>": "<STRING>" * }, ?
      "createdat": "<TIMESTAMP>",
      "modifiedat": "<TIMESTAMP>",
      "deprecated": { ... }, ?

      "things": {                                  # mixed-kind Things collection
        "KEY": {                                   # thingid
          "thingid": "<STRING>",                   # xRegistry core attributes
          "versionid": "<STRING>",
          "self": "<URL>",
          "xid": "<XID>",

          #  Start of default Version's attributes
          "epoch": <UINTEGER>,
          "name": "<STRING>", ?
          "description": "<STRING>", ?
          "documentation": "<URL>", ?
          "labels": { "<STRING>": "<STRING>" * }, ?
          "createdat": "<TIMESTAMP>",
          "modifiedat": "<TIMESTAMP>",
          "ancestorid": "<STRING>",
          "contenttype": "<STRING>",               # media type for kind; see 4.5
          "kind": "<STRING>",                      # ThingDescription, ThingModel or ThingProjection
          "format": "<STRING>",                    # MUST be "JSON-LD/1.1"
          "wotid": "<STRING>",                     # the document's authored 'id'
          "derivedfrom": [ "<STRING>" * ], ?       # TD/TM only: referenced TM wotids
          "license": "<STRING>", ?                 # provenance metadata
          "publisher": "<STRING>", ?
          "standardsbody": "<STRING>", ?
          "canonicalurl": "<URL>", ?
          "maturity": "<STRING>", ?
          "formatvalidated": <BOOLEAN>, ?
          "formatvalidatedreason": "<STRING>", ?
          "compatibilityvalidated": <BOOLEAN>, ?
          "compatibilityvalidatedreason": "<STRING>", ?

          "thingurl": "<URL>", ?
          "thing": <ANY>, ?                        # the TD, TM or TP JSON-LD document
          "thingbase64": "<STRING>", ?
          #  End of default Version's attributes

          "metaurl": "<URL>",
          "meta": { ... }, ?

          "versions": { ... }, ?
          "versionsurl": "<URL>",
          "versionscount": <UINTEGER>
        } *
      }, ?
      "thingsurl": "<URL>",
      "thingscount": <UINTEGER>
    } *
  }, ?
  "thinggroupsurl": "<URL>",
  "thinggroupscount": <UINTEGER>
}
```

## 4. WoT Registry

The WoT Registry organizes Thing Descriptions, Thing Models, Thing Projections,
and their Versions in one document store.

Implementations of this specification MAY include additional extension
attributes, including the `*` attribute of type `any`.

Since the WoT Registry is an application of the
[xRegistry specification][xRegistry Core], all attributes for Groups,
Resources, and Resource Version objects are inherited from there.

### 4.1. Thing Groups

The Group Type (`<GROUP>`) name is `thinggroup` (singular).
The plural, used as the collection name, is `thinggroups`. A Thing Group
does not have any specific extension attributes.

A Thing Group collects related WoT documents in an application-defined way.
Every `thing` Resource MUST reside inside a Thing Group. Groups MUST NOT
require separate Resource collections for different kinds.

Example:

```yaml
{
  # xRegistry top-level attributes excluded for brevity

  "thinggroups": {
    "fabrikam.factory-floor-01": {
      "thinggroupid": "fabrikam.factory-floor-01",
      # other xRegistry Group-level attributes excluded for brevity

      "thingsurl": "https://example.com/thinggroups/fabrikam.factory-floor-01/things",
      "thingscount": 12
    }
  },
  "thinggroupsurl": "https://example.com/thinggroups",
  "thinggroupscount": 1
}
```

### 4.2. Thing Resources

The Resource Type (`<RESOURCE>`) inside of Thing Groups is named `thing`. The
plural, used as the collection name, is `things`. Any single `thing` is a
container for one or more `versions`, each of which holds the concrete
TD, TM, or TP JSON-LD document. The document attributes are `thing`,
`thingurl`, and `thingbase64`, regardless of kind.

The `format` attribute of a `thing` Resource Version MUST be
`"JSON-LD/1.1"`. [model.json](model.json) declares the `format` enumeration
as `strict`, so a registry rejects any other value rather than merely
discouraging it.

The `contenttype` of a `thing` document MUST be supplied and MUST match its
kind as specified in [Section 4.5](#45-formats), or be another non-active
media type the deployment has explicitly registered for that kind. A registry
MUST reject a write with a missing or incompatible `contenttype`.
`contenttype` is client-supplied, and the document view serves the stored
bytes under it
([Section 1.4](#14-document-store)), so a registry MUST NOT serve a stored
document under a client-supplied media type that causes it to be interpreted
as active content — for example `text/html`, `image/svg+xml` or
`application/xhtml+xml`. A registry MUST reject such a write. Because a Version's
document-view URL is intended to be dereferenced directly by WoT tooling, a
registry SHOULD additionally return `X-Content-Type-Options: nosniff` for
documents it did not itself author, or serve them from an origin separate
from any registry user interface. See [Section 7](#7-security).

The `wotid` attribute is REQUIRED and holds the document's authored WoT
identifier, which is distinct from the `thingid`. See
[Section 5.1](#51-wot-identifiers-and-registry-ids). The OPTIONAL
`derivedfrom` attribute lists the `wotid`s of the Thing Models a TD extends
or composes, or a TM extends via `tm:extends` or references via `tm:ref`.
This draft does not define TP lineage; Producers MUST omit `derivedfrom`
for `kind=ThingProjection` until such semantics are defined.
For TDs and TMs it is a producer-supplied index rather than an authority
over the document's own references, as
[Section 5.2](#52-preserving-customer-documents) describes.

All Versions of a single Thing Resource MUST adhere to the semantic rules of
the Resource's [`compatibility`][xRegistry compatibility] attribute, if specified.

Implementations of this specification SHOULD use the xRegistry default
algorithm for generating new `versionid` values. Which Version is the default
Version — the one served when no Version is named — MUST be determined by the
xRegistry Core rules, including the Resource's `defaultversionsticky`
setting, which a deployment MAY use to pin the default to a Version other
than the newest. This specification does not redefine either. See
[Version IDs][xRegistry version-ids] for more information.

### 4.3. Document Kind

`kind` is a REQUIRED string Version attribute. Its permitted values are
exactly `ThingDescription`, `ThingModel`, and `ThingProjection`; the model
declares a strict enumeration and no default. A registry MUST reject a
write that omits `kind` or supplies another value. It MUST NOT infer a kind
from a Group, Resource id, media type, title, or JSON-LD `@type`.

The model declares `kind` with `matchversions: true`. All Versions of one
Resource MUST have the same kind. A Producer MUST create a separate Resource
when changing kind, including when deriving a TD from a TM. In the
serialization without an explicit `versions` collection, `kind` appears on
the Resource alongside its implicit Version's attributes. With an explicit
`versions` collection it MUST be supplied on each Version.

`kind` is registry metadata, not a WoT vocabulary member. A registry MUST
NOT insert it into or otherwise rewrite the stored document. JSON-LD `@type`
and HTTP `Accept` are not substitutes for this attribute or for a kind filter.

### 4.4. Validation by Kind

Format validation MUST use the declared kind: TD and TM validation apply
their respective contracts in [Section 4.5](#45-formats). A registry that
parses documents MUST reject a write whose declared kind contradicts that
contract, rather than silently reclassifying it. A non-parsing store still
MUST enforce the metadata rules for `kind`, `format`, and `contenttype`.
Kind-filtered retrieval selects the declared metadata; it is not proof that
the document has passed format validation.

TP validation in this draft checks JSON-LD 1.1 only, not conformance to an
as-yet undefined TP vocabulary. It MUST NOT report TD or TM validation as
TP-specific conformance. The Core `validateformat`, `formatvalidated`,
`validatecompatibility`, and `compatibilityvalidated` mechanisms apply
unchanged; the unified collection does not waive validation for any kind.

### 4.5. Formats

All three kinds are serialized as JSON-LD 1.1
documents in this draft and use the
[core specification's `format`](../../../core/spec.md#format-attribute) identifier
`JSON-LD/1.1`. `kind` distinguishes document classes, while `contenttype`
controls their document-view representation. Neither the Group nor the
Resource collection name distinguishes kinds.

#### 4.5.1. WoT Thing Description

- `kind`: `ThingDescription`
- Format identifier: `JSON-LD/1.1`
- `contenttype`: `application/td+json`
- Document: a JSON-LD 1.1 document conformant with
  [W3C WoT Thing Description 1.1][WoT-TD-1.1].
- The document's `@context` MUST include
  `https://www.w3.org/2022/wot/td/v1.1`.
- A URI-reference pointing to a TD MAY use a JSON-Pointer
  ([RFC 6901](https://www.rfc-editor.org/rfc/rfc6901)) fragment to deep-link
  into a particular property, action, or event affordance, e.g.
  `…/things/lamp-42#/properties/status`.

#### 4.5.2. WoT Thing Model

- `kind`: `ThingModel`
- Format identifier: `JSON-LD/1.1`
- `contenttype`: `application/tm+json`
- Document: a JSON-LD 1.1 document conformant with
  [W3C WoT Thing Model 1.1][WoT-TM-1.1].
- The document's `@context` MUST include
  `https://www.w3.org/2022/wot/td/v1.1` and the document's top-level
  `@type` MUST include `tm:ThingModel`.
- Deep-linking via JSON-Pointer fragments is permitted, as for TDs.

#### 4.5.3. WoT Thing Projection

- `kind`: `ThingProjection`
- Format identifier: `JSON-LD/1.1`
- `contenttype`: `application/json` (provisional)
- Document: a JSON-LD 1.1 document. This draft does not define TP-specific
  vocabulary, a REQUIRED `@type`, projection source links, or lineage.

This is a provisional registry convention, not a claim that a W3C TP media
type or document specification has been standardized. Consumers MUST NOT
infer a projection's source or derivation from `wotid`, `derivedfrom`, or
the Group layout. A later draft will define TP lineage.

### 4.6. Provenance and Selection Metadata

A registry is consumed by tools and by autonomous agents that have to choose
between several documents describing similar Things. Choosing well needs
metadata that is *explicit*, rather than inferred from a title or a naming
convention. All `thing` Resources therefore carry
the following OPTIONAL attributes:

| Attribute | Type | Meaning |
|---|---|---|
| `license` | string | The license the document is offered under, as an [SPDX][SPDX] license expression or a URL |
| `publisher` | string | The organization that published the document |
| `standardsbody` | string | The standards organization that defines or endorses the document, where one does |
| `canonicalurl` | url | The canonical upstream location of the document, where it is also published outside this registry |
| `maturity` | string | One of `Standard`, `Vendor`, `Community` or `Experimental` |

A Consumer choosing between candidate Thing Models SHOULD prefer, in order:

1. `maturity` of `Standard` accompanied by a `standardsbody`.
2. `maturity` of `Vendor`, **or** `maturity` of `Standard` with no
   `standardsbody` — the two rank equally, because a document is not an
   interoperable standard merely because its writer marked it `Standard`.
3. `maturity` of `Community`.
4. `maturity` of `Experimental`.
5. No `maturity` at all.

Where the choice remains open the Consumer SHOULD prefer the document whose
`canonicalurl` it already trusts. [model.json](model.json) declares the
`maturity` enumeration as `strict`, so a registry rejects a value outside
this set; a Consumer that nonetheless encounters one — from a federated
registry, for example — MUST NOT rank it above `Experimental`, because this
specification defines no precedence for it.

These attributes are **advisory and unverified**. They describe where a
document claims to have come from and how established its writer says it is.
They are asserted by whoever writes the Resource, and this specification
defines no mechanism by which a registry validates that a `publisher` or
`standardsbody` claim is genuine; a registry MUST NOT be assumed to have done
so. A Consumer MUST NOT treat them as authenticated provenance, and the
preference order above is a tie-break among documents the Consumer has
*already* decided to trust — by Group, by writer identity, or by an
out-of-band signature. It MUST NOT be used to establish trust in a document
from an untrusted writer. [Section 5.3](#53-lookup) notes that one `wotid`
MAY legitimately match several Resources, so this is a real choice among
candidates written by different parties; see also
[Section 7](#7-security).

These attributes are also not part of a document's semantic identity. A
registry MUST NOT treat two documents as the same document because their
provenance attributes agree, nor as different documents because they differ:
kind-specific identity is `(kind, wotid)`, not provenance
([Section 5.1](#51-wot-identifiers-and-registry-ids)).

They are Version attributes, carried on each Version alongside the document
they describe, as `format` and `wotid` are. This specification defines no
special update semantics for them; they are written and updated exactly as any
other Version attribute is, under the xRegistry Core rules.

## 5. Identity and Resolution

### 5.1. WoT Identifiers and Registry Ids

xRegistry gives every entity an id — a `thingid` for a Resource —
and an [`xid`][xRegistry Core], the stable
path those ids form within the registry. Each entity id is constrained to
[RFC 3986][RFC3986] `unreserved` characters plus `:` and `@`, starting with a
letter, a digit or `_`, at most 128 characters long, and unique
case-insensitively within its parent. A WoT identifier is the value of a document's
`id` member, where present: a URI, most often a URN such as `urn:fabrikam:lamp:42`,
but equally a URL such as `https://fabrikam.example/things/lamp-42`.

The two express the same idea but are **not the same grammar**:
`https://fabrikam.example/things/lamp-42` is not a valid entity id, so it is
also not a valid `xid` component, and an `xid` is not what a Thing author
writes. Where an authored identifier does satisfy the id grammar a client MAY
use it as the Resource id, but a registry cannot rely on that.

This specification therefore does not equate them, and does not define a
mapping between them:

> A `thing`'s `wotid` is its document's identity in the WoT
> identifier space ([Section 2.2.3](#223-wot-identifier)). Its
> `thingid` is the Resource's id *within this registry* and is
> chosen by the client that creates the Resource, subject to the xRegistry
> Core id rules and to whatever further naming constraints the deployment
> imposes. Neither is derived from the other.

Kind-specific resolution uses `(kind, wotid)`. Different kinds MAY share a
`wotid`, including within one Group, but MUST occupy separate Resources
with distinct `thingid` values. This does not declare the documents
interchangeable or define a derivation relationship between them.

A client creating a Resource therefore chooses its id the same way it chooses
a Group id: it either names the id in the request path, or supplies it in the
request body, or omits it and lets the registry assign one under the xRegistry
Core rules. Nothing in the document dictates the choice, and nothing later
depends on it, because `wotid` is a first-party attribute: a Consumer holding
a WoT identifier finds the Resource by querying on it
([Section 5.3](#53-lookup)) rather than by reconstructing a path. A deployment
MAY derive its Resource ids from `wotid` values by a convention of its own —
the [OpenUSD Artifact Registry][OpenUSD Draft] working draft defines one such
construction — but no convention is mandated by this specification, and a
Consumer MUST NOT assume that an id it did not assign was produced by one.

A `wotid` MUST NOT encode a revision of the document it names. Encoding one —
for example as a `:v2` suffix appended when the document is edited — makes the
identifier change whenever the document changes, so the registry can no longer
tell that two documents describe the same logical Thing,
[`ancestorid`][xRegistry ancestorid] lineage is broken, and every consumer
holding a reference has to be rewritten on each revision. The version of a
document is carried by the xRegistry `versionid` and, where the document
declares one, by its own WoT `version` member; neither is part of the
identifier.

This is a prohibition on *versioning an identifier*, not on the characters
that can appear in one. A vendor who deliberately publishes a second,
incompatible Thing alongside the first is naming a different Thing, and the
identifier they author for it — which might well carry a `v2` token — is that
Thing's own stable `wotid`; see
[Section 5.1.1](#511-breaking-changes-and-successor-identifiers).

Consequently, when a document is revised:

- Its `wotid` is unchanged.
- Its `kind` is unchanged.
- Its `thingid` is unchanged, because it is the
  same Resource.
- A new Version is created under the same Resource.

A `wotid` is REQUIRED, and the rule for populating it depends on the document:

- Where the document carries an `id` member, `wotid` MUST equal it verbatim.
  A registry that parses the stored document MUST reject a write whose
  `wotid` differs from that `id`, rather than storing two identities for one
  document. A registry that does not parse the document cannot detect the
  disagreement; neither MUST resolve one by rewriting either value, because
  [Section 5.2](#52-preserving-customer-documents) forbids editing the
  document.
- Where the document carries no `id` member — which
  [WoT-TD 1.1][WoT-TD-1.1] permits for TDs served from a fixed URL, and which
  is common for TMs; the same registry rule applies to a TP without `id` —
  the Producer MUST supply a `wotid` at write time, and
  that supplied value is thereafter the document's identity in this registry.
- A registry MUST reject a write that supplies neither an `id` member nor a
  `wotid`, rather than inventing one, because an invented identifier is not
  stable across registries.

[Decision 4](decisions.md#4-wotid-is-a-required-indexed-first-party-attribute)
records that whether a future revision ought to define a derivation for the
second case is not yet settled.

#### 5.1.1. Breaking Changes and Successor Identifiers

[Section 1.3](#13-versioning) requires a breaking change that violates the
Resource's [`compatibility`][xRegistry compatibility] policy to result in a
new Resource rather than a new Version. Since a `wotid` does not change when
its document is revised, and every Version of a Resource carries the same
one, a successor cannot be produced by editing an existing document: it is
produced by authoring a **new logical Thing** with its own `wotid`, stored as
a new Resource.

This successor rule applies within a kind. Creating a different kind of
document is not a revision of the first and MAY reuse its `wotid` as
described in [Section 5.1](#51-wot-identifiers-and-registry-ids).

- The successor's `wotid` is a new authored identifier, distinct from the
  predecessor's. It is that Thing's permanent identity and is itself never
  revised thereafter.
- The successor is a distinct Resource with its own `thingid`, so
  predecessor and successor occupy distinct paths and are
  independently retrievable.
- The predecessor's Versions are retained and remain retrievable. A breaking
  change does not remove history.
- The predecessor SHOULD set [`deprecated`][xRegistry deprecated], naming the
  successor Resource, so a consumer holding the old identifier can find the
  new one without a side channel.

Where a solution versions its Things semantically, it is RECOMMENDED that the
authored identifier carry a major-version token — `urn:fabrikam:lamp:v2`, or
`https://fabrikam.example/tm/lamp/v2` — so that incompatible but historically
related Things are recognizable to users and developers. The `versionid` then
functions as the minor-version identifier within each of them. This mirrors
the convention the [Schema Registry][xRegistry Schema] recommends for
`schemaid`.

This does not contradict
[Section 5.1](#51-wot-identifiers-and-registry-ids): the
token is chosen once, by the author, as part of naming a distinct Thing, and
that Thing's `wotid` is thereafter stable across all of its own revisions. What
Section 5.1 forbids is a registry or a Producer *mutating* an identifier — a
`wotid` that becomes `…:v2` because the document it already names was edited.

For example, a lamp whose control interface changes incompatibly:

| | Predecessor | Successor |
|---|---|---|
| `wotid` | `urn:fabrikam:lamp` | `urn:fabrikam:lamp:v2` |
| `thingid` | `urn.fabrikam.lamp` | `urn.fabrikam.lamp.v2` |
| Versions | `1`, `2`, `3` — retained | `1`, growing independently |
| `deprecated` | set, naming the successor | absent |

### 5.2. Preserving Customer Documents

Registries are populated with WoT documents that already
exist: authored by a vendor, published by a standards body, or generated by a
toolchain, and referenced from artifacts the registry never sees. Such a
document is stored as it was authored.

- A registry MUST store the WoT document byte-for-byte as supplied, apart from
  transformations the client explicitly requested.
- A registry MUST NOT rewrite the document's `id` member, its `links[].href`
  values, its `tm:extends` or `tm:ref` targets, or any other identifier
  internal to the document, into registry-specific identifiers.
- A retrieval of a stored Version through the document view MUST return the
  exact bytes supplied, as the xRegistry Core document view already requires.
  Re-serializing the document — reordering members, re-indenting, or
  normalizing its JSON-LD — is not permitted.

Rewriting is incompatible with these documents for three reasons. A TM
published by a standards body is referenced by `id` from artifacts outside the
registry, and rewriting the `id` would break those references while leaving
the registry's own copy claiming to be the standard document. A TD's
`tm:extends` target resolves in the WoT identifier space, so a rewritten
target no longer matches what any other WoT tool would look for. And a
document copied between two registries would acquire two different identities
for the same bytes, so neither registry could tell the copies apart from
genuinely distinct documents.

The registry's own identity for a document — its `thingid` and the `xid`
that includes it — therefore lives *outside* the
document, and the identifiers the document itself authored are carried
alongside it, unchanged, in the `wotid` and `derivedfrom` attributes. This
keeps the authored identifier space and the registry identifier space
separate and allows a document to round-trip unchanged.

Where a registry wants the TD-to-TM link to be traversable without parsing the
document, it records the referenced Thing Models' *authored* identifiers in
the `derivedfrom` attribute. `derivedfrom` holds `wotid` values, not `xid`s,
precisely so that it can be compared directly against what the document
authored.

`derivedfrom` is a producer-supplied *index* of the document's references,
not an authority over them. A registry MAY verify that it matches the
`tm:extends`, `tm:ref` and `links[].rel="type"` targets in the stored
document, and SHOULD reject a write where the two disagree; where a registry
does not verify, the document is authoritative. A Consumer making a trust,
allow-list or compliance decision about a document's lineage MUST derive that
lineage from the document itself and MUST NOT rely on `derivedfrom` alone.

### 5.3. Lookup

A Consumer holding a WoT identifier — typically taken from a `tm:extends`
link, a `tm:ref`, another `links[].href`, or a message attribute — resolves it
to a stored document in one of two ways.

**By path.** Where the Consumer already knows the Resource's Group and id —
because it was given them, or because it follows a stored `self` URL — it
addresses the Resource directly:

```
/thinggroups/<thinggroupid>/things/<thingid>
```

**By `wotid`.** Otherwise — the usual case, since WoT documents reference one
another by authored identifier rather than by registry path — it queries on
the `wotid` attribute:

```
GET /thinggroups/Fabrikam.Lighting/things?filter=kind=ThingModel,wotid=urn:fabrikam:lamp
```

An implementation SHOULD serve this query in time that does not grow with the
size of the collection — in practice by indexing `(kind, wotid)` on
`things`. Implementations SHOULD also index `kind` for kind-only queries.
Resolution is on the critical path of
composing a TD from its Thing Models, so a linear scan per reference does not
scale.

A `(kind, wotid)` pair SHOULD be unique within a Group, so that a Group-scoped
query for both identifies a single Resource. Different kinds MAY share a
`wotid` in one Group; a query on `wotid` alone MUST return all matching
kinds, not select one implicitly. Across Groups a pair MAY repeat — the
same vendor TM legitimately appears in two tenants' Groups — so a
registry-wide query MAY match more than one Resource, and a caller that needs
exactly one narrows the query by naming the Group. A registry-wide match MUST
return every matching Resource rather than an arbitrary one of them, and
[Section 4.6](#46-provenance-and-selection-metadata) governs how a Consumer
chooses among them.

If a Group contains more than one Resource with the same pair, a
Group-scoped query MUST likewise return every match, not choose one
arbitrarily. The uniqueness recommendation is not a guarantee.

Version selection is a second, separate step, and is never encoded in the
*identifier*. It is, of course, encoded in the URL — that is what the
`versions` collection is for:

| Intent | Request |
|---|---|
| Latest Version | the Resource's URL, which serves its default Version |
| A specific Version | `<resource-url>/versions/<versionid>` |
| Enumerate Versions | `<resource-url>/versions` |

`<resource-url>` above is the Resource's [`self`][xRegistry self] URL for the
metadata view, or that URL with the `$details` suffix removed for the
document view; see [Section 1.4](#14-document-store).

"Latest" is the Resource's [default Version][xRegistry version-ids], as
determined by the xRegistry Core rules and the Resource's `defaultversionsticky`
setting; this specification does not redefine it. A registry MUST serve the
default Version when no Version is named. A Consumer MUST NOT infer the
latest Version by sorting `versionid`s itself.

What a caller SHOULD NOT do is fold the identifier and Version into one
opaque string. A caller that carries an identifier and a version through
a transport — for example in
message headers — SHOULD carry them as two separate values, such as a
`wotid` header and a `versionid` header, rather than a single compound token
like `urn:fabrikam:lamp@3` that every recipient has to take apart. The
identifier stays a WoT identifier, and the version stays a `versionid` the
recipient can put straight into a URL.

#### 5.3.1. Kind-Filtered Discovery and Access

A conforming WoT Registry MUST support the xRegistry Core
[`filter` flag][xRegistry filter] for `kind`, alone and combined with
`wotid`, on collection queries and on direct Resource and Version retrieval,
including document-view retrieval. A server MUST apply the filter before
returning a document. It MUST NOT ignore a kind filter or return an
unfiltered successful response when it cannot evaluate the filter.

The following HTTP examples use Core dot-notation relative to the request
URL. There is no root-level `/things` collection endpoint:

| Intent | Request |
|---|---|
| Only TDs in a Group | `GET /thinggroups/Fabrikam.Lighting/things?filter=kind=ThingDescription` |
| Only TMs across all Groups | `GET /?filter=thinggroups.things.kind=ThingModel&inline=thinggroups.things` |
| Only TPs across all Groups | `GET /?filter=thinggroups.things.kind=ThingProjection&inline=thinggroups.things` |
| Resolve a TM across Groups | `GET /?filter=thinggroups.things.kind=ThingModel,thinggroups.things.wotid=urn:fabrikam:lamp&inline=thinggroups.things` |
| TDs or TPs in a Group | `GET /thinggroups/Fabrikam.Lighting/things?filter=kind=ThingDescription&filter=kind=ThingProjection` |
| Retrieve a TM's default document only if kind matches | `GET /thinggroups/Fabrikam.Lighting/things/urn.fabrikam.lamp?filter=kind=ThingModel` |
| Retrieve a specific TM Version's document only if kind matches | `GET /thinggroups/Fabrikam.Lighting/things/urn.fabrikam.lamp/versions/1?filter=kind=ThingModel` |
| Retrieve TM metadata only if kind matches | `GET /thinggroups/Fabrikam.Lighting/things/urn.fabrikam.lamp$details?filter=kind=ThingModel` |
| Enumerate only TM Versions | `GET /thinggroups/Fabrikam.Lighting/things/urn.fabrikam.lamp/versions?filter=kind=ThingModel` |

Commas within one HTTP `filter` parameter express AND; repeated `filter`
parameters express OR. Each AND clause MUST apply to the same candidate
Resource, not be satisfied by different Resources in a Group. String
comparisons follow Core's case-insensitive filter rules; the canonical
stored kind values remain those in [Section 4.3](#43-document-kind).
Values containing reserved query characters MUST be URL-encoded according
to the HTTP binding.

Collection responses MUST exclude nonmatching Resources or Versions and
count only matches. Root-scoped responses retain the Registry/Group
structure; `inline` includes matching metadata, not a new raw-document
collection. Consumers retrieve document bytes using the matching Resource
or Version's document-view URL. A Consumer that requires kind-restricted
access MUST retain `filter=kind=...` on that request; discovery alone is
not an access-time check. When following collection URLs or pagination
links, the effective kind filter MUST be preserved, including by the
Consumer reapplying it if the returned URL does not carry it.

A collection with no matches returns an empty collection. A direct
Resource or Version request whose `kind` does not match MUST return
`404 Not Found`, not a document of another kind. Since `kind` is fixed
across Versions, default-Version selection, sticky defaults, and explicitly
pinned Versions cannot change the result's kind. Resource filtering uses
the default Version's metadata; Version filtering uses the named Version's.

These are selection semantics, not authorization. A kind filter grants no
access to otherwise unauthorized documents and does not replace access
controls or validation of document contents.

### 5.4. Migration from Separate Collections

This is a breaking working-draft change from model version `0.1` to `0.2`.
The former `thingdescriptiongroups` / `thingdescriptions` and `thingmodelgroups` /
`thingmodels` structures are replaced by `thinggroups` / `things`.
No legacy endpoint aliases or dual-serving period are specified.

Migration MUST assign `kind=ThingDescription` to former TD Versions and
`kind=ThingModel` to former TM Versions, including every explicit Version.
The metadata document attributes become `thing`, `thingurl`, and
`thingbase64`; Group and Resource ids become `thinggroupid` and `thingid`.
Deployments MUST resolve colliding Group and Resource ids when merging
collections, respecting Core's case-insensitive id rules. Same-`wotid`
documents of different kinds remain distinct Resources.

Registry paths and links to them change. Producers and Consumers need their
registry references updated, but migration MUST NOT rewrite authored WoT
document bytes or `wotid` values. Existing embedded URLs therefore need an
operator-managed compatibility route or continued hosting at the old
location if they are to remain dereferenceable. That deployment choice
does not restore the former collections to this model.

## 6. Relationships and Cross-References

Sections [6.1](#61-thing-description-to-thing-model) through
[6.3](#63-thing-description-to-schema-registry) describe how existing WoT and
xRegistry mechanisms compose. They place no requirements on a conformant
registry and use no RFC 2119 keywords;
[Section 6.4](#64-affordance-grouping) is normative.

### 6.1. Thing Description to Thing Model

A WoT-TD 1.1 document can declare that it conforms to one or more Thing
Models using the `links` member ([WoT-TD 1.1 §6.3.8][WoT-TD-1.1]) with
`"rel": "type"`, the convention specified in
[WoT-TD 1.1 §9.4, Derivation of Thing Description Instances][WoT-TD-1.1].
When the referenced Thing Model resides in the same WoT Registry, the `href`
can point at that Thing Model's document-view URL — its
[`self`][xRegistry self] URL with the `$details` suffix removed, or
equivalently its [`shortself`][xRegistry shortself] URL — since a `link`
carrying `"type": "application/tm+json"` is expected to dereference to the TM
document itself and not to xRegistry metadata
([Section 1.4](#14-document-store)). Because
[Section 5.2](#52-preserving-customer-documents) forbids rewriting, a document
that already carried an `href` in the WoT identifier space keeps it, and the
link is recorded in `derivedfrom` instead.

The `href` in such a link is an absolute URL. A registry-relative path would
not survive a copy of the document to another registry, which is the outcome
[Section 5.2](#52-preserving-customer-documents) exists to prevent.

For example:

```json
{
  "@context": "https://www.w3.org/2022/wot/td/v1.1",
  "@type": "Thing",
  "title": "Lamp #42",
  "links": [
    {
      "rel": "type",
      "href": "https://example.com/thinggroups/Fabrikam.Lighting/things/urn.fabrikam.lamp",
      "type": "application/tm+json"
    }
  ]
}
```

A Thing Description and the Thing Model it derives from are two distinct
Resources with independent lifecycles, so this relationship is expressed
through the TD document's `links` member rather than through the xRegistry
[`xref`][xRegistry xref] attribute, which exists to surface the *same*
Resource under more than one Group.

### 6.2. Thing Description to Endpoint Registry

A WoT-TD 1.1 `forms` entry binds an interaction affordance to a network
endpoint. When a Thing Description shares an endpoint that is independently
managed by an xRegistry [Endpoint Registry][xRegistry Endpoint],
implementations typically make the `forms[].href` value a URL that resolves to
one of the protocol bindings declared by the corresponding `endpoint`
Resource, so that the two descriptions of the same endpoint do not drift.

This specification does not require an `endpoint` Resource to exist for every
`forms` entry, nor does it require any specific naming or correlation
mechanism. Implementations are free to define their own conventions to
correlate the two.

### 6.3. Thing Description to Schema Registry

A WoT-TD 1.1 property, action, or event affordance can reference an external
data schema rather than declaring its data schema inline. When the referenced
schema is managed by an xRegistry [Schema Registry][xRegistry Schema],
implementations typically express the reference using the WoT
[`tm:ref`][WoT-TM-1.1] mechanism (in TMs) or a `links` entry with
`"rel": "describedby"` (in TDs), with the `href` resolving to the `schema`
Resource Version's document-view URL — the `self` URL with the `$details`
suffix removed.

### 6.4. Affordance Grouping

A Thing Description declares its properties, actions and events in the
`properties`, `actions` and `events` members of a single document, as defined
by [WoT-TD 1.1][WoT-TD-1.1]. This specification requires nothing more:

- A registry MUST accept and serve a valid TD whose affordances are all
  declared in one document, with no grouping construct of any kind.
- A registry MUST NOT require an affordance to belong to a group in order to
  be stored, retrieved, or referenced.
- Nothing in this specification — Resource layout, identity, versioning, or
  cross-referencing — depends on affordances being partitioned.

Proposals to sub-divide a large TD's affordances, such as a `td:submodel`
grouping member, are being discussed in the W3C WoT community. Were such a
mechanism to be standardized, a WoT Registry would store a TD that uses it exactly as
it stores any other TD, since the grouping is a member of the document rather
than of the registry model. Support for it is OPTIONAL, and a registry that
does not understand it MUST still store and serve the document unchanged, per
[Section 5.2](#52-preserving-customer-documents).

This matters for documents the registry did not author: those routinely
contain no grouping construct, and MUST remain fully supported.

## 7. Security

Like the [xRegistry Core][xRegistry Core] specification, this specification
does not explicitly address authentication or authorization levels of users,
nor how to securely protect the APIs.

It is expected that any implementation of this specification will use
authentication and authorization mechanisms that are appropriate for the
application domain and the deployment environment. This MAY include, but is
not limited to, OAuth 2.0, OpenID Connect, API keys, or other mechanisms
appropriate for the use case.

For authorization, the `thinggroup` concept provides a
natural authorization boundary, where users can be granted access to specific
groups, and therefore to the WoT documents contained within those
groups. The `thing` Resources themselves can be used to
further restrict access to specific Versions, allowing for fine-grained
access control.

Mixing kinds in a Group does not make their authorization requirements
identical. Operators that previously used separate TD and TM Groups as
security boundaries MUST preserve the REQUIRED access controls when
migrating. A client-supplied `kind` filter is not a security boundary.

Operators of a WoT Registry SHOULD be aware that Thing Descriptions can
expose detailed information about deployed devices, including network
locations, operational endpoints, and security schemes. The
[WoT Security and Privacy Considerations][WoT-Security] document gives
additional guidance.

Three further considerations follow from this specification's own rules.

- **Resolution is composition.** A Thing Model composes other Thing Models
  through `tm:extends` and `tm:ref`, and a Thing Description names network
  endpoints through `links[].href` and `forms[].href`. These are authored
  strings taken verbatim from a document the registry did not write
  ([Section 5.2](#52-preserving-customer-documents)), and resolving one is a
  fetch performed with the resolver's network position and credentials, not
  the author's. A Consumer or registry that resolves them SHOULD confine
  resolution to the registry and its declared federation links. Where a
  deployment has to dereference an authored URL it SHOULD restrict the scheme
  to `https`, reject targets that resolve to loopback, link-local or other
  internal address ranges, decline to follow cross-origin redirects, and
  bound both the depth and the total size of the composition closure. The
  same applies to the `thingurl` attribute,
  whose bytes come from a location the registry does not control and for
  which this specification defines no integrity check.

- **Provenance metadata is self-asserted.** `license`, `publisher`,
  `standardsbody`, `canonicalurl` and `maturity` are written by whoever
  creates the Resource and are verified by nothing in this specification
  ([Section 4.6](#46-provenance-and-selection-metadata)). Because the same
  `wotid` MAY appear in more than one Group
  ([Section 5.3](#53-lookup)), a writer with access to any Group in a
  registry-wide query's scope can publish a document carrying another
  party's `wotid` and a flattering `maturity`/`standardsbody` pair. A
  Consumer that selects on those attributes alone would then compose an
  attacker's Thing Model and bind its affordances to the endpoints that
  model declares. Selection MUST therefore be scoped to writers the Consumer
  already trusts.

- **Stored documents are served from the registry's origin.** A document is
  stored byte-for-byte ([Section 5.2](#52-preserving-customer-documents)) and
  served under a client-supplied `contenttype`, so
  [Section 4.2](#42-thing-resources) constrains which media types
  a registry will serve it under. Format validation does not help here: a
  document can be valid JSON-LD 1.1 and still execute as script if served as
  `text/html`.

---

[WoT-TD-1.1]: https://www.w3.org/TR/wot-thing-description11/
[WoT-TM-1.1]: https://www.w3.org/TR/wot-thing-description11/
[WoT-Discovery]: https://www.w3.org/TR/wot-discovery/
[WoT-Security]: https://www.w3.org/TR/wot-security/
[RFC3986]: https://www.rfc-editor.org/rfc/rfc3986
[SPDX]: https://spdx.org/licenses/
[OpenUSD Draft]: ../openusd/spec.md
[xRegistry Core]: https://xregistry.io/xreg/xregistryspecs/core-v1/docs/spec.html
[xRegistry Endpoint]: https://xregistry.io/xreg/xregistryspecs/endpoint-v1/docs/spec.html
[xRegistry Message]: https://xregistry.io/xreg/xregistryspecs/message-v1/docs/spec.html
[xRegistry Schema]: https://xregistry.io/xreg/xregistryspecs/schema-v1/docs/spec.html
[xRegistry self]: https://xregistry.io/xreg/xregistryspecs/core-v1/docs/spec.html#self-attribute
[xRegistry shortself]: https://xregistry.io/xreg/xregistryspecs/core-v1/docs/spec.html#shortself-attribute
[xRegistry compatibility]: https://xregistry.io/xreg/xregistryspecs/core-v1/docs/spec.html#compatibility-attribute
[xRegistry ancestorid]: https://xregistry.io/xreg/xregistryspecs/core-v1/docs/spec.html#ancestorid-attribute
[xRegistry deprecated]: https://xregistry.io/xreg/xregistryspecs/core-v1/docs/spec.html#deprecated
[xRegistry matchversions]: https://xregistry.io/xreg/xregistryspecs/core-v1/docs/model.html#attributesstringmatchversions
[xRegistry version-ids]: https://xregistry.io/xreg/xregistryspecs/core-v1/docs/spec.html#version-ids
[xRegistry hasdocument]: https://xregistry.io/xreg/xregistryspecs/core-v1/docs/spec.html#hasdocument
[xRegistry xref]: https://xregistry.io/xreg/xregistryspecs/core-v1/docs/spec.html#xref-attribute
[xRegistry filter]: https://xregistry.io/xreg/xregistryspecs/core-v1/docs/spec.html#filter-flag
