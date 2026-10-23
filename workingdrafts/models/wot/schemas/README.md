# WoT Resolution and Processing Application Schemas

These Draft 2020-12 JSON Schemas and fixtures define the xRegistry WoT
domain's local reference-resolution evidence and portable processing
descriptor/configuration formats. They are owned by this working draft and
are not normative imports from W3C WoT proposals or OPC UA specifications.

| File | Purpose |
|---|---|
| [resolution-policy.schema.json](resolution-policy.schema.json) | Root-bound, scoped policy for exact or registry-default TD/TM selection |
| [resolution-record.schema.json](resolution-record.schema.json) | Retained artifact, occurrence, transformation, and out-of-core observation record |
| [samples](../samples/resolution) | Captured default selection and locked replay after the live default changes |
| [processing-profile.schema.json](processing-profile.schema.json) | Portable, non-executable processing profile descriptor |
| [processing-profile-definition.schema.json](processing-profile-definition.schema.json) | Complete fixed definition for the bounded TM property-reference operation |
| [processing-configuration.schema.json](processing-configuration.schema.json) | Root-free rules, closed xRegistry authority scope, exact/default selection, and finite limits |
| [processing-evidence.schema.json](processing-evidence.schema.json) | Disjoint local-definition and retained-resolution evidence branches plus retained-artifact manifest |
| [processing samples](../samples/processing) | Profile/configuration Resources, single-config selection, local and imported evidence |

The root-bound resolution-policy profile identifier is
`https://xregistry.io/workingdrafts/models/wot/profiles/reference-resolution/0.2`.
Both schemas use standard JSON Schema 2020-12; they do not reference an
external proposal schema. Schema validation checks shape, not authorization,
URI resolution, pointer existence, digest correctness, artifact references,
or record approval. An implementation MUST perform those semantic checks
before claiming a successful lock or replay.

Portable descriptor versions are opaque labels. The profile and configuration
schemas do not define SemVer constraints or merge/inheritance behavior. A
registry's `stableprofileuri`/`configurationuri` attributes identify document
logical identity only; consumer invocation evidence binds exact Core Version
IDs where present, complete file digests, document URLs, and interpretation
bases. A local or shared configuration is selected explicitly and alone.

The processing evidence schema is a local owner definition. The profile,
configuration, definition, and evidence schemas use only local JSON Schema
references and do not fetch sibling proposal schemas. Retained artifact bytes
are separate files in the archive; the manifest records their descriptors and
paths but does not carry credentials. Schema validation alone does not prove
that archive files exist or match digests, that a closure is complete, that a
configuration rule is unique, or that replay is authorized. Those are
consumer-side semantic checks; the repository tests validate the example
evidence contract only and do not implement a resolver.

Replay callers pin both the invocation digest and the complete evidence
object's JCS digest independently of the evidence being checked. These
expected digest values are trust inputs to a consumer API, not serialized
members of the descriptor, configuration, or evidence schemas.

For file artifacts, `digest` is the full SHA-256 of the complete decoded file
octets before parsing or normalization, and `byteLength` is the decimal
length of those exact octets. Native metadata artifacts use the separately
named `frozen-native-metadata-v1` digest scope and MUST identify a
`representationProfile` that specifies the complete frozen semantic
representation, lossless field mapping, and exact canonical encoding. They do
not claim to recover original source-file bytes. The xRegistry WoT adapter
itself emits file artifacts only.

Three digests remain distinct:

- The attachment digest covers the exact complete policy or record file and
  is carried by an attachment that refers to the file.
- The semantic-core digest, when used, covers the profile's canonical
  representation of `core` with its defined ordering. It is not embedded in
  `core` and is not a publisher signature.
- Each artifact digest covers its declared file or frozen native
  representation. It is not a compact SchemaId or a registry Version ID.

The fixtures are illustrative evidence, not an implementation of a registry
resolver. The focused repository test checks their internal digest, identity,
and default-drift relationships in addition to schema validity.
