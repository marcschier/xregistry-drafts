# ACF Descriptor Profiles - Working Draft

<!-- words: ACF README AttributeDefinitions standalone -->

This working draft proposes two profiles of the
[Descriptor Registry](../../models/descriptor/spec.md): a reusable
Conversation Deployment Descriptor and an OPTIONAL Execution Evidence
Descriptor for publishing snapshots. A standalone trace binding records
execution identity, the exact deployment Version, actual participants,
message observations and processing attempts.

One ACF definition can serve many deployments, and each deployment Version
can serve many executions. Participant URIs identify concrete actors
directly. Actor Descriptors and additional Processing Descriptors are
OPTIONAL. The evidence wrapper packages the same independently usable trace.
These are integration proposals, not existing ACF features or approved
xRegistry standards.

- [Specification](spec.md): normative profile rules and example.
- [Attribute definitions](attributes.json): partial Core AttributeDefinitions
  map, merged into the generic Descriptor Resource's `attributes`.
- [Structural schema](profile.schema.json): JSON Schema Draft 7 definitions
  for deployment/evidence fields and standalone trace extension values.
- [Publication example](examples/publication.json): offline fixture mapping
  exact example URLs to original JSON representations.

The generic Descriptor model and its generated schemas remain authoritative
for inherited fields. Select a schema definition explicitly, for example
`profile.schema.json#/definitions/deployment`; the schema root rejects all
instances. The definitions compose with the generic Descriptor Version
schema. Reference, role, participant, inheritance and evidence correlations
also need semantic validation.

The publication fixture includes a fixed deployment without Actor or
Processing Descriptors, an explicitly runtime-bound role, standalone traces,
OPTIONAL additional descriptions and an OPTIONAL wrapper of the same trace.

## Sources and publication scope

The draft was checked against the ACF review source at commit
`f19003251394778dfa128306ac805ff0aef7fad1`, specifically its specification,
normative JSON Structure schema and conversation resource model:

- ACF specification: `specification/acf.md`.
- ACF structure: `specification/schemas/acf-1.0.struct.json`.
- ACF resource model: `specification/models/conversation-model.json`.

These are source paths in `clemensv/acf` at the revision above. Access to
that review revision is not assumed; public source links were unavailable
when this layer was prepared.

Those sources are proprietary review-only materials; their public location
does not grant reuse or implementation rights. The requester confirmed
separate written permission from the copyright holder covering drafting
and publication of these integration profiles. That confirmation is not
a general license grant, standards approval, certification or endorsement.
This layer contains original integration prose and narrow original examples,
not redistributed ACF schemas, implementation code, figures or license text.
Readers need their own applicable rights for the underlying materials.
