# WoT Registry Service - Version 1.0-rc4

<!-- words: WoT readme -->
<!-- words: py pytest workingdrafts -->
<!-- words: workflows -->
<!-- words: describedby marcschier standalone -->
<!-- words: thingdescription thingmodel -->

This unreleased working draft describes an xRegistry for Web of Things
(WoT) Thing Descriptions and Thing Models. The [specification][Spec]
defines storage, identity, and resolution. A Registry uses the
[SemVer model][Model] for Semantic Versioning or the
[incremental model](model-incremental.json) for increasing integer Versions.
The [decision record][Decisions] explains the rationale. The informative
[versioning design][Versioning] and [samples][Samples] provide supporting detail.

The [CloudEvents WoT draft][CloudEvents WoT] owns Descriptor entries,
TD/TM selection, event routing, affordance selectors and provenance fields.
The WoT Registry [provisions ordinary resolved documents](spec.md#66-provisioning-documents-for-cloudevents)
for that mapping without defining a second Descriptor format or changing
its [model](model.json). CloudEvents using the WoT mapping select the
Descriptor through `describedby`; standalone registry access is unchanged.
The [samples](samples/README.md) illustrate document URLs and Descriptor
entries.

The informative [publication design][Publication] explains dependency
binding and publication of related documents. The
[generic publication specification](../../publication/spec.md) defines the
publication contract; the [WoT closure section](spec.md#544-publication-closure)
defines the WoT-specific requirements and identifies open mapping decisions.
The contract covers:
- [manifest integrity][Manifest]
- [channel operations][Channel]
- [export and federation][Export]
- [domain closure][Closure]

The [closure schema](schemas/publication-closure.schema.json) and
[fixture checks](tests/test_wot_examples.py) check structural examples,
not deployed resolver conformance.

The [generated model schemas](../../tools/README.md) describe selected Registry
metadata in JSON Schema, JSON Structure, Avro and OpenAPI. Reproduction and
syntax checks do not establish complete model coverage; the generated
descriptions do not validate the Thing Model's Meta compatibility field.

The [33 representative vectors](tests/resolution/README.md) exercise version
assignment and reference resolution, including floors, caller pins, sticky
defaults and prerelease selection. Run
`python workingdrafts/models/wot/tests/resolution/check_vectors.py` from the
repository root. The [vector guide](tests/resolution/README.md#running-the-checker)
also gives the pytest command for running them with schema validation.
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
[CloudEvents WoT]: https://github.com/marcschier/spec/blob/6ac67d40c38e63621d32f29c9f1a0d69c2d583da/cloudevents/extensions/wot.md
