# WoT Registry Service - Version 1.0-rc4

<!-- words: WoT readme -->
<!-- words: py pytest workingdrafts -->
<!-- words: workflows -->
<!-- words: planurl -->

The [WoT Registry specification][Spec] and [model][Model] define this draft's
document storage, identity and resolution rules. The
[decision record][Decisions] explains the design decisions. The informative
[versioning design][Versioning] and [samples][Samples] provide supporting detail.

The [WoT Descriptor profile](spec.md#66-wot-descriptor-profile) specializes
the [Descriptor Registry draft](https://github.com/xregistry/spec/pull/796)
when a deployment selects it. TD and TM References identify resolved
documents; OPTIONAL `planurl` records projection provenance without replacing
the result. The [CloudEvents WoT draft][CloudEvents WoT]
owns event routing and subject syntax. Its direct TD route does not require a
Descriptor. The CloudEvents link pins the committed draft used by this profile;
neither draft is a released specification.

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
[CloudEvents WoT]: https://github.com/marcschier/spec/blob/2b122bb9ea420b24ffccb53c6e0a05c20082ac7a/cloudevents/extensions/wot.md
