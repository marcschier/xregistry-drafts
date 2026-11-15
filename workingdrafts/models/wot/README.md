# WoT Registry Service - Version 1.0-rc4

<!-- words: WoT readme -->
<!-- words: py pytest workingdrafts -->
<!-- words: workflows -->
<!-- words: planurl wotsubject marcschier -->

The [WoT Registry specification][Spec] and [model][Model] define this draft's
document storage, identity and resolution rules. The
[decision record][Decisions] explains the design decisions. The informative
[versioning design][Versioning] and [samples][Samples] provide supporting detail.

The [WoT Descriptor profile](spec.md#66-wot-descriptor-profile) specializes
the [Descriptor Registry draft](https://github.com/xregistry/spec/pull/796)
when a deployment selects it. TD and TM References identify resolved
documents; OPTIONAL `planurl` records projection provenance without replacing
the result. This profile defines the TD and TM URI class identifiers, and
[`wotsubject`](spec.md#664-subject-descriptors) selects an annotated Thing
or affordance without supplying processing metadata. The
[attribute model fragment](descriptor-profile.model.json) and
[profile schema fragment](schemas/descriptor-profile.schema.json) describe
its fields alongside the generic Descriptor model; they do not change the
WoT Registry's [model](model.json).

The [CloudEvents WoT extension draft][CloudEvents WoT]
owns event routing and subject syntax. Its direct TD route does not require a
Descriptor. The same pinned draft defines the Subject Descriptor route.
These drafts are not released specifications.

The [publication companion][Publication] defines dependency binding and set
publication using the [generic publication contract](../../publication/spec.md).
The contract covers:
- [manifest integrity][Manifest]
- [channel operations][Channel]
- [export and federation][Export]
- [domain closure][Closure]

The companion's closure schema and checks validate shape, not deployed resolver
conformance.

The [generated model schemas](../../tools/README.md) describe selected Registry
metadata in JSON Schema, JSON Structure, Avro and OpenAPI. Reproduction and
syntax checks do not establish complete model coverage; the generated
descriptions do not validate the Thing Model's Meta compatibility field.

The [33 representative vectors](tests/resolution/README.md) exercise version
assignment and reference resolution, including floors, caller pins, sticky
defaults and prerelease selection. Run
`python workingdrafts/models/wot/tests/resolution/check_vectors.py` from the
repository root. Normal pytest runs the same cases with schema validation.
The vectors do not provide exhaustive regression coverage.

[Manifest]: ../../publication/spec.md#manifest-and-integrity
[Channel]: ../../publication/spec.md#publishing-and-opening-a-channel
[Export]: ../../publication/spec.md#export-federation-and-binding-equivalence
[Closure]: ../../publication/spec.md#domain-closure-and-compatibility
[Publication]: ../../publication/design/design.md#wot-channels-snapshots-and-dependency-bindings
[Spec]: spec.md
[Model]: model.json
[Decisions]: decisions.md
[Versioning]: ../../publication/design/design.md#wot-versioning-design-overview
[Samples]: samples/README.md
[CloudEvents WoT]: https://github.com/marcschier/spec/blob/1c4caca73c69a7e076e75fe0727f6a216c83e500/cloudevents/extensions/wot.md
