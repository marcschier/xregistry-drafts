# WoT Registry Service - Version 1.0-rc5

<!-- words: WoT JSON-LD Servient affordances affordance discoverability tm td -->
<!-- words: thingdescription thingdescriptionid thingdescriptionurl thingdescriptions thingdescriptionsurl thingdescriptionscount thingdescriptionbase -->
<!-- words: thingmodel thingmodels thingmodelid thingmodelurl thingmodelsurl thingmodelscount thingmodelbase -->
<!-- words: thingdescriptiongroup thingdescriptiongroups thingdescriptiongroupid thingdescriptiongroupsurl thingdescriptiongroupscount -->
<!-- words: thingmodelgroup thingmodelgroups thingmodelgroupid thingmodelgroupsurl thingmodelgroupscount -->
<!-- words: invokeaction readproperty writeproperty subscribeevent securitydefinitions versionmode urn href -->
<!-- words: workbench fabrikam lamp lighting jwt tenantid deviceid -->
<!-- words: formatvalidated compatibilityvalidated formatvalidatedreason compatibilityvalidatedreason -->
<!-- words: coap describedby integrators lifecycles modbus opc tds tms ua matchversions -->
<!-- words: wotid wotids derivedfrom canonicalurl standardsbody submodel spdx openusd -->
<!-- words: toolchain byom contoso maturity publisher nosniff validateformat -->
<!-- words: shortself -->
<!-- words: processingprofile processingconfiguration stableprofileuri configurationuri wotprocessinggroup -->
<!-- words: archivepath digestscope documentbase documentdigest documenturl -->
<!-- words: effectivepolicydigest expecteddigest expectedevidencedigest -->
<!-- words: expectedinvocationdigest formatversion interpretationbase -->
<!-- words: invocationdigest jcs localreferences maxbytes maxdepth maxmilliseconds -->
<!-- words: plugin processingconfigurations processingprofiles rebased -->
<!-- words: replayability replayable representationprofile representationprofiles -->
<!-- words: resolutionpolicy resolutionrecords retainedartifacts rootdigest -->
<!-- words: sourcepointer subdocument targetpointer toolchains workingdrafts -->
<!-- words: wotprocessinggroupid wotprocessinggroups wotprocessinggroupscount -->
<!-- words: wotprocessinggroupsurl -->

## Abstract

This specification extends the xRegistry document format and API
[specification][xRegistry Core] with a WoT (Web of Things) Registry model. A
WoT Registry stores, manages, and discovers W3C
[WoT Thing Description (WoT-TD)][WoT-TD-1.1] and
[WoT Thing Model (WoT-TM)][WoT-TM-1.1] documents, together with WoT processing
profile descriptors and reusable configuration documents.

## Table of Contents

- [WoT Registry Service - Version 1.0-rc5](#wot-registry-service---version-10-rc5)
  - [Abstract](#abstract)
  - [Table of Contents](#table-of-contents)
  - [1. Overview](#1-overview)
    - [1.1. Thing Descriptions and Thing Models](#11-thing-descriptions-and-thing-models)
    - [1.2. Relationship to Other xRegistry Specs](#12-relationship-to-other-xregistry-specs)
    - [1.3. Versioning](#13-versioning)
    - [1.4. Document Store](#14-document-store)
  - [2. Notations and Terminology](#2-notations-and-terminology)
    - [2.1. Notational Conventions](#21-notational-conventions)
    - [2.2. Terminology](#22-terminology)
      - [2.2.1. Thing Description](#221-thing-description)
      - [2.2.2. Thing Model](#222-thing-model)
      - [2.2.3. WoT Identifier](#223-wot-identifier)
      - [2.2.4. Processing Profile](#224-processing-profile)
      - [2.2.5. Processing Configuration](#225-processing-configuration)
    - [2.3. Thing Description Group](#23-thing-description-group)
    - [2.4. Thing Model Group](#24-thing-model-group)
    - [2.5. WoT Processing Group](#25-wot-processing-group)
  - [3. WoT Registry Model](#3-wot-registry-model)
  - [4. WoT Registry](#4-wot-registry)
    - [4.1. Thing Description Groups](#41-thing-description-groups)
    - [4.2. Thing Description Resources](#42-thing-description-resources)
    - [4.3. Thing Model Groups](#43-thing-model-groups)
    - [4.4. Thing Model Resources](#44-thing-model-resources)
    - [4.5. Formats](#45-formats)
      - [4.5.1. WoT Thing Description](#451-wot-thing-description)
      - [4.5.2. WoT Thing Model](#452-wot-thing-model)
    - [4.6. Provenance and Selection Metadata](#46-provenance-and-selection-metadata)
    - [4.7. Processing Profile and Configuration Resources](#47-processing-profile-and-configuration-resources)
  - [5. Identity and Resolution](#5-identity-and-resolution)
    - [5.1. WoT Identifiers and Registry Ids](#51-wot-identifiers-and-registry-ids)
      - [5.1.1. Breaking Changes and Successor Identifiers](#511-breaking-changes-and-successor-identifiers)
    - [5.2. Preserving Customer Documents](#52-preserving-customer-documents)
    - [5.3. Lookup](#53-lookup)
    - [5.4. Processing Invocation and Evidence](#54-processing-invocation-and-evidence)
  - [6. Relationships and Cross-References](#6-relationships-and-cross-references)
    - [6.1. Thing Description to Thing Model](#61-thing-description-to-thing-model)
    - [6.2. Thing Description to Endpoint Registry](#62-thing-description-to-endpoint-registry)
    - [6.3. Thing Description to Schema Registry](#63-thing-description-to-schema-registry)
    - [6.4. Affordance Grouping](#64-affordance-grouping)
  - [7. Security](#7-security)

## 1. Overview

A WoT Registry stores and manages W3C Web of Things documents. A **Thing
Description** (TD) describes a deployed Thing; a **Thing Model** (TM) describes
a reusable class of Things. The registry also stores WoT processing profile
descriptors and reusable configuration documents.

A WoT Registry is generally used to share Thing metadata amongst multiple
parties: device fleets, gateways, integrators, and consuming applications. The
registry is intended to make Things and their templates **discoverable** in a
manner aligned with the W3C
[WoT Discovery][WoT-Discovery] specification, while also allowing TDs and TMs
to be cross-referenced from xRegistry [Endpoint][xRegistry Endpoint],
[Message][xRegistry Message], and [Schema][xRegistry Schema] entries.

### 1.1. Thing Descriptions and Thing Models

A **Thing Description** (TD) is a JSON-LD 1.1 document conforming to
[WoT-TD 1.1][WoT-TD-1.1]. It identifies a deployed Thing instance, declares its
properties, actions, and events, and provides one or more `forms` that bind
those interaction affordances to network endpoints over specific protocols
(HTTP, MQTT, CoAP, OPC-UA, Modbus, etc.).

A **Thing Model** (TM) is a JSON-LD 1.1 document conforming to
[WoT-TM 1.1][WoT-TM-1.1]. It describes an **abstract** class of Things and
typically has no concrete `href` values in its forms. A Thing Description can
associate itself with a Thing Model through a `links` entry with
`rel: "type"`. That link and a JSON-LD `@type` declaration identify a
relationship; neither imports or merges another document.

Both document classes use JSON-LD and share some vocabulary, but their intended
use, validation rules, and lifecycle differ. A WoT Registry MUST therefore
treat them as distinct Resource types. WoT-TM operators apply to Thing Models.
A TD's `rel: "type"` link associates it with a Thing Model, and JSON-LD
`@type` supplies semantic type information; neither directs a consumer to
fetch or compose another document. Any TD composition operator or
unresolved-plan marker belongs to a separately identified processing profile
and does not change ordinary TD or TM interpretation.

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
cross-references. An implementation MAY check that a referent exists, but MUST
still store and serve a document whose referent is absent. Consumers that
compose a TD from its Thing Models or bind an affordance to an endpoint remain
responsible for resolving those references.

### 1.3. Versioning

Each Version of a `thingdescription` or `thingmodel` Resource holds a complete
WoT-TD or WoT-TM document. This specification does not require a registry to
parse the document in order to derive registry metadata; the document is
stored as supplied, and the xRegistry [`versionid`][xRegistry version-ids]
follows the Core rules. Core's server-assignment default uses increasing,
integer-looking IDs, but clients MAY supply IDs when the Resource's
`setversionid` policy permits it. The Resource's `versionmode` determines how
Version ancestry and default selection are handled. This specification defines
no separate version mode.

A Version's identifier — its [`versionid`][xRegistry version-ids] — is never
part of a Resource's identity. A Resource's `wotid`, `thingdescriptionid` and
`thingmodelid` are stable across revisions of the document they name; `wotid`
is declared with [`matchversions`][xRegistry matchversions], so a registry
MUST reject a Version that supplies a different one. See
[Section 5.1](#51-wot-identifiers-and-registry-ids).

The xRegistry Core versioning rules (`versionid` identity,
[`ancestorid`][xRegistry ancestorid] lineage, and default-Version selection)
apply unchanged. A Version ID is not the TD/TM document's own `version` label
and MUST NOT be inferred from or substituted for it. A breaking change to a TD
or TM that violates the
Resource's [`compatibility`][xRegistry compatibility] policy MUST result in a
new Resource, not a new Version. `compatibility` is OPTIONAL in Core and this
specification does not set it, so a deployment that wants this rule to bind
sets `compatibility` on the Resource; where it is absent, Core makes no
statement about the relationship between Versions and the registry behaves as
a plain document store.

Because all Versions of a Resource share one `wotid`, a successor Resource is
reached by authoring a *new* WoT identifier, and the superseded Resource
records where the successor lives; see
[Section 5.1.1](#511-breaking-changes-and-successor-identifiers).

The `processingprofile` and `processingconfiguration` Resources introduced
in [Section 4.7](#47-processing-profile-and-configuration-resources) also use
ordinary Core Versions. Their document `version` labels are opaque application
values; they are neither Core Version IDs nor SemVer constraints, and they do
not replace a digest. A replayable invocation MUST bind each selected
descriptor and configuration to its exact Core Version ID, complete
document-file digest, document URL, and interpretation base. A stable URI or
unchanged Core Version ID does not prove that the bytes are unchanged.

### 1.4. Document Store

The WoT Registry is a document store: the `thingdescriptions`,
`thingmodels`, `processingprofiles`, and `processingconfigurations` Resources
rely on the xRegistry Core default of
[`hasdocument`][xRegistry hasdocument] `true`, which is why
[model.json](model.json) does not declare it.

Such a Resource is exposed through two views:

- The **document view** serves the stored JSON-LD TD or TM document itself,
  using its stored media type — `application/td+json` for TDs and
  `application/tm+json` for TMs, per
  [WoT-TD 1.1 §12.1 and §12.2][WoT-TD-1.1].
- The **metadata view** serves the entity's xRegistry attributes. The
  applicable protocol binding defines how the two views are selected; the
  xRegistry HTTP Binding uses the `$details` URL suffix to select the
  metadata view.

Processing profile descriptors and configurations are JSON documents and use
the same Core document/metadata-view distinction. They are not JSON-LD, do not
use TD or TM media types, and carry no TD/TM validation claim.

Because these document Resources have a document, an entity's
[`self`][xRegistry self] URL is its **metadata-view** URL — in the HTTP
binding, the `$details`-suffixed one. The URL that serves the document is that
same URL *without* the `$details` suffix, which is also what
[`shortself`][xRegistry shortself] is an alternative for where a deployment
enables that capability.

A WoT consumer that does not understand xRegistry MAY use a
`thingdescription` or `thingmodel` Version's `self` URL with the `$details`
suffix removed, or its `shortself` URL, as a regular WoT document URL. The
unchanged `self` URL returns xRegistry metadata instead. Processing profile
and configuration documents are not TDs or TMs.

Addressing a `thingdescription` or `thingmodel` Resource without naming a
Version serves that Resource's [default Version][xRegistry version-ids];
[Section 5.3](#53-lookup) describes both forms of retrieval.

If a registry exposes `documentdigest` under
[Section 4.6](#46-provenance-and-selection-metadata), the value identifies the
stored, decoded file octets. It does not make the Version immutable. A registry
MAY advertise a reproducible-publication capability. It MUST state the
retention term, how deletion and revocation work, and whether the document
bytes or interpretation bindings can change. Without that commitment, Core
rules for Version updates, deletion, and pruning apply. A `maxversions` value
of zero, a sticky default, or a temporarily read-only attribute does not
commit the registry to retain a Version.

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

We use the term **Thing Description** (or `thingdescription` Resource) in this specification as a
logical grouping of **Thing Description Versions**. A **Thing Description Version** is a concrete
WoT-TD 1.1 JSON-LD document. The **Thing Description** Resource names one or
more concrete Thing Description documents that represent iterations of the
same logical Thing instance. It is more than a container for them: addressing
the Resource without naming a Version addresses its
[default Version][xRegistry version-ids], so the Resource also acts as a
stable alias for whichever Version is current. Per the definition of the
[`compatibility`][xRegistry compatibility] attribute, all Versions of a single
**Thing Description** MUST adhere to the rules defined by the `compatibility` attribute.
A breaking change that violates that policy MUST result in a new **Thing
Description** Resource being created; see [Section 1.3](#13-versioning).

#### 2.2.2. Thing Model

We use the term **Thing Model** (or `thingmodel` Resource) in this
specification as a logical grouping of **Thing Model Versions**. A **Thing
Model Version** is a concrete WoT-TM 1.1 JSON-LD document. As with Things,
versioning is governed by the Resource's `compatibility` attribute.

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
xRegistry `thingdescriptionid`/`thingmodelid`, which is the Resource's id
*within a registry*. The two MAY hold the same string where the authored
identifier happens to satisfy the xRegistry id grammar, but most do not — a
URL such as `https://fabrikam.example/things/lamp-42` is not a legal
xRegistry id — so this specification keeps them as two attributes rather than
reusing the Resource id for both.
[Section 5.1](#51-wot-identifiers-and-registry-ids) defines how the two
relate.

#### 2.2.4. Processing Profile

A **processing profile** is a locally supported, owner-defined description of
one or more bounded WoT document-processing operations, their reference roles,
and supported representation profiles. Its registry descriptor identifies and
discovers that description; it is not executable code, a trust grant, or proof
that a consumer implements the declared operations.

#### 2.2.5. Processing Configuration

A **processing configuration** is one reusable, root-free set of exact
reference-selection rules and finite processing limits for a processing
profile. A consumer selects exactly one configuration for an invocation. A
configuration does not identify a root document, requested operation or
part, deployment target, credentials, or authorization decision.

### 2.3. Thing Description Group

A Thing Description Group is a container for Thing Descriptions that are related to each
other in some application-defined way (for example, all TDs for a tenant, a
fleet, or a physical site). This specification does not impose any
restrictions on what Thing Descriptions can be contained in a Thing Description Group.

### 2.4. Thing Model Group

A Thing Model Group is a container for Thing Models that are related to each
other in some application-defined way (for example, all TMs published by a
single vendor, or all TMs for a product family). This specification does not
impose any restrictions on what Thing Models can be contained in a Thing
Model Group.

### 2.5. WoT Processing Group

A **WoT Processing Group** contains `processingprofiles` and
`processingconfigurations` as ordinary document Resources. It is a discovery
and distribution boundary only. It does not make a descriptor trusted, select
a configuration implicitly, merge configurations, or authorize retrieval or
execution.

## 3. WoT Registry Model

The authoritative xRegistry extension model of the WoT Registry resides in
the [model.json](model.json) file. Its `modelversion` versions *this* model
and moves independently of the xRegistry Core specification version that
appears in a Registry's `specversion`. This revision defines model version
`0.3` in all six Group and Resource declarations. The
`modelcompatiblewith` URI is a model claim, not runtime enforcement;
consumers MUST inspect the advertised model version before relying on the
attributes and profile defined here.

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

  "thingdescriptiongroups": {                      # ThingDescriptionGroups collection
    "KEY": {                                       # thingdescriptiongroupid
      "thingdescriptiongroupid": "<STRING>",                  # xRegistry core attributes
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

      "thingdescriptions": {                       # ThingDescriptions collection
        "KEY": {                                   # thingdescriptionid
          "thingdescriptionid": "<STRING>",                   # xRegistry core attributes
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
          "contenttype": "<STRING>", ?             # application/td+json; see 4.2
          "format": "<STRING>",                    # MUST be "JSON-LD/1.1"
          "wotid": "<STRING>",                     # the document's authored 'id'
          "derivedfrom": [ "<STRING>" * ], ?       # wotids of the TMs it derives from
          "license": "<STRING>", ?                 # provenance metadata
          "publisher": "<STRING>", ?
          "standardsbody": "<STRING>", ?
          "canonicalurl": "<URL>", ?
          "maturity": "<STRING>", ?
          "documentdigest": { "algorithm": "sha-256", "scope": "decoded-file-octets",
            "value": "<64 lowercase hexadecimal digits>" }, ?
          "documentbase": "<URI>", ?
          "resolutionpolicy": { "url": "<URL>", "digest": "<SHA-256>", "profile": "<URI>" }, ?
          "resolutionrecords": [ { "url": "<URL>", "digest": "<SHA-256>",
            "profile": "<URI>", "rootdigest": "<SHA-256>", "purpose": "<STRING>" } * ], ?
          "formatvalidated": <BOOLEAN>, ?
          "formatvalidatedreason": "<STRING>", ?
          "compatibilityvalidated": <BOOLEAN>, ?
          "compatibilityvalidatedreason": "<STRING>", ?

          "thingdescriptionurl": "<URL>", ?
          "thingdescription": <ANY>, ?                        # the WoT-TD JSON-LD document
          "thingdescriptionbase64": "<STRING>", ?
          #  End of default Version's attributes

          "metaurl": "<URL>",
          "meta": { ... }, ?

          "versions": { ... }, ?
          "versionsurl": "<URL>",
          "versionscount": <UINTEGER>
        } *
      }, ?
      "thingdescriptionsurl": "<URL>",
      "thingdescriptionscount": <UINTEGER>
    } *
  }, ?
  "thingdescriptiongroupsurl": "<URL>",
  "thingdescriptiongroupscount": <UINTEGER>,

  "thingmodelgroups": {                            # ThingModelGroups collection
    "KEY": {                                       # thingmodelgroupid
      "thingmodelgroupid": "<STRING>",                        # xRegistry core attributes
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

      "thingmodels": {                             # ThingModels collection
        "KEY": {                                   # thingmodelid
          "thingmodelid": "<STRING>",                         # xRegistry core attributes
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
          "contenttype": "<STRING>", ?             # application/tm+json; see 4.4
          "format": "<STRING>",                    # MUST be "JSON-LD/1.1"
          "wotid": "<STRING>",                     # the document's authored 'id'
          "derivedfrom": [ "<STRING>" * ], ?       # wotids of the TMs it extends
          "license": "<STRING>", ?                 # provenance metadata
          "publisher": "<STRING>", ?
          "standardsbody": "<STRING>", ?
          "canonicalurl": "<URL>", ?
          "maturity": "<STRING>", ?
          "documentdigest": { "algorithm": "sha-256", "scope": "decoded-file-octets",
            "value": "<64 lowercase hexadecimal digits>" }, ?
          "documentbase": "<URI>", ?
          "resolutionpolicy": { "url": "<URL>", "digest": "<SHA-256>", "profile": "<URI>" }, ?
          "resolutionrecords": [ { "url": "<URL>", "digest": "<SHA-256>",
            "profile": "<URI>", "rootdigest": "<SHA-256>", "purpose": "<STRING>" } * ], ?
          "formatvalidated": <BOOLEAN>, ?
          "formatvalidatedreason": "<STRING>", ?
          "compatibilityvalidated": <BOOLEAN>, ?
          "compatibilityvalidatedreason": "<STRING>", ?

          "thingmodelurl": "<URL>", ?
          "thingmodel": <ANY>, ?                              # the WoT-TM JSON-LD document
          "thingmodelbase64": "<STRING>", ?
          #  End of default Version's attributes

          "metaurl": "<URL>",
          "meta": { ... }, ?

          "versions": { ... }, ?
          "versionsurl": "<URL>",
          "versionscount": <UINTEGER>
        } *
      }, ?
      "thingmodelsurl": "<URL>",
      "thingmodelscount": <UINTEGER>
    } *
  }, ?
  "thingmodelgroupsurl": "<URL>",
  "thingmodelgroupscount": <UINTEGER>,

  "wotprocessinggroups": {                       # WoT processing documents
    "KEY": {
      "wotprocessinggroupid": "<STRING>",        # xRegistry core attributes
      "processingprofiles": {
        "KEY": {
          "stableprofileuri": "<URI>",           # equals descriptor document id
          "format": "JSON",
          "processingprofile": <ANY>             # JSON descriptor document
        } *
      }, ?
      "processingconfigurations": {
        "KEY": {
          "configurationuri": "<URI>",           # equals configuration document id
          "format": "JSON",
          "processingconfiguration": <ANY>       # JSON configuration document
        } *
      }, ?
    } *
  }, ?
  "wotprocessinggroupsurl": "<URL>",
  "wotprocessinggroupscount": <UINTEGER>
}
```

## 4. WoT Registry

The WoT Registry is a metadata store for organizing Thing Descriptions, Thing
Models, processing profile descriptors, reusable configurations, and their
Versions; it is a document store.

Implementations of this specification MAY include additional extension
attributes, including the `*` attribute of type `any`.

Since the WoT Registry is an application of the
[xRegistry specification][xRegistry Core], all attributes for Groups,
Resources, and Resource Version objects are inherited from there.

### 4.1. Thing Description Groups

The Group Type (`<GROUP>`) name for Thing Descriptions is `thingdescriptiongroup` (singular).
The plural, used as the collection name, is `thingdescriptiongroups`. The Thing Description Group
does not have any specific extension attributes.

A Thing Description Group is a collection of Thing Descriptions that are related to each
other in some application-defined way. A Thing Description Group does not impose any
restrictions on the contained Thing Descriptions.

Every Thing Description (i.e. the `thingdescription` Resource) MUST reside inside a Thing
Description Group.

Example:

```yaml
{
  # xRegistry top-level attributes excluded for brevity

  "thingdescriptiongroups": {
    "fabrikam.factory-floor-01": {
      "thingdescriptiongroupid": "fabrikam.factory-floor-01",
      # other xRegistry Group-level attributes excluded for brevity

      "thingdescriptionsurl": "https://example.com/thingdescriptiongroups/fabrikam.factory-floor-01/thingdescriptions",
      "thingdescriptionscount": 12
    }
  },
  "thingdescriptiongroupsurl": "https://example.com/thingdescriptiongroups",
  "thingdescriptiongroupscount": 1
}
```

### 4.2. Thing Description Resources

The Resource Type (`<RESOURCE>`) inside of Thing Description Groups is named `thingdescription`. The
plural, used as the collection name, is `thingdescriptions`. Any single `thingdescription` is a
container for one or more `versions`, each of which holds the concrete
WoT-TD 1.1 JSON-LD document.

The `format` attribute of a `thingdescription` Resource Version MUST be
`"JSON-LD/1.1"`. [model.json](model.json) declares the `format` enumeration
as `strict`, so a registry rejects any other value rather than merely
discouraging it.

The `contenttype` of a `thingdescription` document MUST be
`application/td+json` per [WoT-TD 1.1 §12.1][WoT-TD-1.1], or another media
type the deployment has explicitly registered for WoT documents. `contenttype`
is client-supplied, and the document view serves the stored bytes under it
([Section 1.4](#14-document-store)), so a registry MUST NOT serve a stored
document under a client-supplied media type that causes it to be interpreted
as active content — for example `text/html`, `image/svg+xml` or
`application/xhtml+xml`. A registry MUST either reject such a write or serve
the document under the media type this section requires. Because a Version's
document-view URL is intended to be dereferenced directly by WoT tooling, a
registry SHOULD additionally return `X-Content-Type-Options: nosniff` for
documents it did not itself author, or serve them from an origin separate
from any registry user interface. See [Section 7](#7-security).

The `wotid` attribute is REQUIRED and holds the document's authored WoT
identifier, which is distinct from the `thingdescriptionid`. See
[Section 5.1](#51-wot-identifiers-and-registry-ids). The OPTIONAL
`derivedfrom` attribute lists the `wotid`s of the Thing Models this Thing
Description extends or composes; it is a producer-supplied index rather than
an authority over the document's own references, as
[Section 5.2](#52-preserving-customer-documents) describes.

If a TD is a recognized unresolved processing plan, validation of its syntax
or plan profile is not validation of the ordinary resolved result. A registry
or processor MUST keep those validation targets distinct. It MUST NOT report
the authored plan as an ordinary resolved TD solely because a separately
generated result passed TD validation.

All Versions of a single Thing Description Resource MUST adhere to the semantic rules of
the Thing Description's [`compatibility`][xRegistry compatibility] attribute, if specified.

Implementations of this specification SHOULD use the xRegistry default
algorithm for generating new `versionid` values. Which Version is the default
Version — the one served when no Version is named — MUST be determined by the
xRegistry Core rules, including the Resource's `defaultversionsticky`
setting, which a deployment MAY use to pin the default to a Version other
than the newest. This specification does not redefine either. A default is a selection rule,
not an immutable reference: a consumer that needs repeatable processing MUST
record the selected Version and retain or verify the exact bytes. Resource
`epoch` or metadata-epoch alone does not prove that an existing child
Version's document bytes are unchanged. See
[Version IDs][xRegistry version-ids] for more information.

### 4.3. Thing Model Groups

The Group Type name for Thing Models is `thingmodelgroup` (singular), with
collection name `thingmodelgroups`. The Thing Model Group does not have any
specific extension attributes.

A Thing Model Group is a collection of Thing Models related in some
application-defined way (typically by vendor or product family).

Every Thing Model (i.e. the `thingmodel` Resource) MUST reside inside a Thing
Model Group.

### 4.4. Thing Model Resources

The Resource Type inside of Thing Model Groups is named `thingmodel`, with
collection name `thingmodels`. Any single `thingmodel` is a container for one
or more `versions`, each of which holds the concrete WoT-TM 1.1 JSON-LD
document.

The `format` attribute of a `thingmodel` Resource Version MUST be
`"JSON-LD/1.1"`, enforced by the same `strict` enumeration used for
`thingdescription`. The `contenttype` MUST be `application/tm+json` per
[WoT-TM 1.1 §12.2][WoT-TM-1.1], or another media type the deployment has
explicitly registered for WoT documents, and the same constraint on serving
stored bytes as active content applies as in
[Section 4.2](#42-thing-description-resources).

The same `compatibility`, `versionid`, and
[`ancestorid`][xRegistry ancestorid] rules described for `thingdescription`
Resources apply to `thingmodel` Resources.

The `wotid` attribute is REQUIRED on a `thingmodel` and holds the document's
authored WoT identifier, which is distinct from the `thingmodelid`. Where a
Thing Model extends another via a `tm:extends` link relation, or references
one via `tm:ref`, the referenced Thing Models' `wotid`s SHOULD be listed in
`derivedfrom`.

As with Thing Descriptions, a `thingmodel` MAY be stored even when a
referenced model is unavailable. Storage or structural validation of a
recognized unresolved processing plan does not establish that its contents
have been resolved or validated as an ordinary result. A processing profile
that accepts such plans MUST distinguish plan-aware validation from
validation of the completed TD/TM result and MUST identify which
representation was validated. The plan remains a `thingmodel` with the
ordinary `application/tm+json` media type; this specification does not
introduce a third document Resource kind.

### 4.5. Formats

Both Thing Descriptions and Thing Models are serialized as JSON-LD 1.1
documents, so both use the
[core specification's `format`](../../../core/spec.md#format-attribute) identifier
`JSON-LD/1.1`. The distinction between the two document classes is carried by
the Resource type (`thingdescriptions` versus `thingmodels`) and by the
`contenttype` attribute, not by `format`.

#### 4.5.1. WoT Thing Description

- Format identifier: `JSON-LD/1.1`
- `contenttype`: `application/td+json`
- Document: a JSON-LD 1.1 document conformant with
  [W3C WoT Thing Description 1.1][WoT-TD-1.1].
- The document's `@context` MUST include
  `https://www.w3.org/2022/wot/td/v1.1`.
- A URI-reference pointing to a TD MAY use a JSON-Pointer
  ([RFC 6901](https://www.rfc-editor.org/rfc/rfc6901)) fragment to deep-link
  into a particular property, action, or event affordance, e.g.
  `…/thingdescriptions/lamp-42#/properties/status`. A resolver MUST select and
  verify the document before evaluating such a fragment; absence or invalidity
  of the selected fragment is an error and MUST NOT trigger selection of a
  different Version.

#### 4.5.2. WoT Thing Model

- Format identifier: `JSON-LD/1.1`
- `contenttype`: `application/tm+json`
- Document: a JSON-LD 1.1 document conformant with
  [W3C WoT Thing Model 1.1][WoT-TM-1.1].
- The document's `@context` MUST include
  `https://www.w3.org/2022/wot/td/v1.1` and the document's top-level
  `@type` MUST include `tm:ThingModel`.
- Deep-linking via JSON-Pointer fragments is permitted, as for TDs. A resolver
  MUST select and verify the document before evaluating a fragment and MUST
  fail if that fragment is absent; it MUST NOT retry against another Version.

### 4.6. Provenance and Selection Metadata

A registry serves tools and autonomous agents that choose among documents
describing similar Things. That choice needs explicit metadata rather than
inference from a title or naming convention. Both `thingdescription` and
`thingmodel` Resources therefore carry
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

These attributes are **advisory and unverified**. The Resource writer asserts
the document's origin and maturity. This specification defines no way for a
registry to verify a `publisher` or `standardsbody` claim, and a registry MUST
NOT be assumed to have verified one. A Consumer MUST NOT treat these values as
authenticated provenance. The preference order above is only a tie-break
among documents the Consumer already trusts by Group, writer identity, or an
out-of-band signature; it MUST NOT establish trust in a document from an
untrusted writer. One `wotid` MAY match several Resources, as described in
[Section 5.3](#53-lookup), so a Consumer might need to choose among documents
from different parties. See also
[Section 7](#7-security).

These attributes are also not part of a document's semantic identity. A
registry MUST NOT treat two documents as the same document because their
provenance attributes agree, nor as different documents because they differ:
identity is `wotid` alone
([Section 5.1](#51-wot-identifiers-and-registry-ids)).

They are Version attributes, carried on each Version alongside the document
they describe, as `format` and `wotid` are. This specification defines no
special update semantics for them; they are written and updated exactly as any
other Version attribute is, under the xRegistry Core rules.

The WoT Resource model defines four OPTIONAL Version attributes for deployments
that exchange document integrity and resolution evidence:

| Attribute | Definition |
|---|---|
| `documentdigest` | When supplied by a conforming digest-publication implementation, the server-computed digest of the complete stored file octets after HTTP transfer/content decoding and before parsing, BOM removal, or JSON-LD processing. `algorithm` is `sha-256`, `scope` is `decoded-file-octets`, and `value` is 64 lowercase hexadecimal digits. |
| `documentbase` | An absolute URI identifying the original location from which imported document bytes were obtained. It is a document-loader starting location only when an authorized resolver profile uses it. It MUST NOT override authored TD `base`, JSON-LD `@base`, or applicable context-loading rules. `canonicalurl` remains advisory provenance and is not an implicit base. |
| `resolutionpolicy` | A suggested policy locator, full SHA-256 digest, and profile identifier. It does not authorize retrieval, selection, or activation. |
| `resolutionrecords` | Zero or more suggested immutable, digest-pinned resolution records, each bound to its root document digest and profile. Multiple records can describe different approved uses of the same document. Array order does not imply priority or a default. |

The policy and record application formats defined by this draft are described
in the [local schemas](schemas/README.md). Their profile identifier is
`https://xregistry.io/workingdrafts/models/wot/profiles/reference-resolution/0.2`.
A registry MAY host the files using an existing artifact store; this model
does not introduce another TD/TM Resource kind, media type, Core attribute, or
HTTP endpoint.

WoT document artifacts retrieved through this xRegistry adapter use the
`file` representation and `decoded-file-octets` digest scope. A record from
another adapter MAY include `native-metadata` only when its
`representationProfile` explicitly defines the complete frozen semantic
representation, its lossless field mapping, and the exact bytes/canonical
encoding covered by the digest. That digest MUST NOT be described as a hash of
unavailable source-file bytes. The xRegistry WoT profile does not define or
claim a native-metadata adapter.

A registry implementing the digest-publication capability MUST compute or
verify `documentdigest` from the bytes it actually stores and update it in the
same atomic operation as any byte change. It MUST NOT accept a producer's
claimed digest as a server-computed value. If it cannot maintain that
association, it MUST omit the attribute and MUST NOT claim the capability.
The digest is not `matchversions`: it MAY differ between Versions and is not
an identity attribute. `readonly` prevents a client from setting the
server-controlled attribute; it does not prevent Core-authorized updates to
the Version or promise archival retention.

An implementation claiming a reproducible-publication capability MUST
positively advertise that support through a trusted, negotiated
domain-profile mechanism or deployment configuration. Accepting or echoing
unknown extension fields is not capability evidence. Such an implementation
MUST honor its declared retention term, refuse writes that would violate it,
and state the effect of explicit revocation. Where it cannot prevent pruning
or deletion for the declared term, it MUST NOT claim that commitment.

An administrator MAY import a referenced policy into a protected local
deployment store as an immutable revision after validating and authorizing its
exact bytes. Editing a working file or attaching a policy in registry metadata
does not import, approve, or activate it. The authoritative policy is the
deployment host's protected durable state, not the registry attachment. A
consumer replaying a record MUST use the approved retained policy and inputs.
If REQUIRED bytes are missing, changed, corrupt, or unauthorized, it MUST
fail rather than resolve today's default or choose another attachment.

### 4.7. Processing Profile and Configuration Resources

The WoT model adds `wotprocessinggroups`, which contains the document
Resource collections `processingprofiles` and `processingconfigurations`.
Both are ordinary Core document Resources with `format: "JSON"`. Their
`stableprofileuri` and `configurationuri` attributes MUST equal the
corresponding document's `id` and use Core `matchversions: true`. These
attributes identify the logical document; they do not identify a Core Version,
freeze its bytes, or establish trust in its producer or consumer. The document
view MUST use `application/json`.

A processing profile descriptor MUST conform to
[processing-profile.schema.json](schemas/processing-profile.schema.json). It
contains `formatVersion`, `id`, an opaque `version`, `definition`,
`operations`, `roles`, and `representationProfiles`. The `definition` member
identifies the exact reviewed processing definition by URI, opaque version
label, and SHA-256 digest of the complete file octets. This owner-local
definition is self-contained. The initial profile defines the
`resolve-definition` operation for a complete property definition, the
`tm:ref` role, and the `decoded-file-octets` representation profile. Its fixed
context value and bounded operation rules appear in
[the processing-profile definition schema](schemas/processing-profile-definition.schema.json)
and the corresponding sample. The profile does not load remote contexts or
schemas. A context change or override, unsupported schema dependency,
operation, role, or representation profile MUST fail explicitly. A caller
MUST NOT claim an empty dependency closure when a REQUIRED interpretation
input is missing.

The descriptor's declared operations, roles, and representation profiles are
claims, not an implementation capability. A consumer MUST independently
require an installed, explicitly supported profile identity and the exact
definition version and digest. It MUST NOT execute code, load a plugin, expand
its authority, or treat the descriptor as trusted merely because the document
was accepted, discovered, or echoed by a registry. Profile and configuration
document schemas use this draft's local JSON Schema 2020-12 definitions and
do not import a W3C proposal or OPC UA model.

A reusable processing configuration MUST conform to
[processing-configuration.schema.json](schemas/processing-configuration.schema.json).
It contains `formatVersion`, `id`, an opaque `version`, the exact supported
`profile` descriptor binding (`id`, `version`, and full document digest),
`rules`, and finite positive `limits` named `maxDepth`, `maxBytes`, and
`maxMilliseconds`. Each rule is independent of a root or deployment target.
It specifies one role, expected document kind and authored identity, a closed
authority scope, and either an exact Core Version ID or the `registry-default`
selection. `expectedDigest` MAY add a content pin. A scope for the xRegistry
WoT adapter names exactly one adapter URI
(`https://xregistry.io/workingdrafts/models/wot/adapters/xregistry/1`),
registry origin, `thingmodelgroups` Group id, and `thingmodels` collection; it
MAY also pin an exact Resource id. That pin does not permit a search fallback.
When deriving the existing root-bound policy format, the adapter URI maps to
the established `resolver.adapter` value `xregistry-wot`. The portable
configuration does not change that policy schema or its attachment shape.

Before acquiring a REQUIRED reference, a consumer MUST find exactly one
configuration rule matching its role, expected kind, and logical identity.
Rules have no precedence, wildcard, first-match, fallback, or implicit
inheritance. The consumer MUST fail on zero or multiple matching rules, an
unsupported adapter, an out-of-scope source, or a mismatched authored pin. It
MUST NOT search another Group, collection, origin, or provider to recover.
The caller MUST explicitly select the configuration as `own` or `shared`,
and the consumer MUST use only that configuration. It MUST NOT merge, overlay,
extend, or fall back to another configuration. A different configuration
requires a separate invocation.

The `version` labels in descriptors and configurations are opaque and MUST
match exactly. This draft defines no SemVer ranges or compatible-version
constraints. For invocation and replay, consumers MUST bind each selected
descriptor and configuration to its exact registry Version ID, where
applicable, full document-file digest, document URL, and interpretation base.
They MUST verify these bindings against the retained bytes. If the bytes
change while a Core Version ID remains the same, integrity validation MUST
fail. A stable URI, `matchversions`, sticky default, registry epoch, or
read-only metadata flag does not make the document immutable or guarantee
retention.

The consumer MUST enforce the configuration's finite limits alongside its
own ceilings, checking them before retrieval or descent and after decoding. A
missing, zero, or unbounded limit MUST NOT grant permission. An empty `rules`
array is valid when the requested closure has no external reference that
requires provider selection. Any external acquisition without exactly one
matching rule MUST fail. Reusable configurations MUST NOT contain credentials,
deployment targets, approvals, activation commands, root documents, operation
requests, or occurrence pointers.

These Resources make profiles and configurations discoverable and distributable.
A registry need not become a composition, validation, authorization, or
activation engine. The OPTIONAL `resolutionpolicy` and `resolutionrecords`
attachments remain separate and root-bound on TD/TM Versions; this revision
does not change their schemas or semantics. Attaching a policy to a reusable
configuration does not grant authority. When a deployment requires a policy,
the deployment host MUST import it as an immutable revision into protected
state. A `resolutionpolicy` attachment remains advisory until an authorized
local import and approval.

## 5. Identity and Resolution

### 5.1. WoT Identifiers and Registry Ids

xRegistry assigns each entity an id — `thingdescriptionid` or
`thingmodelid` for a Resource — and an [`xid`][xRegistry Core], the stable
registry path formed from those ids. An entity id is constrained to
[RFC 3986][RFC3986] `unreserved` characters plus `:` and `@`, starting with a
letter, a digit or `_`, at most 128 characters long, and unique
case-insensitively within its parent. A WoT identifier is the value of a TD's
or TM's `id` member: a URI, most often a URN such as `urn:fabrikam:lamp:42`,
but equally a URL such as `https://fabrikam.example/things/lamp-42`.

The two identify the same document but use different grammars:
`https://fabrikam.example/things/lamp-42` is not a valid entity id, so it is
also not a valid `xid` component, and an `xid` is not what a Thing author
writes. Where an authored identifier does satisfy the id grammar a client MAY
use it as the Resource id, but a registry cannot rely on that.

This specification keeps the identifiers separate and defines no mapping
between them:

> A `thingdescription`'s `wotid` is its document's identity in the WoT
> identifier space ([Section 2.2.3](#223-wot-identifier)). Its
> `thingdescriptionid` is the Resource's id *within this registry* and is
> chosen by the client that creates the Resource, subject to the xRegistry
> Core id rules and to whatever further naming constraints the deployment
> imposes. Neither is derived from the other. The same applies to a
> `thingmodel`'s `wotid` and `thingmodelid`.

A client chooses a Resource id when creating it, just as it chooses a Group
id: it can put the id in the request path, include it in the request body, or
omit it and let the registry assign one under the Core rules. This document
does not prescribe a mapping. A Consumer holding a WoT identifier finds the
Resource by querying its first-party `wotid` attribute
([Section 5.3](#53-lookup)) rather than by reconstructing a path. A deployment
MAY derive Resource ids from `wotid` values by a local convention —
the [OpenUSD Artifact Registry][OpenUSD Draft] working draft defines one such
construction — but no convention is mandated by this specification, and a
Consumer MUST NOT assume that an id it did not assign was produced by one.

A `wotid` MUST NOT encode a revision of the document it names. Appending a
suffix such as `:v2` when editing the document changes its identifier, so the
registry cannot identify revisions of the same logical Thing. It also breaks
[`ancestorid`][xRegistry ancestorid] lineage and forces every consumer holding
a reference to update it. The xRegistry `versionid` identifies the registry
Version. A document's own WoT `version` member, when present, identifies its
WoT version. Neither belongs in `wotid`.

This is a prohibition on *versioning an identifier*, not on the characters
that can appear in one. A vendor who deliberately publishes a second,
incompatible Thing alongside the first is naming a different Thing, and the
identifier they author for it — which might well carry a `v2` token — is that
Thing's own stable `wotid`; see
[Section 5.1.1](#511-breaking-changes-and-successor-identifiers).

When a document is revised:

- Its `wotid` is unchanged.
- Its `thingdescriptionid` (or `thingmodelid`) is unchanged, because it is the
  same Resource.
- A new Version is created under the same Resource.

A `wotid` is REQUIRED. Populate it as follows:

- Where the document carries an `id` member, `wotid` MUST equal it verbatim.
  A registry that parses the stored document MUST reject a write whose
  `wotid` differs from `id`; it MUST NOT store two identities for one
  document. A registry that does not parse the document cannot detect the
  mismatch and MUST NOT resolve it by rewriting either value, because
  [Section 5.2](#52-preserving-customer-documents) forbids editing the
  document.
- Where the document carries no `id` member — which
  [WoT-TD 1.1][WoT-TD-1.1] permits for TDs served from a fixed URL, and which
  is common for TMs — the Producer MUST supply a `wotid` at write time, and
  that supplied value is thereafter the document's identity in this registry.
- A registry MUST reject a write that supplies neither an `id` member nor a
  `wotid`, rather than inventing one, because an invented identifier is not
  stable across registries.

[Decision 4](decisions.md#4-wotid-is-a-required-indexed-first-party-attribute)
leaves a derivation for the second case undecided.

#### 5.1.1. Breaking Changes and Successor Identifiers

[Section 1.3](#13-versioning) requires a breaking change that violates the
Resource's [`compatibility`][xRegistry compatibility] policy to use a new
Resource, not a new Version. The `wotid` remains the same across a Resource's
Versions. A successor therefore needs a new authored `wotid` and a new
Resource; it is a **new logical Thing**.

- The successor's `wotid` is a new authored identifier, distinct from the
  predecessor's. It is that Thing's permanent identity and is itself never
  revised thereafter.
- The successor is a distinct Resource with its own `thingdescriptionid` (or
  `thingmodelid`), so predecessor and successor occupy distinct paths and are
  independently retrievable.
- A new successor does not by itself retain the predecessor's Versions.
  Retention, pruning, and deletion remain governed by Core unless the
  deployment advertises and honors the reproducible-publication commitment in
  [Sections 1.4](#14-document-store) and
  [4.6](#46-provenance-and-selection-metadata).
- The predecessor SHOULD set [`deprecated`][xRegistry deprecated], naming the
  successor Resource, so a consumer holding the old identifier can find the
  new one without a side channel.

To group related identifiers into a compatibility family, a deployment MAY
adopt a naming convention such as a major-version token —
`urn:fabrikam:lamp:v2`, or `https://fabrikam.example/tm/lamp/v2`. This is a
domain/deployment convention, not a WoT identity rule, and does not establish
that an interface change creates a different physical Thing. The registry
MUST preserve the document's authored `id`; it MUST NOT rewrite it to fit a
family convention. A `versionid` identifies a registry Version and is not a
minor-version label for that policy.

If a deployment uses such a convention, the token is chosen by the author as
part of the stable authored identifier. Section 5.1 forbids a registry or
Producer from mutating an identifier that a document already carries.

For example, if a lamp's control interface changes incompatibly:

| | Predecessor | Successor |
|---|---|---|
| `wotid` | `urn:fabrikam:lamp` | `urn:fabrikam:lamp:v2` |
| `thingmodelid` | `urn.fabrikam.lamp` | `urn.fabrikam.lamp.v2` |
| Versions | registry policy applies | registry policy applies independently |
| `deprecated` | set, naming the successor | absent |

### 5.2. Preserving Customer Documents

Registries store Thing Models and Thing Descriptions authored by vendors,
standards bodies, or toolchains. Other artifacts can reference those documents
without the registry's knowledge. The registry stores each document as
authored.

- A registry MUST store the WoT document byte-for-byte as supplied, apart from
  transformations the client explicitly requested.
- A registry MUST NOT rewrite the document's `id` member, its `links[].href`
  values, its `tm:extends` or `tm:ref` targets, or any other identifier
  internal to the document, into registry-specific identifiers.
- A retrieval of a stored Version through the document view MUST return the
  exact bytes supplied, as the xRegistry Core document view already requires.
  Re-serializing the document — reordering members, re-indenting, or
  normalizing its JSON-LD — is not permitted.
- Where a digest-publication profile is implemented, it MUST compute the
  digest over the complete file octets after HTTP transfer framing and any
  `Content-Encoding` are decoded, but before parsing, BOM removal, or
  canonicalization. Equivalent JSON parsed from differently encoded or
  serialized files therefore has different file digests. An HTTP
  `Content-Digest` or `Repr-Digest` MUST NOT be copied into `documentdigest`
  unless its defined byte scope is exactly the scope above.

Rewriting can break references from artifacts outside the registry and make
the registry's copy misrepresent the published document. A TM's
`tm:extends` target resolves in the WoT identifier space; changing it makes
the target invisible to other WoT tools. If two registries rewrite the same
document differently, they assign different identities to identical bytes.

The registry's `thingdescriptionid` or `thingmodelid` and resulting `xid`
remain outside the document. The WoT document's own identifiers travel beside
it, unchanged, in `wotid` and `derivedfrom`. This separation lets the document
round-trip without changing either identifier space.

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
/thingmodelgroups/<thingmodelgroupid>/thingmodels/<thingmodelid>
```

**By `wotid`.** Otherwise — the usual case, since WoT documents reference one
another by authored identifier rather than by registry path — it queries on
the `wotid` attribute:

```
GET /thingmodels?filter=wotid=urn:fabrikam:lamp
```

An implementation SHOULD serve this query in time that does not grow with the
size of the collection — in practice by indexing `wotid` on both
`thingdescriptions` and `thingmodels`. Resolution is on the critical path of
composing a TD from its Thing Models, so a linear scan per reference does not
scale.

A `wotid` SHOULD be unique within a Group, so that a Group-scoped query for
one identifies a single Resource. Across Groups a `wotid` MAY repeat — the
same vendor TM legitimately appears in two tenants' Groups — so a
registry-wide query MAY match more than one Resource, and a caller that needs
exactly one narrows the query by naming the Group. A registry-wide match MUST
return every matching Resource rather than an arbitrary one of them, and
[Section 4.6](#46-provenance-and-selection-metadata) governs how a Consumer
chooses among them.

Version selection is a second, separate step, and is never encoded in the
*identifier*. It is, of course, encoded in the URL — that is what the
`versions` collection is for:

| Intent | Document view | Metadata view |
|---|---|---|
| Default Version | `<resource-entity-path>` | `<resource-entity-path>$details` |
| Exact Version | `<resource-entity-path>/versions/<versionid>` | `<resource-entity-path>/versions/<versionid>$details` |
| Enumerate Versions | `<resource-entity-path>/versions` | `<resource-entity-path>/versions` |

`<resource-entity-path>` is the Resource path without a `$details` suffix.
Construct the Version path by appending `/versions/<versionid>` to that path;
only then select the metadata or document view. In the xRegistry HTTP Binding,
the `$details` suffix is appended directly to the Resource or Version ID for
the metadata view. Do not append `/versions/...` to a `self` URL that already
contains `$details`. See [Section 1.4](#14-document-store).

The Default Version is determined by the xRegistry Core rules and the
Resource's `defaultversionsticky` setting; this specification does not
redefine either. A registry MUST serve the default Version when no Version is
named. A Consumer MUST NOT infer the default by sorting `versionid`s, or
assume the ID is an integer or matches the document's own version label.

What a caller SHOULD NOT do is fold the two into one opaque string. A caller
that carries an identifier and a version through a transport — for example in
message headers — SHOULD carry them as two separate values, such as a
`wotid` header and a `versionid` header, rather than a single compound token
like `urn:fabrikam:lamp@3` that every recipient has to take apart. The
identifier stays a WoT identifier, and the version stays a `versionid` the
recipient can put straight into a URL.

A consumer implementing this draft's resolution profile MUST scope lookup to
an authorized registry origin, Group, Resource type, and exact authored
`wotid` association. A registry-wide query that returns more than one
candidate is ambiguous for this purpose; publisher, maturity, standards-body,
or canonical-URL attributes MUST NOT be used to choose a candidate or grant
trust. A consumer MUST distinguish no match, ambiguity, authorization
failure, invalid/corrupt content, and a mismatch with a REQUIRED kind,
identity, or digest. A failed explicit selection MUST NOT be hidden by trying
another Resource, alias, or provider.

The OPTIONAL resolution policy and record use the domain-owned schemas in
`workingdrafts/models/wot/schemas/`. A policy binds the exact root file digest,
the authored occurrence (including its source JSON Pointer), expected TD/TM
kind and identity, authorized registry/Group scope, and either `exact` with a
Version ID or `registry-default`. `registry-default` means the Version selected
by the Resource's actual Core default when the record is captured; it does not mean the
largest ID, highest WoT version label, or currently active projection.

When processing references, a consumer MUST traverse only roles defined by
the applicable WoT vocabulary or profile. Interaction forms and navigational
Thing links are not automatically document imports. The consumer MUST resolve
and verify the selected document before applying a fragment, check authored
identity and digest constraints, and retain the exact bytes and
interpretation inputs used. These inputs include REQUIRED JSON-LD contexts,
schemas, catalogs, base information, and semantic processing configuration.
The consumer MUST preserve the authored document, reference strings, and
occurrence pointers. A changed `documentbase` or registry location MUST NOT
override the authored TD `base` or JSON-LD context semantics.

For each moving or default selection, a resolution record MUST capture the
exact selected Version ID and its retained artifact. Repeated default
references to the same scoped Resource in one operation MUST reuse that
selection. Different explicit Versions MAY coexist when the consuming
semantics permit them. A Resource or registry `epoch` cannot replace the
selected Version's digest: Core does not require a Resource meta epoch to
change when an existing Version's document changes.

Record capture and replay are lifecycle steps, not separate xRegistry or
processing-profile operations. A consumer MAY consult a moving default when
capturing a record. To claim replayability, it MUST retain the verified input
closure. During replay, it MUST use the approved record and exact retained
inputs without checking the current default. Replay MUST fail if an input is
absent, corrupt, unauthorized, or inconsistent with the approved digest; it
MUST NOT select a new default. An upgrade requires a new record and explicit
approval. This lifecycle applies only when a consumer offers replayable
processing; one-time resolution against the current Core default does not
require a record. Retained inputs reproduce the captured selections but do
not prove that defaults across multiple Resources were observed at the same
instant. The `lock` member in the processing-evidence schema binds an
existing resolution record; it does not define an xRegistry lock or a separate
operation.

A record digest, semantic-core digest, and document-file digest cover
different data. The full-record digest covers the exact record file. An OPTIONAL
semantic-core digest covers the domain profile's RFC 8785 JSON
Canonicalization Scheme representation, with defined ordering for artifacts,
edges, and transformations. For this profile, an artifact descriptor contains
its digest, media type, document URL, interpretation base, context bindings,
and scoped registry identity. Omit absent OPTIONAL values. Sort descriptors
by the unsigned UTF-8 octets of their JCS representation; reject contradictory
duplicates and coalesce exact duplicates. Assign artifact IDs `a0`, `a1`, and
so on in that order. Identify the root separately; it need not be `a0`.
Sort edges by `(from, sourcePointer, role, to, fragment)` and reject
conflicting duplicates. Record an explicit position for semantically ordered
inputs. Order transformations topologically; break independent ties using
their canonical profile, configuration, and input descriptors. Reject cycles
in recursive imports. Keep registry observations and retrieval timestamps
outside `core`.

Neither digest is the xRegistry `documentdigest`, and neither authenticates a
publisher or authorizes activation. A replayed result MUST be validated
separately from the authored unresolved plan. A plan-validation flag alone
MUST NOT be reported as validation of the resolved output.

### 5.4. Processing Invocation and Evidence

A processing invocation MUST identify one supported profile, one selected
configuration, one root document, and one request. The initial profile
supports only `resolve-definition`. Its `pointer` is an absolute RFC 6901 JSON
Pointer into the original root document and selects a complete property
definition; it is not rebased to a detached subdocument. Unsupported
operations, parts, reference roles, profile identities, or definition
versions fail. This operation is not a general Thing Model, JSON-LD, or schema
processor.

The `invocation` object contains exactly these semantic inputs:

```json
{
  "profile": {
    "id": "https://example.com/profiles/tm-property-reference",
    "version": "1",
    "digest": "sha-256:<descriptor-file-digest>",
    "documentUrl": "https://example.com/profiles/tm-property-reference.json",
    "interpretationBase": "https://example.com/profiles/"
  },
  "configuration": {
    "id": "https://example.com/configurations/plant",
    "version": "r1",
    "digest": "sha-256:<configuration-file-digest>",
    "documentUrl": "https://example.com/configurations/plant.json",
    "interpretationBase": "https://example.com/configurations/",
    "source": "shared"
  },
  "root": {
    "identity": "urn:example:plant:controller",
    "digestScope": "decoded-file-octets",
    "digest": "sha-256:<root-file-digest>",
    "documentUrl": "https://plant.example/controller.tm.json",
    "interpretationBase": "https://plant.example/"
  },
  "request": {
    "operation": "resolve-definition",
    "pointer": "/properties/temperature"
  }
}
```

For registry documents, the profile, configuration, and root bindings also
record the exact registry origin, Group and Resource identity, and selected
Core Version ID. The configuration binding records `source` as `own` or
`shared` to show the caller's selection; it does not indicate authorization.
For local files, record the same byte digest, document location, and
interpretation base without adding registry coordinates. `stableprofileuri`
and `configurationuri` identify descriptors logically, but do not replace
their document digest or location.

`invocationDigest` is SHA-256 over the UTF-8 bytes of the RFC 8785 JCS
serialization of exactly `{profile, configuration, root, request}`. It omits
`effectivePolicyDigest`, output, local-reference evidence, policy and lock
bindings, and retained-artifact descriptors. In the `retained-resolution`
branch, `invocation` also contains `effectivePolicyDigest`, which binds the
exact derived root-bound policy bytes. This member is not part of
`invocationDigest`. The resolution record's semantic configuration MUST bind the
invocation digest and exact retained profile, configuration, root, and
request inputs without creating a digest cycle.

Before replay, the consumer MUST receive independently caller-pinned
`expectedInvocationDigest` and `expectedEvidenceDigest` trust inputs.
`expectedInvocationDigest` MUST match both the JCS digest of the invocation
preimage and the serialized `invocationDigest`. `expectedEvidenceDigest` MUST
match the JCS digest of the complete serialized `evidence` object, not the
archive manifest. Neither value is a profile, configuration, or evidence
member. A consumer MUST NOT take either expected value from the untrusted
evidence under review. Pinning only the invocation leaves selected-source,
policy/lock, local-reference, and result evidence unbound.

The consumer MUST retain the exact bytes of each profile descriptor,
reviewed profile definition, selected configuration, root, and every
interpretation or imported document REQUIRED by the operation. A separate
`retainedArtifacts` archive manifest lists artifact descriptors and relative
archive-entry names. It contains no credentials, embedded authentication
material, or host filesystem paths. An `archivePath` MUST NOT be absolute,
contain a drive prefix, use backslashes, or traverse above the archive root.
On replay, the consumer MUST verify each retained file's digest and
interpretation binding. A missing, changed, or unauthorized REQUIRED artifact
MUST cause failure. The consumer MUST NOT switch to the current default,
another configuration, or a newly discovered descriptor.

For each same-document `tm:ref`, evidence records a `localReferences` entry
with the original containing artifact descriptor, original-root
`sourcePointer`, and local `targetPointer`. Keep this mapping separate from
external provider-selection edges; it requires neither a registry lookup nor
a provider rule. The consumer MUST verify that both pointers resolve in the
retained containing document and that reconstruction produces the same
mapping. Identify each nested occurrence by its containing artifact and
pointer. Equal pointers in different documents or interpretation bases refer
to different occurrences. This profile resolves only references in its
declared closure and MUST NOT rewrite authored reference strings or occurrence
pointers.

The evidence uses the disjoint branches defined by
[processing-evidence.schema.json](schemas/processing-evidence.schema.json):

* **`local-definition`** applies only when the requested operation has no
  verified external definition imports. An empty closure does not mean that a
  REQUIRED context or interpretation input was ignored. This branch requires
  `invocation`, `invocationDigest`, `localReferences`, and `output`. It MUST
  omit `effectivePolicyDigest`, `policy`, and `lock`. Set
  `output.digestScope` to `json-jcs`; `output.digest` is SHA-256 of the exact
  JCS UTF-8 representation of `output.value`. Replay re-derives the requested
  definition from the retained root and verifies the output digest and local
  occurrence mappings.
* **`retained-resolution`** applies when the requested closure has external
  imports. It requires `effectivePolicyDigest` and bindings to the existing
  root-bound `resolutionpolicy` and `resolutionrecords` record. Retain their
  exact bytes and digest bindings, along with all imported and interpretation
  inputs. Derive the policy from the selected configuration for this root and
  request; it MUST conform to the existing policy schema. The record MUST
  conform to the existing resolution-record schema, and its semantic
  configuration MUST bind the invocation digest and selected portable inputs.
  Neither schema is weakened. Do not create a policy or lock for the
  no-import branch.

The initial profile definition contains the complete fixed inline context
mapping used to recognize `tm:ref`. It does not load a remote JSON-LD context.
If a REQUIRED context is absent, changed, remotely overridden, or outside
that definition, processing MUST fail with `missing-interpretation-input` or
an equivalent diagnostic. An empty caller-supplied import list does not prove
that the closure is empty. The profile MUST inspect the retained root and
supported reference syntax, and fail on any unknown REQUIRED dependency.

For a supported `tm:ref`, the authored value identifies a complete property
definition in the same retained document or an authorized external Thing
Model. It MAY include a JSON Pointer fragment. The profile selects the
complete definition and applies the referencing property's remaining
siblings as an RFC 7396 Merge Patch. It preserves the source document,
reference string, and original source and target pointers. It does not apply
other Thing Model operators or treat links, forms, schema references, or
arbitrary JSON-LD terms as imports.

A consumer MUST use one frozen acquisition/default-choice cache per
invocation for both rule derivation and transformation. Before resolving an
external occurrence, it MUST find exactly one configuration rule matching
the occurrence's role, expected kind, and authored identity, and verify that
the source is within that rule's authority scope. An exact selection uses the
named Core Version ID. `registry-default` observes the Core default once and
records the exact Version ID and bytes. Repeated references to the same
scoped Resource reuse that choice. The consumer MUST NOT make a second moving
lookup during transformation or replay. It MUST detect cycles using the exact
containing artifact and property pointer, not only a URL or pointer. It MUST
enforce the selected configuration's positive finite limits alongside its
own ceilings.

These operations produce definition data only. They do not validate a
complete WoT-TM, execute actions, resolve TD interaction forms, authorize an
endpoint, or activate a deployment. Registry metadata and reusable
configurations support discovery; they do not grant authority. Deployment
policy remains an authorized immutable revision in deployment-host protected
state. Deployment binding, approval, target selection, and activation are
outside this WoT registry model.

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
      "href": "https://example.com/thingmodelgroups/Fabrikam.Lighting/thingmodels/urn.fabrikam.lamp",
      "type": "application/tm+json"
    }
  ]
}
```

A Thing Description and the Thing Model it derives from are two distinct
Resources with independent lifecycles, so this relationship is expressed
through the TD document's `links` member rather than through the xRegistry
[`xref`][xRegistry xref] attribute, which exists to surface the *same*
Resource under more than one Group. The `rel: "type"` association does not,
by itself, instruct a consumer to fetch or merge the Thing Model; processing
that follows such references requires an explicitly supported profile.

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

For authorization, the `thingdescriptiongroup` and `thingmodelgroup` concepts provide a
natural authorization boundary, where users can be granted access to specific
groups, and therefore to the Things or Thing Models contained within those
groups. The `thingdescription` and `thingmodel` Resources themselves can be used to
further restrict access to specific Versions, allowing for fine-grained
access control.

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
  same applies to the `thingdescriptionurl` and `thingmodelurl` attributes,
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
  [Section 4.2](#42-thing-description-resources) constrains which media types
  a registry will serve it under. Format validation does not help here: a
  document can be valid JSON-LD 1.1 and still execute as script if served as
  `text/html`.

- **Policy and record attachments are not authority.** A registry attachment
  is a suggestion and MUST NOT expand a consumer's retrieval scope or grant
  permission to activate a result. An administrator MUST explicitly authorize
  and import the exact policy bytes into a protected durable deployment-host
  store before use. Policy import, record approval, and target activation are
  separate actions. Current authorization and revocation remain applicable
  to retained records.

- **Integrity is not authentication.** A matching document, policy, or record
  digest proves only that the bytes match the recorded digest. It does not
  authenticate the publisher, resolver, or deployment approver. An
  implementation MUST use its authorized local approval or signature
  mechanism to protect records used for execution. Portable records MUST NOT
  contain credentials, session tokens, or local filesystem paths.

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
