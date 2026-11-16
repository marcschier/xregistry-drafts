# ACF Descriptor Profiles - Working Draft

<!-- words: ACF acfconversation acfexecution conversationref -->
<!-- words: resolutioncontextref actorbindings messagebindings configurationref -->
<!-- words: traceref traceid observationid observerref processingref activityid -->
<!-- words: actorref observationids supersedes sent received accepted processed -->
<!-- words: entityid entitytype describedby baseflow XID XIDs RFC -->
<!-- words: AttributeDefinitions matchversions jsonschema -->
<!-- words: allOf conversationgroups deduplicate dereferenceable -->
<!-- words: descriptorgroups descriptorVersion namespace NormalizedHop RawHop -->
<!-- words: TraceRecord unversioned workingdrafts -->

## Abstract

This working draft defines Conversation and Execution Evidence profiles of
the [Descriptor Registry][Descriptor]. A Conversation Descriptor selects a
versioned Actor Conversation Flow (ACF) contract and retained resolution
context. An Execution Evidence Descriptor selects that configuration and
a stable trace snapshot. Typed values in ACF's existing extension maps bind
message observations and processing attempts to concrete CloudEvents.

These profiles are proposed integrations of existing ACF and xRegistry
models. The [source and rights note](README.md#sources-and-publication-scope)
identifies the ACF review revision used and the draft's publication status.

## Table of Contents

- [Abstract](#abstract)
- [1. Overview](#1-overview)
- [2. Notations and Terminology](#2-notations-and-terminology)
- [3. Model and Representations](#3-model-and-representations)
- [4. Conversation Descriptor](#4-conversation-descriptor)
  - [4.1. `acfconversation` Attribute](#41-acfconversation-attribute)
  - [4.2. `conversationref` and `resolutioncontextref` Attributes](#42-conversationref-and-resolutioncontextref-attributes)
  - [4.3. `actorbindings` Attribute](#43-actorbindings-attribute)
  - [4.4. `messagebindings` Attribute](#44-messagebindings-attribute)
- [5. Execution Evidence Descriptor](#5-execution-evidence-descriptor)
  - [5.1. `entityid` and `entitytype` Attributes](#51-entityid-and-entitytype-attributes)
  - [5.2. `acfexecution` Attribute](#52-acfexecution-attribute)
  - [5.3. `supersedes` Attribute](#53-supersedes-attribute)
- [6. Trace Provenance Binding](#6-trace-provenance-binding)
  - [6.1. Extension Locations](#61-extension-locations)
  - [6.2. Observation Fields](#62-observation-fields)
  - [6.3. Processing Attempts](#63-processing-attempts)
  - [6.4. Replay and Conflicts](#64-replay-and-conflicts)
- [7. Publication and Resolution](#7-publication-and-resolution)
- [8. Failures, Replay and Conformance](#8-failures-replay-and-conformance)
- [9. Security](#9-security)
- [10. Complete Integration Example](#10-complete-integration-example)
- [11. References](#11-references)

## 1. Overview

A conversation in ACF specifies permitted interactions among actor roles.
Its Flow document declares the actors, scopes, terminals, steps, conditions
and control flow. In the Descriptor Registry, an Actor Descriptor identifies
a concrete participant independently of its ACF roles. A Processing
Descriptor supplies the complete shared inputs needed to interpret one
message under an agreed processing profile.

A Conversation Descriptor selects the ACF Flow and binds its roles and
message-bearing steps to Actor and Processing Descriptors. Cross-resource
links within the Flow are XIDs resolved against separately supplied
xRegistry context.

An Execution Evidence Descriptor describes one execution and selects a
retained ACF Trace snapshot. ACF TraceRecord objects report observations of
message exchanges. This profile uses ACF's extension maps to describe local
action attempts, processing results and event derivation.

The CloudEvents `describedby` extension selects the event's current
Processing Descriptor. An application can convey the
Execution Evidence Descriptor URL out of band or through an independently
agreed transport or application contract. Looking up an exact event identity
can yield several observations, attempts and executions. An evidence query
API and a W3C PROV mapping are deferred.

## 2. Notations and Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in
[RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and
[RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) when, and only when, they
appear in all capitals.

| Term | Meaning |
| --- | --- |
| Configuration | One exact Conversation Descriptor Version and its selected retained inputs. |
| Flow | The ACF document of an xRegistry conversation Resource Version. |
| Role | An actor ID declared in the resolved ACF Flow. |
| Participant | A concrete entity identified by an Actor Descriptor's `entityid` and bound to an ACF role. |
| Trace | An ACF collection of message observations within a Flow. |
| Step | An ACF operation declared within a Flow's scope. |
| Processing attempt | A reported execution of one ACF action step, represented by this profile's trace extension. |
| Covered role | A role participating in a profiled observation or attempt, including the record's modeled sender and receiver when present. |
| Snapshot | A published, stable representation retained for an agreed replay or audit period. |
| Event identity | The pair of decoded CloudEvents `source` and `id` values. |
| Observation identity | Execution `entityid` plus `observationid`. |
| Attempt identity | Execution `entityid` plus `activityid`. |
| Trace identity | Exact trace document Version/snapshot URL plus local `traceid`. |
| Profile validator | A Consumer or publication service explicitly applying these profile rules. |

JSON examples are concrete JSON. Common Core response bookkeeping is omitted
from the create inputs in the example. All string comparisons in this draft
are exact and case-sensitive, without URI normalization. Omission of an
OPTIONAL binding array means no entries; an empty array is equivalent.
A present profile field MUST NOT be `null`. There are no inferred selector
or outcome defaults.

Bindings are arrays with explicit ACF identifier members. ACF role and step
IDs can contain uppercase letters; Core Reference
names follow Core map-key syntax. A Consumer MUST preserve both exactly and
MUST NOT lowercase, truncate or otherwise rewrite an ACF identifier to make
it a Reference name. The identifier member selects the bound role or step.

## 3. Model and Representations

Both profiles use the existing metadata-only Descriptor Resource and its
Versions. They add the `acfconversation` and `acfexecution` Version attributes
defined below. A deployment merges the Core AttributeDefinitions map in the
[attribute fragment](attributes.json) into the generic Descriptor Resource's
`attributes` map. The selected profile establishes each attribute's presence.

The deployment agreement MUST select which profile applies. A Consumer MUST
NOT infer a profile from Group names or Reference names. Under this draft,
a Descriptor MUST NOT apply both profiles to the same Version. Actor and
Processing Descriptors remain governed by their own selected profiles.

The URI prefix `https://xregistry.io/workingdrafts/profiles/acf/` is the
proposed vocabulary namespace of this working draft. This section defines
each class URI's meaning; a Reference's `url` selects its representation.
Class URIs MUST be used in full, without fragments:

| Class suffix under that prefix | Representation and obligations |
| --- | --- |
| `classes/conversation` | JSON document view of one explicit ACF conversation Version, with resource `format` equal to `ACF/1.0`. It MUST contain static configuration, not `traces` or `runtime`. |
| `classes/resolution-context` | Stable JSON Registry export, with selected Versions and retained documents sufficient to resolve every used ACF XID and inherited definition deterministically. |
| `classes/actor-descriptor` | JSON metadata of an exact Actor Descriptor Version; `entityid` and `entitytype` are REQUIRED by the generic Actor specialization. |
| `classes/processing-descriptor` | JSON metadata of an exact Processing Descriptor Version, complete independently under its selected processing profile. |
| `classes/conversation-descriptor` | JSON metadata of an exact Descriptor Version conforming to Section 4. |
| `classes/trace` | JSON document view of a stable ACF Flow containing `traces`, including the selected Trace. An explicit conversation Version URL or a distinct immutable snapshot URL is REQUIRED. |
| `classes/evidence-descriptor` | JSON metadata of an exact Descriptor Version conforming to Section 5, used only for explicit predecessor links. |

All referenced JSON representations use media type `application/json`.
Every Reference inherits the generic absolute, fragment-free URL rule.
Descriptor classes select metadata URLs; ACF conversation and trace classes
select document URLs. Consumers MUST use URLs unchanged, not add or remove
`$details`, append XIDs, or guess Version paths. Selecting a Version requires
checking the returned Version identity. External snapshots require an
explicit retention agreement.

The [structural schema](profile.schema.json) defines `conversation`,
`execution`, `observation` and `attempts`. The first two constrain a
Descriptor metadata object; the latter two constrain extension values.
For Descriptor validation, implementations combine the applicable definition
with the generic `descriptorVersion` schema using `allOf` or equivalent
independent validation. Structural validation checks field shapes. Profile
validation also checks Reference classes, participant identity, inherited
resolution and dependency completeness. Trust and ACF conformance require
the checks described in Sections 8 and 9.

## 4. Conversation Descriptor

### 4.1. `acfconversation` Attribute

- Type: Object
- Description: Static conversation selection and OPTIONAL bindings for this
  Descriptor Version.

- Constraints:
  - REQUIRED for the Conversation Descriptor profile.
  - Only the members defined in this section are permitted.
  - The object MUST contain `conversationref` and `resolutioncontextref`.
  - `entityid` and `entitytype` are OPTIONAL. If present, generic Descriptor
    identity rules apply; a conversation role MUST NOT be used as the
    identity of a concrete actor.

- Examples:
  - `{"conversationref":"flow","resolutioncontextref":"context"}`

### 4.2. `conversationref` and `resolutioncontextref` Attributes

- Type: String
- Description: Exact Reference names in this Conversation Descriptor.

- Constraints:
  - Both are REQUIRED and non-empty.
  - `conversationref` MUST select class `classes/conversation` from Section 3.
  - `resolutioncontextref` MUST select class `classes/resolution-context`.
  - The retained export MUST select the same conversation Version and
    document as `conversationref`. Any inconsistent duplicate is invalid.
  - The Consumer MUST resolve inherited structure before validating role
    or step bindings. Unresolved or ambiguous inheritance is not a match.

- Examples:
  - `"conversationref": "flow"`

The export MUST retain each selected default Version for an unversioned
Resource XID, each explicitly addressed Version, all used base flows and
message definitions, and the documents those definitions need. A Consumer
MUST resolve an XID by its exact Registry hierarchy and selected Version.
It MUST NOT use substring matching, concatenate the XID to a Reference URL,
replace internal XIDs with absolute URLs or JSON Pointers, or fall back to
the current live Registry. A versioned XID MUST select that Version.

Where ACF's inherited augmentation or override rules permit more than one
interpretation for a collision, this profile accepts only an unambiguous
resolved graph. The Publisher MUST remove the ambiguity or publish a
separately resolved static conversation Version. Cycles, conflicting IDs
and exhausted resolution limits MUST be reported, not broken arbitrarily.
This draft does not define a second inheritance algorithm.

### 4.3. `actorbindings` Attribute

- Type: Array of objects
- Description: Bindings from exact role IDs to configured REQUIRED actors.

- Constraints:
  - OPTIONAL; each entry MUST contain exactly `actor` and `actorref`.
  - `actor` MUST exactly identify a resolved ACF actor role. Its value
    MUST be unique within this array.
  - `actorref` MUST select a local `classes/actor-descriptor` Reference.
  - A present entry requires that exact Actor Descriptor Version in an
    execution. The actual participant's `entityid` MUST equal its `entityid`.
  - For a role omitted from configuration, the execution selects its actual
    participant under Section 5.
  - The role and the Actor Descriptor's `entityid` are distinct identities.

- Examples:
  - `[{"actor":"Worker","actorref":"worker"}]`

### 4.4. `messagebindings` Attribute

- Type: Array of objects
- Description: Bindings from exact message-bearing step IDs to Processing
  Descriptors for each step's single message interpretation.

- Constraints:
  - OPTIONAL; each entry MUST contain exactly `step` and `processingref`.
  - `step` MUST exactly identify a resolved step having exactly one
    message definition, such as a `flow` step. Its value MUST be unique
    within this array.
  - `processingref` MUST select a local
    `classes/processing-descriptor` Reference.
  - An action's input/output bindings and a method's request/response are
    not a single-message slot. Such steps MUST NOT appear in this array.
    Their message interpretations are explicit in Section 6 evidence.
  - A present binding fixes the exact Processing Descriptor Version for
    observations of that step. An omitted binding requires an explicit
    evidence-local selection when interpretation is recorded.
  - A Processing Descriptor MUST supply all inputs of its own processing
    profile locally. It MUST NOT inherit missing References or selectors
    from the Conversation Descriptor.

- Examples:
  - `[{"step":"RawHop","processingref":"raw"}]`

## 5. Execution Evidence Descriptor

### 5.1. `entityid` and `entitytype` Attributes

- Type: URI
- Description: Identity and type of the execution described by this evidence.

- Constraints:
  - Both are REQUIRED for this profile.
  - `entityid` MUST be an absolute, fragment-free globally scoped execution
    URI assigned by the Publisher. Local Trace IDs are insufficient.
  - `entitytype` MUST equal
    `https://xregistry.io/workingdrafts/profiles/acf/types/execution`.
  - Additional evidence Versions for the same execution MUST retain the
    same `entityid`, as REQUIRED by the base model's `matchversions`.
  - The execution's selected configuration MUST remain unchanged across
    these evidence Versions. A different configuration requires a new
    execution identity.

- Examples:
  - `"entityid": "urn:example:execution:normalize:42"`

### 5.2. `acfexecution` Attribute

- Type: Object
- Description: Configuration, trace selection and actual participant bindings
  for one retained execution snapshot.

- Constraints:
  - REQUIRED; only members defined in this section are permitted.
  - `configurationref`, `traceref` and `traceid` are REQUIRED non-empty strings.
  - `configurationref` MUST name a local `classes/conversation-descriptor`
    Reference to the exact configuration Version.
  - `traceref` MUST name a local `classes/trace` Reference.
  - `traceid` MUST exactly select one Trace's local `id` in that document.
    Missing or duplicate IDs are invalid.
  - The trace document MUST use `baseflow` to select the configuration's
    exact conversation Version in its retained context. Under this profile
    it MUST NOT locally override or augment actors, scopes or gates.
  - `actorbindings` is OPTIONAL for an execution with no covered roles.
    It is REQUIRED for every covered role. Each entry contains exactly
    `actor` (the exact role ID) and `actorref` (a local
    `classes/actor-descriptor` Reference name). `actor` values MUST be
    unique within the array.
  - Every actual binding MUST have exactly one corresponding Trace
    participant entry. That entry's `participant` MUST equal the selected
    Actor Descriptor's `entityid`, not its local Descriptor ID or role ID.
    Every Trace participant MUST have an actual binding.
  - If configuration fixes that role, the execution MUST reference the
    same Actor Descriptor Version URL. Otherwise it selects the actual
    participant independently.
  - One role MUST NOT change participant within a Trace. A participant
    change requires separate Traces and execution identities; a Publisher
    MAY link them through a separately agreed relationship, not overwrite
    a binding or reuse `supersedes` for a different execution.

- Examples:
  - `{"configurationref":"config","traceref":"trace","traceid":"Run42"}`

Every Reference name in `acfexecution`, a selected observation, or a selected
attempt resolves in the containing Execution Evidence Descriptor's map.
Names inside the configuration resolve in the configuration's own map.
Consumers MUST NOT search another map for an absent name. Different local
names can select the same exact URL.

### 5.3. `supersedes` Attribute

- Type: String
- Description: Local Reference name selecting the preceding evidence Version.

- Constraints:
  - OPTIONAL for the first snapshot; REQUIRED for each later snapshot of
    the same execution published under this profile.
  - The Reference MUST have class `classes/evidence-descriptor` and select
    the immediate preceding evidence Version of the same execution.
  - The chain MUST be finite and acyclic. The Publisher MUST serialize
    publication for one execution rather than create ambiguous successors.
  - A new snapshot MUST preserve carried-forward observations and attempts
    unchanged by identity. Additional or corrected evidence uses new
    identities. Corrections follow Section 6.4; original snapshots and
    replaced evidence MUST remain available through this chain.

- Examples:
  - `"supersedes": "previous"`

## 6. Trace Provenance Binding

### 6.1. Extension Locations

This draft defines two full extension keys:

| Location | Key under `https://xregistry.io/workingdrafts/profiles/acf/` | Value |
| --- | --- | --- |
| `TraceRecord.extensions` | `observation` | One typed observation object. |
| `Trace.extensions` | `attempts` | Array of typed local action attempts, possibly empty. |

The typed values occupy ACF's existing extension maps. Every record in the
selected ACF Trace MUST carry this observation extension. `attempts` is
OPTIONAL; omission represents an empty collection. ACF TraceRecord objects
carry message observations. A local action without a message MUST NOT be
fabricated as a TraceRecord.

### 6.2. Observation Fields

| Field | Presence and meaning |
| --- | --- |
| `observationid` | REQUIRED non-empty opaque string, unique per execution except identical replay. |
| `kind` | REQUIRED: `sent`, `received`, `accepted` or `processed`. |
| `observerref` | REQUIRED local Actor Descriptor Reference identifying who reports the fact. |
| `event` | REQUIRED object with exactly `source` and `id` strings. `id` is non-empty. |
| `processingref` | Conditional local Processing Descriptor Reference. REQUIRED for `processed`, or whenever the observer reports payload interpretation or uses a configured step binding. |
| `corrects` | OPTIONAL observation ID replaced from an earlier snapshot of the same execution; see Section 6.4. |

The enclosing record MUST supply `step` and RFC 3339 `timestamp`. `step`
MUST identify a resolved message-bearing step and the record's message
definition MUST agree with that step under ACF. For a step with multiple
message slots, the record MUST supply `message` and identify exactly one
slot; if several slots remain possible, the observation is invalid under
this profile. ACF's `TraceRecord.message` identifies a message definition by
its xRegistry XID.

The decoded `source` value MUST be a CloudEvents URI-reference; relative
values, including the empty URI-reference, retain their exact value. The
Consumer MUST NOT resolve them against a registry or trace URL, normalize
them, or compare encoded header spellings instead of decoded values.
`source` and `id` together identify the event.
Repeated transmission of the same event retains both values.

`observerref` MUST select an actual Actor Descriptor bound to a covered role
participating in that message slot. `sent` requires a sender role; `received`,
`accepted` and `processed` require a receiver role. For a message slot with
no such modeled role, these kinds are invalid under this profile. An
independent monitor's report needs a separately agreed evidence contract.

If a configured `messagebindings` entry exists, `processingref` MUST resolve
to that exact Processing Descriptor Version URL. Otherwise a present
`processingref` selects its own complete processing inputs. Consumers MUST
check compatibility with the message slot's retained definition and the
agreed processing profile, not infer it from event type strings.

| Kind | Reported fact |
| --- | --- |
| `sent` | The sender reports emission. |
| `received` | The receiver reports receipt. |
| `accepted` | The receiver reports accepting responsibility for work. Evidence of durable custody requires a separate agreement. |
| `processed` | The receiver reports completing the processing defined by the selected processing contract. |

Each reported fact requires its own observation. A business result requires
evidence of the corresponding modeled message or separately defined outcome
contract. Consumers evaluate observation assertions under the trust checks
in Section 9.

### 6.3. Processing Attempts

Each attempt has exactly these fields:

| Field | Presence and meaning |
| --- | --- |
| `activityid` | REQUIRED non-empty opaque attempt ID, unique per execution except identical replay. |
| `step` | REQUIRED resolved ACF `action` step ID. |
| `actorref` | REQUIRED local Actor Descriptor Reference for that action's actual role. |
| `inputs`, `outputs` | REQUIRED arrays of event uses; empty when none is reported. |
| `outcome` | REQUIRED: `succeeded`, `failed`, `partial` or `unknown`. |
| `corrects` | OPTIONAL attempt ID replaced from an earlier snapshot of the same execution; see Section 6.4. |

An event use contains exactly `event`, `processingref` and `observationids`.
`event` has the same exact identity shape as an observation.
`processingref` is REQUIRED and selects a complete, local Processing
Descriptor Reference. `observationids` is a non-empty array of distinct
observation IDs in this execution snapshot. All selected observations MUST
have that exact event identity and exact Processing Descriptor Version URL.
An input requires at least one `received`, `accepted` or `processed`
observation by the attempt actor. An output requires at least one `sent`
observation by that actor. Selecting another actor's observation alone is
insufficient. Unknown observation IDs are invalid, not external links.

`actorref` MUST identify the actual participant bound to the action's role.
Every event use MUST match an allowed input or output message binding of
that action, through its selected observations' message definitions,
terminals and actor roles. ACF actions have at most one input binding and
can have many output bindings. Several concrete input events MAY be listed
only when an explicitly agreed action contract permits several instances
through that one binding. Without such a contract, this profile permits
at most one input event per attempt.

One input to many outputs or many permitted concrete inputs to one output
expresses reported derivation only when the action contract permits it.
Conditions, state, multiplicity and control-flow constraints remain ACF's
and the action contract's responsibility. The provenance arrays MUST NOT
broaden the action or its interfaces.

| Outcome | Constraint |
| --- | --- |
| `succeeded` | The actor reports successful completion of this attempt under the action contract; every listed output has its emission observation. |
| `failed` | The actor reports failure with no emitted outputs; `outputs` MUST be empty. |
| `partial` | The actor reports failure or incomplete completion after some outputs were emitted; `outputs` MUST be non-empty and contain only evidenced emissions. |
| `unknown` | Completion is not established. Evidenced outputs MAY be listed, but MUST NOT be called successful completion. |

A failed attempt MUST NOT invent successful output events to fill an
expected interface. A retry MUST receive a new `activityid`, even if it
consumes the same event or retransmits an output with the same identity.
An additional observation of that retransmission has a new `observationid`.
Explicit event uses establish reported attempt links.

### 6.4. Replay and Conflicts

A Consumer MUST deduplicate repeated observation and attempt identities
within one execution, including when comparing successive snapshots.
An observation's content for this comparison is its entire enclosing
record, including extensions. An attempt's content is its entire object.
Equality compares decoded JSON structurally, ignoring object member order
but preserving array order and exact scalar values.

Identical repeats are one item. Different content under the same identity
is a conflicting replay and MUST invalidate the snapshot. A Consumer MUST
NOT silently choose the latest value. Sent and received observations of one
event have distinct observation identities.
IDs in different executions are independent even if their local strings
match. A Consumer MUST reject duplicate JSON object keys before validation.

A corrected snapshot MUST use the same execution identity and configuration,
new evidence identities and a new trace snapshot URL. A new replacement's
`corrects` MUST identify an observation or attempt, respectively, in the
preceding snapshot. Each replaced identity MUST have exactly one replacement
and MUST be absent from the corrected snapshot. Other preceding items MUST
be carried forward unchanged. A correction target cannot be its own
replacement or an identity of the other evidence kind. These conditions
prevent conflicting corrections and silent removal.

The Consumer MUST validate the predecessor chain and record which assertions
were replaced. Earlier snapshots retain their content and validity reports.
An attempt that used a replaced observation MUST
itself be replaced with a new attempt identity and corrected observation
links. The same applies to downstream replacements as needed to leave no
unresolved links. A missing predecessor makes correction checking incomplete.
Snapshot corrections revise evidence about an existing execution; retries
report new action attempts with new attempt IDs.

## 7. Publication and Resolution

The Publisher MUST agree a replay or audit period with Consumers and retain
all selected Descriptor Versions, the context export, every used inherited
definition and document, trace snapshots, and processing dependencies for
that period. The Publisher's retention policy enforces availability
throughout the agreed period.

Publication proceeds in dependency order:

1. Publish stable actor and complete Processing Descriptor Versions and
   their dependencies. Retain the ACF conversation and resolution export.
2. Resolve and validate the conversation against that export; publish the
   Conversation Descriptor Version only after its inputs are available.
3. Capture the ACF trace snapshot with typed observations and attempts.
   The snapshot can be finalized before the Evidence Descriptor URL is
   assigned.
4. Publish the Execution Evidence Descriptor Version referencing the
   configuration, stable trace snapshot and actual actors. Validate all
   correlations before reporting validated-conformant.

Further observations require a new trace snapshot URL and Evidence
Descriptor Version, retaining the original snapshot. The execution
`entityid` remains the same for additional or corrected evidence under
Section 5.3. Publishers MUST NOT turn a shared Processing or Conversation
Descriptor into an ever-growing evidence log. This order avoids circular
requirements for final trace and Evidence Descriptor URLs.

The Consumer MUST capture the selected Evidence Descriptor Version, resolve
its configuration and retained context, resolve inheritance, select the
Trace, validate actual participants, and then validate observations and
attempts. It MUST use each Descriptor's own Reference map. It MUST NOT
substitute a live default when a retained dependency is missing.

Ordinary retrieval and generic Descriptor bundle negotiation apply.
A bundle contains exactly the representations selected by the Descriptor's
direct References. The Consumer resolves transitive dependencies, including
processing schemas and inherited ACF Flows, through explicit References or
separate authorized retrieval.

## 8. Failures, Replay and Conformance

A profile validator MUST distinguish at least these results in its report:

| Result | Meaning |
| --- | --- |
| Validated-conformant | Structure, all selected dependencies and every applicable semantic rule in this profile were checked and satisfied. |
| Invalid | A checked rule was violated, such as a wrong class, participant mismatch, unknown role, unknown observation or conflicting replay. |
| Incomplete | A needed retained input is missing, denied, unavailable or exceeds a resolution limit. |
| Unsupported | A needed well-formed class, ACF construct, processing contract or extension interpretation cannot be evaluated by this validator. |

These labels describe validation results in a profile validator's report.
A validator MUST report the affected selector, Reference, step
or evidence identity and reason, subject to privacy policy. It MUST NOT
report validated-conformant while any needed check is incomplete or
unsupported. A known violation remains invalid even if other checks are
incomplete; reports SHOULD preserve all independently established findings.

Schema acceptance alone is only structural acceptance. A Core server that
stores extension metadata need not implement this profile validator.
Recognized invalid profile content MUST NOT be advertised as validated.
Writes and retrieval failures use the governing Core and HTTP error rules.

Profile conformance and execution outcome are separate results. Valid
evidence can report `failed`, `partial` or `unknown` attempts. Profile
validation covers the structural and semantic rules defined here. Claims
about complete execution capture, ACF control-flow conformance, successful
delivery, business success or trustworthy observation origins each require
explicitly identified checks and evidence contracts.

## 9. Security

Consumers MUST authenticate origins and authorize access independently for
each selected representation. An Actor Descriptor's `entityid` or an
observation's `observerref` expresses an identity claim. Consumers MUST
apply an explicit trust policy before relying on an observation, participant
binding or outcome assertion.

Reference URLs, redirects and resolved addresses are untrusted retrieval
inputs. Consumers MUST enforce origin and scheme policy, including
protection against access to disallowed internal services. Credentials
MUST NOT be forwarded between origins without an explicit origin-specific
policy. Retained XIDs MUST NOT trigger fallback network discovery.

Implementations MUST bound bytes, Reference count, recursion and inherited
depth, document count, records, attempts, retrieval time and concurrency.
Cycles and limit exhaustion MUST produce explicit failures. Consumers MUST
also bound decompression and decoded payload size. Generic bundle access,
caching and completeness rules still apply.

Execution identifiers, participant identities, payloads and correlation
links can expose sensitive relationships. Publishers MUST apply access,
retention and disclosure policy to the metadata as well as the documents.
Redaction that removes needed evidence makes the affected check incomplete.
The validator MUST NOT retain a validated-conformant result for that check.
Publication stability and retention remain subject to applicable privacy
duties.

## 10. Complete Integration Example

[publication.json](examples/publication.json) is an offline example fixture
mapping exact illustrative retrieval URLs to original JSON representations.
Descriptor objects are Version create inputs.
The retained export omits Core response bookkeeping and includes selected
Versions and document-view links.

| Representation | Example URL suffix after `https://registry.example/` |
| --- | --- |
| Sender, Worker and Receiver Actor Descriptor Versions | `descriptorgroups/actors/descriptors/{sender,worker,receiver}/versions/1` |
| Raw and normalized Processing Descriptor Versions | `descriptorgroups/processing/descriptors/{raw,normalized}/versions/1` |
| Conversation Descriptor Version | `descriptorgroups/config/descriptors/normalize/versions/1` |
| Static ACF conversation document | `conversationgroups/demo/conversations/normalize/versions/1` |
| Retained Registry context | `snapshots/context/1` |
| Trace document snapshot | `snapshots/trace/42/1` |
| Execution Evidence Descriptor Version | `descriptorgroups/evidence/descriptors/run42/versions/1` |
| Raw and normalized payload schemas | `schemas/{raw,normalized}/1` |

The example ACF Flow declares three roles. Its `RawHop` step carries a raw
reading from Sender to Worker. Worker's `Normalize` action consumes one raw
reading and emits one normalized reading. `NormalizedHop` carries it to
Receiver. ACF actor IDs identify roles; Actor Descriptor `entityid` values
identify actual services.
Configuration fixes Worker; Sender and Receiver are unconstrained until
execution binds them.

The Processing Descriptors independently select their schemas using the
generic Schema Descriptor profile. Each supplies its complete set of
References. The example processing agreement defines raw as a numeric
`value` with constant `unit` equal to `C`; normalized uses numeric
`celsius`. Both are whole CloudEvents data objects. The action contract
accepts exactly one raw event and can emit one normalized event with
`celsius` equal to `value`; it permits retry after a failed attempt.

The retained context selects the exact conversation and two message
definitions as xRegistry metadata. All ACF message and `baseflow` links are
XIDs. The ACF trace document inherits the static conversation's structure.

The trace records emission and receipt of event `("sensor/7","r42")`.
The relative source retains its exact value. Attempt `try1` reports
failure with no output. Retry `try2` consumes the same event, reports
success and links emitted event `("urn:example:normalizer","n42")`.
`NormalizedHop` has sent and received observations. Evidence of receiver
processing or a business outcome would require its own observation under
the applicable processing or outcome contract.

The following adverse cases have distinct results:

| Change to the example | Result |
| --- | --- |
| Remove `conversationref`, set it to `null`, or use an array | Structural rejection. |
| Select a missing local Reference or wrong class | Invalid profile selection, even if a different Descriptor has that name. |
| Remove a retained base flow or schema | Incomplete; no live Registry fallback. |
| Change Worker's Trace participant to `Worker` | Invalid identity binding; the Actor Descriptor's `entityid` is REQUIRED. |
| Reuse `try1` for the successful retry | Invalid conflicting attempt identity. |
| Repeat an identical observation record | Deduplicate; not a new event or processing success. |
| Keep an observation ID but change its timestamp or event | Invalid conflicting replay. |
| Reference an absent observation ID from an attempt | Invalid attempt link. |
| Change `received` to an unknown kind | Invalid typed extension, not an inferred weaker observation. |
| Require an unimplemented action interpretation | Unsupported validation, not validated-conformant. |

## 11. References

- [Descriptor Registry][Descriptor], working draft.
- [xRegistry Core](../../../core/spec.md) and
  [Core model](../../../core/model.md).
- [ACF source revision and publication scope](README.md#sources-and-publication-scope).
- [CloudEvents Core](https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md).

[Descriptor]: ../../models/descriptor/spec.md
