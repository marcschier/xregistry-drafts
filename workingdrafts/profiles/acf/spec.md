# ACF Descriptor Profiles - Working Draft

<!-- words: ACF acfconversation acfexecution conversationref -->
<!-- words: resolutioncontextref actorbindings messagebindings deploymenturl -->
<!-- words: traceref traceid observationid processingref processingurl activityid -->
<!-- words: actorref actorurl actordescriptions observationids supersedes corrects -->
<!-- words: entityid entitytype describedby baseflow XID XIDs RFC executionid -->
<!-- words: AttributeDefinitions matchversions allOf conversationgroups -->
<!-- words: descriptorgroups descriptorVersion namespace NormalizedHop RawHop -->
<!-- words: TraceRecord unversioned workingdrafts deduplicate allowedparticipants -->
<!-- words: standalone -->

## Abstract

This working draft defines a Conversation Deployment profile of the
[Descriptor Registry][Descriptor] and a trace binding for Actor Conversation
Flow (ACF). A deployment selects a reusable ACF definition, retained
resolution context and participant bindings. Each execution records its
actual participants, message observations and processing attempts in an
ACF Trace. An OPTIONAL Execution Evidence Descriptor publishes a retained
trace snapshot for discovery and retrieval.

## Table of Contents

- [Abstract](#abstract)
- [1. Overview](#1-overview)
- [2. Notations and Terminology](#2-notations-and-terminology)
- [3. Model and Representations](#3-model-and-representations)
- [4. Conversation Deployment Descriptor](#4-conversation-deployment-descriptor)
  - [4.1. `acfconversation` Attribute](#41-acfconversation-attribute)
  - [4.2. `conversationref` and `resolutioncontextref` Attributes](#42-conversationref-and-resolutioncontextref-attributes)
  - [4.3. `actorbindings` Attribute](#43-actorbindings-attribute)
  - [4.4. `messagebindings` Attribute](#44-messagebindings-attribute)
- [5. Execution Evidence Descriptor](#5-execution-evidence-descriptor)
  - [5.1. `entityid` and `entitytype` Attributes](#51-entityid-and-entitytype-attributes)
  - [5.2. `acfexecution` Attribute](#52-acfexecution-attribute)
  - [5.3. `supersedes` Attribute](#53-supersedes-attribute)
- [6. Standalone Trace Binding](#6-standalone-trace-binding)
  - [6.1. Execution and Participants](#61-execution-and-participants)
  - [6.2. Observation Fields](#62-observation-fields)
  - [6.3. Processing Attempts](#63-processing-attempts)
  - [6.4. Snapshots, Replay and Corrections](#64-snapshots-replay-and-corrections)
- [7. Publication and Resolution](#7-publication-and-resolution)
- [8. Failures, Replay and Conformance](#8-failures-replay-and-conformance)
- [9. Security](#9-security)
- [10. Complete Integration Example](#10-complete-integration-example)
- [11. References](#11-references)

## 1. Overview

A conversation in ACF specifies permitted interactions among actor roles.
Its Flow document declares the actors, scopes, terminals, steps, conditions
and control flow. A Conversation Deployment Descriptor binds that reusable
definition to participants and any additional shared processing inputs.

One ACF definition can serve thousands of sensor or ATM deployments.
Each deployment references an exact conversation Version and can be reused
by many executions. The conversation remains independent of the deployments
that select it. Deployments contain bindings; ACF owns the interaction graph.
Cross-resource links within ACF remain XIDs resolved under retained context.

A participant is identified directly by a stable URI. An Actor Descriptor
can supply additional descriptions. A Processing Descriptor is useful when
an opportunity needs independently managed inputs beyond the message and
endpoint definitions already selected through ACF.

Each execution records its deployment Version and actual participants in
an ACF Trace. Typed values in ACF's extension maps associate message
observations and local processing attempts with concrete events. A trace
can be exchanged independently or published through an Execution Evidence
Descriptor. Both representations have the same execution meaning.

The CloudEvents `describedby` extension continues to select an event's
Processing Descriptor under the applicable event profile. Execution
correlation uses an out-of-band binding or an agreed transport or
application contract. An exact event identity can occur in several
observations, attempts and executions. An evidence query API and a
W3C PROV mapping are deferred.

## 2. Notations and Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in
[RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and
[RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) when, and only when, they
appear in all capitals.

| Term | Meaning |
| --- | --- |
| Flow | The ACF document of an xRegistry conversation Resource Version. |
| Deployment | One Conversation Deployment Descriptor Version and its selected retained inputs. |
| Role | An actor ID declared in the resolved ACF Flow. |
| Participant | A concrete entity identified by a stable absolute, fragment-free URI. |
| Trace | An ACF collection of message observations within a Flow. |
| Step | An ACF operation declared within a Flow's scope. |
| Processing attempt | A reported execution of one ACF action step, represented by this profile's trace extension. |
| Covered role | A role participating in a profiled observation or attempt, including the record's modeled sender and receiver when present. |
| Snapshot | A published, stable representation retained for an agreed replay or audit period. |
| Event identity | The pair of decoded CloudEvents `source` and `id` values. |
| Observation identity | Execution `executionid` plus `observationid`. |
| Attempt identity | Execution `executionid` plus `activityid`. |
| Trace identity | Exact trace document Version/snapshot URL plus local `traceid`. |
| Profile validator | A Consumer or publication service explicitly applying these profile rules. |

JSON examples are concrete JSON. Common Core response bookkeeping is omitted
from the create inputs in the examples. String comparisons are exact and
case-sensitive, without URI normalization. A present profile field MUST NOT
be `null`. Selectors and outcomes have no inferred defaults.

Bindings are arrays with explicit ACF identifier members. ACF role and step
IDs can contain uppercase letters and are independent of Core Reference
names. A Consumer MUST preserve those IDs exactly. Each binding array MUST
have unique role or step identifiers, as appropriate; array position has no
identity meaning.

## 3. Model and Representations

The deployment and OPTIONAL evidence profiles use the existing metadata-only
Descriptor Resource and its Versions. A deployment merges the Core
AttributeDefinitions map in the [attribute fragment](attributes.json) into
the generic Descriptor Resource's `attributes` map. The selected profile
establishes each attribute's presence.

The deployment agreement MUST select which profile applies. Consumers MUST
NOT infer a profile from Group names or Reference names. A Descriptor
Version MUST NOT apply both the deployment and evidence profiles.

The URI prefix `https://xregistry.io/workingdrafts/profiles/acf/` is the
proposed vocabulary namespace of this working draft. Class URIs MUST be
used in full, without fragments:

| Class suffix under that prefix | Representation and obligations |
| --- | --- |
| `classes/conversation` | JSON document view of one explicit static ACF conversation Version, with resource `format` equal to `ACF/1.0`. It MUST omit `traces` and `runtime`. |
| `classes/resolution-context` | Stable JSON Registry export with selected Versions and retained documents sufficient to resolve every used ACF XID and inherited definition deterministically. |
| `classes/actor-descriptor` | JSON metadata of an exact Actor Descriptor Version; generic Actor specialization identity rules apply. |
| `classes/processing-descriptor` | JSON metadata of an exact Processing Descriptor Version, complete independently under its selected processing profile. |
| `classes/deployment-descriptor` | JSON metadata of an exact Descriptor Version conforming to Section 4. |
| `classes/trace` | JSON document view of a stable ACF Flow containing the selected Trace. An explicit conversation Version URL or distinct immutable snapshot URL is REQUIRED. |
| `classes/evidence-descriptor` | JSON metadata of an exact Descriptor Version conforming to Section 5, for predecessor links. |

All referenced JSON representations use media type `application/json`.
Descriptor References inherit the generic absolute, fragment-free URL rule.
Descriptor classes select metadata URLs; conversation and trace classes
select document URLs. Consumers MUST use URLs unchanged and verify the
returned Version identity.

The trace extension's `deploymenturl`, `actorurl` and `processingurl` fields
are explicitly typed absolute, fragment-free metadata retrieval URLs.
They have the representation obligations of the corresponding Descriptor
classes above. They are independent of Descriptor-local Reference names.
The same applies to the predecessor trace document URL in Section 6.4.
ACF's own cross-resource fields retain their XID semantics.

The [structural schema](profile.schema.json) defines `deployment` and
`evidence` constraints for Descriptor metadata, plus `execution`,
`observation` and `attempts` constraints for trace extension values.
Descriptor validation combines the applicable definition with the generic
`descriptorVersion` schema using `allOf` or independent validation.
Structural acceptance also needs the semantic checks in this draft.

## 4. Conversation Deployment Descriptor

### 4.1. `acfconversation` Attribute

- Type: Object
- Description: The conversation, resolution context and reusable bindings
  for one deployment Version.

- Constraints:
  - REQUIRED for the Conversation Deployment profile.
  - The object MUST contain `conversationref`, `resolutioncontextref` and
    `actorbindings`. Only members defined in this section are permitted.
  - The deployment Version MUST remain stable after publication for use.
    A binding change requires a new Version.
  - `entityid` and `entitytype` are OPTIONAL. Generic Descriptor identity
    rules apply when present.

### 4.2. `conversationref` and `resolutioncontextref` Attributes

- Type: String
- Description: Exact Reference names in the deployment Descriptor.

- Constraints:
  - Both are REQUIRED and non-empty.
  - `conversationref` MUST select class `classes/conversation`.
  - `resolutioncontextref` MUST select class `classes/resolution-context`.
  - The retained export MUST select the same conversation Version and
    document as `conversationref`. Inconsistent duplicates are invalid.
  - The Consumer MUST resolve inherited structure before validating
    bindings. Resolution MUST produce one unambiguous graph.

The export MUST retain each selected default Version for an unversioned
Resource XID, each explicitly addressed Version, all used base flows and
message definitions, and the documents those definitions need. A Consumer
MUST resolve an XID by its exact Registry hierarchy and selected Version.
It MUST NOT use substring matching, concatenate the XID to a Reference URL,
replace internal XIDs with absolute URLs or JSON Pointers, or fall back to
the current live Registry. A versioned XID MUST select that Version.

ACF's inheritance rules govern augmentation and overrides. If a collision
has ambiguous interpretation, the Publisher MUST remove the ambiguity or
publish a separately resolved static conversation Version. Cycles,
conflicting IDs and exhausted resolution limits MUST be reported.

### 4.3. `actorbindings` Attribute

- Type: Array of objects
- Description: Fixed or runtime participant selection for every resolved
  ACF role.

- Constraints:
  - REQUIRED, with exactly one entry per resolved role and no unknown roles.
  - Every entry MUST contain `actor`, the exact role ID, and `mode`.
    `mode` MUST be `fixed` or `runtime`. Missing, `null` or unknown modes
    are invalid; omission of a role is invalid configuration.
  - For `fixed`, `participant` is REQUIRED and MUST be a stable absolute,
    fragment-free participant URI. The execution's actual participant
    MUST equal it. `allowedparticipants` MUST be absent.
  - For `runtime`, `participant` and `actorref` MUST be absent. The
    execution supplies its actual participant. `allowedparticipants`
    MAY contain a non-empty array of distinct participant URIs; when
    present, the actual participant MUST equal one of them.
  - An explicit `runtime` entry without `allowedparticipants` permits
    selection from the participant URI space. This is the deployment's
    explicit runtime agreement. Participant authentication and role
    authorization still follow Section 9.
  - A fixed entry MAY contain `actorref`, selecting a local
    `classes/actor-descriptor` Reference for additional descriptions.
    If supplied, its `entityid` MUST equal `participant` exactly.
    Its `entitytype` MUST satisfy the generic Actor specialization.
  - Entries MUST contain only the fields defined here.

For example, the following binds Worker and permits Sender selection at
execution time from a declared set:

```json
[
  {"actor":"Worker","mode":"fixed","participant":"urn:example:service:normalizer"},
  {"actor":"Sender","mode":"runtime","allowedparticipants":["urn:example:sensor:7","urn:example:sensor:8"]}
]
```

This is a binding-array fragment; a complete deployment includes every role.
Many deployment Descriptors can select the same ACF Version with different
fixed participants. Alternatively, an explicit runtime role can serve
several participants across executions. Neither form changes ACF's rule
that each role is bound at most once within one Trace.

### 4.4. `messagebindings` Attribute

- Type: Array of objects
- Description: OPTIONAL additional Processing Descriptor selections for
  message-bearing opportunities.

- Constraints:
  - OPTIONAL; omission or an empty array selects no additional inputs.
    Message, endpoint and schema facts selected by ACF remain authoritative.
  - Each entry MUST contain exactly `step` and `processingref`.
  - `step` MUST exactly identify a resolved step with one message
    definition, such as a `flow` step, and MUST be unique in the array.
  - `processingref` MUST select a local `classes/processing-descriptor`
    Reference. Several steps MAY select the same Reference.
  - An action's input/output bindings and a method's request/response
    MUST NOT appear as a single-message entry. Section 6 permits explicit
    selections for their individual observations.
  - A supplied selection MUST be validated, including Reference existence,
    class, Version and compatibility with the ACF message opportunity.
    It MUST NOT silently fall back to ACF-only interpretation if invalid.
  - Each selected Processing Descriptor MUST supply its own complete
    processing inputs. Consumers MUST NOT merge missing fields from the
    deployment or use it to override conflicting ACF definitions.

## 5. Execution Evidence Descriptor

The evidence profile publishes a stable standalone trace snapshot through
ordinary Descriptor discovery, retrieval and bundle operations.
An execution needs no Descriptor per message or processing attempt.

### 5.1. `entityid` and `entitytype` Attributes

- Type: URI
- Description: Identity and type of the execution described by the snapshot.

- Constraints:
  - Both are REQUIRED for this OPTIONAL profile.
  - `entityid` MUST exactly equal the selected trace's `executionid`.
  - `entitytype` MUST equal
    `https://xregistry.io/workingdrafts/profiles/acf/types/execution`.
  - All evidence Versions for one execution MUST retain that `entityid`
    and deployment selection.

### 5.2. `acfexecution` Attribute

- Type: Object
- Description: Selection of one standalone ACF Trace snapshot.

- Constraints:
  - REQUIRED for this profile; contains exactly `traceref`, `traceid`
    and OPTIONAL `supersedes`.
  - `traceref` MUST name a local `classes/trace` Reference.
  - `traceid` MUST exactly select one Trace's local `id` in that document.
  - The selected Trace MUST conform to Section 6. The wrapper supplies no
    participant, deployment or processing overrides.

### 5.3. `supersedes` Attribute

- Type: String
- Description: Local Reference name selecting the preceding evidence Version.

- Constraints:
  - OPTIONAL when first wrapping a trace, including a trace that already
    has standalone predecessors. REQUIRED for subsequent evidence Versions.
  - The Reference MUST have class `classes/evidence-descriptor` and select
    the immediate preceding evidence Version of the same execution.
  - Its selected snapshot MUST be an ancestor of the new snapshot under
    Section 6.4. Standalone snapshots MAY exist between wrapped snapshots.
  - Both chains MUST be finite and acyclic. The Publisher MUST serialize
    publication for one execution rather than create ambiguous successors.
  - A new evidence Version MUST select a new stable trace snapshot URL.
    Previously published evidence Versions and their inputs remain retained.

## 6. Standalone Trace Binding

### 6.1. Execution and Participants

This draft defines three keys under
`https://xregistry.io/workingdrafts/profiles/acf/`:

| Location | Key suffix | Value |
| --- | --- | --- |
| `Trace.extensions` | `execution` | Execution identity and exact deployment selection. |
| `TraceRecord.extensions` | `observation` | One typed message observation. |
| `Trace.extensions` | `attempts` | Array of local action attempts, possibly empty. |

The `execution` object has these fields:

| Field | Presence and meaning |
| --- | --- |
| `executionid` | REQUIRED globally scoped absolute, fragment-free execution URI assigned by the Publisher. |
| `deploymenturl` | REQUIRED exact Conversation Deployment Descriptor Version metadata URL. |
| `actordescriptions` | OPTIONAL array of runtime-role descriptions, each containing exactly `actor` and `actorurl`. |
| `previous` | Conditional predecessor snapshot selection, containing exactly absolute fragment-free document `url` and local `traceid`; Section 6.4 applies. |

The containing Flow MUST use `baseflow` to select the deployment's exact
conversation Version in its retained context. Under this binding, it MUST
NOT locally augment or override actors, scopes or gates. Every selected
TraceRecord MUST carry the observation extension. `attempts` is OPTIONAL;
omission represents an empty collection. ACF requires at least one message
record per Trace. Evidence consisting solely of local actions needs a
different representation; Consumers MUST NOT fabricate message records.

Actual participants use ACF's `Trace.participants` array. There MUST be
exactly one entry for every covered role, and MAY be entries for other
declared roles. Each `participant` MUST be a stable absolute, fragment-free
URI and satisfy its deployment binding. Unknown or duplicate roles are
invalid. A participant change requires separate Traces and execution
identities; it MUST NOT overwrite a fixed deployment or a Trace binding.

Runtime descriptions in `actordescriptions` are OPTIONAL. Each `actor` MUST
be a distinct runtime role with an actual participant in this Trace.
`actorurl` MUST retrieve an Actor Descriptor Version whose `entityid`
exactly equals that participant and whose `entitytype` satisfies the generic
Actor specialization. Fixed-role descriptions come from the deployment's
OPTIONAL `actorref`. Every supplied description MUST be validated.

Every mandatory trace field resolves from the trace, its selected deployment
and retained ACF context. Observation and attempt identities are scoped by
`executionid`. An Evidence Descriptor's Reference map has no role in trace
resolution. Wrapping a trace MUST preserve its meaning.

### 6.2. Observation Fields

| Field | Presence and meaning |
| --- | --- |
| `observationid` | REQUIRED non-empty opaque string, unique per execution except identical replay. |
| `kind` | REQUIRED: `sent`, `received`, `accepted` or `processed`. |
| `observer` | REQUIRED stable participant URI identifying who reports the fact. |
| `event` | REQUIRED object with exactly `source` and `id` strings; `id` is non-empty. |
| `processingurl` | OPTIONAL exact Processing Descriptor Version metadata URL for additional processing inputs. |
| `corrects` | OPTIONAL observation ID replaced from the preceding snapshot; Section 6.4 applies. |

Only these fields are permitted. The enclosing ACF record MUST supply
`step` and RFC 3339 `timestamp`. The resolved step MUST be message-bearing.
Its message definition and any supplied `message`, `from` or `to` MUST
agree under ACF. Where multiple message slots exist, `message` MUST select
exactly one; remaining ambiguity is invalid. `TraceRecord.message` remains
a message definition XID. The extension's `event` identifies an instance.

The decoded CloudEvents `source` is a URI-reference. Relative values,
including the empty URI-reference, retain their exact value. Consumers MUST
NOT resolve them against trace URLs or normalize them. `source` and `id`
together identify the event. Retransmission retains both values.
When recorded envelope metadata contains either value, it MUST agree with
the extension's decoded value.

`observer` MUST equal the actual participant bound to the message slot's
sender for `sent`, or receiver for the other kinds. A kind without its
modeled role is invalid. Independent monitors need their own evidence
agreement.

If the deployment binds this step to a Processing Descriptor, that exact
Version URL is the effective additional processing selection. A present
`processingurl` MUST equal it. Otherwise a present `processingurl` selects
the additional inputs itself. When both are absent, interpretation uses
the retained ACF message and endpoint definitions and their dependencies.
Every explicit selection MUST be validated independently and checked for
compatibility; failures MUST NOT silently trigger fallback or merging.
The observation and deployment are thereby consistent selections of one
Version.

| Kind | Reported fact |
| --- | --- |
| `sent` | The sender reports emission. |
| `received` | The receiver reports receipt. |
| `accepted` | The receiver reports accepting responsibility for work. Evidence of durable custody requires a separate agreement. |
| `processed` | The receiver reports completing the processing defined by the applicable message or action contract and any selected additional inputs. |

Each reported fact needs its own observation. A business result requires
evidence of the corresponding modeled message or separately defined
outcome contract. Consumers evaluate observation origins under Section 9.

### 6.3. Processing Attempts

Each attempt has these fields and no others:

| Field | Presence and meaning |
| --- | --- |
| `activityid` | REQUIRED non-empty opaque attempt ID, unique per execution except identical replay. |
| `step` | REQUIRED resolved ACF `action` step ID. |
| `participant` | REQUIRED actual participant URI for that action's role. |
| `inputs`, `outputs` | REQUIRED arrays of event uses; empty when none is reported. |
| `outcome` | REQUIRED: `succeeded`, `failed`, `partial` or `unknown`. |
| `corrects` | OPTIONAL attempt ID replaced from the preceding snapshot. |

An event use contains REQUIRED `event` and `observationids`, plus OPTIONAL
`processingurl`. Only those fields are permitted. `observationids` MUST
be a non-empty array of distinct observation IDs in this snapshot. All
selected observations MUST identify that exact event and the same effective
additional processing Version URL, or all have no additional selection.
Each event identity MUST occur at most once in each input or output array.
A supplied event-use `processingurl` MUST equal their effective URL.
Omission takes the observations' selection; it adds no processing fields.

An input requires at least one `received`, `accepted` or `processed`
observation by the attempt participant; an output requires at least one
`sent` observation by that participant. Unknown observation IDs are invalid.
Each event use MUST match an allowed input or output binding of the action,
including the message definition, terminal and actor role.

ACF actions have at most one input binding and can have many output bindings.
Several concrete input events MAY be listed only when the agreed action
contract permits several instances through that single binding. Otherwise
at most one input event is permitted per attempt. One-to-many or many-to-one
reported derivation remains subject to that contract. Provenance MUST NOT
broaden ACF conditions, control flow, multiplicity or action interfaces.

| Outcome | Constraint |
| --- | --- |
| `succeeded` | The participant reports successful completion of this attempt under the action contract; every listed output has its emission observation. |
| `failed` | The participant reports failure with no emitted outputs; `outputs` MUST be empty. |
| `partial` | The participant reports failure or incomplete completion after some outputs were emitted; `outputs` MUST be non-empty and contain only evidenced emissions. |
| `unknown` | Completion is not established. Evidenced outputs MAY be listed, but MUST NOT be called successful completion. |

A failed attempt MUST NOT invent successful outputs. A retry MUST receive
a new `activityid`, even when consuming or retransmitting the same event.
An additional observation of retransmission has a new `observationid`.
Explicit event uses establish reported attempt links; timestamp ordering
and equal event identities alone establish no derivation.

### 6.4. Snapshots, Replay and Corrections

Published trace snapshots MUST remain stable. An additional or corrected
snapshot MUST use a new document URL, retain the same `executionid` and
exact `deploymenturl`, and preserve existing role-to-participant bindings.
Newly covered roles MAY be added under the same deployment.

The first snapshot MUST omit `execution.previous`. Each later snapshot
MUST select the immediate preceding snapshot by its exact document URL and
local Trace ID. The Publisher MUST retain a finite, acyclic, serialized
chain with no ambiguous successors. These rules apply to standalone and
wrapped traces alike. Each execution MUST have one such publication chain.

A Consumer MUST deduplicate repeated observation and attempt identities
within one execution, including across snapshots. Compare an observation's
entire enclosing record and an attempt's entire object as decoded JSON:
object member order is ignored; array order and exact scalar values are
preserved. Identical repeats are one item. Different content under the
same identity MUST invalidate the snapshot as conflicting replay.
Consumers MUST reject duplicate JSON object keys.

Carried-forward evidence MUST remain unchanged by identity. A replacement
MUST have a new identity and `corrects` selecting an item of the same kind
in the immediate predecessor. Its target MUST be absent from the new
snapshot and have exactly one replacement. Every removed item MUST have
such a replacement. Identities MUST NOT be reassigned or reused, including
those replaced in earlier snapshots.

An attempt using a replaced observation MUST itself be replaced with a new
identity and updated links. Consumers MUST validate the predecessor chain
and replacement links; missing predecessors make that check incomplete.
Earlier snapshots retain their contents and validity reports. Corrections
revise evidence about an execution; retries report new action attempts.

## 7. Publication and Resolution

The Publisher MUST agree a replay or audit period and retain all selected
deployment Versions, context exports, used inherited definitions, documents,
trace snapshots and any additional Descriptors for that period.

Publication proceeds in dependency order:

1. Retain the ACF conversation and sufficient resolution context. Publish
   any additional Actor or Processing Descriptor Versions that are used.
2. Resolve and validate the deployment, then publish its Descriptor Version.
   The same deployment Version can serve many executions.
3. Capture and retain the standalone trace snapshot with actual participants,
   observations and attempts. Validate its inputs and correlations.
4. If evidence discovery or packaging is needed, publish an Execution
   Evidence Descriptor Version selecting that same snapshot.

The trace can be finalized before an Evidence Descriptor URL is assigned.
Additional or corrected evidence uses new trace snapshots and, when wrapped,
new Evidence Descriptor Versions. Shared deployment and Processing
Descriptors MUST NOT accumulate per-execution observations.

A Consumer starts with the trace, or unwraps the selected trace from an
Evidence Descriptor. It retrieves the exact deployment Version, resolves
its retained ACF context and inheritance, then checks participant bindings,
observations, attempts and predecessor links. Missing historical inputs
MUST NOT be replaced with live defaults.

Generic Descriptor bundles collect direct References only. A deployment
bundle includes its conversation and context References plus any explicitly
listed descriptions. An evidence bundle includes its trace and other direct
References. Consumers resolve the trace's typed URLs and other transitive
dependencies separately under the applicable access policy.

## 8. Failures, Replay and Conformance

A profile validator MUST distinguish at least these results:

| Result | Meaning |
| --- | --- |
| Validated-conformant | Structure, selected dependencies and every applicable semantic rule of this profile were checked and satisfied. |
| Invalid | A checked rule was violated, such as a missing binding mode, participant mismatch, wrong Reference class, unknown observation or conflicting replay. |
| Incomplete | A needed retained input is missing, denied, unavailable or exceeds a resolution limit. |
| Unsupported | A needed well-formed class, ACF construct or processing contract cannot be evaluated by this validator. |

The validator MUST report the affected selector, Reference, step or evidence
identity and reason, subject to privacy policy. It MUST NOT report
validated-conformant while any needed check is incomplete or unsupported.
A known violation remains invalid even if other checks are incomplete.
Reports SHOULD preserve all independently established findings.

These are validation results. Writes and retrieval failures use the
governing Core and HTTP error rules. A Core server storing extension metadata
need not implement this profile validator.

Profile conformance and execution outcome are separate results. Valid
evidence can report `failed`, `partial` or `unknown` attempts. Complete
execution capture, ACF control-flow conformance, delivery, business success
and trustworthy observation origins each require their own checks.

## 9. Security

Consumers MUST authenticate origins and authorize access independently for
each selected representation. Participant URIs and observation assertions
MUST be evaluated under an explicit trust and role-authorization policy,
including runtime roles. A supplied description does not authenticate its
participant. Unknown authorization or observation attribution MUST be
reported; it MUST NOT default to trusted evidence.

Reference URLs, typed extension URLs, redirects and resolved addresses are
untrusted retrieval inputs. Consumers MUST enforce origin and scheme
policy, including protection against disallowed internal services.
Credentials MUST NOT be forwarded between origins without an explicit
origin-specific policy. Retained XIDs MUST NOT trigger network discovery.

Implementations MUST bound bytes, Reference count, recursion and inherited
depth, documents, records, attempts, retrieval time and concurrency.
Cycles and limit exhaustion MUST produce explicit failures. Consumers MUST
bound decompression and decoded payload size. Generic bundle access,
caching and completeness rules still apply.

Execution identifiers, participant identities, payloads and correlation
links can expose sensitive relationships. Publishers MUST apply access,
retention and disclosure policy to metadata and documents. Redaction that
removes needed evidence makes the affected check incomplete. The validator
MUST NOT retain a validated-conformant result for that check. Publication
stability and retention remain subject to applicable privacy duties.

## 10. Complete Integration Example

[publication.json](examples/publication.json) is an offline fixture mapping
illustrative retrieval URLs to original JSON representations. Descriptor
objects are Version create inputs. The retained context omits Core response
bookkeeping and selects explicit Versions and document-view links.

| Representation | Suffix after `https://registry.example/` |
| --- | --- |
| Reusable static ACF definition | `conversationgroups/demo/conversations/normalize/versions/1` |
| Retained resolution context | `snapshots/context/1` |
| Minimal fixed deployment | `descriptorgroups/deployments/descriptors/sensor7/versions/1` |
| Runtime Sender deployment | `descriptorgroups/deployments/descriptors/fleet/versions/1` |
| Deployment with additional descriptions | `descriptorgroups/deployments/descriptors/enriched/versions/1` |
| Standalone runtime trace | `snapshots/trace/42/1` |
| Standalone fixed-participant trace | `snapshots/trace/43/1` |
| OPTIONAL wrapper of the runtime trace | `descriptorgroups/evidence/descriptors/run42/versions/1` |

The ACF Flow has Sender, Worker and Receiver roles. `RawHop` carries a raw
reading to Worker. Its `Normalize` action consumes one raw event and emits
one normalized event. `NormalizedHop` carries the result to Receiver.
The retained message definitions select the payload schemas. The example
action contract emits `celsius` equal to input `value` and permits a retry
after a failed attempt.

The fixed deployment binds all three roles by participant URI. It has no
Actor or Processing Descriptor dependency. Trace 43 uses this deployment
with a message observation and no evidence wrapper.

The fleet deployment fixes Worker and Receiver and explicitly permits
Sender to be sensor 7 or sensor 8 at runtime. Trace 42 binds sensor 7. Its
first attempt fails with no output; the retry consumes the same event and
emits the normalized event. No extra Processing Descriptor is needed.
The OPTIONAL wrapper selects this unchanged trace. Removing that wrapper
from the fixture leaves the trace fully resolvable.

The enriched deployment illustrates OPTIONAL descriptions: Worker's
`actorref` describes its exact participant, and two message opportunities
select one reusable Processing Descriptor. That Descriptor supplies an
independently managed processing note and does not repeat the message
schemas. Trace 44 demonstrates those selections through the deployment;
no repeated processing URLs or Actor Descriptors are needed in its records.

The relative source `sensor/7` retains its exact decoded value. Sent and
received observations remain separate. Receiver processing and business
outcomes require their own evidence under the applicable contract.

| Change to the examples | Result |
| --- | --- |
| Remove a role binding or its `mode`, or supply an unknown mode | Invalid deployment. |
| Change a fixed participant in a trace | Invalid actual binding. |
| Use an undeclared role or a runtime participant outside the declared set | Invalid actual binding. |
| Remove the OPTIONAL evidence wrapper | Standalone trace keeps the same meaning. |
| Select an Actor Descriptor with a different `entityid` | Invalid supplied description. |
| Supply a Processing Descriptor URL conflicting with the deployment | Invalid selection; no fallback or merge. |
| Reuse an observation or attempt ID with changed content | Invalid conflicting replay. |
| Link an attempt to an unknown observation | Invalid attempt link. |
| Remove a retained dependency | Incomplete validation. |

## 11. References

- [Descriptor Registry][Descriptor], working draft.
- [xRegistry Core](../../../core/spec.md) and
  [Core model](../../../core/model.md).
- [ACF source revision and publication scope](README.md#sources-and-publication-scope).
- [CloudEvents Core](https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md).

[Descriptor]: ../../models/descriptor/spec.md
