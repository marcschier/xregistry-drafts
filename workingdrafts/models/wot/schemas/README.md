# WoT Resolution and Processing Application Schemas

<!-- words: bytelength configurationuri jcs opc representationprofile -->
<!-- words: stableprofileuri ua workingdrafts -->

These Draft 2020-12 JSON Schemas and fixtures define this xRegistry WoT
draft's reference-resolution evidence and portable processing
descriptor/configuration formats. The draft owns these definitions; they do
not normatively import W3C WoT proposals or OPC UA specifications.

| File | Purpose |
|---|---|
| [resolution-policy.schema.json](resolution-policy.schema.json) | Root-bound, scoped policy for exact or registry-default TD/TM selection |
| [resolution-record.schema.json](resolution-record.schema.json) | Retained artifact, occurrence, transformation, and out-of-core observation record |
| [samples](../samples/resolution) | Captured default selection and replay from the retained record after the live default changes |
| [processing-profile.schema.json](processing-profile.schema.json) | Portable, non-executable processing profile descriptor |
| [processing-profile-definition.schema.json](processing-profile-definition.schema.json) | Complete fixed definition for the bounded TM property-reference operation |
| [processing-configuration.schema.json](processing-configuration.schema.json) | Root-free rules, closed xRegistry authority scope, exact/default selection, and finite limits |
| [processing-evidence.schema.json](processing-evidence.schema.json) | Disjoint local-definition and retained-resolution evidence branches plus retained-artifact manifest |
| [processing samples](../samples/processing) | Profile/configuration Resources, single-config selection, local and imported evidence |

The root-bound resolution-policy profile uses the identifier
`https://xregistry.io/workingdrafts/models/wot/profiles/reference-resolution/0.2`.
The schemas use JSON Schema 2020-12 and reference no external proposal
schema. Schema validation checks structure, not authorization, URI resolution,
pointer existence, digest correctness, artifact references, or record
approval. An implementation MUST complete those semantic checks before it
claims a successful record capture or replay.

Portable descriptor versions are opaque labels; the schemas define neither
SemVer constraints nor merge or inheritance behavior. Registry attributes
`stableprofileuri` and `configurationuri` identify logical documents only.
Invocation evidence binds each selected document to its exact Core Version
ID, where present, full file digest, document URL, and interpretation base.
The consumer explicitly selects one `own` or `shared` configuration.

The processing evidence schema is defined locally. The profile,
configuration, definition, and evidence schemas use local JSON Schema
references only; they do not fetch schemas from sibling proposals. The archive
stores retained artifact bytes as separate files. Its manifest lists their
descriptors and paths, not credentials. Schema validation does not prove that
archive files exist or match their digests, that a closure is complete, that a
configuration rule is unique, or that replay is authorized. Consumers MUST
check those semantics. Repository tests check the example evidence contract;
they do not implement a resolver.

Before replay, the caller independently pins the invocation digest and the
JCS digest of the complete evidence object. These expected digests are trust
inputs to the consumer API, not serialized members of the descriptor,
configuration, or evidence.

For file artifacts, `digest` is SHA-256 over all decoded file octets, before
parsing or normalization. `byteLength` is the decimal length of those bytes.
Native metadata artifacts use the separate `frozen-native-metadata-v1` digest
scope and MUST identify a `representationProfile` defining the complete
frozen semantic representation, lossless field mapping, and exact canonical
encoding. This digest does not claim to recover source-file bytes. The
xRegistry WoT adapter emits file artifacts only.

Three digests remain distinct:

- The attachment digest covers the exact complete policy or record file and
  is carried by an attachment that refers to the file.
- The semantic-core digest, when used, covers the profile's canonical
  representation of `core` with its defined ordering. It is not embedded in
  `core` and is not a publisher signature.
- Each artifact digest covers its declared file or frozen native
  representation. It is not a compact SchemaId or a registry Version ID.

The fixtures illustrate evidence; they do not implement a registry resolver.
In addition to schema validation, the focused repository test checks their
digest, identity, and default-drift relationships.
