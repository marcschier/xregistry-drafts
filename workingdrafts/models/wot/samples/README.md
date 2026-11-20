# WoT Registry Samples

<!-- words: WoT thingdescriptiongroups thingmodelgroups fabrikam wotid derivedfrom byom contoso standardsbody maturity affordance minversion versionorigin -->
<!-- words: factoryfloor inletpressure cloudevents describedby descriptorid -->
<!-- words: thingdescription thingdescriptions quantitykind affordanceselector -->
<!-- words: affordances bundleurl nonselecting planurl standalone tds -->

[registry.json](registry.json) illustrates the
[WoT Registry model](../model.json): stable authored identifiers, compatible
Versions and provenance metadata.

| Group | Content |
| --- | --- |
| `Fabrikam.Lighting` | The complete dimmable lamp Thing Model, indexed by its authored `wotid`. |
| `Fabrikam.FactoryFloor.01` | Lamp #42, with an absolute `rel: "type"` link to the lamp model and its identifier in `derivedfrom`. |
| `Contoso.Pumps` | Authored pump and device Thing Models, including two compatible pump Versions. |

The pump defaults to `1.1.0` and retains `1.0.0`. Revision `1.1.0` adds
the OPTIONAL `inletPressure` affordance without adding a mandatory member.
Both models retain their authored identifiers and references; their
`maturity` is `Vendor`, without a `standardsbody` claim.

TM `versionid` values match authored `version.model`; the lamp TD's
`versionid` matches `version.instance`. The pump's `tm:minVersion: "1.0.0"`
requires a compatible device model. The publication requests omit
`versionorigin`; the registry assigns it.

[publication-closure.json](publication-closure.json) illustrates the
[closure envelope](../../../publication/design/design.md#selection-and-acceptance).
It is not a complete snapshot. Its checks validate shape, not whether the
captured dependencies reconstruct a resolved view.

## CloudEvents document provision

The [CloudEvents WoT draft][CloudEvents WoT] defines Descriptor entry shape,
class-owned metadata, selection and failure outcomes. The registry supplies
the ordinary resolved TD/TM documents under its
[document-provision rules](../spec.md#66-provisioning-documents-for-cloudevents).
No older immutable revision is used as authority for the new format.

[cloudevents.json](cloudevents.json) contains five standalone event examples,
not a transport batch. All use `com.fabrikam.lamp.overheated.v1` and the
agreed numeric `temperature` payload contract.

| Event | Provision and selection |
| --- | --- |
| 1 | Direct TD Version URL with `#/events/overheated`; no Descriptor. |
| 2 | Direct default-Version TD URL with `#` for the whole Thing. |
| 3 | Descriptor Version URL in `subject`, using the agreed subject-driven mode. |
| 4 | Explicit `describedby` and a direct TD subject referring to the same document. |
| 5 | Descriptor Version URL in `source`, with agreed source binding and named subject-driven selection. |

The first source identifies a factory line; the actor-source events identify
the telemetry service. The fifth source intentionally identifies the
Descriptor as the originating context and has a different source-plus-id
identity scope. In an explicitly agreed Descriptor-driven mode, `subject`
can instead be omitted or remain nonselecting; CE defines that interpretation.

[subject-descriptor.json](subject-descriptor.json) uses named `entries`.
Its `lamp42` entry has class `thingdescription`, an ordinary TD document
URL, and the OPTIONAL plain JSON Pointer `affordanceselector` selecting
`/events/overheated`. This deployment defines `quantitykind` as an
absolute-URI annotation identifying the measured quantity; it is not
authorization or a universal WoT vocabulary.

The entry URL serves the resolved lamp TD at Version `1.0.0`, not Registry
metadata. Removing `affordanceselector` leaves the whole Thing available
under the class's profile rules. The CE profile determines when a chosen
entry name or a unique TD entry selects it and when repeated TDs are
ambiguous. A TM entry can bind an event type and model declaration; it does
not replace a TD's instance description.

Entry `url` can be `null` in the CE representation. These provision samples
use retrievable URLs; inline content and REQUIRED-input handling follow the
entry class's CE profile. A projection plan, when supplied through `planurl`,
is provenance for the ordinary resolved document, not a replacement for it.
Bundle assembly and `bundleurl` follow the CE contract.

For direct TD use, Consumers retrieve the fragment-free document URL and
evaluate the URI-fragment pointer locally. For a Descriptor entry, the stored
selector is a plain RFC 6901 string and is not percent-decoded. This sample's
TD declares its affordances directly; no reconstruction is needed to select
the overheated event. The samples do not claim that a Version proves content
integrity or that the closure envelope reconstructs a composed TD.

[CloudEvents WoT]: https://github.com/cloudevents/spec/pull/1406
